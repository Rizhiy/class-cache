# Class based cache

![tests](https://github.com/Rizhiy/class-cache/actions/workflows/test_and_version.yml/badge.svg)
[![codecov](https://codecov.io/gh/Rizhiy/class-cache/graph/badge.svg?token=7CAJG2EBLG)](https://codecov.io/gh/Rizhiy/class-cache)
![publish](https://github.com/Rizhiy/class-cache/actions/workflows/publish.yml/badge.svg)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FRizhiy%2Fclass-cache%2Fmaster%2Fpyproject.toml)
[![PyPI - Version](https://img.shields.io/pypi/v/class-cache)](https://pypi.org/project/class-cache/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Installation

Recommended installation with pip:

```bash
pip install class-cache
```

## Usage

- Basic usage:

  ```python
  from class_cache import Cache

  # Create cache
  cache = Cache()
  # Set item in cache
  # NOTE: Keys and values have to be pickle-serialisable
  cache["foo"] = "bar"
  # Save cache to backend (disk by default)
  cache.write()

  # During another program run just create same cache again and you can retrieve data
  del cache
  cache2 = Cache()
  assert cache2["foo"] == "bar"
  ```

- Use multiple caches:

  ```python
  cache1 = Cache(1)
  cache2 = Cache(2)

  cache1["foo"] = "bar"
  cache2["foo"] = "zar"

  assert cache1["foo"] != cache2["foo"]
  ```

- Use cache with default factory:

  ```python
  from class_cache import CacheWithDefault

  class MyCache(CacheWithDefault[str, str]):
      NON_HASH_ATTRIBUTES = frozenset({*CacheWithDefault.NON_HASH_ATTRIBUTES, "_misc"})
      def __init__(self, name: str):
          # Attributes which affect default value generation should come before super().__init__()
          self._name = name
          super().__init__()
          # Other attributes should not affect how default value is generated, add them to NON_HASH_ATTRIBUTES
          self._misc = "foo"

      # Define logic for defaults in _get_data
      def _get_data(self, key: str) -> str:
          return f"{self._name}_{key}"

  cache = MyCache("first")
  assert cache["foo"] == "first_foo"
  ```
