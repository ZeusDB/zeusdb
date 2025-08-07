# Getting Started

This guide will help you get up and running quickly with high-performance vector similarity search.

## 📦 Installation

You can install ZeusDB Vector Database with 'uv' or alternatively using 'pip'.

Recommended (with uv):
```python
uv pip install zeusdb
```

Alternatively (just with pip):
```{code-block} python
pip install zeusdb
```

<br />

## 🔥 Quick Start Example

Here's a complete example showing the core functionality of ZeusDB Vector Database:


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

*Results Output:*
```text
--- Add Results Summary ---
✅ 5 inserted, ❌ 0 errors

--- Raw Results Format ---
[{'id': 'doc_001', 'score': 0.0, 'metadata': {'author': 'Alice'}}, {'id': 'doc_003', 'score': 0.0009883458260446787, 'metadata': {'author': 'Alice'}}]

--- Formatted Results ---
1. ID: doc_001, Score: 0.0000, Metadata: {'author': 'Alice'}
2. ID: doc_003, Score: 0.0010, Metadata: {'author': 'Alice'}
```
