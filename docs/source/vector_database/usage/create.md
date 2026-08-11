# Create an Index

Create a new vector index for similarity search operations.


**VectorDatabase.<span style="color: #663399;">create</span>**(<br/>
&emsp;&emsp;*index_type: str = "hnsw"*,<br/>
&emsp;&emsp;*dim: int = 1536*,<br/>
&emsp;&emsp;*space: str = "cosine"*,<br/>
&emsp;&emsp;*m: int = 16 or 32, see below*,<br/>
&emsp;&emsp;*ef_construction: int = 200*,<br/>
&emsp;&emsp;*expected_size: int = 10000*,<br/>
&emsp;&emsp;*quantization_config: dict | None = None*<br/>
)

Creates and initializes a new vector index with the specified configuration. The index is optimized for fast similarity search on high-dimensional vector embeddings.



```{admonition} Parameters
:class: note

index_type : *str, default "hnsw"*
:   The type of vector index algorithm to create. Currently only supports `"hnsw"` (Hierarchical Navigable Small World). Case-insensitive.

dim : *int, default 1536*
:   Dimensionality of the vectors to be indexed. All vectors added to this index must have exactly this number of dimensions. Must be positive. The default of 1536 matches the output dimensionality of OpenAI's `text-embedding-3-small` and `text-embedding-ada-002` models.

space : *str, default "cosine"*
:   Distance metric used for similarity calculations during search operations. One of `"cosine"`, `"l1"`, `"l2"`. Case-insensitive.

m : *int, default 16 or 32, see below*
:   Number of bi-directional connections created for each node during graph construction, from 2 to 256. Higher values improve search recall at the cost of increased memory usage and longer build times. The default depends on `expected_size`: 16 for 25,000 or less, 32 above that. Passing `m` explicitly always wins. The minimum is 2 because a graph at `m=1` is degenerate and loses nearly all recall.

ef_construction : *int, default 200*
:   Size of the dynamic candidate list used during index construction. Must be positive. Larger values result in better index quality but increase build time and memory consumption. Typical range: 100-800.

expected_size : *int, default 10000*
:   Estimated number of vectors that will be added to the index, from 1 to 100,000,000. Used for pre-allocating internal data structures and for choosing the default `m`. This is not a hard limit, but `m` is fixed once the index is created, so declare it honestly. An index that grows past twice its declaration logs a warning once, on the `add()` that crosses it.

quantization_config : *dict or None, default None*
:   Product Quantization configuration for memory-efficient vector compression. Compression costs accuracy unless results are reranked, so read the [Product Quantization](../product_quantization.md) page before enabling it.
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

```python
index = vdb.create()
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

`create()` emits a `UserWarning` when a quantization configuration cannot repay its fixed memory cost at the declared `expected_size`, when `expected_size` is below `training_size` so training would never trigger, when the dimension is too low for quantization to save much, and when a `subvectors` value you passed yourself implies a compression ratio above 50x.
