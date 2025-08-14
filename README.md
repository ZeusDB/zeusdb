<p align="center" width="100%">
  <img src="https://github.com/user-attachments/assets/d2c33f8d-ba76-444e-89a5-96b572a25120" />
  <h1 align="center">ZeusDB</h1>
</p>

<div align="center">
  <table>
    <tr>
      <td><strong>Meta</strong></td>
      <td>
        <a href="https://pypi.org/project/zeusdb/"><img src="https://img.shields.io/pypi/v/zeusdb?label=PyPI&color=blue"></a>&nbsp;
        <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%7C3.11%7C3.12%7C3.13-blue?logo=python&logoColor=ffdd54"></a>&nbsp;
        <a href="https://github.com/zeusdb/zeusdb/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg"></a>&nbsp;
        <a href="https://docs.zeusdb.com"><img src="https://readthedocs.org/projects/zeusdb/badge/?version=latest" alt="Documentation Status"></a>&nbsp;
        <a href="https://github.com/ZeusDB"><img src="https://github.com/user-attachments/assets/e140d900-1160-4eaa-85c0-2b3507a5f0f5" alt="ZeusDB"></a>&nbsp;
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

Whether you are building a GenAI backend, managing large-scale time-series data, or architecting a unified analytics layer, ZeusDB gives you the foundation to move fast, at scale, with the flexibility of modular architecture.

<br/>

## 🛠️ Installation

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

## 📦 ZeusDB Vector Database

ZeusDB Vector Database is a high-performance, Rust-powered vector database built for fast and scalable similarity search across high-dimensional embeddings. Designed for modern machine learning and AI workloads, it provides efficient approximate nearest neighbor (ANN) search, supports real-time querying at scale, and seamlessly transitions from in-memory performance to durable disk persistence.

Whether you're powering document search, enabling natural language interfaces, or building custom vector-based tools, ZeusDB offers a lightweight, extensible foundation for high-performance vector retrieval. It’s also well-suited for Retrieval-Augmented Generation (RAG) pipelines, where fast and semantically rich context retrieval is critical to enhancing large language model (LLM) responses.

<br/>

### ⭐ Features

*"Start fast. Tune deep. Build for any scale."*

🐍 User-friendly Python API for adding vectors and running similarity searches

🔥 High-performance Rust backend optimized for speed and concurrency

🔍 Approximate Nearest Neighbor (ANN) search using HNSW for lightning fast results

📦 Product Quantization (PQ) for compact storage, faster distance computations, and scalability for Big Data

📥 Flexible input formats, including native Python types and NumPy arrays

🗂️ Metadata filtering for precise and contextual querying

💾 Save and reload full indexes, metadata, and quantized vectors across systems

📝 Enterprise-grade logging with flexible formats and output targets

<br/>

### 🔥 Quick Start Example 

```python
# Import the vector database module
from zeusdb import VectorDatabase

# Instantiate the VectorDatabase class
vdb = VectorDatabase()

# Initialize and set up the database resources
index = vdb.create(index_type="hnsw", dim=8)

# Vector embeddings with accompanying ID's and Metadata
records = [
    {"id": "doc_001", "values": [0.1, 0.2, 0.3, 0.1, 0.4, 0.2, 0.6, 0.7], "metadata": {"author": "Alice"}},
    {"id": "doc_002", "values": [0.9, 0.1, 0.4, 0.2, 0.8, 0.5, 0.3, 0.9], "metadata": {"author": "Bob"}},
    {"id": "doc_003", "values": [0.11, 0.21, 0.31, 0.15, 0.41, 0.22, 0.61, 0.72], "metadata": {"author": "Alice"}},
    {"id": "doc_004", "values": [0.85, 0.15, 0.42, 0.27, 0.83, 0.52, 0.33, 0.95], "metadata": {"author": "Bob"}},
    {"id": "doc_005", "values": [0.12, 0.22, 0.33, 0.13, 0.45, 0.23, 0.65, 0.71], "metadata": {"author": "Alice"}},
]

# Upload records using the `add()` method
add_result = index.add(records)
print("\n--- Add Results Summary ---")
print(add_result.summary())

# Perform a similarity search and print the top 2 results
# Query Vector
query_vector = [0.1, 0.2, 0.3, 0.1, 0.4, 0.2, 0.6, 0.7]

# Query with no filter (all documents)
results = index.search(vector=query_vector, filter=None, top_k=2)
print("\n--- Query Results Output - Raw ---")
print(results)

print("\n--- Query Results Output - Formatted ---")
for i, res in enumerate(results, 1):
    print(f"{i}. ID: {res['id']}, Score: {res['score']:.4f}, Metadata: {res['metadata']}")
```

*Output*
```
--- Add Results Summary ---
✅ 5 inserted, ❌ 0 errors

--- Raw Results Format ---
[{'id': 'doc_001', 'score': 0.0, 'metadata': {'author': 'Alice'}}, {'id': 'doc_003', 'score': 0.0009883458260446787, 'metadata': {'author': 'Alice'}}]

--- Formatted Results ---
1. ID: doc_001, Score: 0.0000, Metadata: {'author': 'Alice'}
2. ID: doc_003, Score: 0.0010, Metadata: {'author': 'Alice'}
```

<br/>

## 📄 License

This project is licensed under the Apache License 2.0.
