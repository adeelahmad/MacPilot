# automation_framework/examples/orchestration_example.py
# Revision No: 001
# Goals: Demonstrate orchestration usage.
# Type of Code Response: Add new code

import asyncio
import logging
from automation_framework.services.orchestration.orchestrator import Orchestrator
from automation_framework.services.state.manager import StateManager
from automation_framework.actors.generic.mouse_keyboard import GenericActorStack
from automation_framework.actors.chrome.browser import ChromeActorStack
from automation_framework.actors.finder.filesystem import FinderActorStack
from automation_framework.core.config import AutomationConfig
from pathlib import Path

logging.basicConfig(level=logging.INFO)


async def main():
    # Initialize components
    config = AutomationConfig.from_env()  # Use config from environment
    state_manager = StateManager()
    actors = {
        'generic': GenericActorStack(),
        'chrome': ChromeActorStack(),
        'finder': FinderActorStack()
    }

    orchestrator_config = {
        'config': config,  # Pass config object
        'state_manager': state_manager,
        'actors': actors,
    }

    orchestrator = Orchestrator(orchestrator_config)

    # Example instructions
    instructions = [
        "Open Chrome and go to google.com",
        "Search for 'Python automation'",
        "Click the first link",
        "In Finder, create a new folder named 'Automation Results' on the Desktop",
        "Download the current page as a PDF and save it to the 'Automation Results' folder on your Desktop"
    ]

    for instruction in instructions:
        try:
            success = await orchestrator.execute_instruction(instruction)
            if success:
                print(f"Instruction '{instruction}' completed successfully.")
            else:
                print(f"Instruction '{instruction}' failed.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())

# Dependencies: asyncio, logging, automation_framework.services.orchestration.orchestrator, \
#               automation_framework.services.state.manager, automation_framework.actors.generic.mouse_keyboard, \
#               automation_framework.actors.chrome.browser, automation_framework.actors.finder.filesystem, \
#               automation_framework.core.config, pathlib
# Required Actions: None
# CLI Commands: Run with `python orchestration_example.py`
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
