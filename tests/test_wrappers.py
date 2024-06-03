from class_cache import Cache
from class_cache.wrappers import BrotliCompressWrapper


def test_brotli_wrapper(test_id, test_key, test_value):
    cache = BrotliCompressWrapper(Cache(test_id))
    cache.clear()
    assert test_key not in cache
    cache[test_key] = test_value
    assert test_key in cache
    assert cache[test_key] == test_value
    assert len(cache) == 1
    assert list(cache) == [test_key]
    del cache[test_key]
    assert test_key not in cache
