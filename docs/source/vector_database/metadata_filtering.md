# Metadata Filtering

ZeusDB supports rich metadata with full type fidelity. This means your metadata preserves the original Python data types (integers stay integers, floats stay floats, etc.) and enables powerful filtering capabilities.

## Supported Types

The following Python types are supported for metadata and preserved during filtering and retrieval.

| Type | Python Example | Notes |
|------|----------------|-------|
| **String** | `"Alice"` | Text data, IDs, categories |
| **Integer** | `42`, `2024` | Counts, years, IDs |
| **Float** | `4.5`, `29.99` | Ratings, prices, scores |
| **Boolean** | `True`, `False` | Flags, status indicators |
| **Null** | `None` | Missing/empty values |
| **Array** | `["ai", "science"]` | Tags, categories, lists |
| **Nested Object** | `{"key": "value"}` | Structured data |

Integers and floats compare by magnitude across every operator, so a stored integer `10` matches `{"eq": 10.0}` and `{"gte": 10.0}` alike. Booleans and strings do not cross into numbers.

<br/>

### Filter Operators Reference

A filter is a dict of field names. A field maps either to a plain value, which means equality, or to a dict of operators, all of which must hold.

| Operator | Usage | Example | Description |
|----------|-------|---------|-------------|
| **Direct equality** | `{"field": value}` | `{"author": "Alice"}` | Equality for strings, numbers, booleans, null and arrays |
| `eq` | `{"eq": value}` | `{"source": {"eq": {"kind": "web"}}}` | Equality, including for nested objects |
| `ne` | `{"ne": value}` | `{"author": {"ne": "Alice"}}` | Not equal |
| `gt` | `{"gt": value}` | `{"rating": {"gt": 4.0}}` | Greater than (numeric) |
| `gte` | `{"gte": value}` | `{"year": {"gte": 2024}}` | Greater than or equal (numeric) |
| `lt` | `{"lt": value}` | `{"price": {"lt": 30}}` | Less than (numeric) |
| `lte` | `{"lte": value}` | `{"pages": {"lte": 100}}` | Less than or equal (numeric) |
| `contains` | `{"contains": value}` | `{"tags": {"contains": "ai"}}` | String contains substring or array contains value |
| `startswith` | `{"startswith": value}` | `{"title": {"startswith": "The"}}` | String starts with substring |
| `endswith` | `{"endswith": value}` | `{"file": {"endswith": ".pdf"}}` | String ends with substring |
| `in` | `{"in": [values]}` | `{"lang": {"in": ["en", "es"]}}` | Value is in the provided array |

Three behaviours are worth knowing.

**A record that lacks the field never matches, whatever the operator.** That includes `ne`. `{"status": {"ne": "archived"}}` does not match a record with no `status` at all, so a filter for "status is not archived" excludes records that never had a status.

**A dict value is always read as operators.** Direct equality against a nested object has no plain form, because the two would be indistinguishable, so write it as `{"source": {"eq": {"kind": "web"}}}`. Writing `{"source": {"kind": "web"}}` raises `ValueError: Unknown filter operation: kind`.

**An unrecognised operator raises `ValueError` before the search runs**, rather than quietly matching nothing.

**Filtering happens after the graph search.** The index finds the `top_k` nearest vectors first and then discards the ones the filter rejects, so a selective filter can return fewer than `top_k` results, or none. Raise `top_k` when you filter.

<br/>

### Practical Filter Examples

The examples below all run against this index:

```python
from zeusdb import VectorDatabase

vdb = VectorDatabase()
index = vdb.create("hnsw", dim=4, space="l2")
index.add([
    {"id": "doc_1", "values": [0.1, 0.1, 0.1, 0.1], "metadata": {
        "author": "Alice", "rating": 4.5, "year": 2024, "price": 29.99,
        "published": True, "tags": ["ai", "science"], "title": "The Guide",
        "filename": "report.pdf", "lang": "en"}},
    {"id": "doc_2", "values": [0.2, 0.2, 0.2, 0.2], "metadata": {
        "author": "Bob", "rating": 3.0, "year": 2023, "price": 45.00,
        "published": False, "tags": ["cooking"], "title": "A Book",
        "filename": "notes.txt", "lang": "es"}},
    {"id": "doc_3", "values": [0.3, 0.3, 0.3, 0.3], "metadata": {
        "author": "Charlie", "rating": 5.0, "year": 2026, "price": 25.00,
        "published": True, "tags": ["ai"], "title": "Theory",
        "filename": "paper.pdf", "lang": "fr"}},
])
query_embedding = [0.1, 0.1, 0.1, 0.1]

def matched(filter, top_k=10):
    return [hit["id"] for hit in index.search(vector=query_embedding, filter=filter, top_k=top_k)]
```

**Example 1 - Filtering happens after the search, so raise `top_k`**

```python
# doc_3 is the furthest of the three from the query, so a top_k of 1 finds
# nothing once the filter is applied
print(matched({"author": "Charlie"}, top_k=1))
print(matched({"author": "Charlie"}, top_k=10))
```

*Output*
```text
[]
['doc_3']
```

<br />

**Example 2 - Find high-quality recent documents**
```python
print(matched({"published": True, "rating": {"gte": 4.0}, "year": {"gte": 2024}}))
# ['doc_1', 'doc_3']
```

<br />

**Example 3 - Find documents by specific authors**
```python
print(matched({"author": {"in": ["Alice", "Bob"]}}))
# ['doc_1', 'doc_2']
```

<br />

**Example 4 - Find AI-related content**
```python
print(matched({"tags": {"contains": "ai"}}))
# ['doc_1', 'doc_3']
```

<br />

**Example 5 - Find documents in price range**
```python
print(matched({"price": {"gte": 20.0, "lte": 40.0}}))
# ['doc_1', 'doc_3']
```

<br />

**Example 6 - Find documents with specific file types**
```python
print(matched({"filename": {"endswith": ".pdf"}}))
# ['doc_1', 'doc_3']
```

<br />

**Example 7 - Exclude an author**
```python
print(matched({"author": {"ne": "Alice"}}))
# ['doc_2', 'doc_3']
```

<br />

**Example 8 - Match a whole array**
```python
print(matched({"tags": ["ai"]}))
# ['doc_3']
```


<br/>
