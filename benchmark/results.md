# Benchmark results

## Environment

CPU: AMD Ryzen 9 5950X (32) @ 3.400GHz
RAM: 64GB
SSD: SAMSUNG M.2 970 EVO Plus
OS: Ubuntu 22.04.4 LTS x86_64
Python: Python 3.11.7

### Evaluating pickle backend

```python
Got 3072 elements
Write took  12.469 seconds
Read took    3.761 seconds
944 total blocks
Size on disk: 203.89 MiB
```

### Evaluating sqlite backend

```python
Got 3072 elements
Write took  20.466 seconds
Read took    0.508 seconds
Size on disk: 364.14 MiB
```

### Evaluating brotli_pickle backend

```python
Got 3072 elements
Write took 245.952 seconds
Read took    1.422 seconds
120 total blocks
Size on disk: 36.57 MiB
```

### Evaluating brotli_sql backend

```python
Got 3072 elements
Write took 264.981 seconds
Read took    0.420 seconds
Size on disk: 52.2 MiB
```
