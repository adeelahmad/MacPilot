# File: automation_framework/services/ai/openai_service.py

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import logging
from pydantic import BaseModel
from models.pydantic_models import (
    ActionStep,
    AnalysisResult,
    DynamicBaseModel,
    ValidationResult,
    RecoveryStep,
)
import instructor
from openai import OpenAI, OpenAIError
import os
import json
from ..shared.serialization import recursive_dict_conversion, DateTimeEncoder
from core.config import AutomationConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an advanced AI Agent Controller specializing in UI automation. Your role is to:
1. Analyze user instructions and break them down into concrete UI automation steps
2. Generate precise action sequences using available tools/actors
3. Handle UI state changes and validations
4. Provide recovery strategies when actions fail

Important Guidelines:
- Break complex tasks into atomic actions
- Use exact parameters required by each action
- Consider UI state changes between steps
- Plan for potential failures and edge cases
- Always verify action results

When generating plans, focus on:
1. Pre-conditions required for each step
2. Exact parameters needed for actions
3. Expected UI state changes
4. Verification steps
5. Potential error states and recovery paths"""


class OpenAIService:
    def __init__(self, config: AutomationConfig):
        self.config = config
        self.logger = logger
        try:
            self.client = instructor.from_openai(
                OpenAI(
                    base_url="http://0.0.0.0:8080/v1",
                    api_key=os.getenv("OPENAI_API_KEY", "sk-adminas123"),
                ),
                instructor.Mode.MD_JSON,
            )
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise

    async def analyze_instruction(
        self,
        instruction: str,
        current_state: Any,
        available_actions: Dict[str, Any],
    ) -> AnalysisResult:
        """Analyzes a user instruction and generates an AnalysisResult."""
        try:
            # Convert state to safely serializable format
            current_state_dict = recursive_dict_conversion(current_state)

            # Safely serialize with error handling
            try:
                state_json = json.dumps(
                    current_state_dict, cls=DateTimeEncoder, indent=2
                )
                actions_json = json.dumps(
                    available_actions, cls=DateTimeEncoder, indent=2
                )
            except Exception as e:
                logger.error(f"Serialization error: {e}")
                # Fallback to simplified state
                state_json = json.dumps(str(current_state_dict))
                actions_json = json.dumps(str(available_actions))

            prompt = f"""As an AI Agent Controller, analyze this automation task:

Instruction: {instruction}

Required: Create a detailed browser automation plan for seek.com.au job search that:
1. Handles browser initialization and navigation
2. Performs job search with specified parameters:
   - Keywords: AWS, DevOps
   - Location: Melbourne
3. Manages page loading and dynamic content
4. Extracts relevant job listings
5. Validates successful completion

Include specific steps for:
- Browser setup and verification
- Navigation to seek.com.au
- Search form interaction
- Results page handling
- Error recovery strategies

Generate a precise AnalysisResult with complete automation details.
"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=AnalysisResult,
            )
            return response
        except Exception as e:
            logger.exception(f"Error analyzing instruction: {e}")
            return AnalysisResult(
                goal="Error analyzing instruction",
                estimated_steps=0,
                required_actions=[
                    "chrome.open_url",
                    "chrome.type_text",
                    "chrome.click",
                ],
                constraints=["Handle browser state"],
                prerequisites=["Browser must be installed"],
            )

    async def generate_action_plan(
        self, analysis: AnalysisResult, available_actions: Dict[str, Any]
    ) -> List[ActionStep]:
        try:
            analysis_json = json.dumps(analysis.model_dump(), cls=DateTimeEncoder)
            actions_json = json.dumps(available_actions, cls=DateTimeEncoder, indent=2)

            prompt = f"""As an AI Agent Controller, create a detailed action plan:

    Analysis Results:
    {analysis_json}

    Available Tools/Actions:
    {actions_json}

    Generate a precise step-by-step action plan that:
    1. Uses exact actor and action combinations
    2. Specifies complete parameters for each action
    3. Includes state validation between steps
    4. Handles potential errors
    5. Verifies action success

    For browser automation:
    1. First actions should establish browser state:
       - Launch browser if needed
       - Verify browser is ready
       - Handle any initial dialogs/popups
    2. URL navigation steps should:
       - Include full URL
       - Wait for page load
       - Verify correct page
    3. Interaction steps should:
       - Wait for elements
       - Verify element state
       - Include precise coordinates/parameters
    4. Data extraction steps should:
       - Verify data presence
       - Include backup strategies
       - Handle pagination if needed

    Each step must include:
    1. Exact actor to use
    2. Precise action with all parameters
    3. Expected outcome
    4. Validation criteria
    5. Failure handling approach

    Response must be a List[ActionStep] with complete details for each step."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=List[ActionStep],
            )
            return response
        except Exception as e:
            logger.exception(f"Error generating action plan: {e}")
            return []

    async def validate_results(
        self,
        original_instruction: str,
        action_plan: List[ActionStep],
        execution_results: List[Dict[str, Any]],
        current_state: Dict[str, Any],
    ) -> ValidationResult:
        """Validates execution results."""
        try:
            prompt = f"""As an AI Agent Controller, validate the automation results:

    Main Goal & Instruction:
    {original_instruction}

    Executed Plan:
    {json.dumps([step.model_dump() for step in action_plan], cls=DateTimeEncoder, indent=2)}

    Execution Results:
    {json.dumps(execution_results, cls=DateTimeEncoder, indent=2)}

    Validation Requirements:
    1. Compare achieved state vs expected state
    2. Verify all critical actions completed
    3. Check for any unhandled errors
    4. Identify any missing objectives
    5. Assess overall task success

    For browser automation:
    - Verify correct final URL/page
    - Check all required data was accessed
    - Validate any extracted information
    - Identify any missing elements

    Provide comprehensive validation results including:
    1. Overall success status
    2. Specific issues found
    3. Impact of any failures
    4. Recommendations for improvement"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=ValidationResult,
            )
            return response
        except Exception as e:
            logger.exception(f"Error validating results: {e}")
            return ValidationResult(
                success=False,
                goal_achieved=False,
                issues=["Error during validation"],
                recommendations=["Retry the operation"],
            )

    async def generate_recovery_plan(
        self, step: ActionStep, failures: List[str], current_state: DynamicBaseModel
    ) -> List[RecoveryStep]:
        """Generates recovery plan for failed actions."""
        try:
            prompt = f"""As an AI Agent Controller, generate a recovery plan:

    Failed Step Details:
    {json.dumps(step.model_dump(), cls=DateTimeEncoder, indent=2)}

    Failure Information:
    {json.dumps(failures, cls=DateTimeEncoder, indent=2)}

    Current System State:
    {json.dumps(current_state.model_dump(), cls=DateTimeEncoder, indent=2)}

    Recovery Plan Requirements:
    1. Analyze failure cause
    2. Determine system state impact
    3. Create step-by-step recovery
    4. Include verification steps
    5. Handle potential cascading issues

    For browser automation recovery:
    - Check page state/URL
    - Verify element presence
    - Handle any error dialogs
    - Consider page refresh/reload
    - Plan for session recovery

    Generate specific recovery steps that:
    1. Return system to known good state
    2. Verify recovery success
    3. Resume original task flow
    4. Include additional validations
    5. Handle potential secondary failures"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=List[RecoveryStep],
            )
            return response
        except Exception as e:
            logger.exception(f"Error generating recovery plan: {e}")
            return []
