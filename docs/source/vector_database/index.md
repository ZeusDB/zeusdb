# ZeusDB Vector Database

ZeusDB Vector Database is a high-performance, Rust-powered vector database built for fast and scalable similarity search across high-dimensional embeddings. Designed for modern machine learning and AI workloads, it provides efficient approximate nearest neighbor (ANN) search, supports real-time querying at scale, and seamlessly transitions from in-memory performance to durable disk persistence.

Whether you're powering document search, enabling natural language interfaces, or building custom vector-based tools, ZeusDB offers a lightweight, extensible foundation for high-performance vector retrieval. It’s also well-suited for Retrieval-Augmented Generation (RAG) pipelines, where fast and semantically rich context retrieval is critical to enhancing large language model (LLM) responses.

<br/>

## ⭐ Features

*"Start fast. Tune deep. Build for any scale."*

🐍 User-friendly Python API for adding vectors and running similarity searches

🔥 High-performance Rust backend optimized for speed and concurrency

🔍 Approximate Nearest Neighbor (ANN) search using HNSW for lightning fast results

📦 Product Quantization (PQ) for compact storage, faster distance computations, and scalability for Big Data

📥 Flexible input formats, including native Python types and NumPy arrays

🗂️ Metadata filtering for precise and contextual querying

💾 Save and reload full indexes, metadata, and quantized vectors across systems

📝 Enterprise-grade logging with flexible formats and output targets

<br/>

## ✅ Supported Distance Metrics

ZeusDB Vector Database supports the following metrics for vector similarity search. All metric names are case-insensitive, so "cosine", "COSINE", and "Cosine" are treated identically.

| Metric | Description                          | Accepted Values (case-insensitive)  |
|--------|--------------------------------------|--------|
| cosine | Cosine Distance (1 - Cosine Similiarity) | "cosine", "COSINE", "Cosine" |
| l1     | Manhattan distance                   | "l1", "L1" |
| l2     | Euclidean distance                 | "l2", "L2" |


### 📏 Scores vs Distances 

All distance metrics in ZeusDB Vector Database return distance values, not similarity scores:

 - Lower values = more similar
 - A score of 0.0 means a perfect match

This applies to all distance types, including cosine.



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