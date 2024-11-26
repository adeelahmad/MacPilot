
class AutomationManager:
    """Manages UI automation actions"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.pending_actions: List[ActionRequest] = []
        self.action_history: List[ActionResult] = []
        self.current_action: Optional[ActionRequest] = None
    
    async def execute_action(self, action: ActionRequest) -> ActionResult:
        """Execute an automation action"""
        start_time = datetime.now()
        
        try:
            self.current_action = action
            
            # Execute with retries
            for attempt in range(action.retries):
                try:
                    if await self._execute_single_action(action):
                        return ActionResult(
                            type=action.type,
                            success=True,
                            duration=(datetime.now() - start_time).total_seconds(),
                            details={'attempt': attempt + 1}
                        )
                
                except asyncio.TimeoutError:
                    if attempt < action.retries - 1:
                        logger.warning(
                            f"Action {action.type} timed out, retrying "
                            f"({attempt + 1}/{action.retries})"
                        )
                        continue
                    raise
                
                except Exception as e:
                    if attempt < action.retries - 1:
                        logger.warning(
                            f"Action {action.type} failed, retrying "
                            f"({attempt + 1}/{action.retries}): {e}"
                        )
                        
                        # Try recovery script if specified
                        if action.recovery_script:
