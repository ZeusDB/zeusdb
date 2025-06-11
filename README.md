# ZeusDB

<div align="left">
  <table>
    <tr>
      <td><strong>Meta</strong></td>
      <td>
        <a href="https://pypi.org/project/zeusdb/"><img src="https://img.shields.io/pypi/v/zeusdb?label=PyPI&color=blue"></a>&nbsp;
        <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%7C3.11%7C3.12%7C3.13-blue?logo=python&logoColor=ffdd54"></a>&nbsp;
        <a href="https://github.com/zeusdb/zeusdb/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg"></a>&nbsp;
        <!-- &nbsp;
        <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv"></a>&nbsp;
        <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>&nbsp;
        <a href="https://www.rust-lang.org"><img src="https://img.shields.io/badge/Powered%20by-Rust-black?logo=rust&logoColor=white" alt="Powered by Rust"></a>&nbsp;
        <a href="https://pypi.org/project/zeusdb/"><img src="https://img.shields.io/pypi/dm/zeusdb?label=PyPI%20downloads"></a>&nbsp;
        <a href="https://pepy.tech/project/zeusdb"><img src="https://static.pepy.tech/badge/zeusdb"></a>
        -->
      </td>
    </tr>
  </table>
</div>

<!-- badges: end -->


## ✨ What is ZeusDB?

ZeusDB is a next-generation, high-performance data platform designed for modern analytics, machine learning, and real-time insights. Born out of the need for scalable, intelligent data infrastructure, ZeusDB fuses the power of traditional databases with the flexibility and performance of modern data architectures. It is built for data teams, engineers, and analysts who need low-latency access to complex analytical workflows, without sacrificing ease of use or developer control.

ZeusDB serves as the backbone for demanding applications, offering advanced features such as:

  - Vector and structured data support to power hybrid search, recommendation engines, and LLM integrations.

  - Real-time analytics with low-latency querying, ideal for dashboards and ML model serving.

  - Extensibility and safety through modern languages like Rust and Python, enabling custom logic and high-performance pipelines.

  - DevOps-ready deployment across cloud or on-prem, with version-controlled configuration, observability hooks, and minimal operational overhead.

Whether you are building a GenAI backend, managing large-scale time-series data, or architecting a unified analytics layer, ZeusDB gives you the foundation to move fast and with incredible scale.

<br/>

## 📦 Installation

You can install ZeusDB with 'uv' or alternatively using 'pip'.

### Recommended (with uv):
```bash
uv pip install zeusdb
```

### Alternatively (using pip):
```bash
pip install zeusdb
```

<br/>



## ZeusDB Vector Database

### Quick Start Example 

```python
# Import the vector database module from ZeusDB
from zeusdb import VectorDatabase

# Instantiate the VectorDatabase class
vdb = VectorDatabase()

# Initialize and set up the database resources
vdb.create(method="HNSW")

# Upload vector records
vdb.upsert()

# Perform a similarity search and print the top 5 results 
results = vdb.search(query, k=5)
print(results)
```

<br/>

## 📄 License

This project is licensed under the Apache License 2.0.
