import datetime as dt
import pickle  # noqa: S403
from typing import Iterable, Iterator

import brotli

from class_cache.types import CacheInterface, IdType, KeyType, ValueType


# TODO: Make this a register
class BaseWrapper(CacheInterface[KeyType, ValueType]):
    """
    :param backend: backend to be wrapped
    """

    def __init__(self, wrapped: CacheInterface[KeyType, ValueType]) -> None:
        super().__init__()
        self._wrapped = wrapped

    @property
    def id(self) -> IdType:
        return f"{self.__class__.__name__}({self.wrapped.id})"

    @property
    def wrapped(self) -> CacheInterface[KeyType, ValueType]:
        return self._wrapped

    @property
    def __hash__(self) -> int:
        return hash((self.__class__.__name__, hash(self.wrapped)))

    def __eq__(self, other) -> bool:
        if not (isinstance(other, self.__class__) and isinstance(other.wrapped, self.wrapped.__class__)):
            return False
        return hash(self) == hash(other)

    def __len__(self) -> int:
        return len(self.wrapped)

    def __iter__(self) -> Iterable[KeyType]:
        yield from self.wrapped  # type: ignore

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        self.wrapped[key] = value

    def __getitem__(self, key: KeyType) -> ValueType:
        return self.wrapped[key]

    def __delitem__(self, key: KeyType) -> None:
        del self.wrapped[key]

    def __contains__(self, key: KeyType) -> bool:
        return key in self.wrapped

    def contains_many(self, keys: Iterable[KeyType]) -> Iterator[tuple[KeyType, bool]]:
        return self.wrapped.contains_many(keys)

    def get_many(self, keys: Iterable[KeyType]) -> Iterator[tuple[KeyType, ValueType]]:
        return self.wrapped.get_many(keys)

    def set_many(self, items: Iterable[tuple[KeyType, ValueType]]) -> None:
        return self.wrapped.set_many(items)

    def del_many(self, keys: Iterable[KeyType]) -> None:
        return self.wrapped.del_many(keys)

    def clear(self) -> None:
        return self.wrapped.clear()


class BrotliCompressWrapper(BaseWrapper[KeyType, ValueType]):
    def _encode(self, obj: KeyType | ValueType) -> bytes:
        return brotli.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL))

    def _decode(self, stored: bytes) -> KeyType | ValueType:
        return pickle.loads(brotli.decompress(stored))  # noqa: S301

    def __getitem__(self, key: KeyType) -> ValueType:
        return self._decode(super().__getitem__(key))  # type: ignore

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        super().__setitem__(key, self._encode(value))  # type: ignore

    def set_many(self, items: Iterable[tuple[KeyType, ValueType]]) -> None:
        return super().set_many((key, self._encode(value)) for key, value in items)  # type: ignore


class ExpirationWrapper(BaseWrapper[KeyType, ValueType]):
    def __init__(
        self,
        wrapped: CacheInterface[KeyType, tuple[dt.datetime, ValueType]],
        lifespan=dt.timedelta(days=1),
    ) -> None:
        super().__init__(wrapped)  # type: ignore
        self._lifespan = lifespan

    @property
    def wrapped(self) -> CacheInterface[KeyType, tuple[dt.datetime, ValueType]]:
        return self._wrapped  # type: ignore

    @property
    def lifespan(self) -> dt.timedelta:
        return self._lifespan

    @property
    def _now(self) -> dt.datetime:
        return dt.datetime.now(dt.timezone.utc)

    def _check_item(self, key: KeyType) -> bool:
        expiration_time, _ = self.wrapped[key]
        if expiration_time < self._now:
            del self.wrapped[key]
            return False
        return True

    def __len__(self) -> int:
        # TODO: This is very inefficient.
        # Need to store expiration_time in a separate cache, but will need a way to clone cache for that.
        return sum(int(self._check_item(key)) for key in self.wrapped)  # type: ignore

    def __iter__(self) -> Iterable[KeyType]:
        for key in self.wrapped:  # type: ignore
            if self._check_item(key):
                yield key

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        self.wrapped[key] = self._now + self.lifespan, value

    def __getitem__(self, key: KeyType) -> ValueType:
        if self._check_item(key):
            return self.wrapped[key][1]
        raise KeyError(key)

    def __contains__(self, key: KeyType) -> bool:
        return super().__contains__(key) and self._check_item(key)
