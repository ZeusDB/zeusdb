# Useful Utilities

ZeusDB Vector Database includes a suite of utility functions to help you inspect, manage, and maintain your index. You can view index configuration, attach custom metadata, list stored records, inspect statistics, remove vectors by ID, and reclaim the space removals leave behind. These tools make it easy to monitor and evolve your index over time, whether you are experimenting locally or deploying in production.

## Examples

The examples below all run against this index:

```python
from zeusdb import VectorDatabase

vdb = VectorDatabase()
index = vdb.create(index_type="hnsw", dim=8, expected_size=5)
index.add([
    {"id": "doc_001", "values": [0.1, 0.2, 0.3, 0.1, 0.4, 0.2, 0.6, 0.7], "metadata": {"author": "Alice"}},
    {"id": "doc_002", "values": [0.9, 0.1, 0.4, 0.2, 0.8, 0.5, 0.3, 0.9], "metadata": {"author": "Bob"}},
    {"id": "doc_003", "values": [0.11, 0.21, 0.31, 0.15, 0.41, 0.22, 0.61, 0.72], "metadata": {"author": "Alice"}},
    {"id": "doc_004", "values": [0.85, 0.15, 0.42, 0.27, 0.83, 0.52, 0.33, 0.95], "metadata": {"author": "Bob"}},
    {"id": "doc_005", "values": [0.12, 0.22, 0.33, 0.13, 0.45, 0.23, 0.65, 0.71], "metadata": {"author": "Alice"}},
])
```

<br/>

**Example 1 - Check the details of your HNSW index**

```python
print(index.info()) 
```
*Output*
```text
HNSWIndex(dim=8, space=cosine, m=16, ef_construction=200, expected_size=5, vectors=5, quantization=none)
```

The `vectors=` field is the live record count, in every storage mode. `get_vector_count()` returns the same number. Other single-value accessors: `index.dim`, `index.get_space()`, `index.contains(id)`, `index.has_quantization()`, `index.can_use_quantization()`, and `VectorDatabase.available_index_types()`.

<br/>


**Example 2 - Add index level metadata**

Index level metadata is a flat string-to-string map, separate from the per-record metadata used for filtering. It is preserved by `save()` and `load()`.

```python
index.add_metadata({
    "creator": "John Smith",
    "version": "0.1",
    "created_at": "2024-01-28T11:35:55Z",
    "embedding_model": "openai/text-embedding-ada-002",
    "environment": "production",
})

# View index level metadata by key
print(index.get_metadata("creator"))

# View all index level metadata
for key, value in sorted(index.get_all_metadata().items()):
    print(f"{key}: {value}")
```
*Output*
```text
John Smith
created_at: 2024-01-28T11:35:55Z
creator: John Smith
embedding_model: openai/text-embedding-ada-002
environment: production
version: 0.1
```

`get_all_metadata()` returns a `dict` whose iteration order is not stable, which is why the example sorts it.

<br/>


**Example 3 - List records in the index**

```python
for record_id, metadata in sorted(index.list(number=5)):
    print(record_id, metadata)
```
*Output*
```text
doc_001 {'author': 'Alice'}
doc_002 {'author': 'Bob'}
doc_003 {'author': 'Alice'}
doc_004 {'author': 'Bob'}
doc_005 {'author': 'Alice'}
```

`list()` returns `(id, metadata)` tuples in no particular order, so the example sorts them. It is not a paging API: `number` takes the first N in whatever order internal storage yields, and the same N are not guaranteed across calls. It lists every record, in every storage mode.

<br/>

**Example 4 - Remove Records**

ZeusDB allows you to remove a vector and its associated metadata from the index using the `.remove_point(id)` method. This performs a <u>logical deletion</u>, meaning:
- The vector is deleted from internal storage.
- The metadata is removed.
- The vector ID is no longer returned by `.contains()`, `.get_records()`, or `.search()`.

```python
index.remove_point("doc_001")

print("doc_001 present:", index.contains("doc_001"))
print("records remaining:", index.get_vector_count())
```
*Output*
```text
doc_001 present: False
records remaining: 4
```

