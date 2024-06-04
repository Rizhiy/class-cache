import pytest

from class_cache import Cache
from class_cache.wrappers import BrotliCompressWrapper, ExpirationWrapper


@pytest.mark.parametrize(("wrapper_cls"), [BrotliCompressWrapper, ExpirationWrapper])
def test_wrapper(wrapper_cls, test_id, test_key, test_value):
    cache = wrapper_cls(Cache(test_id))
    cache.clear()
    assert test_key not in cache
    cache[test_key] = test_value
    assert test_key in cache
    assert cache[test_key] == test_value
    assert len(cache) == 1
    assert list(cache) == [test_key]
    del cache[test_key]
    assert test_key not in cache


# TODO: Add test that brotli actually reduces size on disk
# TODO: Add test that items actually expire in ExpirationWrapper
