# CHANGELOG

## v0.9.0 (2024-07-26)

### Feature

* feat(lru_queue): add pop_many and refactor ([`d05f82d`](https://github.com/Rizhiy/class-cache/commit/d05f82d09a486bc70ed4752e6c34066dc7c4f6aa))

## v0.8.0 (2024-07-25)

### Feature

* feat(lru_queue): add LRUQueue ([`520f470`](https://github.com/Rizhiy/class-cache/commit/520f470efc12dc6c3453edcec155205d0a20784e))

### Test

* test: fix iterator call ([`29f2c0f`](https://github.com/Rizhiy/class-cache/commit/29f2c0f75de2e421dc7a8f1589418469973016e5))

## v0.7.1 (2024-07-22)

### Fix

* fix(core): improve argument types of Cache ([`22281c9`](https://github.com/Rizhiy/class-cache/commit/22281c986534804b6417c7a92f08f49e105598f4))

### Refactor

* refactor(backend): remove BaseBackend ([`3a0b499`](https://github.com/Rizhiy/class-cache/commit/3a0b49991649f236701743eebb44aaff1a5f3a64))

### Style

* style: update ruff in pre-commit and format ([`86a75ee`](https://github.com/Rizhiy/class-cache/commit/86a75eef920ca73424dee40f520e428c381571c8))

## v0.7.0 (2024-06-04)

### Feature

* feat(wrappers): add expiration wrapper ([`0f3483f`](https://github.com/Rizhiy/class-cache/commit/0f3483f74cf78fb2caf62518c75df224a8668c59))

### Fix

* fix(wrapper): fix utc setting for python 3.10 ([`0c95282`](https://github.com/Rizhiy/class-cache/commit/0c952828960883b4aa64870391503e3d98d10cef))

## v0.6.1 (2024-06-03)

### Chore

* chore: remove wrong comment ([`c120521`](https://github.com/Rizhiy/class-cache/commit/c1205210976003ed0b3e7aa5ef1ef75a511f3065))

* chore(benchmark): add results ([`2db93f3`](https://github.com/Rizhiy/class-cache/commit/2db93f301bdaf517e8712cf9863def6661308e8c))

### Documentation

* docs(README): add example of using Brotli wrapper ([`bb31482`](https://github.com/Rizhiy/class-cache/commit/bb3148217a00de6612895006d2a4c1b90d5d3d45))

### Fix

* fix(backend): commit after setting an item in sqlitebackend ([`55ed493`](https://github.com/Rizhiy/class-cache/commit/55ed493380d29bbef4512985ffe77d6425ffa88f))

### Refactor

* refactor(backends): change SQLiteBackend to use connection directly ([`bbd4e92`](https://github.com/Rizhiy/class-cache/commit/bbd4e9276471e4818d4b812e568edc4e7649ce7d))

## v0.6.0 (2024-06-02)

### Chore

* chore(black): bring back magical comma skip ([`35606da`](https://github.com/Rizhiy/class-cache/commit/35606daa8a7fbe745047b9a87b49698623674980))

### Feature

* feat(wrappers): make wrappers more general and refactor a lot ([`debe119`](https://github.com/Rizhiy/class-cache/commit/debe1192687605224a861d2d42c13fc1a22204d3))

### Refactor

* refactor(wrapper): change a bit ([`a1a7273`](https://github.com/Rizhiy/class-cache/commit/a1a72739747ed72149f350d223ce52c3c5d216ff))

## v0.5.0 (2024-06-01)

### Feature

* feat(backend): add brotli compression wrapper ([`cfff762`](https://github.com/Rizhiy/class-cache/commit/cfff762c7e2131fde3b865a4422d6a616555dd04))

## v0.4.1 (2024-05-27)

### Fix

* fix(backend): add proper extension for sqlite db files ([`f2063c6`](https://github.com/Rizhiy/class-cache/commit/f2063c6b69c00925b63143914d1efabc334352d5))

## v0.4.0 (2024-05-27)

### Feature

* feat(backend): add SQLiteBackend ([`f5640ce`](https://github.com/Rizhiy/class-cache/commit/f5640cec799a81e15eb65ef53950f59f6d5decc0))

### Test

* test(backend): add test for block splitting ([`7b6aa1d`](https://github.com/Rizhiy/class-cache/commit/7b6aa1dd127f5ab9f6ef9623f240e054aa83f366))

## v0.3.0 (2024-05-27)

### Chore

* chore(pyproject): add benchmark to exclude ([`26d4219`](https://github.com/Rizhiy/class-cache/commit/26d421977a14d7e0519b86284a1d334064c24b27))

### Feature

* feat(backend): add block splitting to PickleBackend ([`a8fcb94`](https://github.com/Rizhiy/class-cache/commit/a8fcb94d28b8eb5c6bf8264e5d263b9b6a756e89))

## v0.2.1 (2024-05-27)

### Chore

* chore: add pre-commit ([`f7050eb`](https://github.com/Rizhiy/class-cache/commit/f7050eb57345a667a681e6d93233c0c49c389f3b))

### Documentation

* docs(README): add dev instructions ([`878a6a7`](https://github.com/Rizhiy/class-cache/commit/878a6a7441a4cfa4545b3f9fdb659798e0f6392f))

### Fix

* fix(core.py): fix clear() and add more tests ([`7389321`](https://github.com/Rizhiy/class-cache/commit/73893218a52d341b25fda98eea7d97638b70e0f9))

## v0.2.0 (2024-05-26)

### Documentation

* docs(README): add install instructions and basic usage example ([`6572cd5`](https://github.com/Rizhiy/class-cache/commit/6572cd5476e718b4a6c04937006560a7a374b185))

### Feature

* feat(core): implement CacheWithDefault properly ([`b5523d1`](https://github.com/Rizhiy/class-cache/commit/b5523d1bae9e7cbed62276caad1d4bb7e62e4f0c))

### Test

* test(github): fix requests version ([`5052e95`](https://github.com/Rizhiy/class-cache/commit/5052e957d3dab986553f0a3eccad6e6128c647b2))

* test(github): fix coverage module selection ([`8dee97d`](https://github.com/Rizhiy/class-cache/commit/8dee97d67cc66e902e0b9ca285f30649928d3605))

## v0.1.0 (2024-05-26)

### Chore

* chore: add placeholder ([`aa69282`](https://github.com/Rizhiy/class-cache/commit/aa6928222a6152ecc0e89aba0837b86d13d51076))

### Feature

* feat(core): implement basic functionality ([`7d66af5`](https://github.com/Rizhiy/class-cache/commit/7d66af57bb201273ecaf24abfe9684a0bd7c1778))

### Style

* style: fix config ([`3c1c49c`](https://github.com/Rizhiy/class-cache/commit/3c1c49c82f3f968dadadda659362ba04c1f3fb49))

* style: format ([`ac82a7d`](https://github.com/Rizhiy/class-cache/commit/ac82a7d3994089e664330d2270d9e8135d0fa4be))

### Test

* test: remove python 3.9 from CI ([`be4a369`](https://github.com/Rizhiy/class-cache/commit/be4a3698b2fa9793f603a3596ebdc23ad1c047b3))

* test: remove aws auth from CI ([`dcb3a38`](https://github.com/Rizhiy/class-cache/commit/dcb3a38af6baf5a705d6d4590c34c7fb501f7870))

* test: add tests and CI ([`4e9fcc8`](https://github.com/Rizhiy/class-cache/commit/4e9fcc82170de71217de1e12b1527ad08506a91c))
