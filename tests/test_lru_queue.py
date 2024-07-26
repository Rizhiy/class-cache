import pytest
from flaky import flaky
from replete import Timer

from class_cache.lru_queue import LRUQueue

NUM_ITERS = 10_000


def get_queue(size=4) -> LRUQueue:
    queue = LRUQueue()
    for i in range(size):
        queue.update(i)
    return queue


def test_basic_queue():
    queue = get_queue()

    assert len(queue) == 4
    for i in range(4):
        assert i in queue
    assert queue.peek() == 0
    queue.update(0)
    assert queue.peek() == 1
    assert queue.pop() == 1
    assert queue.peek() == 2
    del queue[2]
    assert len(queue) == 2
    assert queue.peek() == 3
    assert list(queue) == [0, 3]


def test_next():
    queue = get_queue()
    assert next(iter(queue)) == 3


def test_str():
    queue = get_queue()
    queue.update(0)

    assert str(queue) == "0 -> 3 -> 2 -> 1"


@flaky(max_runs=3, min_passes=1)  # This is very noisy
def test_contains_speed():
    small_queue = get_queue()
    with Timer(process_only=True) as base_timer:
        for _ in range(NUM_ITERS):
            assert 0 in small_queue

    large_queue = get_queue(1024)
    with Timer(base_timer.time, process_only=True) as timer:
        for _ in range(NUM_ITERS):
            assert 0 in large_queue

    # Some noise is allowed
    assert timer.base_time_ratio < 1.05


@flaky(max_runs=3, min_passes=1)  # This is very noisy
def test_pop_update_speed():
    small_queue = get_queue()
    with Timer(process_only=True) as base_timer:
        for _ in range(NUM_ITERS):
            key = small_queue.pop()
            small_queue.update(key)

    large_queue = get_queue(1024)
    with Timer(base_timer.time, process_only=True) as timer:
        for _ in range(NUM_ITERS):
            key = large_queue.pop()
            large_queue.update(key)

    # Some noise is allowed
    assert timer.base_time_ratio < 1.05


def test_empty_pop_raises_error():
    queue = LRUQueue()
    with pytest.raises(IndexError, match="empty queue"):
        queue.pop()


def test_pop_many():
    small_queue = get_queue()

    assert small_queue.pop_many(3) == [0, 1, 2]
    assert small_queue.pop_many(2) == [3]
    assert small_queue.pop_many(1) == []
