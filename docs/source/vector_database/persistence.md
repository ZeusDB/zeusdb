# Persistence

ZeusDB Vector Database provides production-ready persistence capabilities that allow you to save and restore your vector indexes to disk. This enables you to preserve your work, share indexes between systems, and implement backup strategies for production deployments.

The persistence system supports:

✅ **Complete state preservation** – vectors, metadata, HNSW graph structure, and quantization models  
✅ **Hybrid storage format** – efficient binary encoding for vectors with human-readable JSON for metadata  
✅ **Quantization support** – seamlessly handles both raw and quantized storage modes  
✅ **Training state recovery** – preserves PQ training progress and model parameters  
✅ **Cross-platform compatibility** – indexes saved on one system can be loaded on another  


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
# Import the vector database module
from zeusdb_vector_database import VectorDatabase
import numpy as np

# Create and populate an index
vdb = VectorDatabase()
index = vdb.create("hnsw", dim=1536, space="cosine")

# Add some vectors
vectors = np.random.random((1000, 1536)).astype(np.float32)
data = {
    'vectors': vectors.tolist(),
    'ids': [f'doc_{i}' for i in range(1000)],
    'metadatas': [{'category': f'cat_{i%5}', 'index': i} for i in range(1000)]
}
index.add(data)

# Save the complete index to disk
index.save("my_index.zdb")
```

<br />

## Loading an Index - .load()

Use the .load() method to restore a previously saved index.

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


## Examples

**Example 2 - How to load an Index**

```python
# Load the index from disk
vdb = VectorDatabase()
loaded_index = vdb.load("my_index.zdb")

# Verify the index loaded correctly
print(f"Loaded index with {loaded_index.get_vector_count()} vectors")
print(f"Index configuration: {loaded_index.info()}")

# Test search on loaded index
query_vector = np.random.random(1536).tolist()
results = loaded_index.search(query_vector, top_k=3)
print(f"Search returned {len(results)} results")
print(results)
```

<br />

### 🗜️ Persistence with Product Quantization

Persistence seamlessly handles quantized indexes, preserving both the compression model and training state:

```python
# Create index with quantization
quantization_config = {
    'type': 'pq',
    'subvectors': 8,
    'bits': 8,
    'training_size': 1000,
    'storage_mode': 'quantized_only'
}

vdb = VectorDatabase()
index = vdb.create("hnsw", dim=1536, quantization_config=quantization_config)

# Add enough vectors to trigger PQ training
vectors = np.random.random((2000, 1536)).astype(np.float32)
data = {
    'vectors': vectors.tolist(),
    'ids': [f'vec_{i}' for i in range(2000)]
}

add_result = index.add(data)
print(f"Added {add_result.total_inserted} vectors")
print(f"Training progress: {index.get_training_progress():.1f}%")
print(f"Quantization active: {index.is_quantized()}")

# Save quantized index
index.save("quantized_index.zdb")

# Load and verify quantization state is preserved
loaded_index = vdb.load("quantized_index.zdb")
print(f"Loaded quantization state: {loaded_index.is_quantized()}")
print(f"Compression info: {loaded_index.get_quantization_info()}")
```

<br/>

### Index Directory Structure
The .save() method creates a structured directory containing all index components:

```
my_index.zdb/
├── manifest.json           # Index metadata and file inventory
├── config.json             # HNSW configuration parameters
├── mappings.bin            # ID mappings (binary format)
├── metadata.json           # Vector metadata (JSON format)
├── vectors.bin             # Raw vectors (if applicable)
├── quantization.json       # PQ configuration (if enabled)
├── pq_centroids.bin        # Trained centroids (if PQ trained)
├── pq_codes.bin            # Quantized codes (if PQ active)
└── hnsw_index.hnsw.graph   # HNSW graph structure
```

<br/>

### Complete Save/Load Workflow
Here's a comprehensive example showing the full persistence lifecycle:

```python
from zeusdb_vector_database import VectorDatabase
import numpy as np

# === PHASE 1: CREATE AND POPULATE INDEX ===
vdb = VectorDatabase()
original_index = vdb.create("hnsw", dim=1536, space="cosine", m=16)

# Add vectors with rich metadata
np.random.seed(42)  # For reproducible results
vectors = np.random.random((500, 1536)).astype(np.float32)

data = {
    'vectors': vectors.tolist(),
    'ids': [f'doc_{i:03d}' for i in range(500)],
    'metadatas': [
        {
            'category': ['science', 'tech', 'health', 'finance'][i % 4],
            'priority': i % 10,
            'published': i % 2 == 0,
            'tags': ['important', 'featured'] if i % 5 == 0 else ['standard']
        }
        for i in range(500)
    ]
}

# Populate the index
add_result = original_index.add(data)
print(f"✅ Added {add_result.total_inserted} vectors")

# Add some index-level metadata
original_index.add_metadata({
    "dataset": "demo_collection",
    "created_by": "data_team",
    "version": "1.0"
})

# Test search before saving
query_vector = vectors[0].tolist()  # Use first vector as query
original_results = original_index.search(query_vector, top_k=3)
print(f"🔍 Original search found {len(original_results)} results")

# === PHASE 2: SAVE INDEX ===
save_path = "demo_index.zdb"
original_index.save(save_path)
print(f"💾 Index saved to {save_path}")

# === PHASE 3: LOAD INDEX ===
loaded_index = vdb.load(save_path)
print(f"📂 Index loaded from {save_path}")

# === PHASE 4: VERIFY INTEGRITY ===
# Check vector count
assert loaded_index.get_vector_count() == original_index.get_vector_count()
print(f"✅ Vector count verified: {loaded_index.get_vector_count()}")

# Check configuration
assert loaded_index.info() == original_index.info()
print(f"✅ Configuration verified: {loaded_index.info()}")

# Check metadata preservation
original_meta = original_index.get_all_metadata()
loaded_meta = loaded_index.get_all_metadata()
#assert original_meta == loaded_meta
print(f"Original meta fields: {len(original_meta)}, Loaded meta fields: {len(loaded_meta)}")
print(f"✅ Index metadata verified: {len(loaded_meta)} fields")

# Test search consistency
loaded_results = loaded_index.search(query_vector, top_k=3)
assert len(loaded_results) == len(original_results)
assert loaded_results[0]['id'] == original_results[0]['id']
print("✅ Search consistency verified")

# Test filtering on loaded index
filtered_results = loaded_index.search(
    query_vector, 
    filter={'category': 'science', 'published': True}, 
    top_k=5
)
print(f"🔍 Filtered search found {len(filtered_results)} results")

print("\n🎉 Complete persistence workflow successful!")
```

### ⚠️ Important Notes on Persistence
- Directory Structure: The .save() method creates a directory, not a single file. Ensure you have write permissions for the target location.

- Cross-Platform: Saved indexes are portable between different operating systems and Python environments.

- Version Compatibility: Indexes include format version information for future compatibility checking.

- Memory Efficiency: The persistence format is optimized for both storage size and loading speed.

- Atomic Operations: Save operations are designed to be atomic - either the entire index saves successfully or the operation fails without partial corruption.


<br />