import pytest
from ...actors.finder.filesystem import FinderActorStack
from pathlib import Path
import tempfile
import shutil
from unittest.mock import AsyncMock


@pytest.fixture
def finder_actor():
    return FinderActorStack()


@pytest.fixture
def temp_folder():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_new_folder(finder_actor, temp_folder, monkeypatch):
    monkeypatch.setattr(finder_actor, "_run_apple_script", AsyncMock(return_value="ok"))
    result = await finder_actor.execute_action('new_folder', path=temp_folder, name='test_folder')
    assert result is True


@pytest.mark.asyncio
async def test_list_items(finder_actor, temp_folder, monkeypatch):
    # Create a test file
    test_file = Path(temp_folder, 'test.txt')
    test_file.touch()

    monkeypatch.setattr(
        finder_actor,
        "_list_items",
        AsyncMock(return_value=[{"name": "test.txt", "kind": "text"}]),
    )
    items = await finder_actor.execute_action('list_items', path=temp_folder)
    assert isinstance(items, list)
    assert len(items) > 0
    assert any(item['name'] == 'test.txt' for item in items)


@pytest.mark.asyncio
async def test_select_item(finder_actor, temp_folder, monkeypatch):
    # Create a test file
    test_file = Path(temp_folder, 'test.txt')
    test_file.touch()

    monkeypatch.setattr(finder_actor, "_run_apple_script", AsyncMock(return_value="ok"))
    result = await finder_actor.execute_action('select_item', path=str(test_file))
    assert result is True


@pytest.mark.asyncio
async def test_get_selection(finder_actor, monkeypatch):
    monkeypatch.setattr(finder_actor, "_get_selection", AsyncMock(return_value=[]))
    selection = await finder_actor.execute_action('get_selection')
    assert isinstance(selection, list)
