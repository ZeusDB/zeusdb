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
:   Optional metadata filter. A field maps either to a plain value, meaning equality, or to a dict of operators, and `$and`, `$or` and `$not` compose whole filters. See [Metadata Filtering](../metadata_filtering.md) for the operators and their behaviour.

top_k : *int, default 10*
:   Number of nearest neighbors to return for each query vector, from 0 to 65,536. A larger value raises `ValueError`.

ef_search : *int or None, default None*
:   Search complexity parameter, from 0 to 131,072. Higher values improve accuracy at the cost of speed. The default depends on the distance metric: `max(2 × top_k, 100)` for `cosine` and `dot`, and `max(2 × top_k, 150)` for `l1` and `l2`. It has no effect on a reranked quantized search, where the traversal is widened to the rerank fetch instead; see [Product Quantization](../product_quantization.md).

return_vector : *bool, default False*
:   If `True`, the result objects will include the stored embedding vector as a `list` of Python floats. Under `cosine` this is the normalized form, not the values you supplied; under `l1`, `l2` and `dot` it is the values as given. Useful for downstream processing like re-ranking or hybrid search.

rerank : *int or None, default None*
:   Candidates fetched per requested result before rescoring against raw vectors. Only applies to a quantized index whose `storage_mode` is `quantized_with_raw`; an unquantized or `quantized_only` index ignores it. Omitted, the fetch is calibrated from the index's own data. `rerank=0` turns reranking off and returns the distances to the reconstructions. See [Product Quantization](../product_quantization.md).
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

**The filter decides which records are ranked, not which results survive.** A search asking for five results with a filter matching a hundred records returns the five nearest of those hundred. `top_k` is the page size and nothing else, so there is no need to raise it when you filter. A filter matching fewer records than `top_k` returns that many, and one matching none returns an empty list. See [Metadata Filtering](../metadata_filtering.md) for what a filtered search costs and how to make it cheap.

**On a quantized index the score is a distance to the record's reconstruction unless the page is reranked.** With rerank on, which is the default for `quantized_with_raw`, the score is the exact distance to the raw vector. With `rerank=0` it is the distance to the reconstruction. Both are on the scale the index's own space reports, so a page is on one scale whichever you asked for, but the two are not equal and the difference is the quantization error.

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

The filter chooses which records are ranked, so the page holds the nearest of Alice's documents and nothing else.

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

Three records match, so a page of five holds three. That is not a truncation.

<br />

**🔍 Search Example 3 - Search results include vectors**

You can optionally return the stored embedding vectors alongside metadata and similarity scores by setting `return_vector=True`. Under `cosine` the stored vector is normalized to unit length, which is why the values below differ from the ones supplied. The vector is a `list` of Python floats, from both `search()` and `get_records()`.

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

Perform a similarity search on multiple query vectors from a NumPy array, returning results for each query. A 2-D array of `float32` or `float64` is read directly.

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

The same filter is applied to every query in the batch. Each query gets the two nearest of Alice's documents, which for the second query are not among its two nearest documents overall.

```python
results = index.search(batch, filter={"author": "Alice"}, top_k=2)
for q, hits in enumerate(results):
    print(f"query {q}:", [h["id"] for h in hits])
```

*Output*
```text
query 0: ['doc_001', 'doc_003']
query 1: ['doc_005', 'doc_003']
```

<br />

**🔍 Search Example 7 - The bounds on `top_k` and `ef_search`**

Both are capped, because each sizes an allocation the graph makes before it visits a node.

```python
try:
    index.search(query_vector, top_k=65537)
except ValueError as error:
    print(str(error).split(".")[0])

try:
    index.search(query_vector, ef_search=131073)
except ValueError as error:
    print(str(error).split(".")[0])
```

*Output*
```text
top_k must be at most 65536, got 65537
ef_search must be at most 131072, got 131073
```
