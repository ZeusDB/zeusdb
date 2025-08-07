# Similarity Search

Perform similarity search to find the most similar vectors in your index.

**HNSWIndex.<span style="color: #663399;">search</span>**(<br/>
&emsp;&emsp;**vector: list[float] | list[list[float]] | np.ndarray**,<br/>
&emsp;&emsp;**filter: dict[str, str] | None = None**,<br/>
&emsp;&emsp;**top_k: int = 10**,<br/>
&emsp;&emsp;**ef_search: int | None = None**,<br/>
&emsp;&emsp;**return_vector: bool = False**<br/>
)

Query the index using a new vector and retrieve the top-k nearest neighbors. Supports both single vector queries and batch searches with multiple vectors. You can also filter by metadata or return the original stored vectors.

```{admonition} Parameters
:class: note

vector : *list[float], list[list[float]], or np.ndarray, required*
:   The query vector (single: `list[float]`) or batch of query vectors (`list[list[float]]` or 2D `np.ndarray`) to compare against the index. Must match the index dimension.

filter : *dict[str, str] or None, default None*
:   Optional metadata filter. Only vectors with matching key-value metadata pairs will be considered in the search.

top_k : *int, default 10*
:   Number of nearest neighbors to return for each query vector.

ef_search : *int or None, default None*
:   Search complexity parameter. Higher values improve accuracy at the cost of speed. Defaults to `max(2 × top_k, 100)` when not specified.

return_vector : *bool, default False*
:   If `True`, the result objects will include the original embedding vector. Useful for downstream processing like re-ranking or hybrid search.
```


<br />

```{admonition} Returns
:class: tip

Single Query
:   Returns `list[dict]` where each dict contains:
    
    * `id` - The vector ID
    * `score` - Similarity score (lower = more similar)
    * `metadata` - Associated metadata dictionary
    * `vector` - Original embedding vector (only if `return_vector=True`)

Batch Query
:   Returns `list[list[dict]]` - a list of result lists, one for each input query vector.
```

## Examples

<br />

**🔍 Search Example 1 - Basic (Returning Top 2 most similar)**

```python
results = index.search(vector=query_vector, top_k=2)
print(results)
```

*Output*
```
[
  {'id': 'doc_37', 'score': 0.016932480037212372, 'metadata': {'index': '37', 'split': 'test'}}, 
  {'id': 'doc_33', 'score': 0.019877362996339798, 'metadata': {'split': 'test', 'index': '33'}}
]
```

<br />

**🔍 Search Example 2 - Query with metadata filter**

This filters on the given metadata after conducting the similarity search.

```python
query_vector = [0.1, 0.2, 0.3, 0.1, 0.4, 0.2, 0.6, 0.7]
results = index.search(vector=query_vector, filter={"author": "Alice"}, top_k=5)
print(results)
```

*Output*
```
[
  {'id': 'doc_001', 'score': 0.0, 'metadata': {'author': 'Alice'}}, 
  {'id': 'doc_003', 'score': 0.0009883458260446787, 'metadata': {'author': 'Alice'}}, 
  {'id': 'doc_005', 'score': 0.0011433829786255956, 'metadata': {'author': 'Alice'}}
]
```

<br />

**🔍 Search Example 3 - Search results include vectors**

You can optionally return the stored embedding vectors alongside metadata and similarity scores by setting `return_vector=True`. This is useful when you need access to the raw vectors for downstream tasks such as re-ranking, inspection, or hybrid scoring.

```python
results = index.search(vector=query_vector, filter={"split": "test"}, top_k=2, return_vector=True)
print(results)
```

*Output*
```
[
  {'id': 'doc_37', 'score': 0.016932480037212372, 'metadata': {'index': '37', 'split': 'test'}, 'vector': [0.36544516682624817, 0.11984539777040482, 0.7143614292144775, 0.8995016813278198]}, 
  {'id': 'doc_33', 'score': 0.019877362996339798, 'metadata': {'split': 'test', 'index': '33'}, 'vector': [0.8367619514465332, 0.6394991874694824, 0.9291712641716003, 0.9777664542198181]}
]
```

<br />

**🔍 Search Example 4 - Batch Search with a list of vectors**

Perform a similarity search on multiple query vectors simultaneously, returning results for each query.

```python
query_vector =
[
    [0.1, 0.2, 0.3],
    [0.4, 0.5, 0.6]
]
results = index.search(vector=query_vector, top_k=3)
print(results)
```

*Output*
```
[
[{'id': 'a', 'score': 4.999447078546382e-09, 'metadata': {'category': 'A'}}, {'id': 'b', 'score': 0.02536815218627453, 'metadata': {'category': 'B'}}, {'id': 'c', 'score': 0.04058804363012314, 'metadata': {'category': 'A'}}],
[{'id': 'b', 'score': 4.591760305316939e-09, 'metadata': {'category': 'B'}}, {'id': 'c', 'score': 0.0018091063247993588, 'metadata': {'category': 'A'}}, {'id': 'a', 'score': 0.025368161499500275, 'metadata': {'category': 'A'}}]
]
```

<br />

**🔍 Search Example 5 - Batch Search with NumPy Array**

Perform a similarity search on multiple query vectors from a NumPy array, returning results for each query.

```python
query_vector = np.array(
[
    [0.1, 0.2, 0.3],
    [0.7, 0.8, 0.9]
], dtype=np.float32)

results = index.search(vector=query_vector, top_k=3)
print(results)
```

<br />

**🔍 Search Example 6 - Batch Search with metadata filter**

Performs similarity search on multiple query vectors with metadata filtering, returning filtered results for each query.

```python
results = index.search(
    [[0.1, 0.2, 0.3], [0.7, 0.8, 0.9]],
    filter={"category": "A"},
    top_k=3
)
print(results)
```
