#!/usr/bin/env python3

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import json

from automation_state import StateCapture, SystemState, UIElementState
from automation_manager import AutomationManager, ActionRequest, ActionType, ActionResult

logger = logging.getLogger(__name__)

class AutomationTask(BaseModel):
    """Represents an automation task to be executed"""
    id: str = Field(..., description="Unique task identifier")
    description: str = Field(..., description="Human readable description")
    actions: List[ActionRequest] = Field(..., description="Sequence of actions to execute")
    timeout: float = Field(default=300.0, description="Overall task timeout in seconds")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="Retry settings for failed actions")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Rules for validating task success")
    recovery_actions: List[ActionRequest] = Field(default_factory=list, description="Actions to try on failure")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must complete first")
    
class TaskResult(BaseModel):
    """Result of executing an automation task"""
    task_id: str = Field(..., description="ID of executed task")
    success: bool = Field(..., description="Whether task completed successfully")
    start_time: datetime = Field(..., description="When task started")
    end_time: datetime = Field(..., description="When task finished")
    action_results: List[ActionResult] = Field(..., description="Results of individual actions")
    error: Optional[str] = Field(None, description="Error message if task failed")
    recovery_attempted: bool = Field(default=False, description="Whether recovery was attempted")
    state_changes: List[Dict[str, Any]] = Field(default_factory=list, description="UI state changes during task")

