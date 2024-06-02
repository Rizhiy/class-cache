from class_cache.backends import PickleBackend
from class_cache.wrappers import BrotliCompressWrapper


def test_brotli_wrapper(test_id, test_key, test_value):
    backend = BrotliCompressWrapper(PickleBackend(test_id))
    backend.clear()
    assert test_key not in backend
    backend[test_key] = test_value
    assert test_key in backend
    assert backend[test_key] == test_value
    assert len(backend) == 1
    assert list(backend) == [test_key]
    del backend[test_key]
    assert test_key not in backend
