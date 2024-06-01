import logging
import math
import random
import string
from functools import partial
from time import monotonic

import numpy as np
from replete.logging import setup_logging

from class_cache import Cache
from class_cache.backends import BaseBackend, BrotliCompressWrapper, PickleBackend, SQLiteBackend

LOGGER = logging.getLogger("class_cache.benchmark.main")
SIZE = 512
NP_RNG = np.random.default_rng()


class MyObj:
    def __init__(self, name: str, number: int):
        self._name = name
        self._number = number


def get_random_string(size: int) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(size))  # noqa: S311


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def evaluate(name: str, backend_type: type[BaseBackend] = PickleBackend):
    LOGGER.info(f"Evaluating {name} backend")
    arrays = {f"arr_{idx}": NP_RNG.standard_normal((SIZE, 32)) for idx in range(SIZE)}
    strings = {f"str_{idx}": get_random_string(SIZE) for idx in range(SIZE)}
    objects = {f"obj_{idx}": MyObj(str(idx) * SIZE, idx) for idx in range(SIZE)}

    data = arrays | strings | objects
    LOGGER.info(f"Got {len(data)} elements")

    cache = Cache(backend_type=backend_type)
    cache.clear()
    start_write = monotonic()
    cache.update(data)
    cache.write()
    end_write = monotonic()
    LOGGER.info(f"Write took {end_write - start_write:3f} seconds")

    del cache
    read_cache = Cache(backend_type=backend_type)
    start_read = monotonic()
    for key in read_cache:
        read_cache[key]
    end_read = monotonic()
    LOGGER.info(f"Read took {end_read - start_read:3f} seconds")

    backend = read_cache.backend
    match backend:
        case PickleBackend():
            total_size = 0
            for block_id in backend.get_all_block_ids():
                total_size += backend.get_path_for_block_id(block_id).stat().st_size
            LOGGER.info(f"{len(list(backend.get_all_block_ids()))} total blocks")
        case SQLiteBackend():
            total_size = backend.db_path.stat().st_size
        case BrotliCompressWrapper():
            total_size = 0
            for block_id in backend._backend.get_all_block_ids():  # noqa: SLF001
                total_size += backend._backend.get_path_for_block_id(block_id).stat().st_size  # noqa: SLF001
            LOGGER.info(f"{len(list(backend._backend.get_all_block_ids()))} total blocks")  # noqa: SLF001

    LOGGER.info(f"Size on disk: {convert_size(total_size)}")


def main():
    setup_logging(print_level=logging.INFO)
    for name, backend_type in {
        "pickle": PickleBackend,
        "sqlite": SQLiteBackend,
        "brotli_pickle": partial(BrotliCompressWrapper, backend_type=PickleBackend),
    }.items():
        evaluate(name, backend_type)


if __name__ == "__main__":
    main()
