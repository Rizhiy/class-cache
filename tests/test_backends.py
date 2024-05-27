import random

import pytest

from class_cache.backends import BaseBackend, PickleBackend, SQLiteBackend

TEST_ID = "class_cache.tests.backends.id"
TEST_KEY = "class_cache.tests.backends.key"
TEST_VALUE = "class_cache.tests.backends.value"


@pytest.mark.parametrize(("backend_type"), [PickleBackend, SQLiteBackend])
class TestCore:
    def test_basic(self, backend_type: type[BaseBackend]):
        backend = backend_type(TEST_ID)
        backend.clear()
        assert TEST_KEY not in backend
        backend[TEST_KEY] = TEST_VALUE
        assert TEST_KEY in backend
        assert backend[TEST_KEY] == TEST_VALUE
        assert len(backend) == 1
        assert list(backend) == [TEST_KEY]
        del backend[TEST_KEY]
        assert TEST_KEY not in backend

    def test_write_read(self, backend_type: type[BaseBackend]):
        write_backend = backend_type(TEST_ID)
        write_backend.clear()
        assert TEST_KEY not in write_backend
        write_backend[TEST_KEY] = TEST_VALUE

        read_backend = backend_type(TEST_ID)
        assert TEST_KEY in read_backend
        assert read_backend[TEST_KEY] == TEST_VALUE


def test_max_block_size():
    size = 256
    backend = PickleBackend(TEST_ID, 1024)
    backend.clear()
    for i in range(size):
        backend[i] = random.sample(list(range(size)), size)
    assert len(list(backend.get_all_block_ids())) > 100
