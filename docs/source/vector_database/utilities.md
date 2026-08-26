# Useful Utilities

ZeusDB Vector Database includes a suite of utility functions to help you inspect, manage, and maintain your index. You can view index configuration, attach custom metadata, list and page through stored records, inspect statistics, count and test membership, remove vectors one at a time or in bulk, change a record's metadata, reclaim the space removals leave behind, empty the index, and rebuild the graph at a new configuration. These tools make it easy to monitor and evolve your index over time, whether you are experimenting locally or deploying in production.

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

The `vectors=` field is the live record count, in every storage mode. `get_vector_count()` and `len(index)` return the same number. `get_stats()["raw_vectors_stored"]` is the one that counts raw vectors specifically, and on a trained `quantized_only` index it is zero.

`index.dim`, `index.space`, `index.m`, `index.ef_construction`, `index.expected_size` and `index.indexed_fields` are read-only properties. `get_space()` is the same value as `index.space` as a method and is kept for callers already using it. Other single-value accessors: `index.contains(id)`, `index.has_quantization()`, `index.can_use_quantization()`, and `VectorDatabase.available_index_types()`.

```python
print(index.dim, index.space, index.m, index.ef_construction, index.expected_size, index.indexed_fields)
```
*Output*
```text
8 cosine 16 200 5 []
```

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


**Example 3 - List and page through the records in the index**

```python
for record_id, metadata in index.list(number=5):
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

`list()` returns `(id, metadata)` tuples **in the order the records were added**, and `offset` pages through them. `number` defaults to 10. It lists every record, in every storage mode, and the order survives `save()` and `load()`.

```python
print(index.list(number=2, offset=0))
print(index.list(number=2, offset=2))
print(index.list(number=2, offset=4))
print(index.list(number=2, offset=99))
```
*Output*
```text
[('doc_001', {'author': 'Alice'}), ('doc_002', {'author': 'Bob'})]
[('doc_003', {'author': 'Alice'}), ('doc_004', {'author': 'Bob'})]
[('doc_005', {'author': 'Alice'})]
[]
```

An offset past the end returns an empty list rather than raising.

**Deleting while you page shifts the pages under `offset`.** Removing a record ahead of your cursor moves everything behind it up by one, so the next page skips one. Page with `after` instead, which names the last ID you saw.

```python
paged = vdb.create("hnsw", dim=2)
paged.add({"ids": [f"p{n}" for n in range(5)], "embeddings": [[n, 0.0] for n in range(5)]})

