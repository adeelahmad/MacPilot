import pytest
from ...services.macos_ui_service.macos_ui_service import MacOSUIService
import os
import tempfile
import shutil
from PIL import Image


@pytest.fixture
def macos_service():
    service = MacOSUIService.alloc().init()
    yield service
    service.dealloc()


@pytest.fixture
def temp_dir():
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


def test_screenshot_focused_only(macos_service, temp_dir):
    """Test taking screenshot of focused window."""
    macos_service.screenshot_applications(temp_dir, focused_only=True)
    files = os.listdir(temp_dir)
    assert len(files) > 0
    assert any(f.endswith('.png') for f in files)
    assert 'clipboard.txt' in files


def test_screenshot_all_windows(macos_service, temp_dir):
    """Test taking screenshots of all windows."""
    macos_service.screenshot_applications(temp_dir, focused_only=False)
    files = os.listdir(temp_dir)
    assert len(files) > 0
    assert any(f.endswith('.png') for f in files)
    assert 'clipboard.txt' in files


def test_clipboard_saving(macos_service, temp_dir):
    """Test clipboard content saving."""
    clipboard_file = os.path.join(temp_dir, 'clipboard.txt')
    macos_service._save_clipboard(clipboard_file)
    assert os.path.exists(clipboard_file)
    with open(clipboard_file) as f:
        content = f.read()
    assert isinstance(content, str)
