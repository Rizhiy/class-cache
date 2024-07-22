import pytest


@pytest.fixture
def test_id() -> str:
    return "class_cache.tests.id"


@pytest.fixture
def test_key() -> str:
    return "class_cache.tests.key"


@pytest.fixture
def test_value() -> list[str]:
    # Return a list to test that unhashable types can also be stored
    return ["class_cache.tests.value"]
