# Persistence

ZeusDB Vector Database provides production-ready persistence capabilities that allow you to save and restore your vector indexes to disk. This enables you to preserve your work, share indexes between systems, and implement backup strategies for production deployments.

The persistence system supports:

✅ **Complete state preservation** – vectors, per-record metadata, index level metadata, ID mappings, HNSW graph structure, and quantization models  
✅ **Hybrid storage format** – efficient binary encoding for vectors with human-readable JSON for metadata  
✅ **Quantization support** – seamlessly handles both raw and quantized storage modes, including the trained codebook and rerank calibration  
✅ **Training state recovery** – an index saved mid-collection resumes collecting toward its training threshold  
✅ **Format versioning** – a directory this build cannot interpret is refused rather than misread  

**`save()` and `load()` print progress to stdout.** Every step writes a line. This is not configurable, so redirect stdout if it is a problem in your application.

## Saving an Index - .save()

Use the `.save()` method to persist your index to a `.zdb` directory structure.

**HNSWIndex.<span style="color: #663399;">save</span>**(<br/>
&emsp;&emsp;**path: str**<br/>
) 

Saves the complete index state to disk, including vectors, metadata, HNSW graph structure, and quantization models.

```{admonition} Parameters
:class: note

path : *str, required*
:   Directory path where the index will be saved. Creates a `.zdb` directory structure containing all index components including vectors, metadata, HNSW graph, and quantization models if present.

```

```{admonition} Returns
:class: tip
None
:   The method saves the index to disk and returns nothing. Raises an exception if the save operation fails.
```

## Examples

**Example 1 - How to save an Index**

```python
from zeusdb import VectorDatabase
import numpy as np
import os

# Create and populate an index
vdb = VectorDatabase()
index = vdb.create("hnsw", dim=1536, space="cosine", expected_size=1000)

rng = np.random.default_rng(1)
vectors = rng.random((1000, 1536), dtype=np.float32)
index.add({
    "ids": [f"doc_{i}" for i in range(1000)],
    "embeddings": vectors,
    "metadatas": [{"category": f"cat_{i % 5}", "index": i} for i in range(1000)],
})

# Save the complete index to disk
index.save("my_index.zdb")
print("saved:", sorted(os.listdir("my_index.zdb")))
```

*Output, with the progress lines omitted*
```text
saved: ['config.json', 'hnsw_index.hnsw.data', 'hnsw_index.hnsw.graph', 'manifest.json', 'mappings.bin', 'metadata.json', 'vectors.bin']
```

<br />

## Loading an Index - .load()

Use the `.load()` method to restore a previously saved index.

**VectorDatabase.<span style="color: #663399;">load</span>**(<br/>
&emsp;&emsp;**path: str**<br/>
) 

Restores a complete index from disk with all data and configuration preserved.

```{admonition} Parameters
:class: note

path : *str, required*
:   Directory path to a previously saved `.zdb` index. Must point to a valid index directory created by the `.save()` method.
```

```{admonition} Returns
:class: tip

HNSWIndex
:   A fully restored index instance with all vectors, metadata, graph structure, and quantization state preserved from the saved version.
```


**Example 2 - How to load an Index**

```python
# Load the index from disk
loaded_index = vdb.load("my_index.zdb")

print("vectors:", loaded_index.get_vector_count())
print(loaded_index.info())

results = loaded_index.search(vectors[0].tolist(), top_k=3)
print("top hit:", results[0]["id"])
```

*Output, with the progress lines omitted*
```text
vectors: 1000
HNSWIndex(dim=1536, space=cosine, m=16, ef_construction=200, expected_size=1000, vectors=1000, quantization=none)
top hit: doc_0
```

**Loading reads the saved graph back rather than rebuilding it**, so a reloaded index returns the same result pages as the index that was saved, with the same IDs and the same scores. Load time is proportional to the size of the directory rather than to the cost of building the index: 50,000 records at 1,536 dimensions load in about a second against a build of over two minutes.

The graph is rebuilt by re-inserting every record only when the saved graph cannot be used, which covers a directory whose graph files were lost or damaged and one written by a release too old for this build to interpret. An index saved by an earlier release therefore still loads, with no user action required. Set `ZEUSDB_LOAD_REBUILD_GRAPH=1` to ask for that rebuild on a directory whose graph is perfectly readable, which is how an index built by an earlier release picks up graph improvements made since.

<br />

### 🗜️ Persistence with Product Quantization

Persistence seamlessly handles quantized indexes. A quantized index comes back quantized, with its codebook, training state and rerank calibration intact:

