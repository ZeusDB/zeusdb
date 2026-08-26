# Create an Index

Create a new vector index for similarity search operations.


**VectorDatabase.<span style="color: #663399;">create</span>**(<br/>
&emsp;&emsp;*index_type: str = "hnsw"*,<br/>
&emsp;&emsp;*dim: int*,<br/>
&emsp;&emsp;*space: str = "cosine"*,<br/>
&emsp;&emsp;*m: int = 16 or 32, see below*,<br/>
&emsp;&emsp;*ef_construction: int = 200*,<br/>
&emsp;&emsp;*expected_size: int = 10000*,<br/>
&emsp;&emsp;*quantization_config: dict | None = None*,<br/>
&emsp;&emsp;*indexed_fields: list[str] | None = None*<br/>
)

Creates and initializes a new vector index with the specified configuration. The index is optimized for fast similarity search on high-dimensional vector embeddings.



```{admonition} Parameters
:class: note

index_type : *str, default "hnsw"*
:   The type of vector index algorithm to create. Currently only supports `"hnsw"` (Hierarchical Navigable Small World). Case-insensitive.

dim : *int, required*
:   Dimensionality of the vectors to be indexed, from 1 to 65,536. All vectors added to this index must have exactly this number of dimensions. There is no default, because `dim` has to equal the width your embedding model produces and an index built at any other width rejects every vector you add to it. Omitting it raises `TypeError`. Read the width off one embedding with `len(vector)`, or pass the width your model documents, for example `dim=1536` for OpenAI `text-embedding-3-small` or `dim=768` for most sentence-transformers models.

space : *str, default "cosine"*
:   Distance metric used for similarity calculations during search operations. One of `"cosine"`, `"l1"`, `"l2"`, `"dot"`. Case-insensitive. `"l1"` and `"dot"` cannot be combined with `quantization_config`; see [Metrics that cannot be quantized](#metrics-that-cannot-be-quantized).

m : *int, default 16 or 32, see below*
:   Number of bi-directional connections created for each node during graph construction, from 2 to 256. Higher values improve search recall at the cost of increased memory usage and longer build times. The default depends on `expected_size`: 16 for 25,000 or less, 32 above that. Passing `m` explicitly always wins, and `rebuild()` changes it afterwards; see [Useful Utilities](../utilities.md). The minimum is 2 because a graph at `m=1` is degenerate and loses nearly all recall.

ef_construction : *int, default 200*
:   Width of the candidate search each insertion runs, from 1 to 4,096. It costs build time and buys graph quality, and it changes neither search latency nor the size of the finished index. Build time is linear in it above 100. Recall stops improving at or near the default on most data, so raise `ef_search` before raising this. Keep it above `2 × m`; at or below that the neighbour selection heuristic does not run, and `create()` warns.

expected_size : *int, default 10000*
:   Estimated number of vectors that will be added to the index, from 1 to 100,000,000. Used for pre-allocating internal data structures and for choosing the default `m`. This is not a hard limit, but `m` is fixed at creation, so declare it honestly or change `m` later with `rebuild()`. An index that grows past twice its declaration logs a warning once, on the `add()` that crosses it.

quantization_config : *dict or None, default None*
:   Product Quantization configuration for memory-efficient vector compression. Compression costs accuracy unless results are reranked, so read the [Product Quantization](../product_quantization.md) page before enabling it.

indexed_fields : *list[str] or None, default None*
:   Metadata fields to build a column for, so that a filter naming only those fields is answered from the columns rather than by reading every record's metadata. Up to 32 names, no duplicates, none of `$and`, `$or` or `$not`. A filter on an undeclared field still returns the same records and logs one warning. See [Declaring the fields you filter on](../metadata_filtering.md#declaring-the-fields-you-filter-on).
```


<br />

```{admonition} Returns
:class: tip

**HNSWIndex**
    A configured vector index ready for adding data and performing similarity searches. `HNSWIndex` cannot be constructed directly; instances come from `VectorDatabase.create()` or `VectorDatabase.load()`.

```



