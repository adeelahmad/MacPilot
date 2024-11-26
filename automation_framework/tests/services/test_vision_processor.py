import pytest
from ...services.vision.processor import VisionProcessor
from PIL import Image
import numpy as np


@pytest.fixture
def vision_processor():
    return VisionProcessor()


@pytest.mark.asyncio
async def test_capture_screen(vision_processor):
    screenshot = await vision_processor.capture_screen()
    assert isinstance(screenshot, Image.Image)
    assert screenshot.size[0] > 0
    assert screenshot.size[1] > 0


@pytest.mark.asyncio
async def test_detect_ui_elements(vision_processor):
    # Create a test image
    test_image = Image.new('RGB', (800, 600), color='white')

    # Detect elements
    elements = await vision_processor.detect_ui_elements(test_image)
    assert isinstance(elements, list)


@pytest.mark.asyncio
async def test_get_window_info(vision_processor):
    # Test with the frontmost window
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )

    if window_list and len(window_list) > 0:
        window_id = window_list[0].get(Quartz.kCGWindowNumber, 0)
        info = await vision_processor.get_window_info(window_id)
        assert isinstance(info, dict)
        assert 'id' in info
        assert 'title' in info
        assert 'bounds' in info


def test_image_conversion(vision_processor):
    # Create test image
    pil_image = Image.new('RGB', (100, 100), color='white')

    # Convert to CGImage
    cg_image = vision_processor._pil_to_cgimage(pil_image)
    assert cg_image is not None

    # Convert back to PIL
    converted_image = vision_processor._cgimage_to_pil(cg_image)
    assert isinstance(converted_image, Image.Image)
    assert converted_image.size == pil_image.size
