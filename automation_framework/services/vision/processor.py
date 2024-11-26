import asyncio
from typing import List, Dict, Any, Tuple, Optional
import Quartz
from PIL import Image
import numpy as np
import objc
import Vision
import logging
import AppKit
from Cocoa import NSWorkspace, NSScreen
from core.config import AutomationConfig

logger = logging.getLogger(__name__)


class VisionProcessor:
    """Vision framework processor for UI analysis."""

    def __init__(self):
        self.config = AutomationConfig.from_env()
        self.workspace = NSWorkspace.sharedWorkspace()
        self.screen = NSScreen.mainScreen()
        self._setup_vision()

    def _setup_vision(self):
        """Setup Vision framework requests."""
        self.text_request = Vision.VNRecognizeTextRequest.alloc().init()
        self.text_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

        self.element_request = Vision.VNDetectTextRectanglesRequest.alloc().init()
        self.element_request.setReportCharacterBoxes_(True)

    async def capture_screen(self) -> Optional[Image.Image]:
        """Capture screen content."""
        try:
            frame = self.screen.frame()
            image = Quartz.CGWindowListCreateImage(
                Quartz.CGRectMake(0, 0, frame.size.width, frame.size.height),
                Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID,
                Quartz.kCGWindowImageDefault
            )

            if image:
                return self._cgimage_to_pil(image)
            return None

        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None

    async def capture_window(self, window_id: int) -> Optional[Image.Image]:
        """Capture specific window content."""
        try:
            image = Quartz.CGWindowListCreateImage(
                Quartz.CGRectNull,
                Quartz.kCGWindowListOptionIncludingWindow,
                window_id,
                Quartz.kCGWindowImageDefault
            )

            if image:
                return self._cgimage_to_pil(image)
            return None

        except Exception as e:
            logger.error(f"Error capturing window: {e}")
            return None

    async def detect_ui_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Detect UI elements using Vision framework."""
        if image is None:
            logger.error("Received None image for UI element detection")
            return []

        try:
            # Convert to CGImage
            cg_image = self._pil_to_cgimage(image)
            if not cg_image:
                return []

            # Create Vision handler
            handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
                cg_image,
                None
            )

            # Perform requests
            success = handler.performRequests_error_([
                self.text_request,
                self.element_request
            ], None)

            if not success:
                return []

            elements = []

            # Process text results
            for observation in self.text_request.results():
                bbox = observation.boundingBox()
                confidence = observation.confidence()

                if confidence > 0.5:  # Filter low confidence results
                    elements.append({
                        'text': observation.text(),
                        'bounds': {
                            'x': bbox.origin.x,
                            'y': bbox.origin.y,
                            'width': bbox.size.width,
                            'height': bbox.size.height
                        },
                        'type': 'text',
                        'confidence': confidence,
                        'attributes': {
                            'recognized_text': observation.text(),
                            'confidence': confidence
                        },
                        'clickable': self._is_element_clickable(bbox)
                    })

            # Process rectangle results
            for observation in self.element_request.results():
                bbox = observation.boundingBox()
                elements.append({
                    'text': None,
                    'bounds': {
                        'x': bbox.origin.x,
                        'y': bbox.origin.y,
                        'width': bbox.size.width,
                        'height': bbox.size.height
                    },
                    'type': 'rectangle',
                    'confidence': 1.0,
                    'attributes': {
                        'character_boxes': observation.characterBoxes()
                    },
                    'clickable': self._is_element_clickable(bbox)
                })

            return elements

        except Exception as e:
            logger.error(f"Error detecting UI elements: {e}")
            return []

    def _pil_to_cgimage(self, pil_image: Image.Image) -> Optional[Quartz.CGImageRef]:
        """Convert PIL Image to CGImage."""
        try:
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            # Get raw bytes
            bitmap = pil_image.tobytes()

            # Create CGImage
            data_provider = Quartz.CGDataProviderCreateWithData(
                None,
                bitmap,
                len(bitmap),
                None
            )

            color_space = Quartz.CGColorSpaceCreateDeviceRGB()

            return Quartz.CGImageCreate(
                pil_image.width,
                pil_image.height,
                8,  # Bits per component
                32,  # Bits per pixel
                pil_image.width * 4,  # Bytes per row
                color_space,
                Quartz.kCGImageAlphaPremultipliedLast,
                data_provider,
                None,
                True,
                Quartz.kCGRenderingIntentDefault
            )

        except Exception as e:
            logger.error(f"Error converting PIL to CGImage: {e}")
            return None

    def _cgimage_to_pil(self, cg_image: Quartz.CGImageRef) -> Optional[Image.Image]:
        """Convert CGImage to PIL Image."""
        try:
            width = Quartz.CGImageGetWidth(cg_image)
            height = Quartz.CGImageGetHeight(cg_image)
            bytes_per_row = Quartz.CGImageGetBytesPerRow(cg_image)

            pixel_data = Quartz.CGDataProviderCopyData(
                Quartz.CGImageGetDataProvider(cg_image)
            )

            np_array = np.frombuffer(pixel_data, dtype=np.uint8)
            np_array = np_array.reshape((height, bytes_per_row // 4, 4))

            return Image.fromarray(np_array)

        except Exception as e:
            logger.error(f"Error converting CGImage to PIL: {e}")
            return None

    def _is_element_clickable(self, bounds: Vision.VNRectangleObservation) -> bool:
        """Determine if element is likely clickable based on size."""
        min_size = 20  # Minimum clickable size in pixels
        return bounds.size.width >= min_size and bounds.size.height >= min_size

    async def get_window_info(self, window_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed window information."""
        try:
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionIncludingWindow,
                window_id
            )

            if window_list and len(window_list) > 0:
                window = window_list[0]
                return {
                    'id': window.get(Quartz.kCGWindowNumber, 0),
                    'title': window.get(Quartz.kCGWindowName, ""),
                    'bounds': window.get(Quartz.kCGWindowBounds, {}),
                    'layer': window.get(Quartz.kCGWindowLayer, 0),
                    'alpha': window.get(Quartz.kCGWindowAlpha, 1.0),
                    'memory': window.get(Quartz.kCGWindowMemoryUsage, 0),
                    'sharingState': window.get(Quartz.kCGWindowSharingState, 0)
                }
            return None

        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return None
