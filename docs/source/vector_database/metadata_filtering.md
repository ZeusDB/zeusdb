# Metadata Filtering

ZeusDB supports rich metadata with full type fidelity. This means your metadata preserves the original Python data types (integers stay integers, floats stay floats, etc.) and enables powerful filtering capabilities.

## Supported Types

The following Python types are supported for metadata and preserved during filtering and retrieval.

| Type | Python Example | Stored As | Notes |
|------|----------------|-----------|-------|
| **String** | `"Alice"` | `Value::String` | Text data, IDs, categories |
| **Integer** | `42`, `2024` | `Value::Number` | Counts, years, IDs |
| **Float** | `4.5`, `29.99` | `Value::Number` | Ratings, prices, scores |
| **Boolean** | `True`, `False` | `Value::Bool` | Flags, status indicators |
| **Null** | `None` | `Value::Null` | Missing/empty values |
| **Array** | `["ai", "science"]` | `Value::Array` | Tags, categories, lists |
| **Nested Object** | `{"key": "value"}` | `Value::Object` | Structured data |

<br/>

### Filter Operators Reference

These operators can be used in metadata filters:

| Operator | Usage | Example | Description |
|----------|-------|---------|-------------|
| **Direct equality** | `{"field": value}` | `{"author": "Alice"}` | Exact equality for any type |
| `gt` | `{"gt": value}` | `{"rating": {"gt": 4.0}}` | Greater than (numeric) |
| `gte` | `{"gte": value}` | `{"year": {"gte": 2024}}` | Greater than or equal (numeric) |
| `lt` | `{"lt": value}` | `{"price": {"lt": 30}}` | Less than (numeric) |
| `lte` | `{"lte": value}` | `{"pages": {"lte": 100}}` | Less than or equal (numeric) |
| `contains` | `{"contains": value}` | `{"tags": {"contains": "ai"}}` | String contains substring or array contains value |
| `startswith` | `{"startswith": value}` | `{"title": {"startswith": "The"}}` | String starts with substring |
| `endswith` | `{"endswith": value}` | `{"file": {"endswith": ".pdf"}}` | String ends with substring |
| `in` | `{"in": [values]}` | `{"lang": {"in": ["en", "es"]}}` | Value is in the provided array |

<br/>

### Practical Filter Examples

Below are common real-world examples of how to apply metadata filters using ZeusDB's metadata filtering:

**Example 1 - Find high-quality recent documents**
```python
filter = {
    "published": True,
    "rating": {"gte": 4.0},
    "year": {"gte": 2024}
}

results = index.search(vector=query_embedding, filter=filter, top_k=5)
```

<br />

**Example 2 - Find documents by specific authors**
```python
filter = {"author": {"in": ["Alice", "Bob", "Charlie"]}}
results = index.search(vector=query_embedding, filter=filter, top_k=5)
```

<br />

**Example 3 - Find AI-related content**
```python
filter = {"tags": {"contains": "ai"}}
results = index.search(vector=query_embedding, filter=filter, top_k=5)
```

<br />

**Example 4 - Find documents in price range**
```python
filter = {"price": {"gte": 20.0, "lte": 40.0}}
results = index.search(vector=query_embedding, filter=filter, top_k=5)
```

<br />

**Example 5 - Find documents with specific file types**
```python
filter = {"filename": {"endswith": ".pdf"}}
results = index.search(vector=query_embedding, filter=filter, top_k=5)
```


<br/>