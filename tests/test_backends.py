import random
from concurrent import futures

import pytest

from class_cache.backends import BaseBackend, BrotliCompressWrapper, PickleBackend, SQLiteBackend

TEST_ID = "class_cache.tests.backends.id"
TEST_KEY = "class_cache.tests.backends.key"
TEST_VALUE = "class_cache.tests.backends.value"

MAX_WORKERS = 16
INCREASE_AMOUNT = 32


def _increase_cache(backend_type: type[BaseBackend], offset: int):
    backend = backend_type()
    for idx in range(INCREASE_AMOUNT):
        num = offset + idx
        backend[num] = str(num)


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

    @pytest.mark.parametrize("executor_cls", [futures.ThreadPoolExecutor, futures.ProcessPoolExecutor])
    def test_parallel(self, backend_type, executor_cls):
        backend = backend_type()
        backend.clear()
        with executor_cls(max_workers=MAX_WORKERS) as executor:
            results = [
                executor.submit(_increase_cache, backend_type, idx * INCREASE_AMOUNT) for idx in range(MAX_WORKERS)
            ]
            futures.wait(results)
        total_required = MAX_WORKERS * INCREASE_AMOUNT
        assert len(backend) == total_required
        for idx in range(total_required):
            assert backend[idx] == str(idx)


def test_brotli_wrapper():
    backend = BrotliCompressWrapper(backend_type=PickleBackend)
    backend.clear()
    assert TEST_KEY not in backend
    backend[TEST_KEY] = TEST_VALUE
    assert TEST_KEY in backend
    assert backend[TEST_KEY] == TEST_VALUE
    assert len(backend) == 1
    assert list(backend) == [TEST_KEY]
    del backend[TEST_KEY]
    assert TEST_KEY not in backend


def test_max_block_size():
    size = 256
    backend = PickleBackend(TEST_ID, 1024)
    backend.clear()
    for i in range(size):
        backend[i] = random.sample(list(range(size)), size)
    assert len(list(backend.get_all_block_ids())) > 100