## Examples

Firstly, initialize the vector database module
```python
# Import the vector database module
from zeusdb import VectorDatabase

# Instantiate the VectorDatabase class
vdb = VectorDatabase()
```

<br />

**Example 1 - Create a basic index with default settings**

Only `dim` has to be given. Everything else takes its default.

```python
index = vdb.create(dim=768)
print(index.info())
```

*Output*
```text
HNSWIndex(dim=768, space=cosine, m=16, ef_construction=200, expected_size=10000, vectors=0, quantization=none)
```

Omitting `dim` raises rather than building an index of the wrong width:

```python
try:
    vdb.create()
except TypeError as error:
    print(error)
```

*Output*
```text
create() requires 'dim', the width of the vectors this index will hold. There is no default because dim has to equal the width your embedding model produces, and an index built at any other width rejects every vector you add to it. Read it off one embedding with len(vector), or pass the width your model documents, for example dim=1536 for OpenAI text-embedding-3-small or dim=768 for most sentence-transformers models.
```

<br />

**Example 2 - Create an index optimized for OpenAI embeddings**

```python
index = vdb.create(
    index_type="hnsw",
    dim=1536, # OpenAI text-embedding-3-small dimension
    space="cosine"
)
```

<br />

**Example 3 - Create a high-precision index for larger datasets**

```python
index = vdb.create(
    dim=3072, # OpenAI text-embedding-3-large dimension
    m=32,
    ef_construction=400,
    expected_size=100000
)
```

<br />

**Example 4 - Create a memory-optimized index with quantization**

```python
index = vdb.create(
    dim=1536,
    expected_size=50000,
    quantization_config={
        'type': 'pq'
    }
)
```

With only `type` set, the quantization defaults are derived from the index: `subvectors` from the dimension (48 at `dim=1536`, holding compression at 128x), `bits` at 8, `training_size` at 10,000 and `storage_mode` at `quantized_only`. `quantized_only` returns far lower recall than an unquantized index and cannot be reranked, so see [Product Quantization](../product_quantization.md) for how to choose a storage mode.

<br />

**Example 5 - Declare the fields you will filter on**

```python
index = vdb.create(dim=1536, indexed_fields=["author", "year"])
print(index.indexed_fields)
```

*Output*
```text
['author', 'year']
```

A filter naming only `author` and `year` is answered from the columns. See [Metadata Filtering](../metadata_filtering.md) for what that saves.

<br />

**Example 6 - Read the configuration back**

`dim`, `space`, `m`, `ef_construction`, `expected_size` and `indexed_fields` are read-only properties on the index.

```python
index = vdb.create(dim=8, space="l2", expected_size=30000)
print(index.dim, index.space, index.m, index.ef_construction, index.expected_size, index.indexed_fields)
```

*Output*
```text
8 l2 32 200 30000 []
```

<br />

## Warnings and refusals at `create()`

`create()` raises `RuntimeError` on a value outside its range, naming the bound: `dim` above 65,536, `ef_construction` above 4,096, `m` outside 2 to 256, `expected_size` outside 1 to 100,000,000, or an unknown `space`. It raises `ValueError` on an invalid `quantization_config` and on `indexed_fields` given as a single string, and `RuntimeError` naming the field when `indexed_fields` holds more than 32 names, a duplicate, or one of the reserved keys. It raises `RuntimeError` when `space` is `"l1"` or `"dot"` and a `quantization_config` is given.

It emits a `UserWarning` when `ef_construction` is not above `2 × m`, so the neighbour selection heuristic would not run. With a `quantization_config` it also warns when `storage_mode` is `quantized_with_raw`, which holds more memory than an unquantized index at every record count; when `quantized_only` cannot repay its fixed tables at the declared `expected_size`, naming the record count above which it starts saving; when `expected_size` is below `training_size`, so training would never trigger; when a `subvectors` value you passed yourself implies a compression ratio above 50x; and when the fixed tables a passed `subvectors` or `bits` implies are large.