class AutomationCoordinator:
    """Coordinates execution of UI automation tasks"""
    
    def __init__(self):
        self.state_capturer = StateCapture()
        self.action_manager = AutomationManager()
        self.pending_tasks: Dict[str, AutomationTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.current_task: Optional[AutomationTask] = None
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
    async def add_task(self, task: AutomationTask):
        """Add task to execution queue"""
        self.pending_tasks[task.id] = task
        await self.task_queue.put(task.id)
        
    async def run(self):
        """Process automation tasks"""
        try:
            while True:
                # Get next task
                try:
                    task_id = await self.task_queue.get()
                except asyncio.QueueEmpty:
                    break
                    
                task = self.pending_tasks[task_id]
                
                # Check dependencies
                dependencies_met = True
                for dep_id in task.dependencies:
                    if dep_id not in self.completed_tasks:
                        dependencies_met = False
                        break
                        
                if not dependencies_met:
                    # Re-queue task
                    await self.task_queue.put(task_id)
                    continue
                    
                # Execute task
                result = await self._execute_task(task)
                
                # Store result
                self.completed_tasks[task_id] = result
                del self.pending_tasks[task_id]
                
                self.task_queue.task_done()
                
        except Exception as e:
            logger.error(f"Error running coordinator: {e}")
            raise
            
    async def _execute_task(self, task: AutomationTask) -> TaskResult:
        """Execute single automation task"""
        start_time = datetime.now()
        action_results = []
        state_changes = []
        
        try:
            self.current_task = task
            
            # Start state monitoring
            monitor_task = asyncio.create_task(
                self._monitor_state_changes(state_changes)
            )
            
            try:
                # Execute with timeout
                async with asyncio.timeout(task.timeout):
                    # Execute each action
                    for action in task.actions:
                        result = await self.action_manager.execute_action(action)
                        action_results.append(result)
                        
                        if not result.success:
                            raise Exception(
                                f"Action {action.type} failed: {result.error}"
                            )
                            
                        # Apply retry policy if specified
                        if not result.success and action.type in task.retry_policy:
                            policy = task.retry_policy[action.type]
                            retries = policy.get('max_retries', 3)
                            delay = policy.get('delay', 1.0)
                            
                            for attempt in range(retries):
                                logger.info(
                                    f"Retrying action {action.type} "
                                    f"({attempt + 1}/{retries})"
                                )
                                await asyncio.sleep(delay)
                                
                                result = await self.action_manager.execute_action(
                                    action
                                )
                                action_results.append(result)
                                
                                if result.success:
                                    break
                                    
                            if not result.success:
                                raise Exception(
                                    f"Action {action.type} failed after retries"
                                )
                                
                        # Validate after each action if rules specified
                        if task.validation_rules:
                            state = await self.state_capturer.capture_full_state()
                            if not self._validate_state(state, task.validation_rules):
                                raise Exception("State validation failed")
                                
                    return TaskResult(
                        task_id=task.id,
                        success=True,
                        start_time=start_time,
                        end_time=datetime.now(),
                        action_results=action_results,
                        state_changes=state_changes
                    )
                    
            except Exception as e:
                # Try recovery actions if specified
                if task.recovery_actions:
                    logger.info("Attempting task recovery")
                    recovery_results = []
                    
                    try:
                        for action in task.recovery_actions:
                            result = await self.action_manager.execute_action(action)
                            recovery_results.append(result)
                            
                            if not result.success:
                                raise Exception(
                                    f"Recovery action {action.type} failed"
                                )
                                
                        # Retry original actions after recovery
                        return await self._execute_task(task)
                        
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {recovery_error}")
                        action_results.extend(recovery_results)
                        
                return TaskResult(
                    task_id=task.id,
                    success=False,
                    start_time=start_time,
                    end_time=datetime.now(),
                    action_results=action_results,
                    error=str(e),
                    recovery_attempted=bool(task.recovery_actions),
                    state_changes=state_changes
                )
                
        finally:
            self.current_task = None
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
                
    async def _monitor_state_changes(self, changes: List[Dict[str, Any]]):
        """Monitor UI state changes during task execution"""
        try:
            async def change_callback(change):
                changes.append(change)
                logger.debug(f"State change detected: {change}")
                
            await self.state_capturer.monitor_state_changes(change_callback)
            
        except asyncio.CancelledError:
            pass
            
    def _validate_state(self, state: SystemState,
                       rules: Dict[str, Any]) -> bool:
        """Validate system state against rules"""
        try:
            # Validate window state
            if 'windows' in rules:
                window_rules = rules['windows']
                
                if 'title' in window_rules:
                    title = window_rules['title']
                    if not any(w.title == title for w in state.running_apps):
                        logger.error(f"Window '{title}' not found")
                        return False
                        
                if 'min_count' in window_rules:
                    min_count = window_rules['min_count']
                    window_count = sum(
                        len(app.windows) for app in state.running_apps
                    )
                    if window_count < min_count:
                        logger.error(
                            f"Found {window_count} windows, "
                            f"expected at least {min_count}"
                        )
                        return False
                        
            # Validate application state  
            if 'applications' in rules:
                app_rules = rules['applications']
                
                if 'required' in app_rules:
                    required_apps = app_rules['required']
                    running_apps = {
                        app.name for app in state.running_apps
                    }
                    missing_apps = set(required_apps) - running_apps
                    
                    if missing_apps:
                        logger.error(f"Missing required apps: {missing_apps}")
                        return False
                        
                if 'forbidden' in app_rules:
                    forbidden_apps = app_rules['forbidden']
                    running_apps = {
                        app.name for app in state.running_apps
                    }
                    forbidden_running = running_apps & set(forbidden_apps)
                    
                    if forbidden_running:
                        logger.error(f"Forbidden apps running: {forbidden_running}")
                        return False
                        
            # Validate UI elements
            if 'elements' in rules:
                element_rules = rules['elements']
                
                if 'required_text' in element_rules:
                    required_text = element_rules['required_text']
                    found_text = False
                    
                    for app in state.running_apps:
                        for window in app.windows:
                            for element in window.elements:
                                if element.text == required_text:
                                    found_text = True
                                    break
                            if found_text:
                                break
                        if found_text:
                            break
                            
                    if not found_text:
                        logger.error(f"Required text not found: {required_text}")
                        return False
                        
                if 'clickable_count' in element_rules:
                    min_count = element_rules['clickable_count']
                    clickable_count = sum(
                        1 for app in state.running_apps
                        for window in app.windows
                        for element in window.elements
                        if element.clickable
                    )
                    
                    if clickable_count < min_count:
                        logger.error(
                            f"Found {clickable_count} clickable elements, "
                            f"expected at least {min_count}"
                        )
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Error validating state: {e}")
            return False
            
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of completed task"""
        return self.completed_tasks.get(task_id)
        
    def get_pending_tasks(self) -> List[AutomationTask]:
        """Get list of pending tasks"""
        return list(self.pending_tasks.values())
        
    def clear_completed_tasks(self):
        """Clear history of completed tasks"""
        self.completed_tasks.clear()

async def main():
    """Example usage"""
    coordinator = AutomationCoordinator()
    
    # Create example task
    task = AutomationTask(
        id="example",
        description="Example automation task",
        actions=[
            ActionRequest(
                type=ActionType.LAUNCH_APP,
                params={'name': 'Notes'}
            ),
            ActionRequest(
                type=ActionType.TYPE,
                params={'text': 'Hello world!'}
            ),
            ActionRequest(
                type=ActionType.PRESS_KEY,
                params={'key_code': 36}  # Return key
            )
        ],
        validation_rules={
            'applications': {
                'required': ['Notes']
            },
            'elements': {
                'required_text': 'Hello world!'
            }
        }
    )
    
    # Add task and run
    await coordinator.add_task(task)
    await coordinator.run()
    
    # Get result
    result = coordinator.get_task_result("example")
    if result:
        print(f"Task completed: {'Success' if result.success else 'Failed'}")
        if result.error:
            print(f"Error: {result.error}")
        print("State changes:")
        for change in result.state_changes:
            print(f"  {change}")
            
if __name__ == "__main__":
    asyncio.run(main())
