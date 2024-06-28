# ruff: noqa: S608
import codecs
import json
import logging
import pickle  # noqa: S403
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, cast

from marisa_trie import Trie
from replete.consistent_hash import consistent_hash
from replete.flock import FileLock

from class_cache.types import CacheInterface, IdType, KeyType, ValueType
from class_cache.utils import get_class_cache_dir

LOGGER = logging.getLogger(__name__)


class PickleBackend(CacheInterface[KeyType, ValueType]):
    ROOT_DIR = get_class_cache_dir() / "PickleBackend"
    BLOCK_SUFFIX = ".block.pkl"
    META_TYPE = dict[str, Any]

    def __init__(self, id_: IdType = None, max_block_size=1024 * 1024) -> None:
        super().__init__(id_)
        self._dir = self.ROOT_DIR / str(self.id)
        self._dir.mkdir(exist_ok=True, parents=True)
        self._max_block_size = max_block_size

        self._meta_path = self._dir / "meta.json"
        self._lock = FileLock(self._meta_path)
        self._check_meta()

    @property
    def dir(self) -> Path:
        return self._dir

    # Helper methods, they don't acquire locks, so should only be used inside methods that do
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

    # TODO: Add caching for this
    def _get_block_id_for_key(self, key: KeyType, prefix_len=1) -> str:
        key_hash = self._get_key_hash(key)

        blocks_trie = Trie(self.get_all_block_ids())
        prefixes = blocks_trie.prefixes(key_hash)
        if prefix_len > len(key_hash):
            raise ValueError("Got prefix_len that is larger than key_hash len.")
        return key_hash[:prefix_len] if not prefixes else max(prefixes, key=len)

    # TODO: Add caching for this
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
        with self._lock.read_lock():
            yield from (path.name.split(".")[0] for path in self._dir.glob(f"*{self.BLOCK_SUFFIX}"))

    def _check_meta(self) -> None:
        with self._lock.read_lock():
            if self._meta_path.exists():
                return
            if list(self.get_all_block_ids()):
                raise ValueError(f"Found existing blocks without meta file in {self._dir}")
        with self._lock.write_lock():
            self._write_clean_meta()

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

    def __contains__(self, key: KeyType) -> bool:
        with self._lock.read_lock():
            return key in self._get_block_for_key(key)

    def __len__(self) -> int:
        with self._lock.read_lock():
            return self._read_meta()["len"]

    def __iter__(self) -> Iterator[KeyType]:
        with self._lock.read_lock():
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

        if self.get_path_for_block_id(block_id).stat().st_size > self._max_block_size:
            if len(block) == 1:
                LOGGER.warning(
                    "Got a block that is larger than max_block_size with single item, please increase max_block_size!",
                )
                return
            self._split_block(block_id)

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


class SQLiteBackend(CacheInterface[KeyType, ValueType]):
    ROOT_DIR = get_class_cache_dir() / "SQLiteBackend"
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_TABLE_NAME = "data"

    def __init__(self, id_: IdType = None) -> None:
        super().__init__(id_)
        self._db_path = self.ROOT_DIR / f"{self.id}.db"
        self._con = sqlite3.connect(self._db_path)
        self._check_table()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _check_table(self):
        tables = self._con.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
        if tables is None:
            self._con.execute(f"CREATE TABLE {self.DATA_TABLE_NAME}(key TEXT, value TEXT)")
            self._con.execute(f"CREATE UNIQUE INDEX key_index ON {self.DATA_TABLE_NAME}(key)")

    # TODO: Add caching for keys
    def _encode(self, obj: KeyType | ValueType) -> str:
        return codecs.encode(pickle.dumps(obj), "base64").decode()

    def _decode(self, stored: str) -> KeyType | ValueType:
        return pickle.loads(codecs.decode(stored.encode(), "base64"))  # noqa: S301

    def __contains__(self, key: KeyType) -> bool:
        key_str = self._encode(key)
        sql = f"SELECT EXISTS(SELECT 1 FROM {self.DATA_TABLE_NAME} WHERE key=? LIMIT 1)"
        value = self._con.execute(sql, (key_str,)).fetchone()[0]
        return value != 0

    def __len__(self) -> int:
        return self._con.execute(f"SELECT COUNT(key) FROM {self.DATA_TABLE_NAME}").fetchone()[0]

    def __iter__(self) -> Iterator[KeyType]:
        for key_str in self._con.execute(f"SELECT key FROM {self.DATA_TABLE_NAME}").fetchall():
            yield cast(KeyType, self._decode(key_str[0]))

    def __getitem__(self, key: KeyType) -> ValueType:
        key_str = self._encode(key)
        sql = f"SELECT value FROM {self.DATA_TABLE_NAME} WHERE key=? LIMIT 1"
        res = self._con.execute(sql, (key_str,)).fetchone()
        if res is None:
            raise KeyError(key)
        return cast(ValueType, self._decode(res[0]))

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        key_str = self._encode(key)
        value_str = self._encode(value)
        self._con.execute(f"INSERT INTO {self.DATA_TABLE_NAME} VALUES (?, ?)", (key_str, value_str))
        self._con.commit()

    def __delitem__(self, key: KeyType) -> None:
        key_str = self._encode(key)
        self._con.execute(f"DELETE FROM {self.DATA_TABLE_NAME} WHERE key=?", (key_str,))
        self._con.commit()

    def clear(self) -> None:
        self._con.execute(f"DROP TABLE IF EXISTS {self.DATA_TABLE_NAME}")
        self._con.execute("VACUUM")
        self._con.commit()
        self._check_table()

    def __del__(self):
        self._con.commit()
        self._con.close()

    # TODO: implement *_many methods