first = paged.list(number=2)
print([record_id for record_id, _ in first])
paged.remove_point("p0")
print([record_id for record_id, _ in paged.list(number=2, after=first[-1][0])])
print([record_id for record_id, _ in paged.list(number=2, offset=2)])
```

*Output*
```text
['p0', 'p1']
['p2', 'p3']
['p3', 'p4']
```

`offset` skipped `p2` because a record ahead of it was removed. `after` did not, because it names a position rather than a count.

`after` and `offset` cannot both be given, and passing both raises `ValueError`. If the record `after` names has itself been removed there is no position to resume from, and the call raises `KeyError` rather than returning a page from somewhere else.

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

`remove_points(ids)`, `remove_where(filter)` and `delete()` remove a batch and a filtered set; see Examples 10 and 11 below.

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

`get_stats()` returns a string-to-string map. Every key it carries:

| Key | Holds |
| --- | --- |
| `dimension`, `space`, `m`, `ef_construction`, `expected_size`, `index_type` | The configuration the index was created with |
| `total_vectors` | The live record count |
| `graph_nodes`, `stranded_graph_nodes` | Nodes in the HNSW graph, and how many of them no record uses |
| `raw_vectors_stored`, `quantized_codes_stored` | Records held at full width, and records held as codes |
| `storage_mode`, `storage_mode_description`, `storage_strategy` | What the index is storing and serving |
| `thread_safety` | The locking the index uses |
| `graph_memory_mb` | The HNSW graph, being the neighbour lists and, on a quantized index, the codes it scores against. It holds no raw vector |
| `raw_vectors_memory_mb` | The raw vectors, which are held once |
| `quantized_codes_memory_mb` | The codes, which grow with the record count |
| `codebook_memory_mb`, `sdc_table_memory_mb`, `centroid_norm_memory_mb` | The trained tables, fixed by `dim`, `subvectors` and `bits` |
| `index_bookkeeping_memory_mb` | The hash tables that find a record, including the per-record metadata map |
| `total_memory_mb` | The sum of the seven figures above |
| `quantization_type` | `pq`, or `none` on an unquantized index |

On a quantized index it also carries `quantization_active`, `quantization_trained`, `quantization_compression_ratio`, `quantization_training_size`, `training_progress`, `training_threshold_reached`, `training_vectors_needed`, `raw_vectors_retained` and the rerank calibration keys described on the [Product Quantization](product_quantization.md) page.

**`total_memory_mb` is what the index asked the allocator for, not what the process holds.** Either can be the larger. An arena reserved and not yet written is asked for and not resident, and the allocator's own bookkeeping is resident and not asked for. Measured on 50,000 real 1,536-dimensional embeddings, one index per interpreter, against the resident set delta across the build:

| mode | reported | resident | reported / resident |
|---|---:|---:|---:|
| no quantization | 347.90 MiB | 334.43 MiB | 1.04 |
| `quantized_with_raw` | 348.01 | 361.70 | 0.96 |
| `quantized_only` | 55.04 | 69.12 | 0.80 |

Size infrastructure from the resident figure rather than from this one. The gap is widest under `quantized_only`, where the fixed tables and the hash tables that find a record are most of what is left.

<br/>

**Example 7 - Retrieve records by ID**

Use `get_records()` to fetch one or more records by ID. It returns a list of dicts with `id`, `metadata`, and, unless `return_vector=False`, `vector`, which is a `list` of Python floats.

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

⚠️ `get_records()` only returns results for IDs that exist in the index. Missing IDs are skipped by default, so a shorter list than you asked for is how a missing ID is reported, and the result does not say which one. `strict=True` raises `KeyError` instead, naming every ID the index does not hold.

```python
try:
    index.get_records(["doc_002", "missing_id"], strict=True)
except KeyError as error:
    print(error)
