---
orphan: true
---



# Installation

You can install ZeusDB with 'uv' or alternatively using 'pip'.


Recommended (with uv):
```bash
uv pip install zeusdb
```

Alternatively (just with pip):
```bash
pip install zeusdb
```

<br />

## Python version support
Officially Python 3.10, 3.11, 3.12, 3.13 and 3.14.

<br /> 

## Dependencies

Installing `zeusdb` brings in the vector database and its dependencies automatically.

| Package | Version installed |
|---------|---------------------------|
| [zeusdb-vector-database](https://github.com/ZeusDB/zeusdb-vector-database) | 0.8.x (`>=0.8.0,<0.9.0`) |
| [NumPy](https://numpy.org/) | `>=2.2.6,<3.0.0` (required by the vector database) |

Prebuilt wheels are published for Linux x86_64 and aarch64 (glibc and musl), macOS Apple Silicon, and Windows x86_64.
