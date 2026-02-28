import pytest
from unittest.mock import AsyncMock

from ...actors.chrome.browser import ChromeActorStack


@pytest.fixture
def chrome_actor():
    return ChromeActorStack()


@pytest.mark.asyncio
async def test_open_url(chrome_actor, monkeypatch):
    monkeypatch.setattr(chrome_actor, "_run_apple_script", AsyncMock(return_value="ok"))
    result = await chrome_actor.execute_action('open_url', url='https://www.google.com')
    assert result is True


@pytest.mark.asyncio
async def test_new_tab(chrome_actor, monkeypatch):
    monkeypatch.setattr(chrome_actor, "_run_apple_script", AsyncMock(return_value="ok"))
    result = await chrome_actor.execute_action('new_tab', url='https://www.google.com')
    assert result is True


@pytest.mark.asyncio
async def test_get_tab_count(chrome_actor, monkeypatch):
    monkeypatch.setattr(chrome_actor, "_run_apple_script", AsyncMock(return_value="2"))
    count = await chrome_actor.get_tab_count()
    assert isinstance(count, int)
    assert count > 0


@pytest.mark.asyncio
async def test_get_url(chrome_actor, monkeypatch):
    monkeypatch.setattr(chrome_actor, "_run_apple_script", AsyncMock(return_value="https://www.google.com"))
    url = await chrome_actor.execute_action('get_url')
    assert isinstance(url, str)
    assert url.startswith('http')


@pytest.mark.asyncio
async def test_execute_script(chrome_actor, monkeypatch):
    monkeypatch.setattr(chrome_actor, "_run_apple_script", AsyncMock(return_value="Google"))
    result = await chrome_actor.execute_action('execute_script', script='document.title')
    assert result is not None