```

*Output*
```text
'get_records(strict=True) was asked for 1 id the index does not hold: missing_id. Call it without strict=True to receive the records that are present, or test an id with contains(id) first.'
```

Under `cosine` the returned vector is the normalized form, and on a trained `quantized_only` index it is reconstructed from the code rather than stored raw; see [Product Quantization](product_quantization.md).

<br />

**Example 8 - Count and test membership**

`len(index)` is the live record count. `id in index` tests membership. `count(filter)` counts the records a metadata filter matches, using the same filter language as `search()`, and `count()` with no filter is `len(index)`.

```python
print(len(index))
print("doc_002" in index, "doc_001" in index)
print(index.count())
print(index.count({"author": "Alice"}))
print(index.count({"author": "Nobody"}))
```
*Output*
```text
4
True False
4
2
0
```

`count()` is exact and therefore reads every record's metadata, so it costs what a filtered search costs. `contains(id)` is the same test as `in` and is kept for callers already using it.

<br />

**Example 9 - Change a record's metadata**

`update_metadata(id, metadata)` replaces one record's metadata without resupplying its vector. The record keeps its vector, its quantized codes and its graph node, and no node is stranded.

```python
print(index.get_records("doc_002", return_vector=False)[0]["metadata"])
print(index.update_metadata("doc_002", {"author": "Bob", "status": "reviewed"}))
print(sorted(index.get_records("doc_002", return_vector=False)[0]["metadata"].items()))
print(index.update_metadata("no_such_id", {"author": "Nobody"}))
print(index.get_stats()["stranded_graph_nodes"])
```
*Output*
```text
{'author': 'Bob'}
True
[('author', 'Bob'), ('status', 'reviewed')]
False
0
```

The example sorts the second result because a record's metadata comes back as a `dict` whose key order is not stable between processes. Read metadata by key rather than by position.

**The replacement is wholesale, not a merge.** Any key you leave out is gone, which is what `add(overwrite=True)` already does. It returns `False` for an ID the index does not hold, and writes nothing in that case. Use it rather than reading a record back with `get_records()` and adding it again, which strands a graph node per update.

<br />

**Example 10 - Remove several records at once**

`remove_points(ids)` takes the lock once for the whole batch instead of once per ID. It returns the IDs that were **not** in the index, so an empty list means every one was removed. A repeated ID is removed on its first occurrence and is never reported missing.

```python
print(index.remove_points(["doc_004", "no_such_id"]))
print(len(index))
```
*Output*
```text
['no_such_id']
3
```

`remove_where(filter)` removes every record a metadata filter matches, using the same filter language as `search()`, and returns how many it removed.

```python
print(index.remove_where({"author": "Alice"}))
print(len(index), index.count({"author": "Alice"}))
print(index.remove_where({"author": "Nobody"}))
```
*Output*
```text
2
1 0
0
```

An unrecognised operator raises `ValueError` before any record is removed. A filter matching nothing removes nothing and returns `0`.

**`remove_where({})` is refused.** An empty filter matches every record everywhere else in this language, and here that would destroy the index. Name the records with `remove_points(ids)` if that is what you want, or use `clear()`.

Both leave one stranded graph node per record removed, exactly as `remove_point()` does, and neither calls `compact()`.

<br />

**Example 11 - `delete()`, the shorter name for both**

`delete(ids=...)` dispatches to `remove_points` and `delete(where=...)` to `remove_where`. Both of those stay.

```python
deletable = vdb.create("hnsw", dim=2, expected_size=10)
deletable.add({
    "ids": ["doc_1", "doc_2", "doc_3", "doc_4"],
    "embeddings": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]],
    "metadatas": [{"author": "Alice"}, {"author": "Bob"},
                  {"author": "Bob"}, {"author": "Alice"}],
})

print(deletable.delete(ids="doc_1"))
print(deletable.delete(ids=["doc_2", "no_such_id"]))
print(deletable.delete(where={"author": "Bob"}))
print(len(deletable))
```
*Output*
```text
1
1
1
1
```

It returns **the number of records removed**, an `int`, whichever argument was given. `ids` takes a string or a list of strings. A repeated ID counts once. An ID that was not there counts zero rather than raising.

`remove_points` still returns the IDs it could not find, which is more than a count, so keep calling it where you need that.

**Passing both arguments raises `ValueError`, and so does passing neither.** Use `clear()` when emptying the index is what you mean.

<br />

**Example 12 - Empty the index with `clear()`**

`clear()` drops every record and returns how many went. It replaces the graph rather than removing records one at a time, so `stranded_graph_nodes` reads `0` afterwards.

```python
clearable = vdb.create("hnsw", dim=4, expected_size=10)
clearable.add({
    "ids": ["a", "b", "c", "d", "e"],
    "embeddings": [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
                   [0, 0, 0, 1.0], [1.0, 1.0, 0, 0]],
})
clearable.remove_point("a")

