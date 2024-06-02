from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from typing import Iterable, Iterator, TypeAlias, TypeVar

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")
JsonType: TypeAlias = dict[str, "JsonType"] | list["JsonType"] | str | int | float | bool | None
MetaType = dict[str, JsonType]
IdType: TypeAlias = str | int | None


class CacheInterface(ABC, MutableMapping[KeyType, ValueType]):
    def __init__(self, id_: IdType = None) -> None:
        self._id = id_

    @property
    def id(self) -> IdType:
        return self._id

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return hash(self) == hash(other)

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __iter__(self) -> Iterable[KeyType]:
        pass

    @abstractmethod
    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        pass

    @abstractmethod
    def __getitem__(self, key: KeyType) -> ValueType:
        raise KeyError

    @abstractmethod
    def __delitem__(self, key: KeyType) -> None:
        pass

    def __contains__(self, key: KeyType) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    # Override these methods to allow getting results in a more optimal fashion
    def contains_many(self, keys: Iterable[KeyType]) -> Iterator[tuple[KeyType, bool]]:
        for key in keys:
            yield key, key in self

    def get_many(self, keys: Iterable[KeyType]) -> Iterator[tuple[KeyType, ValueType]]:
        for key in keys:
            yield key, self[key]

    def set_many(self, items: Iterable[tuple[KeyType, ValueType]]) -> None:
        for key, value in items:
            self[key] = value

    def del_many(self, keys: Iterable[KeyType]) -> None:
        for key in keys:
            del self[key]

    def clear(self) -> None:
        self.del_many(self)
