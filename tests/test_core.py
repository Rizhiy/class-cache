import random
import resource

from class_cache import Cache, CacheWithDefault

TEST_DICT = {1: "foo", "foo": "bar", (2, 3): [4, 5]}


class CacheWithAttr(CacheWithDefault[str, str]):
    NON_HASH_ATTRIBUTES = frozenset({*CacheWithDefault.NON_HASH_ATTRIBUTES, "_name"})

    def __init__(self, name: str, *args, **kwargs):
        self._name = name
        super().__init__(*args, **kwargs)

    def _get_data(self, key: str) -> str:
        return self._name + key


def get_new_cache(id_: str = None, *, clear=True, **kwargs) -> Cache:
    cache = Cache(id_, **kwargs)
    if clear:
        cache.clear()
    return cache


def test_basic_cache(test_key, test_value):
    first = get_new_cache()
    first[test_key] = test_value
    first.write()
    del first

    second = get_new_cache(clear=False)
    assert test_key in second


def test_cache_separate(test_key):
    base = get_new_cache()
    base[test_key] = "base"
    base.write()

    first = get_new_cache("first")
    assert first.get(test_key) != "base"
    first[test_key] = "first"
    first.write()

    second = get_new_cache("second")
    assert second.get(test_key) != "first"
    second[test_key] = "second"
    second.write()

    assert base[test_key] == "base"
    assert first[test_key] == "first"
    assert second[test_key] == "second"


def test_del_item(test_key, test_value):
    first = get_new_cache()
    first[test_key] = test_value
    first.write()
    del first

    second = get_new_cache(clear=False)
    del second[test_key]
    assert test_key not in second
    second.write()

    third = get_new_cache(clear=False)
    assert test_key not in third


def test_attribute_cache():
    first = CacheWithAttr("first")
    second = CacheWithAttr("second")
    first.clear()
    second.clear()
    assert first["foo"] == "firstfoo"
    assert second["foo"] == "secondfoo"


def test_keys():
    cache = get_new_cache()
    cache.update(TEST_DICT)
    cache.write()
    del cache

    read_cache = get_new_cache(clear=False)
    assert set(read_cache.keys()) == set(TEST_DICT.keys())


def test_values():
    cache = get_new_cache()
    cache.update(TEST_DICT)
    cache.write()
    del cache

    read_cache = get_new_cache(clear=False)
    read_values = list(read_cache.values())
    for value in TEST_DICT.values():
        read_values.remove(value)
    assert not read_values


def test_items():
    cache = get_new_cache()
    cache.update(TEST_DICT)
    cache.write()

    del cache

    read_cache = get_new_cache(clear=False)
    assert dict(read_cache.items()) == TEST_DICT


def test_len():
    cache = get_new_cache()
    cache.update(TEST_DICT)
    assert len(cache) == len(TEST_DICT)
    cache.write()

    del cache
    cache = get_new_cache(clear=False)
    assert len(cache) == len(TEST_DICT)


def get_max_memory_used() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def get_random_array() -> list[int]:
    return [random.randint(0, 1024) for _ in range(1024)]  # noqa: S311


def test_max_memory_usage():
    cache = get_new_cache(max_items=16)
    # Get an array to account for generation in memory calculation
    _ = get_random_array()
    starting_max_memory = get_max_memory_used()
    for idx in range(1024):
        cache[idx] = get_random_array()
    end_max_memory_usage = get_max_memory_used()
    assert end_max_memory_usage - starting_max_memory < 3_000


# TODO: Add parallel test for cache as well (threading)
