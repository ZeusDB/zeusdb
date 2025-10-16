# LlamaIndex

A high-performance LlamaIndex integration for ZeusDB, bringing enterprise-grade vector search capabilities to your LlamaIndex RAG applications.

## Features

🎯 **LlamaIndex Native**

- Full VectorStore API compliance
- Direct query interface for low-level control
- Seamless VectorStoreIndex integration
- Maximal Marginal Relevance (MMR) search

🚀 **High Performance**

- Rust-powered vector database backend
- Advanced HNSW indexing for sub-millisecond search
- Product Quantization for 4x-256x memory compression
- Concurrent search with automatic parallelization

🏢 **Enterprise Ready**

- Complete persistence with state preservation
- Advanced metadata filtering
- Structured logging with performance monitoring
- Async/await support for non-blocking operations

## Quick Start

### Installation

```bash
pip install llama-index-vector-stores-zeusdb
```

### Getting Started

This example uses *OpenAIEmbeddings*, which requires an OpenAI API key - [Get your OpenAI API key here](https://platform.openai.com/api-keys)

If you prefer, you can also use this package with any other embedding provider (Hugging Face, Cohere, custom functions, etc.).

```bash
pip install llama-index-embeddings-openai llama-index-llms-openai
```

```python
import os
import getpass

os.environ['OPENAI_API_KEY'] = getpass.getpass('OpenAI API Key:')
```

### Basic Usage

```python
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.zeusdb import ZeusDBVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

# Set up embedding model and LLM
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-5")

# Create ZeusDB vector store
vector_store = ZeusDBVectorStore(
    dim=1536,  # OpenAI embedding dimension
    distance="cosine",
    index_type="hnsw"
)

# Create storage context
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Create documents
documents = [
    Document(text="ZeusDB is a high-performance vector database."),
    Document(text="LlamaIndex provides RAG capabilities."),
    Document(text="Vector search enables semantic similarity.")
]

# Create index and store documents
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context
)

# Query the index
query_engine = index.as_query_engine()
response = query_engine.query("What is ZeusDB?")
print(response)
```

**Expected results:**

```text
ZeusDB is a high-performance vector database.
```

## Advanced Features

ZeusDB's enterprise-grade capabilities are fully integrated into the LlamaIndex ecosystem, providing quantization, persistence, advanced search features and many other enterprise capabilities.

All examples below have been tested and verified to work as-is. Copy-paste and run them directly.

### Direct Query Interface

Execute low-level queries against the vector store:

```python
from llama_index.core.vector_stores.types import VectorStoreQuery

# Create query
embed_model = Settings.embed_model
query_embedding = embed_model.get_text_embedding("machine learning")

query_obj = VectorStoreQuery(
    query_embedding=query_embedding,
    similarity_top_k=2
)

# Execute query
results = vector_store.query(query_obj)

# Results contain IDs and similarities
print(f"Found {len(results.ids or [])} results:")
for node_id, similarity in zip(results.ids or [], results.similarities or []):
    print(f"  ID: {node_id}, Similarity: {similarity:.4f}")
```

**Expected results:**

```text
Found 2 results:
  ID: d40de654-67b6-4621-a950-9b29a0742089, Similarity: 0.6730
  ID: 984cf00d-8595-425e-b8a3-3aeaa96207f8, Similarity: 0.7777
```

### MMR Search for Diversity

MMR (Maximal Marginal Relevance) balances relevance and diversity, reducing near-duplicate results:

```python
# MMR search via direct query
mmr_results = vector_store.query(
    query_obj,
    mmr=True,
    fetch_k=10,
    mmr_lambda=0.7  # 0.0=max diversity, 1.0=pure relevance
)

print(f"MMR Results: {len(mmr_results.ids or [])} items (with diversity)")
```

**Expected results:**

```text
MMR Results: 2 items (with diversity)
```

**Note**: MMR re-ranking happens adapter-side after initial search. The adapter automatically enables `return_vector=True` when MMR is requested. Control with `fetch_k` (candidate pool size) and `mmr_lambda` (0.0=max diversity, 1.0=pure relevance).

### Search with Metadata Filtering

Filter results using document metadata:

```python
from llama_index.core.vector_stores.types import (
    MetadataFilters,
    FilterOperator,
    FilterCondition
)

# Create a fresh vector store for this example
vector_store = ZeusDBVectorStore(dim=1536, distance="cosine")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Create documents with metadata
documents_with_meta = [
    Document(
        text="Python is great for data science",
        metadata={"category": "tech", "year": 2024}
    ),
    Document(
        text="JavaScript is for web development",
        metadata={"category": "tech", "year": 2023}
    ),
    Document(
        text="Climate change impacts ecosystems",
        metadata={"category": "environment", "year": 2024}
    ),
]

# Build index with metadata
index = VectorStoreIndex.from_documents(
    documents_with_meta,
    storage_context=storage_context
)

# Create metadata filter
filters = MetadataFilters.from_dicts([
    {"key": "category", "value": "tech", "operator": FilterOperator.EQ},
    {"key": "year", "value": 2024, "operator": FilterOperator.GTE}
], condition=FilterCondition.AND)

# Use the retriever with filters (recommended approach)
retriever = index.as_retriever(similarity_top_k=5, filters=filters)
filtered_results = retriever.retrieve("programming")

# Process results
for r in filtered_results:
    print(f"- {r.node.get_content(metadata_mode='none')}")
    print(f"  Metadata: {r.node.metadata}\n")
```

**Expected results:**

```text
- Python is great for data science
  Metadata: {'category': 'tech', 'year': 2024}
```

**Supported operators:** EQ, NE, GT, GTE, LT, LTE, IN, NIN, ANY, ALL, CONTAINS, TEXT_MATCH, TEXT_MATCH_INSENSITIVE, IS_EMPTY

**Note:** Combine conditions with `AND` only. `OR` and `NOT` conditions are not yet supported by the ZeusDB backend.

### Persistence

Save and load indexes with complete state restoration:

```python
# Save index
save_path = "my_index.zdb"
vector_store.save_index(save_path)
print(f"✅ Index saved to {save_path}")
print(f"   Vector count: {vector_store.get_vector_count()}")

# Load index
loaded_store = ZeusDBVectorStore.load_index(save_path)
print(f"✅ Index loaded from {save_path}")
print(f"   Vector count: {loaded_store.get_vector_count()}")
```

**Expected results:**

```text
✅ Index saved to my_index.zdb
   Vector count: 3
✅ Index loaded from my_index.zdb
   Vector count: 3
```

**What gets saved:**

- Vectors & IDs
- Metadata
- HNSW graph structure
- Quantization config, centroids, and training state (if PQ is enabled)

**Notes:**

- The path is a directory, not a single file. Ensure the target is writable.
- Saved indexes are cross-platform and include format/version info for compatibility checks.
- If you used PQ, both the compression model and state are preserved—no need to retrain after loading.

### Memory-Efficient Setup with Quantization

For large datasets, use Product Quantization to reduce memory usage:

```python
# Create quantized vector store for memory efficiency
quantization_config = {
    'type': 'pq',
    'subvectors': 8,
    'bits': 8,
    'training_size': 1000,
    'storage_mode': 'quantized_only'
}

vector_store = ZeusDBVectorStore(
    dim=1536,
    distance="cosine",
    index_type="hnsw",
    quantization_config=quantization_config
)

# Check quantization status
print(f"Is quantized: {vector_store.is_quantized()}")
print(f"Can use quantization: {vector_store.can_use_quantization()}")
print(f"Training progress: {vector_store.get_training_progress():.1f}%")
print(f"Storage mode: {vector_store.get_storage_mode()}")
```

**Expected results:**

```text
Is quantized: False
Can use quantization: False
Training progress: 0.0%
Storage mode: raw_collecting_for_training
```

Please refer to our [documentation](https://docs.zeusdb.com/en/latest/vector_database/product_quantization.html) for helpful configuration guidelines and recommendations for setting up quantization.

### Delete Operations

Delete vectors by node ID (standalone example):

```python
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.zeusdb import ZeusDBVectorStore

# Create a fresh vector store for this example
delete_vs = ZeusDBVectorStore(dim=1536, distance="cosine")
delete_sc = StorageContext.from_defaults(vector_store=delete_vs)

# Create documents
delete_docs = [
    Document(text=f"Document {i}", metadata={"doc_id": i})
    for i in range(5)
]

# Build index
delete_index = VectorStoreIndex.from_documents(
    delete_docs,
    storage_context=delete_sc
)

print(f"Before delete: {delete_vs.get_vector_count()} vectors")

# Get node IDs to delete
retriever = delete_index.as_retriever(similarity_top_k=10)
results = retriever.retrieve("document")

if results:
    # Extract node IDs from results
    node_ids_to_delete = [result.node.node_id for result in results[:2]]
    print(f"Deleting node IDs: {node_ids_to_delete[0][:8]}...")
    
    # Delete by node IDs
    delete_vs.delete_nodes(node_ids=node_ids_to_delete)
    print(f"After delete: {delete_vs.get_vector_count()} vectors")
    print("✅ delete_nodes(node_ids=[...]) works!")

# Demonstrate unsupported delete by ref_doc_id
try:
    delete_vs.delete(ref_doc_id="doc_1")
    print("❌ Should have raised NotImplementedError")
except NotImplementedError as e:
    print("❌ delete(ref_doc_id='...') raises NotImplementedError")
    print(f"   (This is expected - not supported by backend)")
```

**Expected results:**

```text
Before delete: 5 vectors
Deleting node IDs: 3b1843da...
After delete: 3 vectors
✅ delete_nodes(node_ids=[...]) works!
❌ delete(ref_doc_id='...') raises NotImplementedError
   (This is expected - not supported by backend)
```

## Async Support

ZeusDB supports asynchronous operations for non-blocking, concurrent vector operations.

**When to use async:** web servers (FastAPI/Starlette), agents/pipelines doing parallel searches, or notebooks where you want non-blocking/concurrent operations. For simple scripts, sync methods are fine.

**Available async methods:**

- `await vector_store.async_add(nodes)` - Add nodes asynchronously
- `await vector_store.aquery(query_obj)` - Query asynchronously
- `await vector_store.adelete_nodes(node_ids)` - Delete by node IDs asynchronously
- `await vector_store.aclear()` - Clear the index asynchronously

All async methods follow the LlamaIndex standard naming convention and are thread-offloaded via `asyncio.to_thread()` for non-blocking operations.

**Example:**

```python
import asyncio
from llama_index.core.schema import TextNode

# In Jupyter, use nest_asyncio to handle event loops
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

async def async_operations():
    # Create nodes
    nodes = [
        TextNode(text=f"Document {i}", metadata={"doc_id": i})
        for i in range(10)
    ]
    
    # Generate embeddings (required before adding)
    embed_model = Settings.embed_model
    for node in nodes:
        node.embedding = embed_model.get_text_embedding(node.text)
    
    # Add nodes asynchronously
    node_ids = await vector_store.async_add(nodes)
    print(f"Added {len(node_ids)} nodes")
    
    # Query asynchronously
    query_embedding = embed_model.get_text_embedding("document")
    query_obj = VectorStoreQuery(
        query_embedding=query_embedding,
        similarity_top_k=3
    )
    
    results = await vector_store.aquery(query_obj)
    print(f"Found {len(results.ids or [])} results")
    
    # Delete asynchronously
    await vector_store.adelete_nodes(node_ids=node_ids[:2])
    print(f"Deleted 2 nodes, {vector_store.get_vector_count()} remaining")

# Run async function
await async_operations()  # In Jupyter
# asyncio.run(async_operations())  # In regular Python scripts
```

**Expected results:**

```text
Added 10 nodes
Found 3 results
Deleted 2 nodes, 8 remaining
```

## Monitoring and Observability

### Performance Monitoring

```python
# Get index statistics
stats = vector_store.get_zeusdb_stats()
print(f"Key stats: vectors={stats.get('total_vectors')}, space={stats.get('space')}")

# Get vector count
count = vector_store.get_vector_count()
print(f"Vector count: {count}")

# Get detailed index info
info = vector_store.info()
print(f"Index info: {info}")

# Check quantization status
if vector_store.is_quantized():
    progress = vector_store.get_training_progress()
    quant_info = vector_store.get_quantization_info()
    print(f"Quantization: {progress:.1f}% complete")
    print(f"Compression: {quant_info['compression_ratio']:.1f}x")
else:
    print("Index is not quantized")
```

**Expected results:**

```text
Key stats: vectors=3, space=cosine
Vector count: 3
Index info: HNSWIndex(dim=1536, space=cosine, m=16, ef_construction=200, expected_size=10000, vectors=3, quantization=none)
Is quantized: False
```

### Enterprise Logging

ZeusDB includes enterprise-grade structured logging that works automatically with smart environment detection:

**Environment-Aware Logging:**

- **Development**: Human-readable logs, WARNING level
- **Production**: JSON structured logs, ERROR level
- **Testing**: Minimal output, CRITICAL level
- **Jupyter**: Clean readable logs, INFO level

**Example log output from operations:**

```text
{"operation":"add_vectors","requested":10,"inserted":10,"duration_ms":45}
```

**Control logging with environment variables:**

```bash
ZEUSDB_LOG_LEVEL=debug ZEUSDB_LOG_FORMAT=json python your_app.py
```

To learn more about the full features of ZeusDB's enterprise logging capabilities, see the [documentation](https://docs.zeusdb.com/en/latest/vector_database/logging.html).

## Configuration Options

### Vector Store Parameters

```python
vector_store = ZeusDBVectorStore(
    dim=1536,                    # Vector dimension (required)
    distance="cosine",           # Distance metric: cosine, l2, l1
    index_type="hnsw",           # Index algorithm
    m=16,                        # HNSW connectivity
    ef_construction=200,         # Build-time search width
    expected_size=10000,         # Expected number of vectors
    quantization_config=None     # Optional quantization
)
```

### Query Parameters

```python
results = vector_store.query(
    query_obj,
    mmr=False,                   # Enable MMR
    fetch_k=20,                  # MMR candidate pool size
    mmr_lambda=0.7,              # MMR diversity control
    ef_search=None,              # Runtime search width (auto if None)
    auto_fallback=True           # Retry with broader search if needed
)
```

## Error Handling

The integration includes comprehensive error handling:

```python
try:
    results = vector_store.query(query_obj)
    print(results)
except Exception as e:
    # Graceful degradation with logging
    print(f"Query failed: {e}")
    # Fallback logic here
```

## Requirements

- **Python**: 3.10 or higher
- **ZeusDB**: 0.0.8 or higher
- **LlamaIndex Core**: 0.14.4 or higher

## Installation from Source

```bash
git clone https://github.com/zeusdb/llama-index-vector-stores-zeusdb.git
cd llama-index-vector-stores-zeusdb
pip install -e .
```

## Compatibility

### Distance Metrics

- **Cosine**: Default, normalized similarity
- **Euclidean (L2)**: Geometric distance
- **Manhattan (L1)**: City-block distance

### Embedding Models

Compatible with any LlamaIndex embedding provider:

- OpenAI (`text-embedding-3-small`, `text-embedding-3-large`)
- Hugging Face Transformers
- Cohere Embeddings
- Custom embedding functions

## Known Limitations

- **Query Results**: The `query()` method returns `ids` and `similarities` only (with `nodes=None`). Use the returned IDs to retrieve full node content if needed.
- **Delete Operations**: Only deletion by node ID is supported (`delete_nodes(node_ids=[...])`). Deletion by `ref_doc_id` or metadata filters is not supported.

---

*Making vector search fast, scalable, and developer-friendly.*
