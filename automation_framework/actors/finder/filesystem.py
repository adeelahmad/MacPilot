from typing import Dict, Any, List, Optional
import Quartz
from Cocoa import NSWorkspace, NSAppleScript
import logging
from pathlib import Path
from ..base import ActorStack
import subprocess
import json

logger = logging.getLogger(__name__)


class FinderActorStack(ActorStack):
    """Native macOS Finder control."""

    name = "finder"
    description = "Finder control using native macOS APIs"

    capabilities = {
        'open_folder': {
            'params': ['path'],
            'description': 'Open folder in Finder'
        },
        'new_folder': {
            'params': ['path', 'name'],
            'description': 'Create new folder'
        },
        'move_item': {
            'params': ['source', 'destination'],
            'description': 'Move file or folder'
        },
        'copy_item': {
            'params': ['source', 'destination'],
            'description': 'Copy file or folder'
        },
        'delete_item': {
            'params': ['path'],
            'description': 'Delete file or folder'
        },
        'select_item': {
            'params': ['path'],
            'description': 'Select item in Finder'
        },
        'get_info': {
            'params': ['path'],
            'description': 'Show Get Info window'
        },
        'search': {
            'params': ['query'],
            'description': 'Perform Finder search'
        },
        'list_items': {
            'params': ['path'],
            'description': 'List items in folder'
        },
        'get_selection': {
            'params': [],
            'description': 'Get selected items'
        }
    }

    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()

    @classmethod
    def get_capabilities(cls) -> Dict[str, Any]:
        return cls.capabilities

    async def execute_action(self, action: str, **kwargs) -> Any:
        try:
            if action == 'open_folder':
                return await self._open_folder(kwargs['path'])
            elif action == 'new_folder':
                return await self._new_folder(kwargs['path'], kwargs['name'])
            elif action == 'move_item':
                return await self._move_item(kwargs['source'], kwargs['destination'])
            elif action == 'copy_item':
                return await self._copy_item(kwargs['source'], kwargs['destination'])
            elif action == 'delete_item':
                return await self._delete_item(kwargs['path'])
            elif action == 'select_item':
                return await self._select_item(kwargs['path'])
            elif action == 'get_info':
                return await self._get_info(kwargs['path'])
            elif action == 'search':
                return await self._search(kwargs['query'])
            elif action == 'list_items':
                return await self._list_items(kwargs['path'])
            elif action == 'get_selection':
                return await self._get_selection()
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return False

    def validate_state(self) -> bool:
        # Finder is always available on macOS
        return True

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

    async def _open_folder(self, path: str) -> bool:
        path = str(Path(path).resolve())
        script = f'''
            tell application "Finder"
                open POSIX file "{path}"
                activate
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _new_folder(self, path: str, name: str) -> bool:
        path = str(Path(path).resolve())
        script = f'''
            tell application "Finder"
                make new folder at POSIX file "{path}" with properties {{name:"{name}"}}
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _move_item(self, source: str, destination: str) -> bool:
        source = str(Path(source).resolve())
        destination = str(Path(destination).resolve())
        script = f'''
            tell application "Finder"
                move POSIX file "{source}" to POSIX file "{destination}"
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _copy_item(self, source: str, destination: str) -> bool:
        source = str(Path(source).resolve())
        destination = str(Path(destination).resolve())
        script = f'''
            tell application "Finder"
                duplicate POSIX file "{source}" to POSIX file "{destination}"
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _delete_item(self, path: str) -> bool:
        path = str(Path(path).resolve())
        script = f'''
            tell application "Finder"
                delete POSIX file "{path}"
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _select_item(self, path: str) -> bool:
        path = str(Path(path).resolve())
        script = f'''
            tell application "Finder"
                select POSIX file "{path}"
                activate
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _get_info(self, path: str) -> bool:
        path = str(Path(path).resolve())
        script = f'''
            tell application "Finder"
                activate
                select POSIX file "{path}"
                tell application "System Events"
                    keystroke "i" using command down
                end tell
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _search(self, query: str) -> bool:
        script = f'''
            tell application "Finder"
                activate
                tell application "System Events"
                    keystroke "f" using command down
                    delay 0.5
                    keystroke "{query}"
                    keystroke return
                end tell
            end tell
        '''
        return await self._run_apple_script(script) is not None

    async def _list_items(self, path: str) -> List[Dict[str, Any]]:
        path = str(Path(path).resolve())
        script = f'''
            tell application "Finder"
                set itemList to {{}}
                set folderItems to items of folder (POSIX file "{path}" as alias)
                repeat with i in folderItems
                    set itemInfo to {{name:name of i, kind:kind of i}}
                    set end of itemList to itemInfo
                end repeat
                return itemList as JSON
            end tell
        '''
        result = await self._run_apple_script(script)
        return json.loads(result) if result else []

    async def _get_selection(self) -> List[Dict[str, Any]]:
        script = '''
            tell application "Finder"
                set selItems to {}
                repeat with i in (selection as list)
                    set itemInfo to {name:name of i, kind:kind of i}
                    set end of selItems to itemInfo
                end repeat
                return selItems as JSON
            end tell
        '''
        result = await self._run_apple_script(script)
        return json.loads(result) if result else []
