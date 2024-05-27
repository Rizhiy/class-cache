
from class_cache import Cache, CacheWithDefault

TEST_KEY = "class_cache.tests.core.key"
TEST_VALUE = "class_cache.tests.core.value"
TEST_DICT = {1: "foo", "foo": "bar", (2, 3): [4, 5]}


class CacheWithAttr(CacheWithDefault[str, str]):
    NON_HASH_ATTRIBUTES = frozenset({*CacheWithDefault.NON_HASH_ATTRIBUTES, "_name"})

    def __init__(self, name: str, *args, **kwargs):
        self._name = name
        super().__init__(*args, **kwargs)

    def _get_data(self, key: str) -> str:
        return self._name + key


# TODO: Change this into a fixture and set id based on request to allow running tests in parallel
def get_new_cache(id_: str = None, *, clear=True) -> Cache:
    cache = Cache(id_)
    if clear:
        cache.clear()
    return cache


# TODO: Remake this into a test-suite to test different backends, not just default one
def test_basic_cache():
    first = get_new_cache()
    first[TEST_KEY] = TEST_VALUE
    first.write()
    del first

    second = get_new_cache(clear=False)
    assert TEST_KEY in second


def test_cache_separate():
    base = get_new_cache()
    base[TEST_KEY] = "base"
    base.write()

    first = get_new_cache("first")
    assert first.get(TEST_KEY) != "base"
    first[TEST_KEY] = "first"
    first.write()

    second = get_new_cache("second")
    assert second.get(TEST_KEY) != "first"
    second[TEST_KEY] = "second"
    second.write()

    assert base[TEST_KEY] == "base"
    assert first[TEST_KEY] == "first"
    assert second[TEST_KEY] == "second"


def test_del_item():
    first = get_new_cache()
    first[TEST_KEY] = TEST_VALUE
    first.write()
    del first

    second = get_new_cache(clear=False)
    del second[TEST_KEY]
    assert TEST_KEY not in second
    second.write()

    third = get_new_cache(clear=False)
    assert TEST_KEY not in third


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
