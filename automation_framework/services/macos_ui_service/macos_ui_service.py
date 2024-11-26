import Quartz
from Cocoa import (
    NSWorkspace,
    NSScreen,
    NSEvent,
    NSApplication,
    NSApp,
    NSImage,
    NSBitmapImageRep,
    NSData,
    NSMakeRect,
    NSObject,
    NSNotificationCenter
)
import Vision
import objc
import logging
from typing import List, Dict, Any, Optional, Tuple
import Foundation
import AppKit
from PIL import Image
import numpy as np
import os
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)


class AppObserver(NSObject):
    def initWithCallback_(self, callback):
        self = objc.super(AppObserver, self).init()
        if self is None:
            return None
        self.callback = callback
        return self

    @objc.python_method
    def init(self):
        raise TypeError("Use initWithCallback_: instead")

    def handleAppActivation_(self, notification):
        try:
            app = notification.userInfo()["NSWorkspaceApplicationKey"]
            if self.callback:
                self.callback(app.localizedName())
        except Exception as e:
            logger.error(f"Error handling app activation: {e}")


class MacOSUIService(NSObject):
    """Core service for interacting with macOS UI elements."""

    @classmethod
    def sharedService(cls):
        """Singleton accessor."""
        global _sharedService

        if not getattr(cls, '_sharedService', None):
            cls._sharedService = cls.alloc().init()
        return cls._sharedService

    def init(self):
        """Initialize the service."""
        self = objc.super(MacOSUIService, self).init()
        if self is None:
            return None

        self.workspace = NSWorkspace.sharedWorkspace()
        self.screen = NSScreen.mainScreen()

        def app_callback(app_name):
            logger.info(f"Application activated: {app_name}")

        # Create and setup observer
        self.observer = AppObserver.alloc().initWithCallback_(app_callback)
        center = self.workspace.notificationCenter()

        center.addObserver_selector_name_object_(
            self.observer,
            objc.selector(self.observer.handleAppActivation_, signature=b"v@:@"),
            "NSWorkspaceDidActivateApplicationNotification",
            None
        )

        return self

    @objc.python_method
    def screenshot_applications(self, output_dir: str = "screenshots",
                                focused_only: bool = False):
        """Take screenshots of applications."""
        try:
            # Create timestamped subdir
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            subdir = os.path.join(output_dir, timestamp)
            os.makedirs(subdir, exist_ok=True)

            # Save clipboard content
            clipboard_file = os.path.join(subdir, "clipboard.txt")
            self._save_clipboard(clipboard_file)

            # Get window list
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly |
                Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID
            )

            if focused_only:
                # Get focused window
                focused_window = self._get_focused_window(window_list)
                if focused_window:
                    self._capture_window(focused_window, subdir)
                else:
                    logger.warning("No focused window found")
            else:
                # Capture all windows
                for window in window_list:
                    self._capture_window(window, subdir)

        except Exception as e:
            logger.error(f"Error taking screenshots: {e}")

    @objc.python_method
    def _save_clipboard(self, file_path: str):
        """Save clipboard content to file."""
        try:
            script = '''
                tell application "System Events"
                    return the clipboard as text
                end tell
            '''
            result = self._run_applescript(script)
            if result:
                with open(file_path, "w") as f:
                    f.write(result)
                logger.info(f"Saved clipboard content to {file_path}")
        except Exception as e:
            logger.error(f"Error saving clipboard: {e}")
            # Create empty file
            with open(file_path, "w") as f:
                f.write("No clipboard content available")

    @objc.python_method
    def _get_focused_window(self, window_list) -> Optional[Dict]:
        """Get the focused window info."""
        try:
            app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
            if not app:
                return None

            focused_pid = app.processIdentifier()

            for window in window_list:
                if window.get("kCGWindowOwnerPID") == focused_pid:
                    return window
            return None

        except Exception as e:
            logger.error(f"Error getting focused window: {e}")
            return None

    @objc.python_method
    def _capture_window(self, window: Dict, output_dir: str):
        """Capture screenshot of a window."""
        try:
            # Get window properties
            window_id = window.get("kCGWindowNumber", 0)
            app_name = window.get("kCGWindowOwnerName", "").replace("/", "_").replace(" ", "_")

            # Create image
            image_ref = Quartz.CGWindowListCreateImage(
                Quartz.CGRectNull,
                Quartz.kCGWindowListOptionIncludingWindow,
                window_id,
                Quartz.kCGWindowImageDefault
            )

            if image_ref:
                try:
                    # Convert to NSImage
                    width = Quartz.CGImageGetWidth(image_ref)
                    height = Quartz.CGImageGetHeight(image_ref)

                    ns_image = NSImage.alloc().initWithCGImage_size_(
                        image_ref,
                        NSMakeRect(0, 0, width, height).size
                    )

                    # Save as PNG
                    if ns_image:
                        file_path = os.path.join(output_dir, f"{app_name}_{window_id}.png")

                        try:
                            # Get PNG data
                            tiff_data = ns_image.TIFFRepresentation()
                            bitmap_rep = NSBitmapImageRep.imageRepWithData_(tiff_data)
                            png_data = bitmap_rep.representationUsingType_properties_(
                                AppKit.NSBitmapImageFileTypePNG,
                                None
                            )

                            # Write to file
                            png_data.writeToFile_atomically_(file_path, True)
                            logger.info(f"Saved screenshot to {file_path}")

                        except Exception as e:
                            logger.error(f"Error saving PNG: {e}")
                        finally:
                            del png_data
                            del bitmap_rep
                            del tiff_data

                finally:
                    # Cleanup
                    del ns_image
                    Quartz.CGImageRelease(image_ref)

        except Exception as e:
            logger.error(f"Error capturing window: {e}")

    @objc.python_method
    def _run_applescript(self, script: str) -> Optional[str]:
        """Run AppleScript and return result."""
        try:
            ns_script = AppKit.NSAppleScript.alloc().initWithSource_(script)
            result, error = ns_script.executeAndReturnError_(None)

            if error:
                logger.error(f"AppleScript error: {error}")
                return None

            return result.stringValue() if result else None

        except Exception as e:
            logger.error(f"Error running AppleScript: {e}")
            return None

    def dealloc(self):
        """Clean up observers."""
        try:
            if hasattr(self, 'observer'):
                center = self.workspace.notificationCenter()
                center.removeObserver_(self.observer)
                del self.observer
        finally:
            objc.super(MacOSUIService, self).dealloc()