```python
from zeusdb import VectorDatabase
import numpy as np
import os

quantization_config = {
    'type': 'pq',
    'subvectors': 8,
    'bits': 8,
    'training_size': 1000,
    'storage_mode': 'quantized_with_raw'
}

vdb = VectorDatabase()
index = vdb.create("hnsw", dim=1536, expected_size=2000,
                   quantization_config=quantization_config)

rng = np.random.default_rng(2)
index.add({
    "ids": [f"vec_{i}" for i in range(2000)],
    "embeddings": rng.random((2000, 1536), dtype=np.float32),
})

print("quantization active:", index.is_quantized())
index.save("quantized_index.zdb")

loaded_index = vdb.load("quantized_index.zdb")
print("quantization active after load:", loaded_index.is_quantized())
print("storage mode after load:", loaded_index.get_storage_mode())
print("saved:", sorted(os.listdir("quantized_index.zdb")))
```

*Output, with the progress lines omitted*
```text
quantization active: True
quantization active after load: True
storage mode after load: quantized_active
saved: ['config.json', 'hnsw_index.hnsw.data', 'hnsw_index.hnsw.graph', 'manifest.json', 'mappings.bin', 'metadata.json', 'pq_centroids.bin', 'pq_codes.bin', 'quantization.json', 'vectors.bin']
```

<br/>

### Index Directory Structure
The `.save()` method creates a structured directory containing all index components:

```text
my_index.zdb/
├── manifest.json           # Index metadata and file inventory
├── config.json             # HNSW configuration and index level metadata
├── mappings.bin            # ID mappings (binary format)
├── metadata.json           # Per-record metadata (JSON format)
├── vectors.bin             # Raw vectors (whenever the index holds any)
├── quantization.json       # PQ configuration (if enabled)
├── pq_centroids.bin        # Trained centroids (if PQ trained)
├── pq_codes.bin            # Quantized codes (if PQ active)
├── hnsw_index.hnsw.graph   # HNSW graph structure
└── hnsw_index.hnsw.data    # HNSW graph payload
```

`manifest.json` lists both graph files under `files_included`. The load path restores the saved graph rather than rebuilding it, so both are required to reopen a directory holding records.

<br/>

### Complete Save/Load Workflow
Here's a comprehensive example showing the full persistence lifecycle:

```python
from zeusdb import VectorDatabase
import numpy as np

# === PHASE 1: CREATE AND POPULATE INDEX ===
vdb = VectorDatabase()
original_index = vdb.create("hnsw", dim=1536, space="cosine", expected_size=500)

rng = np.random.default_rng(42)
vectors = rng.random((500, 1536), dtype=np.float32)

original_index.add({
    "ids": [f"doc_{i:03d}" for i in range(500)],
    "embeddings": vectors,
    "metadatas": [
        {
            "category": ["science", "tech", "health", "finance"][i % 4],
            "priority": i % 10,
            "published": i % 2 == 0,
            "tags": ["important", "featured"] if i % 5 == 0 else ["standard"],
        }
        for i in range(500)
    ],
})

# Add some index-level metadata
original_index.add_metadata({
    "dataset": "demo_collection",
    "created_by": "data_team",
    "version": "1.0",
})

query_vector = vectors[0].tolist()
original_results = original_index.search(query_vector, top_k=3)

# === PHASE 2: SAVE, THEN LOAD ===
original_index.save("demo_index.zdb")
loaded_index = vdb.load("demo_index.zdb")

# === PHASE 3: VERIFY INTEGRITY ===
assert loaded_index.get_vector_count() == original_index.get_vector_count()
assert loaded_index.info() == original_index.info()
assert loaded_index.get_all_metadata() == original_index.get_all_metadata()

loaded_results = loaded_index.search(query_vector, top_k=3)
assert [r["id"] for r in loaded_results] == [r["id"] for r in original_results]

filtered = loaded_index.search(
    query_vector,
    filter={"category": "science", "published": True},
    top_k=20,
)

print("records:", loaded_index.get_vector_count())
print("index metadata fields:", len(loaded_index.get_all_metadata()))
print("filtered hits:", len(filtered))
print("all checks passed")
```

*Output, with the progress lines omitted*
```text
records: 500
index metadata fields: 3
filtered hits: 5
all checks passed
```

### ⚠️ Important Notes on Persistence
- **Directory, not a file**: The `.save()` method creates a directory. Ensure you have write permissions for the target location.

- **Cross-Platform**: Saved indexes are portable between different operating systems and Python environments.

- **Version Compatibility**: The manifest records a format version. This build writes 1.1.0 and reads any 1.x. A different major version is refused.

- **Not atomic**: Files are written one at a time into the target directory. An interrupted save leaves a partial directory behind, and a later `load()` of it fails rather than returning a truncated index. Save to a new path and move it into place if you need an atomic swap.

- **Overwriting is not clean either**: Saving over an existing directory replaces files individually and does not remove ones that no longer apply. Save to a fresh directory.

- **Integrity check on load**: The restored record count is checked against the count in `config.json`. A missing or truncated data file fails the load with a message naming what disagreed.


<br />
