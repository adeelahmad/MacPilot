from typing import Dict, Any, Optional, List
import Quartz
from Cocoa import NSWorkspace, NSAppleScript
import logging
import subprocess
import json
from pathlib import Path
from ..base import ActorStack
from models.pydantic_models import ValidationResult

logger = logging.getLogger(__name__)


class ChromeActorStack(ActorStack):
    """Native macOS Chrome browser control."""

    name = "chrome"
    description = "Chrome browser control using native macOS APIs"

    capabilities = {
        'open_url': {
            'params': ['url'],
            'description': 'Open URL in Chrome'
        },
        'new_tab': {
            'params': ['url'],
            'description': 'Open URL in new tab'
        },
        'close_tab': {
            'params': [],
            'description': 'Close active tab'
        },
        'switch_tab': {
            'params': ['index'],
            'description': 'Switch to tab by index'
        },
        'refresh': {
            'params': [],
            'description': 'Refresh active tab'
        },
        'go_back': {
            'params': [],
            'description': 'Navigate back'
        },
        'go_forward': {
            'params': [],
            'description': 'Navigate forward'
        },
        'download_file': {
            'params': ['url', 'destination'],
            'description': 'Download file to destination'
        },
        'get_url': {
            'params': [],
            'description': 'Get current URL'
        },
        'execute_script': {
            'params': ['script'],
            'description': 'Execute JavaScript in active tab'
        }
    }

    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()

    @classmethod
    def get_capabilities(cls) -> Dict[str, Any]:
        return cls.capabilities

    async def execute_action(self, action: str, **kwargs) -> Any:
        try:
            if action == 'open_url':
                return await self._open_url(kwargs['url'])
            elif action == 'new_tab':
                return await self._new_tab(kwargs['url'])
            elif action == 'close_tab':
                return await self._close_tab()
            elif action == 'switch_tab':
                return await self._switch_tab(kwargs['index'])
            elif action == 'refresh':
                return await self._refresh()
            elif action == 'go_back':
                return await self._go_back()
            elif action == 'go_forward':
                return await self._go_forward()
            elif action == 'download_file':
                return await self._download_file(
                    kwargs['url'],
                    kwargs['destination']
                )
            elif action == 'get_url':
                return await self._get_url()
            elif action == 'execute_script':
                return await self._execute_script(kwargs['script'])
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return False

    def validate_state(self) -> bool:
        try:
            # Check if Chrome is installed
            apps = self.workspace.URLForApplicationWithBundleIdentifier_(
                "com.google.Chrome"
            )
            return apps is not None
        except Exception:
            return False

    async def _run_apple_script(self, script: str) -> Optional[str]:
        """Run AppleScript and return result."""
        try:
            ns_script = NSAppleScript.alloc().initWithSource_(script)
            result, error = ns_script.executeAndReturnError_(None)
            if error:
                logger.error(f"AppleScript error: {error}")
                return None
            return result.stringValue() if result else None
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            return None

    async def _open_url(self, url: str) -> bool:
        script = f'''
            tell application "Google Chrome"
                activate
                open location "{url}"
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _new_tab(self, url: str) -> bool:
        script = f'''
            tell application "Google Chrome"
                tell window 1
                    make new tab with properties {{URL:"{url}"}}
                end tell
                activate
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _close_tab(self) -> bool:
        script = '''
            tell application "Google Chrome"
                tell front window
                    close active tab
                end tell
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _switch_tab(self, index: int) -> bool:
        script = f'''
            tell application "Google Chrome"
                tell window 1
                    set active tab index to {index}
                end tell
                activate
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _refresh(self) -> bool:
        script = '''
            tell application "Google Chrome"
                tell front window
                    reload active tab
                end tell
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _go_back(self) -> bool:
        script = '''
            tell application "Google Chrome"
                tell front window
                    tell active tab
                        execute javascript "history.back();"
                    end tell
                end tell
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _go_forward(self) -> bool:
        script = '''
            tell application "Google Chrome"
                tell front window
                    tell active tab
                        execute javascript "history.forward();"
                    end tell
                end tell
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _download_file(self, url: str, destination: str) -> bool:
        # Use Chrome's download manager through JavaScript
        script = f'''
            tell application "Google Chrome"
                tell front window
                    tell active tab
                        execute javascript "
                            let link = document.createElement('a');
                            link.href = '{url}';
                            link.download = '{Path(destination).name}';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                        "
                    end tell
                end tell
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _get_url(self) -> Optional[str]:
        script = '''
            tell application "Google Chrome"
                tell front window
                    get URL of active tab
                end tell
            end tell
        '''
        return await self._run_apple_script(script)

    async def _execute_script(self, js_script: str) -> Optional[str]:
        # Escape quotes in JavaScript
        js_script = js_script.replace('"', '\\"')
        script = f'''
            tell application "Google Chrome"
                tell front window
                    tell active tab
                        execute javascript "{js_script}"
                    end tell
                end tell
            end tell
        '''
        return await self._run_apple_script(script)

    async def get_tab_count(self) -> int:
        """Get number of tabs in front window."""
        script = '''
            tell application "Google Chrome"
                tell front window
                    get number of tabs
                end tell
            end tell
        '''
        result = await self._run_apple_script(script)
        return int(result) if result else 0

    async def get_window_count(self) -> int:
        """Get number of Chrome windows."""
        script = '''
            tell application "Google Chrome"
                get number of windows
            end tell
        '''
        result = await self._run_apple_script(script)
        return int(result) if result else 0

    async def get_tab_info(self) -> List[Dict[str, str]]:
        """Get information about all tabs in front window."""
        script = '''
            tell application "Google Chrome"
                tell front window
                    set tabInfo to {}
                    repeat with t in tabs
                        set end of tabInfo to {title:title of t, URL:URL of t}
                    end repeat
                    return tabInfo as JSON
                end tell
            end tell
        '''
        result = await self._run_apple_script(script)
        return json.loads(result) if result else []

    async def validate_state(self, current_state: Dict[str, Any], expected_state: Dict[str, Any]) -> ValidationResult:
        """Validate Chrome-specific state."""
        failures = []
        warnings = []

        try:
            # Basic state check
            if not await self.validate_browser_state():
                failures.append("Browser not in valid state")

            # Check expected state if provided
            if expected_state:
                if 'url' in expected_state:
                    current_url = await self._get_url()
                    if not current_url or not current_url.startswith(expected_state['url']):
                        failures.append(f"URL mismatch: expected {expected_state['url']}, got {current_url}")

            return ValidationResult(
                success=len(failures) == 0,
                failures=failures,
                warnings=warnings
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                failures=[f"Validation error: {str(e)}"],
                warnings=[]
            )
