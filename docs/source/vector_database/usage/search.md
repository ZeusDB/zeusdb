# Similarity Search

Perform similarity search to find the most similar vectors in your index.

**HNSWIndex.<span style="color: #663399;">search</span>**(<br/>
&emsp;&emsp;**vector: list[float] | list[list[float]] | np.ndarray**,<br/>
&emsp;&emsp;**filter: dict[str, Any] | None = None**,<br/>
&emsp;&emsp;**top_k: int = 10**,<br/>
&emsp;&emsp;**ef_search: int | None = None**,<br/>
&emsp;&emsp;**return_vector: bool = False**,<br/>
&emsp;&emsp;**rerank: int | None = None**<br/>
)

Query the index using a new vector and retrieve the top-k nearest neighbors. Supports both single vector queries and batch searches with multiple vectors. You can also filter by metadata or return the stored vectors.

```{admonition} Parameters
:class: note

vector : *list[float], list[list[float]], or np.ndarray, required*
:   The query vector (single: `list[float]` or 1D `np.ndarray`) or batch of query vectors (`list[list[float]]` or 2D `np.ndarray`) to compare against the index. Must match the index dimension and contain only finite values. A query vector containing `NaN` or an infinity raises `ValueError`.

filter : *dict[str, Any] or None, default None*
:   Optional metadata filter. A field maps either to a plain value, meaning equality, or to a dict of operators. See [Metadata Filtering](../metadata_filtering.md) for the operators and their behaviour.

top_k : *int, default 10*
:   Number of nearest neighbors to return for each query vector.

ef_search : *int or None, default None*
:   Search complexity parameter. Higher values improve accuracy at the cost of speed. The default depends on the distance metric: `max(2 × top_k, 100)` for `cosine` and `max(2 × top_k, 150)` for `l1` and `l2`. It has no effect on a reranked quantized search, where the traversal is widened to the rerank fetch instead; see [Product Quantization](../product_quantization.md).

return_vector : *bool, default False*
:   If `True`, the result objects will include the stored embedding vector. Under `cosine` this is the normalized form, not the values you supplied. Useful for downstream processing like re-ranking or hybrid search.

rerank : *int or None, default None*
:   Candidates fetched per requested result before rescoring against raw vectors. Only applies to a quantized index whose `storage_mode` is `quantized_with_raw`; an unquantized or `quantized_only` index ignores it. Omitted, the fetch is calibrated from the index's own data. `rerank=0` turns reranking off and returns ADC scores. See [Product Quantization](../product_quantization.md).
```


<br />

```{admonition} Returns
:class: tip

Single Query
:   Returns `list[dict]` where each dict contains:
    
    * `id` - The vector ID
    * `score` - Distance (lower = more similar)
    * `metadata` - Associated metadata dictionary
    * `vector` - Stored embedding vector (only if `return_vector=True`)

Batch Query
:   Returns `list[list[dict]]` - a list of result lists, one for each input query vector, in the order the queries were given.
```

**The filter is applied after the graph search, not during it.** The index finds the `top_k` nearest vectors first and then discards the ones the filter rejects, so a selective filter can return fewer than `top_k` results, or none at all. Raise `top_k` when you filter.

**On a reranked quantized search the score is the raw-vector distance.** With `rerank=0` it is the ADC estimate. The two are not comparable, so a threshold tuned against one does not carry to the other.

## Examples

The examples below all run against this index:

