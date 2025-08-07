# Create an Index

Create a new vector index for similarity search operations.


**VectorDatabase.<span style="color: #663399;">create</span>**(<br/>
&emsp;&emsp;*index_type: str = "hnsw"*,<br/>
&emsp;&emsp;*dim: int = 1536*,<br/>
&emsp;&emsp;*space: str = "cosine"*,<br/>
&emsp;&emsp;*m: int = 16*,<br/>
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
:   Dimensionality of the vectors to be indexed. All vectors added to this index must have exactly this number of dimensions. The default of 1536 matches OpenAI's text-embedding-ada-002 model output dimensionality.

space : *str, default "cosine"*
:   Distance metric used for similarity calculations during search operations. Available options:
   * `"cosine"` - Cosine similarity (recommended for normalized embeddings)
   * `"L2"` - Euclidean distance
   * `"L1"` - Manhattan distance

m : *int, default 16*
:   Maximum number of bi-directional connections created for each node during graph construction. Higher values improve search recall at the cost of increased memory usage and longer build times. Typical range: 8-64.

ef_construction : *int, default 200*
:   Size of the dynamic candidate list used during index construction. Larger values result in better index quality but increase build time and memory consumption. Typical range: 100-800.

expected_size : *int, default 10000*
:   Estimated number of vectors that will be added to the index. Used for pre-allocating internal data structures to optimize performance. This is not a hard limit - you can add more vectors than this estimate.

quantization_config : *dict or None, default None*
:   Product Quantization configuration for memory-efficient vector compression. When provided, reduces memory footprint at the cost of slight accuracy loss. See the Product Quantization section for detailed configuration options.
```


<br />

```{admonition} Returns
:class: tip

**HNSWIndex**
    A configured vector index ready for adding data and performing similarity searches.

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
        'type': 'pq',
        'subvectors': 8,
        'bits': 8
    }
)
```



