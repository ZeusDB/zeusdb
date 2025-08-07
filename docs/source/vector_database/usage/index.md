# Usage

ZeusDB Vector Database makes it easy to work with high-dimensional vector data using a fast, memory-efficient HNSW index. Whether you're building semantic search, recommendation engines, or embedding-based clustering, the workflow is simple and intuitive.

It was designed for users of all backgrounds who need to perform fast similarity search on vector embeddings. Built with Rust for performance and wrapped in Python for ease of use, it provides a flexible API that adapts to your expertise level - offering smart presets for quick implementations while allowing advanced users to fine-tune every hyperparameter for optimal performance.

The core API has been thoughtfully designed around three intuitive, user-friendly methods that naturally align with the logical steps any end user would take when working with a vector database. 

**Three simple steps**

1. **Create an index** using `.create()`
2. **Add data** using `.add(...)`
3. **Conduct a similarity search** using `.search(...)`


This streamlined approach eliminates complexity while maintaining full functionality, ensuring that whether you're a data scientist prototyping a new model or a developer building a production search system, the path from concept to implementation remains clear and efficient


```{toctree}
:maxdepth: 1
:hidden:

create
add
search