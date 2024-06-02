import random
from concurrent import futures

import pytest

from class_cache.backends import BaseBackend, PickleBackend, SQLiteBackend

MAX_WORKERS = 16
INCREASE_AMOUNT = 32


def _increase_cache(backend_type: type[BaseBackend], offset: int):
    backend = backend_type()
    for idx in range(INCREASE_AMOUNT):
        num = offset + idx
        backend[num] = str(num)


@pytest.mark.parametrize(("backend_type"), [PickleBackend, SQLiteBackend])
class TestCore:
    def test_basic(self, test_id, test_key, test_value, backend_type: type[BaseBackend]):
        backend = backend_type(test_id)
        backend.clear()
        assert test_key not in backend
        backend[test_key] = test_value
        assert test_key in backend
        assert backend[test_key] == test_value
        assert len(backend) == 1
        assert list(backend) == [test_key]
        del backend[test_key]
        assert test_key not in backend

    def test_write_read(self, test_id, test_key, test_value, backend_type: type[BaseBackend]):
        write_backend = backend_type(test_id)
        write_backend.clear()
        assert test_key not in write_backend
        write_backend[test_key] = test_value

        read_backend = backend_type(test_id)
        assert test_key in read_backend
        assert read_backend[test_key] == test_value

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


def test_max_block_size(test_id):
    size = 256
    backend = PickleBackend(test_id, 1024)
    backend.clear()
    for i in range(size):
        backend[i] = random.sample(list(range(size)), size)
    assert len(list(backend.get_all_block_ids())) > 100
