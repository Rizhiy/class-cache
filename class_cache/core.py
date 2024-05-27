from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterable, MutableMapping

from replete.consistent_hash import consistent_hash

from class_cache.backends import BaseBackend, PickleBackend
from class_cache.types import KeyType, ValueType

DEFAULT_BACKEND_TYPE = PickleBackend


class Cache(ABC, MutableMapping[KeyType, ValueType]):
    def __init__(self, id_: str | int | None = None, backend: type[BaseBackend] = DEFAULT_BACKEND_TYPE) -> None:
        self._backend = backend(id_)
        self._data: dict[KeyType, ValueType] = {}
        self._to_write = set()
        self._to_delete = set()

    @property
    def backend(self) -> BaseBackend:
        return self._backend

    def __contains__(self, key: KeyType) -> bool:
        if key in self._data:
            return True
        return key not in self._to_delete and key in self._backend

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        self._data[key] = value
        self._to_write.add(key)

    def __getitem__(self, key: KeyType) -> ValueType:
        if key not in self._data:
            self._data[key] = self._backend[key]
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


class CacheWithDefault(Cache[KeyType, ValueType]):
    VERSION = 0
    NON_HASH_ATTRIBUTES: ClassVar[frozenset[str]] = frozenset(
        {"_backend", "_backend_set", "_data", "_to_write", "_to_delete"},
    )

    def __init__(self, backend: type[BaseBackend] = DEFAULT_BACKEND_TYPE):
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
            raise TypeError(
                f"Trying to update hash inclusive attribute after hash has been decided: {key}",
            )
        object.__setattr__(self, key, value)
