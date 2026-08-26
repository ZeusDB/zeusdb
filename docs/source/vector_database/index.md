# ZeusDB Vector Database

ZeusDB Vector Database is a high-performance, Rust-powered vector database built for fast and scalable similarity search across high-dimensional embeddings. Designed for modern machine learning and AI workloads, it provides efficient approximate nearest neighbor (ANN) search, supports real-time querying at scale, and seamlessly transitions from in-memory performance to durable disk persistence.

Whether you're powering document search, enabling natural language interfaces, or building custom vector-based tools, ZeusDB offers a lightweight, extensible foundation for high-performance vector retrieval. It’s also well-suited for Retrieval-Augmented Generation (RAG) pipelines, where fast and semantically rich context retrieval is critical to enhancing large language model (LLM) responses.

<br/>

## ⭐ Features

*"Start fast. Tune deep. Build for any scale."*

🐍 User-friendly Python API for adding vectors and running similarity searches

🔥 High-performance Rust backend optimized for speed and concurrency

🔍 Approximate Nearest Neighbor (ANN) search using HNSW for lightning fast results

📦 Product Quantization (PQ) for compact storage, with reranking to hold accuracy

📥 Flexible input formats, including native Python types and NumPy arrays

🗂️ Metadata filtering for precise and contextual querying, with boolean composition and indexed fields

💾 Save and reload full indexes, metadata, and quantized vectors across systems, atomically and verified

📝 Enterprise-grade logging with flexible formats and output targets

<br/>

## ✅ Supported Distance Metrics

ZeusDB Vector Database supports the following metrics for vector similarity search. All metric names are case-insensitive, so "cosine", "COSINE", and "Cosine" are treated identically.

| Metric | Description                          | Accepted Values (case-insensitive)  | Quantization |
|--------|--------------------------------------|--------|--------|
| cosine | Cosine Distance (1 - Cosine Similarity) | "cosine", "COSINE", "Cosine" | supported |
| l1     | Manhattan distance                   | "l1", "L1" | refused |
| l2     | Euclidean distance                 | "l2", "L2" | supported |
| dot    | Inner product, reported as 1 - dot | "dot", "DOT" | refused |

`create()` raises on a refused pair rather than building an index that ranks by the wrong quantity, and `load()` refuses a saved directory that pairs them. See [Metrics that cannot be quantized](#metrics-that-cannot-be-quantized).

### 🎯 When to use `dot`

Use `dot` when the length of a vector should count towards the ranking, which is what a recommender's item and user embeddings usually do and what a model trained with an inner product objective produces. Use `cosine` when only direction matters.

```python
from zeusdb import VectorDatabase

index = VectorDatabase().create("hnsw", dim=4, space="dot")
index.add({"id": "long", "values": [3.0, 0.0, 0.0, 0.0]})
index.add({"id": "unit", "values": [1.0, 0.0, 0.0, 0.0]})
print([(r["id"], round(r["score"], 2)) for r in index.search([1.0, 0.0, 0.0, 0.0], top_k=2)])
```

*Output*
```text
[('long', -2.0), ('unit', 0.0)]
```

Three things follow from `dot` being an inner product rather than a metric.

- **The score is `1 - dot`, so lower is still better.** Recover the inner product as `1 - score`.
- **Scores can be negative**, whenever the inner product is above one. No other metric here produces one.
- **A vector need not be its own nearest neighbour**, because a longer vector pointing much the same way scores lower.

`dot` cannot be combined with `quantization_config`. See [Metrics that cannot be quantized](#metrics-that-cannot-be-quantized).

### 📏 Scores vs Distances 

All distance metrics in ZeusDB Vector Database return distance values, not similarity scores:

 - Lower values = more similar
 - A vector identical to the query scores 0.0, or a value within floating point error of it

This applies to all distance types, including cosine. `dot` is the one exception to the zero, because its score is `1 - dot` and an inner product above one takes it below zero.

Under `cosine`, vectors are normalized to unit length when they are stored. A vector you read back with `return_vector=True` or `get_records()` is therefore the normalized form, not the values you supplied. Under `l1`, `l2` and `dot` the values are stored unchanged.

A zero vector has no direction, so under `cosine` it sits at distance 1.0 from everything, including itself.

**On a quantized index the score is a distance to the record's reconstruction, not to the vector you inserted.** Under `l2` it is the euclidean distance to that reconstruction and under `cosine` it is the cosine distance to it, so either way the number is on the scale a raw index of the same space reports and the two are comparable. It is not equal to the raw score, because the index no longer holds the vector you gave it, and the difference is the quantization error. Rerank replaces it with an exact distance to the raw vector, and it is on by default for `quantized_with_raw`. See [Product Quantization](product_quantization.md).

```python
index = VectorDatabase().create("hnsw", dim=4, space="cosine")
index.add({"id": "a", "values": [1.0, 0.0, 0.0, 0.0]})
print(round(index.search([1.0, 0.0, 0.0, 0.0], top_k=1)[0]["score"], 6))
```

*Output*
```text
0.0
```

<br/>



```{toctree}
:maxdepth: 2
:hidden:

getting_started
usage/index
product_quantization
persistence
metadata_filtering
utilities
logging
upgrading
integrations/index
```