```python
from zeusdb import VectorDatabase

vdb = VectorDatabase()
index = vdb.create(index_type="hnsw", dim=8)
index.add([
    {"id": "doc_001", "values": [0.1, 0.2, 0.3, 0.1, 0.4, 0.2, 0.6, 0.7], "metadata": {"author": "Alice"}},
    {"id": "doc_002", "values": [0.9, 0.1, 0.4, 0.2, 0.8, 0.5, 0.3, 0.9], "metadata": {"author": "Bob"}},
    {"id": "doc_003", "values": [0.11, 0.21, 0.31, 0.15, 0.41, 0.22, 0.61, 0.72], "metadata": {"author": "Alice"}},
    {"id": "doc_004", "values": [0.85, 0.15, 0.42, 0.27, 0.83, 0.52, 0.33, 0.95], "metadata": {"author": "Bob"}},
    {"id": "doc_005", "values": [0.12, 0.22, 0.33, 0.13, 0.45, 0.23, 0.65, 0.71], "metadata": {"author": "Alice"}},
])
query_vector = [0.1, 0.2, 0.3, 0.1, 0.4, 0.2, 0.6, 0.7]
```

<br />

**🔍 Search Example 1 - Basic (Returning Top 2 most similar)**

```python
results = index.search(vector=query_vector, top_k=2)
for res in results:
    print(res["id"], round(res["score"], 6), res["metadata"])
```

*Output*
```text
doc_001 0.0 {'author': 'Alice'}
doc_003 0.000988 {'author': 'Alice'}
```

<br />

**🔍 Search Example 2 - Query with metadata filter**

The filter is applied to the `top_k` nearest results after the similarity search.

```python
results = index.search(vector=query_vector, filter={"author": "Alice"}, top_k=5)
for res in results:
    print(res["id"], round(res["score"], 6), res["metadata"])
```

*Output*
```text
doc_001 0.0 {'author': 'Alice'}
doc_003 0.000988 {'author': 'Alice'}
doc_005 0.001143 {'author': 'Alice'}
```

<br />

**🔍 Search Example 3 - Search results include vectors**

You can optionally return the stored embedding vectors alongside metadata and similarity scores by setting `return_vector=True`. Under `cosine` the stored vector is normalized to unit length, which is why the values below differ from the ones supplied.

```python
results = index.search(vector=query_vector, top_k=1, return_vector=True)
print(results[0]["id"], round(results[0]["score"], 6))
print([round(v, 4) for v in results[0]["vector"]])
```

*Output*
```text
doc_001 0.0
[0.0913, 0.1826, 0.2739, 0.0913, 0.3651, 0.1826, 0.5477, 0.639]
```

<br />

**🔍 Search Example 4 - Batch Search with a list of vectors**

Perform a similarity search on multiple query vectors simultaneously, returning results for each query.

```python
batch = [
    [0.1, 0.2, 0.3, 0.1, 0.4, 0.2, 0.6, 0.7],
    [0.9, 0.1, 0.4, 0.2, 0.8, 0.5, 0.3, 0.9],
]
results = index.search(vector=batch, top_k=2)
for q, hits in enumerate(results):
    print(f"query {q}:", [(h["id"], round(h["score"], 6)) for h in hits])
```

*Output*
```text
query 0: [('doc_001', 0.0), ('doc_003', 0.000988)]
query 1: [('doc_002', 0.0), ('doc_004', 0.002238)]
```

<br />

**🔍 Search Example 5 - Batch Search with NumPy Array**

Perform a similarity search on multiple query vectors from a NumPy array, returning results for each query.

```python
import numpy as np

query_batch = np.array(batch, dtype=np.float32)

results = index.search(vector=query_batch, top_k=2)
for q, hits in enumerate(results):
    print(f"query {q}:", [h["id"] for h in hits])
```

*Output*
```text
query 0: ['doc_001', 'doc_003']
query 1: ['doc_002', 'doc_004']
```

<br />

**🔍 Search Example 6 - Batch Search with metadata filter**

The same filter is applied to every query in the batch. The second query below returns nothing, because both of its two nearest neighbours are Bob's.

```python
results = index.search(batch, filter={"author": "Alice"}, top_k=2)
for q, hits in enumerate(results):
    print(f"query {q}:", [h["id"] for h in hits])
```

*Output*
```text
query 0: ['doc_001', 'doc_003']
query 1: []
```
