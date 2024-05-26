from class_cache import Cache, CacheWithDefault

TEST_KEY = "class_cache.tests.core.key"
TEST_VALUE = "class_cache.tests.core.value"


class CacheWithAttr(CacheWithDefault[str, str]):
    NON_HASH_ATTRIBUTES = frozenset({*CacheWithDefault.NON_HASH_ATTRIBUTES, "_name"})

    def __init__(self, name: str, *args, **kwargs):
        self._name = name
        super().__init__(*args, **kwargs)

    def _get_data(self, key: str) -> str:
        return self._name + key


# TODO: Remake this into a test-suite to test different backends, not just default one
def test_basic_cache():
    first = Cache()
    first[TEST_KEY] = TEST_VALUE
    first.write()
    del first

    second = Cache()
    assert TEST_KEY in second


def test_cache_separate():
    base = Cache()
    base[TEST_KEY] = "base"
    base.write()

    first = Cache("first")
    assert first.get(TEST_KEY) != "base"
    first[TEST_KEY] = "first"
    first.write()

    second = Cache("second")
    assert second.get(TEST_KEY) != "first"
    second[TEST_KEY] = "second"
    second.write()

    assert base[TEST_KEY] == "base"
    assert first[TEST_KEY] == "first"
    assert second[TEST_KEY] == "second"


def test_del_item():
    first = Cache()
    first[TEST_KEY] = TEST_VALUE
    first.write()
    del first

    second = Cache()
    del second[TEST_KEY]
    assert TEST_KEY not in second
    second.write()

    third = Cache()
    assert TEST_KEY not in third


def test_attribute_cache():
    first = CacheWithAttr("first")
    second = CacheWithAttr("second")
    first.clear()
    second.clear()
    assert first["foo"] == "firstfoo"
    assert second["foo"] == "secondfoo"
