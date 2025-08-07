# Product Quantization

Product Quantization (PQ) is a vector compression technique that significantly reduces memory usage while preserving high search accuracy. Commonly used in HNSW-based vector databases, PQ works by dividing each vector into subvectors and quantizing them independently. This enables compression ratios of 4× to 256×, making it ideal for large-scale, high-dimensional datasets.

ZeusDB Vector Database’s PQ implementation features:

✅ Intelligent Training – PQ model trains automatically at defined thresholds

✅ Efficient Memory Use – Store 4× to 256× more vectors in the same RAM footprint

✅ Fast Approximate Search – Uses Asymmetric Distance Computation (ADC) for high-speed search computation

✅ Seamless Operation – Index automatically switches from raw to quantized storage modes

<br />


```{admonition} Quantization Configuration Parameters
:class: note

type : *str, required*
:   Quantization algorithm type. Currently only supports `"pq"` for Product Quantization.

subvectors : *int, default 8*
:   Number of vector subspaces (must divide dimension evenly). The vector is split into this many subvectors for independent quantization. Valid range: 1 to dimension.

bits : *int, default 8*
:   Bits per quantized code (controls centroids per subvector). Determines the number of centroids as 2^bits. Higher values provide better accuracy but use more memory. Valid range: 1-8.

training_size : *int, default 1000*
:   Minimum vectors needed for stable k-means clustering during quantization training. Must be ≥ 1000 for reliable centroid estimation.

max_training_vectors : *int, default None*
:   Maximum vectors used during training (optional limit). When specified, limits the number of vectors used for training even if more are available. Must be ≥ training_size.

storage_mode : *str, default "quantized_only"*
:   Storage strategy for vectors. Options:
    * `"quantized_only"` - Memory optimized, stores only quantized vectors
    * `"quantized_with_raw"` - Keep both quantized and raw vectors for exact reconstruction
```

<br/>


**🗜️ Usage Example 1**

```python
from zeusdb_vector_database import VectorDatabase
import numpy as np

# Create index with product quantization
vdb = VectorDatabase()

# Configure quantization for memory efficiency
quantization_config = {
    'type': 'pq',                  # `pq` for Product Quantization
    'subvectors': 8,               # Divide 1536-dim vectors into 8 subvectors of 192 dims each
    'bits': 8,                     # 256 centroids per subvector (2^8)
    'training_size': 10000,        # Train when 10k vectors are collected
    'max_training_vectors': 50000  # Use max 50k vectors for training
}

# Create index with quantization
# This will automatically handle training when enough vectors are added
index = vdb.create(
    index_type="hnsw",
    dim=1536,                                  # OpenAI `text-embedding-3-small` dimension
    quantization_config=quantization_config    # Add the compression configuration
)

# Add vectors - training triggers automatically at threshold
documents = [
    {
        "id": f"doc_{i}", 
        "values": np.random.rand(1536).astype(float).tolist(),
        "metadata": {"category": "tech", "year": 2026}
    }
    for i in range(15000) 
]

# Training will trigger automatically when 10k vectors are added
result = index.add(documents)
print(f"Added {result.total_inserted} vectors")

# Check quantization status
print(f"Training progress: {index.get_training_progress():.1f}%")
print(f"Storage mode: {index.get_storage_mode()}")
print(f"Is quantized: {index.is_quantized()}")

# Get compression statistics
quant_info = index.get_quantization_info()
if quant_info:
    print(f"Compression ratio: {quant_info['compression_ratio']:.1f}x")
    print(f"Memory usage: {quant_info['memory_mb']:.1f} MB")

# Search works seamlessly with quantized storage
query_vector = np.random.rand(1536).astype(float).tolist()
results = index.search(vector=query_vector, top_k=3)

# Simply print raw results
print(results)
```

Results
```python
[
{'id': 'doc_9719', 'score': 0.5133496522903442, 'metadata': {'category': 'tech', 'year': 2026}},
{'id': 'doc_8148', 'score': 0.5139288306236267, 'metadata': {'category': 'tech', 'year': 2026}}, 
{'id': 'doc_7822', 'score': 0.5151920914649963, 'metadata': {'category': 'tech', 'year': 2026}}, 
]
```

<br />

**🗜️Usage Example 2 - with explicit storage mode**

```python
from zeusdb_vector_database import VectorDatabase
import numpy as np

# Create index with product quantization
vdb = VectorDatabase()

# Configure quantization for memory efficiency
quantization_config = {
    'type': 'pq',                  # `pq` for Product Quantization
    'subvectors': 8,               # Divide 1536-dim vectors into 8 subvectors of 192 dims each
    'bits': 8,                     # 256 centroids per subvector (2^8)
    'training_size': 10000,        # Train when 10k vectors are collected
    'max_training_vectors': 50000,  # Use max 50k vectors for training
    'storage_mode': 'quantized_only'  # Explicitly set storage mode to only keep quantized values
}

# Create index with quantization
# This will automatically handle training when enough vectors are added
index = vdb.create(
    index_type="hnsw",
    dim=3072,                                  # OpenAI `text-embedding-3-large` dimension
    quantization_config=quantization_config    # Add the compression configuration
)

```

<br />

## ⚙️ Configuration Guidelines

For Balanced Memory & Accuracy (Recommended to start with)
```python
quantization_config = {
    'type': 'pq',
    'subvectors': 8,      # Balanced: moderate compression, good accuracy
    'bits': 8,            # 256 centroids per subvector (high precision)
    'training_size': 10000,  # Or higher for large datasets
    'storage_mode': 'quantized_only'  # Default, memory efficient
}
# Achieves ~16x–32x compression with strong recall for most applications
```


For Memory Optimization:
```python
quantization_config = {
    'type': 'pq',
    'subvectors': 16,      # More subvectors = better compression
    'bits': 6,             # Fewer bits = less memory per centroid
    'training_size': 20000,
    'storage_mode': 'quantized_only'
}
# Achieves ~32x compression ratio
```

For Accuracy Optimization:
```python
quantization_config = {
    'type': 'pq',
    'subvectors': 4,       # Fewer subvectors = better accuracy
    'bits': 8,             # More bits = more precise quantization
    'training_size': 50000 # More training data = better centroids
    'storage_mode': 'quantized_with_raw'  # Keep raw vectors for exact recall
}
# Achieves ~4x compression ratio with minimal accuracy loss
```

### 📊 Performance Characteristics

- Training: Occurs once when threshold is reached (typically 1-5 minutes for 50k vectors)
- Memory Reduction: 4x-256x depending on configuration
- Search Speed: Comparable or faster than raw vectors due to ADC optimization
- Accuracy Impact: Typically 1-5% recall reduction with proper tuning

Quantization is ideal for production deployments with large vector datasets (100k+ vectors) where memory efficiency is critical.

`"quantized_only"` is recommended for most use cases and maximizes memory savings.

`"quantized_with_raw"` keeps both quantized and raw vectors for exact reconstruction, but uses more memory.


<br/>
