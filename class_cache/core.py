import math
from abc import abstractmethod
from typing import Any, Callable, ClassVar, Iterable

from replete.consistent_hash import consistent_hash

from class_cache.backends import SQLiteBackend
from class_cache.lru_queue import LRUQueue
from class_cache.types import CacheInterface, IdType, KeyType, ValueType

DEFAULT_BACKEND_TYPE = SQLiteBackend


class Cache(CacheInterface[KeyType, ValueType]):
    """
    :param max_items: Maximum number of items to keep in memory
    :param flush_ratio: Amount of stored items to write to backend when memory if full
        ceiling will be used to calculate the final amount
    """

    def __init__(
        self,
        id_: IdType = None,
        backend_type: type[CacheInterface] | Callable[[IdType], CacheInterface] = DEFAULT_BACKEND_TYPE,
        max_items=128,
        *,
        flush_ratio=0.1,
    ) -> None:
        super().__init__(id_)
        self._backend = backend_type(id_)

        self._max_items = max_items
        self._flush_amount = math.ceil(self._max_items * flush_ratio)
        self._lru_queue = LRUQueue()

        self._data: dict[KeyType, ValueType] = {}
        self._to_write = set()
        self._to_delete = set()

    @property
    def backend(self) -> CacheInterface:
        return self._backend

    def __contains__(self, key: KeyType) -> bool:
        if key in self._data:
            self._lru_queue.update(key)
            return True
        return key not in self._to_delete and key in self._backend

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        self._data[key] = value
        self._to_write.add(key)
        self._lru_queue.update(key)
        self._check_max_items()

    def __getitem__(self, key: KeyType) -> ValueType:
        if key not in self._data:
            self._data[key] = self._backend[key]
            self._check_max_items()
        self._lru_queue.update(key)
        return self._data[key]

    def __iter__(self) -> Iterable[KeyType]:
        self.write()
        return iter(self._backend)

    def __len__(self) -> int:
        self.write()
        return len(self._backend)

    def __delitem__(self, key: KeyType) -> None:
        # Check that key is present. Can't check self._data, since it can be unloaded
        if key not in self:
            raise KeyError(key)
        if key in self._data:
            del self._lru_queue[key]
        self._data.pop(key, None)
        self._to_delete.add(key)

    def write(self) -> None:
        """Write values to backend"""
        self._backend.set_many((key, self._data[key]) for key in self._to_write)
        self._backend.del_many(self._to_delete)
        self._to_write = set()
        self._to_delete = set()

    def clear(self) -> None:
        self._backend.clear()
        self._data = {}
        self._to_write = set()
        self._to_delete = set()
        self._lru_queue.clear()

    def _check_max_items(self) -> None:
        if len(self._data) <= self._max_items:
            return

        keys_to_free = self._lru_queue.pop_many(self._flush_amount)
        if any(key in self._to_write for key in keys_to_free):
            self.write()
        for key in keys_to_free:
            self._data.pop(key)


# TODO: Refactor this, this should use composition, not inheritance. Maybe a wrapper.
class CacheWithDefault(Cache[KeyType, ValueType]):
    VERSION = 0
    NON_HASH_ATTRIBUTES: ClassVar[frozenset[str]] = frozenset(
        {"_backend", "_backend_set", "_data", "_to_write", "_to_delete"},
    )

    def __init__(self, backend: type[CacheInterface] = DEFAULT_BACKEND_TYPE):
        super().__init__(self.id_for_backend, backend)
        self._backend_set = True

    @property
    def id_for_backend(self) -> int:
        return consistent_hash(self._data_for_hash())

    @abstractmethod
    def _get_data(self, key: KeyType) -> ValueType:
        """
        Get default data for missing key.
        This method should always produce the same value for the same instance with same hashable attributes,
        see NON_HASH_ATTRIBUTES.
        """

    def __getitem__(self, key: KeyType) -> ValueType:
        if key not in self:
            self[key] = self._get_data(key)
        return super().__getitem__(key)

    def _data_for_hash(self) -> dict[str, Any]:
        attrs = dict(vars(self))
        for attr in self.NON_HASH_ATTRIBUTES:
            attrs.pop(attr, None)
        return attrs

    def __setattr__(self, key: str, value: Any) -> None:
        if (
            not isinstance(getattr(self.__class__, key, None), property)
            and getattr(self, "_backend_set", None)
            and key not in self.NON_HASH_ATTRIBUTES
        ):
            raise TypeError(f"Trying to update hash inclusive attribute after hash has been decided: {key}")
        object.__setattr__(self, key, value)
