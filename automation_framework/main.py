import asyncio
import logging
from typing import Any, Dict, Optional
import json
from pathlib import Path
import click
from rich.console import Console
from rich.logging import RichHandler

from services.state.manager import StateManager
from core.metaclasses.actor_meta import ActorStackMeta
from actors.generic.mouse_keyboard import GenericActorStack
from actors.chrome.browser import ChromeActorStack
from actors.finder.filesystem import FinderActorStack
from services.instruction.processor import InstructionProcessor
from services.orchestration.orchestrator import Orchestrator
from core.config import AutomationConfig
from services.macos_ui_service.macos_ui_service import MacOSUIService
import rich
from utils.decorators import log_execution

# Setup logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

rich.traceback.install(show_locals=True, max_frames=20)

log = logging.getLogger("rich")
console = Console()


class AutomationFramework:
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the Automation Framework."""
        self.config = (AutomationConfig.from_yaml(config_path)
                       if config_path else AutomationConfig.from_env())

        # Initialize services
        self.state_manager = StateManager()
        self.instruction_processor = InstructionProcessor(self.config)
        self.macos_service = MacOSUIService.sharedService()

        # Initialize actors
        self.actors = ActorStackMeta.get_registered_actors()

        # Initialize orchestrator
        self.orchestrator = Orchestrator({
            'config': self.config,
            'state_manager': self.state_manager,
            'actors': {
                'generic': GenericActorStack(),
                'chrome': ChromeActorStack(),
                'finder': FinderActorStack()
            },
        })

    @log_execution
    async def execute_instruction(self, instruction: str) -> bool:
        """Execute a natural language instruction."""
        return await self.orchestrator.execute_instruction(instruction)

    def list_capabilities(self) -> Dict[str, Any]:
        """List all available actor capabilities."""
        return {
            name: actor.get_capabilities()
            for name, actor in self.actors.items()
        }

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'macos_service'):
            self.macos_service.release()


@click.group()
def cli():
    """macOS UI Automation Framework"""
    pass


@cli.command()
@click.argument('instruction')
@click.option('--config-file', '-c', type=Path, help='Path to YAML configuration file.')
def execute(instruction: str, config_file: Optional[Path] = None):
    """Execute an automation instruction"""
    framework = None
    try:
        framework = AutomationFramework(config_file)
        asyncio.run(framework.execute_instruction(instruction))
    except Exception as e:
        console.print(f"[red]Error: {e}")
    finally:
        if framework:
            framework.cleanup()


@cli.command()
@click.option('--config-file', '-c', type=Path, help='Path to YAML configuration file.')
def capabilities(config_file: Optional[Path] = None):
    """List all available automation capabilities"""
    framework = None
    try:
        framework = AutomationFramework(config_file)
        caps = framework.list_capabilities()
        console.print_json(json.dumps(caps, indent=2))
    except Exception as e:
        console.print(f"[red]Error: {e}")
    finally:
        if framework:
            framework.cleanup()


@cli.command()
@click.option('--output-dir', '-o', default='screenshots', help='Directory to save screenshots.')
@click.option('--focused-only', '-f', is_flag=True, help='Capture only the focused window.')
def screenshot(output_dir: str, focused_only: bool):
    """Take screenshots of applications."""
    service = None
    try:
        service = MacOSUIService.sharedService()
        service.screenshot_applications(output_dir, focused_only)
    except Exception as e:
        console.print(f"[red]Error: {e}")
    finally:
        if service:
            service.release()


if __name__ == "__main__":
    cli()
