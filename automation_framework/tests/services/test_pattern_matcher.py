import pytest
from ...services.patterns.pattern_matcher import PatternMatcher
from ...services.state.manager import StateManager


@pytest.fixture
def state_manager():
    return StateManager()


@pytest.fixture
def pattern_matcher(state_manager):
    return PatternMatcher(state_manager)
    }
    ],
    'active_app': {
        'name': 'Finder',
        'bundle_id': 'com.apple.finder'
    }
    }

    matches = await pattern_matcher.match_patterns(state)
    assert isinstance(matches, list)
    if matches:
        assert 'pattern' in matches[0]
    assert 'confidence' in matches[0]
    assert isinstance(matches[0]['confidence'], float)

           @ pytest.mark.asyncio
    async


    def test_get_window_info(pattern_matcher):
        window_info = await pattern_matcher._get_window_info()
        if window_info:
            assert 'id' in window_info
            assert 'title' in window_info
            assert 'bounds' in window_info
            assert 'app' in window_info


def test_get_active_app(pattern_matcher):
    app_info = pattern_matcher._get_active_app()
    if app_info:
        assert 'name' in app_info
        assert 'bundle_id' in app_info
        assert 'pid' in app_info
