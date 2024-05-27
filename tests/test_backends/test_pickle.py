import random

from class_cache.backends import PickleBackend

TEST_ID = "class_cache.tests.backends.id"
TEST_KEY = "class_cache.tests.backends.key"
TEST_VALUE = "class_cache.tests.backends.value"


def test_basic():
    backend = PickleBackend(TEST_ID)
    backend.clear()
    assert TEST_KEY not in backend
    backend[TEST_KEY] = TEST_VALUE
    assert TEST_KEY in backend
    assert backend[TEST_KEY] == TEST_VALUE
    del backend[TEST_KEY]
    assert TEST_KEY not in backend


def test_write_read():
    write_backend = PickleBackend(TEST_ID)
    write_backend.clear()
    assert TEST_KEY not in write_backend
    write_backend[TEST_KEY] = TEST_VALUE

    del write_backend  # Need to do this for weak_lru_cache to work

    read_backend = PickleBackend(TEST_ID)
    assert TEST_KEY in read_backend
    assert read_backend[TEST_KEY] == TEST_VALUE


def test_max_block_size():
    size = 256
    backend = PickleBackend(TEST_ID, 1024)
    backend.clear()
    for i in range(size):
        backend[i] = random.sample(list(range(size)), size)
    assert len(list(backend.get_all_block_ids())) > 100
