import pickle  # noqa: S403
from abc import ABC
from pathlib import Path
from typing import Iterable, Iterator, MutableMapping

from marisa_trie import Trie
from replete.consistent_hash import consistent_hash

from class_cache.types import KeyType, ValueType
from class_cache.utils import get_user_cache_dir


class BaseBackend(ABC, MutableMapping[KeyType, ValueType]):
    def __init__(self, id_: str | int = None) -> None:
        self._id = id_

    @property
    def id(self) -> str | int | None:
        return self._id

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


class PickleBackend(BaseBackend[KeyType, ValueType]):
    ROOT_DIR = get_user_cache_dir()
    BLOCK_SUFFIX = ".block.pkl"

    def __init__(self, id_: str | int, target_block_size=1024**2) -> None:
        super().__init__(id_)
        self._dir = self.ROOT_DIR / str(self._id)
        self._dir.mkdir(exist_ok=True, parents=True)
        self._target_block_size = target_block_size

    def _get_key_hash(self, key: KeyType) -> str:
        return f"{consistent_hash(key):x}"

    def _get_all_block_ids(self) -> Iterable[str]:
        yield from (path.name.split(".")[0] for path in self._dir.glob(f"*{self.BLOCK_SUFFIX}"))

    def _get_path_for_block_id(self, block_id: str) -> Path:
        return self._dir / f"{block_id}{self.BLOCK_SUFFIX}"

    def _get_block(self, block_id: str) -> dict[KeyType, ValueType]:
        try:
            with self._get_path_for_block_id(block_id).open("rb") as f:
                return pickle.load(f)  # noqa: S301
        except FileNotFoundError:
            return {}

    def _write_block(self, block_id: str, block: dict[KeyType, ValueType]) -> None:
        with self._get_path_for_block_id(block_id).open("wb") as f:
            pickle.dump(block, f)

    def _get_block_id_for_key(self, key: KeyType) -> str:
        key_hash = self._get_key_hash(key)

        blocks_trie = Trie(self._get_all_block_ids())
        prefixes = blocks_trie.prefixes(key_hash)
        return key_hash[:1] if not prefixes else max(prefixes, key=len)

    def _get_block_for_key(self, key: KeyType) -> dict[KeyType, ValueType]:
        return self._get_block(self._get_block_id_for_key(key))

    def __contains__(self, key: KeyType) -> bool:
        return key in self._get_block_for_key(key)

    def __len__(self) -> int:
        total_items = 0
        # TODO: Optimise this
        for block_id in self._get_all_block_ids():
            total_items += len(self._get_block(block_id))
        return total_items

    def __iter__(self) -> Iterator[KeyType]:
        # TODO: Optimise this
        for block_id in self._get_all_block_ids():
            yield from self._get_block(block_id).keys()

    def __getitem__(self, key: KeyType) -> ValueType:
        return self._get_block_for_key(key)[key]

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        block_id = self._get_block_id_for_key(key)
        block = self._get_block(block_id)
        block[key] = value
        # TODO: Measure block size here and split if necessary
        self._write_block(block_id, block)

    def __delitem__(self, key: KeyType) -> None:
        block_id = self._get_block_id_for_key(key)
        block = self._get_block(block_id)
        del block[key]
        self._write_block(block_id, block)
