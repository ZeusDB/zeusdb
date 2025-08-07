# Useful Utilities

ZeusDB Vector Database includes a suite of utility functions to help you inspect, manage, and maintain your index. You can view index configuration, attach custom metadata, list stored records, and remove vectors by ID. These tools make it easy to monitor and evolve your index over time,  whether you are experimenting locally or deploying in production.

## Examples

**Example 1 - Check the details of your HNSW index**

```python
print(index.info()) 
```
*Output*
```
HNSWIndex(dim=8, space=cosine, m=16, ef_construction=200, expected_size=5, vectors=5)
```

<br/>


**Example 2 - Add index level metadata**

```python
index.add_metadata({
  "creator": "John Smith",
  "version": "0.1",
  "created_at": "2024-01-28T11:35:55Z",
  "index_type": "HNSW",
  "embedding_model": "openai/text-embedding-ada-002",
  "dataset": "docs_corpus_v2",
  "environment": "production",
  "description": "Knowledge base index for customer support articles",
  "num_documents": "15000",
  "tags": "['support', 'docs', '2024']"
})

# View index level metadata by key
print(index.get_metadata("creator"))  

# View all index level metadata 
print(index.get_all_metadata())       
```
*Output*
```
John Smith
{'description': 'Knowledge base index for customer support articles', 'environment': 'production', 'embedding_model': 'openai/text-embedding-ada-002', 'creator': 'John Smith', 'tags': "['support', 'docs', '2024']", 'num_documents': '15000', 'version': '0.1', 'index_type': 'HNSW', 'dataset': 'docs_corpus_v2', 'created_at': '2024-01-28T11:35:55Z'}
```

<br/>


**Example 3 - List records in the index**

```python
print("\n--- Index Shows first 5 records ---")
print(index.list(number=5)) # Shows first 5 records
```
*Output*
```
[('doc_004', {'author': 'Bob'}), ('doc_003', {'author': 'Alice'}), ('doc_005', {'author': 'Alice'}), ('doc_002', {'author': 'Bob'}), ('doc_001', {'author': 'Alice'})]
```

<br/>

**Example 4 - Remove Records**

ZeusDB allows you to remove a vector and its associated metadata from the index using the .remove_point(id) method. This performs a <u>logical deletion</u>, meaning:
- The vector is deleted from internal storage.
- The metadata is removed.
- The vector ID is no longer accessible via .contains(), .get_vector(), or .search().

```python
# Remove the point using its ID
index.remove_point("doc1")  # "doc1" is the unique vector ID

print("\n--- Check Removal ---")
exists = index.contains("doc1")
print(f"Point 'doc1' {'found' if exists else 'not found'} in index")
```
*Output*
```
--- Check Removal ---
Point 'doc1' not found in index
```

**⚠️ Please Note:** Due to the nature of HNSW, the underlying graph node remains in memory, even after removing a point. This is common for HNSW implementations. To fully remove stale graph entries, consider rebuilding the index.

<br/>

**Example 5 - Retrieve records by ID**

Use `get_records()` to fetch one or more records by ID, with optional vector inclusion.

```python
# Single record
print("\n--- Get Single Record ---")
rec = index.get_records("doc1")
print(rec)

# Multiple records
print("\n--- Get Multiple Records ---")
batch = index.get_records(["doc1", "doc3"])
print(batch)

# Metadata only
print("\n--- Get Metadata only ---")
meta_only = index.get_records(["doc1", "doc2"], return_vector=False)
print(meta_only)

# Missing ID silently ignored
print("\n--- Partial only ---")
partial = index.get_records(["doc1", "missing_id"])
print(partial)
```

⚠️ `get_records()` only returns results for IDs that exist in the index. Missing IDs are silently skipped.

<br />

