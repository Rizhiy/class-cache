import json
import pickle  # noqa: S403
from abc import ABC
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, MutableMapping

from fasteners import InterProcessReaderWriterLock
from marisa_trie import Trie
from replete.consistent_hash import consistent_hash

from class_cache.types import KeyType, ValueType
from class_cache.utils import get_class_cache_dir


class BaseBackend(ABC, MutableMapping[KeyType, ValueType]):
    def __init__(self, id_: str | int | None = None) -> None:
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
    ROOT_DIR = get_class_cache_dir() / "PickleBackend"
    BLOCK_SUFFIX = ".block.pkl"
    META_TYPE = dict[str, Any]

    def __init__(self, id_: str | int, target_block_size=1024 * 1024) -> None:
        super().__init__(id_)
        self._dir = self.ROOT_DIR / str(self._id)
        self._dir.mkdir(exist_ok=True, parents=True)
        self._target_block_size = target_block_size
        self._meta_path = self._dir / "meta.json"
        self._lock = InterProcessReaderWriterLock(self._dir / "lock.file")
        self._check_meta()

    @property
    def dir(self) -> Path:
        return self._dir

    # Helper methods, don't acquire locks inside them
    def _read_meta(self) -> META_TYPE:
        with self._meta_path.open() as f:
            return json.load(f)

    def _write_meta(self, meta: META_TYPE) -> None:
        with self._meta_path.open("w") as f:
            json.dump(meta, f)

    def _write_clean_meta(self) -> None:
        self._write_meta({"len": 0})

    def get_path_for_block_id(self, block_id: str) -> Path:
        return self._dir / f"{block_id}{self.BLOCK_SUFFIX}"

    def _get_key_hash(self, key: KeyType) -> str:
        return f"{consistent_hash(key):x}"

    def _get_block_id_for_key(self, key: KeyType, prefix_len=1) -> str:
        key_hash = self._get_key_hash(key)

        blocks_trie = Trie(self.get_all_block_ids())
        prefixes = blocks_trie.prefixes(key_hash)
        return key_hash[:prefix_len] if not prefixes else max(prefixes, key=len)

    def _get_block(self, block_id: str) -> dict[KeyType, ValueType]:
        try:
            with self.get_path_for_block_id(block_id).open("rb") as f:
                return pickle.load(f)  # noqa: S301
        except FileNotFoundError:
            return {}

    def _write_block(self, block_id: str, block: dict[KeyType, ValueType]) -> None:
        with self.get_path_for_block_id(block_id).open("wb") as f:
            pickle.dump(block, f, pickle.HIGHEST_PROTOCOL)

    def _update_length(self, change: int) -> None:
        meta = self._read_meta()
        meta["len"] += change
        self._write_meta(meta)

    def _get_block_for_key(self, key: KeyType) -> dict[KeyType, ValueType]:
        return self._get_block(self._get_block_id_for_key(key))

    def get_all_block_ids(self) -> Iterable[str]:
        yield from (path.name.split(".")[0] for path in self._dir.glob(f"*{self.BLOCK_SUFFIX}"))

    # Helper methods end

    def _check_meta(self) -> None:
        with self._lock.read_lock():
            if self._meta_path.exists():
                return
            if list(self.get_all_block_ids()):
                raise ValueError(f"Found existing blocks without meta file in {self._dir}")
        with self._lock.write_lock():
            self._write_clean_meta()

    def __contains__(self, key: KeyType) -> bool:
        with self._lock.read_lock():
            return key in self._get_block_for_key(key)

    def __len__(self) -> int:
        with self._lock.read_lock():
            return self._read_meta()["len"]

    def __iter__(self) -> Iterator[KeyType]:
        # TODO: Optimise this
        # TODO: This should also use a read lock, but it seems to be not working, see:
        # https://github.com/harlowja/fasteners/issues/115
        for block_id in self.get_all_block_ids():
            yield from self._get_block(block_id).keys()

    def __getitem__(self, key: KeyType) -> ValueType:
        with self._lock.read_lock():
            return self._get_block_for_key(key)[key]

    def __setitem__(self, key: KeyType, value: ValueType, prefix_len=1) -> None:
        with self._lock.write_lock():
            block_id = self._get_block_id_for_key(key, prefix_len=prefix_len)
            block = self._get_block(block_id)
            change = 0 if key in block else 1
            block[key] = value
            self._write_block(block_id, block)
            self._update_length(change)

        if self.get_path_for_block_id(block_id).stat().st_size > self._target_block_size:
            self._split_block(block_id)

    def _split_block(self, block_id: str) -> None:
        with self._lock.write_lock():
            block = self._get_block(block_id)
            self.get_path_for_block_id(block_id).unlink()
            new_prefix_len = len(block_id) + 1
            new_blocks = defaultdict(dict)
            for key, value in block.items():
                new_blocks[self._get_block_id_for_key(key, new_prefix_len)][key] = value
            for new_block_id, new_block in new_blocks.items():
                self._write_block(new_block_id, new_block)

    def __delitem__(self, key: KeyType) -> None:
        with self._lock.write_lock():
            block_id = self._get_block_id_for_key(key)
            block = self._get_block(block_id)
            del block[key]
            self._write_block(block_id, block)
            self._update_length(-1)

    def clear(self) -> None:
        with self._lock.write_lock():
            for block_id in self.get_all_block_ids():
                self.get_path_for_block_id(block_id).unlink()
            self._meta_path.unlink()
            self._write_clean_meta()