print(clearable.clear())
print(len(clearable), clearable.get_stats()["stranded_graph_nodes"])
print(clearable.clear())
```
*Output*
```text
4
0 0
0
```

**It keeps the index and drops the records.** `dim`, `space`, `m`, `ef_construction`, `expected_size`, `indexed_fields`, the index level metadata and the quantization configuration all survive, and a fitted PQ codebook survives with them, so a trained quantized index can be refilled and searched without retraining. An index still collecting for training starts collecting again.

Clearing an empty index returns `0` and is not an error. The generated ID counter is not reset, so ids generated after a clear continue the sequence rather than starting again from `vec_1`.

<br />

**Example 13 - Change `m` after the fact with `rebuild()`**

`m` is chosen from `expected_size` when the index is created, so an index declared for far fewer records than it received runs at a degree meant for the smaller one. `rebuild(m=..., expected_size=..., ef_construction=...)` builds the graph again at a new configuration, in place, and every record keeps its vector, its metadata and its id. A quantized index is rebuilt from its stored codes rather than re-encoded. Pass any of the three.

```python
sized_wrong = vdb.create("hnsw", dim=8, expected_size=100, m=4)
sized_wrong.add({
    "ids": [f"v{i}" for i in range(400)],
    "embeddings": [[float(i % 7) + j * 0.1 for j in range(8)] for i in range(400)],
})
print(sized_wrong.m, sized_wrong.expected_size, len(sized_wrong))
print(sized_wrong.rebuild(m=16, expected_size=400))
print(sized_wrong.m, sized_wrong.expected_size, len(sized_wrong))
```

*Output*
```text
4 100 400
400
16 400 400
```

It returns the node count of the graph it built, which is the live record count. Passing none of the three raises `ValueError`, because rebuilding the graph as it stands is `compact()`. The three arguments are held to the rules `create()` applies, so an invalid value raises the message `create()` raises for it.

**Raise `m` where an index outgrew its declaration, and schedule it.** It costs a full rebuild, 27.0 seconds at 100,000 real 128 dimensional vectors, and it holds both graphs in memory while it runs. Nothing outside the graph is touched, so every filter returns what it returned and a save afterwards carries the new `m`.

<br />

**Example 14 - Return the graph's spare capacity**

An index built by inserting grows its graph buffers geometrically, so the last growth leaves the largest of them holding close to twice what they use. `shrink_to_fit()` returns that slack to the allocator and reports the bytes it released. `compact()` calls it.

```python
fresh = vdb.create("hnsw", dim=8, expected_size=300)
fresh.add({
    "ids": [f"v{i}" for i in range(500)],
    "embeddings": [[float(i % 7) + j * 0.1 for j in range(8)] for i in range(500)],
})

before = float(fresh.get_stats()["graph_memory_mb"])
freed = fresh.shrink_to_fit()
after = float(fresh.get_stats()["graph_memory_mb"])
print(freed > 0, after < before)
print(fresh.shrink_to_fit())
```

*Output*
```text
True True
0
```

The index above declared 300 records and was given 500, so its graph grew and left slack behind. A second call finds nothing to release.

**No node, edge or distance is touched**, so every search returns the same page with the same scores. **Call it on an index that holds its records, not on one about to receive them.** On an empty index it hands back the whole creation reservation that `expected_size` bought, so every later insertion regrows the arenas from nothing. The index stays writable, and the buffers grow again on the next `add()`, which costs one reallocation. That is why it is never automatic.

<br />

**Example 15 - Quantization status and performance reporting**

Five further accessors report state that `get_stats()` also carries.

| Method | Returns |
| --- | --- |
| `is_training_ready()` | Whether the training threshold has been reached. `False` on an index with no quantization configuration |
| `training_vectors_needed()` | Records still to collect before training triggers. `0` on an index with no quantization configuration |
| `rebuild_with_quantization()` | Rebuilds the graph against the quantized codes and returns whether it did. Training and `load()` already do this, so calling it is normally redundant |
| `get_performance_info()` | A string-to-string map describing the search and insertion paths |
| `benchmark_concurrent_reads(query_count, max_threads)` | Times sequential against threaded searches over random queries, returning `sequential_qps`, `parallel_qps`, `speedup`, `sequential_time`, `parallel_time` and `threads_used` |

```python
ready = vdb.create("hnsw", dim=8, expected_size=1200, quantization_config={
    "type": "pq", "subvectors": 8, "bits": 8, "training_size": 1000,
})
print(ready.is_training_ready(), ready.training_vectors_needed())
print(sorted(ready.get_performance_info()))
```
*Output*
```text
False 1000
['benefits', 'insertion_path', 'quantization_accuracy_impact', 'quantization_compression', 'search_bottleneck', 'search_speedup_expected']
```

<br />

## Concurrency

Concurrent search from multiple threads is supported and scales, measured at roughly seven times the single-thread throughput at sixteen threads. `add()` and `search()` can also run concurrently from different threads. `benchmark_concurrent_reads()` measures concurrent search throughput on your own index and data.

<br />
