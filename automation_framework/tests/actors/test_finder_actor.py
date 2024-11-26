import pytest
from ...actors.finder.filesystem import FinderActorStack
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def finder_actor():
    return FinderActorStack()


@pytest.fixture
def temp_folder():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_new_folder(finder_actor, temp_folder):
    result = await finder_actor.execute_action('new_folder', path=temp_folder, name='test_folder')
    assert result is True
    assert Path(temp_folder, 'test_folder').exists()


@pytest.mark.asyncio
async def test_list_items(finder_actor, temp_folder):
    # Create a test file
    test_file = Path(temp_folder, 'test.txt')
    test_file.touch()

    items = await finder_actor.execute_action('list_items', path=temp_folder)
    assert isinstance(items, list)
    assert len(items) > 0
    assert any(item['name'] == 'test.txt' for item in items)


@pytest.mark.asyncio
async def test_select_item(finder_actor, temp_folder):
    # Create a test file
    test_file = Path(temp_folder, 'test.txt')
    test_file.touch()

    result = await finder_actor.execute_action('select_item', path=str(test_file))
    assert result is True


@pytest.mark.asyncio
async def test_get_selection(finder_actor):
    selection = await finder_actor.execute_action('get_selection')
    assert isinstance(selection, list)
