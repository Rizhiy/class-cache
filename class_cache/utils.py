import os
from pathlib import Path


def get_user_cache_dir() -> Path:
    cache_home = os.environ.get("XDG_CACHE_HOME", None)
    if cache_home:
        return Path(cache_home)
    return Path(os.environ["HOME"]) / ".cache"


def get_class_cache_dir() -> Path:
    return get_user_cache_dir() / "class_cache"