**⚠️ Please Note:** Due to the nature of HNSW, the underlying graph node remains in memory after a point is removed. Searches never return it, but it still occupies memory and edge slots. Removed and overwritten records no longer consume result slots, so `top_k` does not degrade with churn, and `compact()` reclaims the stranded nodes.

<br/>

**Example 5 - Reclaim space left by removals and overwrites**

Both `remove_point()` and an overwriting `add()` leave a node behind in the graph. `compact()` rebuilds the graph in memory and returns the number of nodes it reclaimed. Nothing else changes: IDs, metadata, stored vectors, quantized codes and PQ training state all survive, so every ID resolves to the same record before and after.

```python
print("stranded graph nodes:", index.get_stats()["stranded_graph_nodes"])
print("reclaimed:", index.compact())
print("stranded graph nodes:", index.get_stats()["stranded_graph_nodes"])
```
*Output*
```text
stranded graph nodes: 1
reclaimed: 1
stranded graph nodes: 0
```

`compact()` costs a full rebuild, proportional to the number of live records rather than to the amount of debris, and it holds both graphs in memory while it runs. It returns 0 and does nothing when there is nothing to reclaim. It is never automatic, so schedule it when your workload has accumulated deletions.

<br/>

**Example 6 - Inspect index statistics**

```python
stats = index.get_stats()
for key in ["total_vectors", "graph_nodes", "stranded_graph_nodes", "storage_mode_description"]:
    print(f"{key}: {stats[key]}")
```
*Output*
```text
total_vectors: 4
graph_nodes: 4
stranded_graph_nodes: 0
storage_mode_description: raw_only
```

`get_stats()` returns a string-to-string map. It also carries `dimension`, `space`, `m`, `ef_construction`, `expected_size`, `index_type`, `raw_vectors_stored`, `quantized_codes_stored` and `storage_mode`, plus training, compression and rerank calibration fields once quantization is configured.

It is also where the memory figures live, on every index rather than only on a quantized one. `graph_memory_mb` is the HNSW graph, `raw_vectors_memory_mb` is the raw vector store and `total_memory_mb` is the sum of the structures the index holds. `total_memory_mb` is not the resident set: the id maps, the metadata map and the allocator's own overhead sit outside it, at roughly 1,500 bytes per record. Size infrastructure from a measured resident figure rather than the reported one.

<br/>

**Example 7 - Retrieve records by ID**

Use `get_records()` to fetch one or more records by ID. It returns a list of dicts with `id`, `metadata`, and, unless `return_vector=False`, `vector`.

```python
# Single record
print(index.get_records("doc_002", return_vector=False))

# Multiple records
print(index.get_records(["doc_002", "doc_003"], return_vector=False))

# Missing IDs are silently skipped
print(index.get_records(["doc_002", "missing_id"], return_vector=False))

# Vectors are included by default
record = index.get_records("doc_002")[0]
print(sorted(record.keys()), len(record["vector"]))
```

*Output*
```text
[{'id': 'doc_002', 'metadata': {'author': 'Bob'}}]
[{'id': 'doc_002', 'metadata': {'author': 'Bob'}}, {'id': 'doc_003', 'metadata': {'author': 'Alice'}}]
[{'id': 'doc_002', 'metadata': {'author': 'Bob'}}]
['id', 'metadata', 'vector'] 8
```

⚠️ `get_records()` only returns results for IDs that exist in the index. Missing IDs are silently skipped, so a shorter list than you asked for is how a missing ID is reported. Under `cosine` the returned vector is the normalized form, and on a trained `quantized_only` index it is reconstructed from the code rather than stored raw; see [Product Quantization](product_quantization.md).

<br />

## Concurrency

Concurrent search from multiple threads is supported and scales, measured at roughly seven times the single-thread throughput at sixteen threads. `add()` and `search()` can also run concurrently from different threads. `benchmark_concurrent_reads()` measures concurrent search throughput on your own index and data.

<br />
