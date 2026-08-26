# Add Data

Add vectors to your index for similarity search operations.

**HNSWIndex.<span style="color: #663399;">add</span>**(<br/>
&emsp;&emsp;**data: dict | list[dict] | dict[str, Union[list, np.ndarray]]**,<br/>
&emsp;&emsp;**overwrite: bool = True**<br/>
) 

Inserts or replaces one or more vectors in the index. 

ZeusDB provides a flexible `.add()` method that supports multiple input formats for inserting or updating vectors in the index. Whether you're adding a single record, a list of documents, or structured arrays, the API is designed to be both intuitive and robust. Each record can include optional metadata for filtering or downstream use.

```{admonition} Parameters
:class: note

data : *dict, list[dict], or dict of arrays, required*
:   Input records to upsert into the index. Supports multiple formats including:
   * single objects
   * lists of objects
   * separate arrays
   * NumPy arrays. 

   See examples below for detailed format specifications.

overwrite : *bool, default True*
:   Whether an ID already in the index is replaced. With `False`, a colliding record is skipped and counted as an error in the returned `AddResult` rather than raising.

```


<br />

```{admonition} Returns
:class: tip

AddResult
:   Result object containing insertion statistics and error information:
    * `total_inserted` - Number of vectors successfully inserted or replaced
    * `total_errors` - Number of failed records  
    * `errors` - List of detailed error messages for debugging
    * `ids` - The ID of every record that was inserted or replaced, in insertion order
    * `vector_shape` - Shape of the processed vector batch, as `(rows, dim)`
    * `summary()` - One-line plain ASCII summary string of the two counts
    * `is_success()` - `True` when `total_errors` is zero
```

Each format is parsed and validated automatically. Invalid records are skipped rather than aborting the call, and the reason for each is returned in `errors`. A record whose vector contains `NaN` or an infinity is rejected this way, and so is a vector of the wrong width.

**A batch is not atomic, and which failures raise is deliberate.** A malformed *batch* raises before anything is inserted, so the call is safe to retry: that covers parallel arrays of different lengths, a parallel array of the wrong type, and an input that is not one of the formats below. A malformed *record* inside a well formed batch does not raise. It is counted in `total_errors`, described in `errors`, and the records around it are inserted. Check `is_success()` rather than assuming the call either inserted everything or nothing.


## Examples

First, create an index to work with:
```python
from zeusdb import VectorDatabase

vdb = VectorDatabase()
index = vdb.create(dim=4)  # 4-dimensional vectors for examples
```

<br />

**Format 1 – Single Object**

Add a single vector record with ID, values, and optional metadata:

```python
add_result = index.add({
    "id": "doc1",
    "values": [0.1, 0.2, 0.3, 0.4],
    "metadata": {"text": "hello"}
})

print(add_result.summary())     # 1 inserted, 0 errors
print(add_result.is_success())  # True
```

<br />

**Format 2 – List of Objects**

Add multiple vector records in a single operation:

```python
add_result = index.add([
    {"id": "doc1", "values": [0.1, 0.2, 0.3, 0.4], "metadata": {"text": "hello"}},
    {"id": "doc2", "values": [0.5, 0.6, 0.7, 0.8], "metadata": {"text": "world"}}
])

print(add_result.summary())       # 2 inserted, 0 errors
print(add_result.vector_shape)    # (2, 4)
print(add_result.errors)          # []
```

<br />

**Format 3 – Separate Arrays**

Use separate arrays for IDs, embeddings, and metadata for efficient batch operations:

```python
add_result = index.add({
    "ids": ["doc1", "doc2"],
    "embeddings": [
        [0.1, 0.2, 0.3, 0.4], 
        [0.5, 0.6, 0.7, 0.8]
        ],
    "metadatas": [
        {"text": "hello"}, 
        {"text": "world"}
        ]
})
print(add_result)  # AddResult(inserted=2, errors=0, shape=Some((2, 4)))
```

The `Some(...)` wrapper appears only in the printed form. `add_result.vector_shape` is the plain tuple `(2, 4)`.

<br />

**Format 4 – Using NumPy Arrays**

ZeusDB also supports NumPy arrays as input for seamless integration with scientific and ML workflows.

```python
import numpy as np

data = [
    {"id": "doc2", "values": np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32), "metadata": {"type": "blog"}},
    {"id": "doc3", "values": np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32), "metadata": {"type": "news"}},
]

result = index.add(data)

print(result.summary())   # 2 inserted, 0 errors
```

<br />

**Format 5 – Separate Arrays with NumPy**

This format is highly performant and leverages NumPy's internal memory layout for efficient transfer of data. A 2-D array of `float32` or `float64` is read directly rather than element by element.

```python
import numpy as np
add_result = index.add({
    "ids": ["doc1", "doc2"],
    "embeddings": np.array([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]], dtype=np.float32),
    "metadatas": [{"text": "hello"}, {"text": "world"}]
})
print(add_result)  # AddResult(inserted=2, errors=0, shape=Some((2, 4)))
```

<br />

## The parallel arrays must be the same length

Formats 3 and 5 pair `ids[i]` with the vector and metadata at position `i`, so a disagreement in length is a caller error and raises `ValueError` naming both lengths and which field is short. Nothing is inserted before the raise, so the call is safe to retry.

```python
try:
    index.add({"ids": ["c", "d", "e"], "embeddings": [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]})
except ValueError as error:
    print(error)
```

*Output*
```text
add received 3 entries under 'ids' and 2 under 'embeddings'. A batch pairs them by position, so the two must be the same length, and 'embeddings' is the short one. Supply one id per vector, or omit 'ids' entirely.
```

The rule covers `ids` and `metadatas`, under every spelling of the vector key, on both the list and the NumPy branch. Omitting `ids` entirely is not a disagreement and still generates one per record. A parallel array must be a `list`; a `tuple` or an `ndarray` of `ids` or `metadatas` raises `TypeError`, so pass `ids.tolist()` for an array.

<br />

## The IDs a call put in the index

`ids` on the returned `AddResult` is how you learn the IDs the index generated for records you supplied without one. It lines up with `total_inserted` and with nothing else, so a rejected record contributes no ID and `errors` is what names it.

```python
fresh = vdb.create(dim=4)
generated = fresh.add({"vectors": [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]})
print(generated.ids)

supplied = fresh.add({"ids": ["a", "b"], "embeddings": [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]})
print(supplied.ids)

partial = fresh.add({"ids": ["ok", "bad"], "embeddings": [[0.1, 0.2, 0.3, 0.4], [0.1]]})
print(partial.ids, partial.total_inserted, partial.total_errors)
print(partial.errors)
```

*Output*
```text
['vec_1', 'vec_2']
['a', 'b']
['ok'] 1 1
['Batch parsing error: ValueError: Vector dimension mismatch: expected 4, got 1']
```

On the separate-arrays formats the error message does not name the record, so `ids` is how you learn which records went in. On the single-object and list-of-objects formats the message is prefixed with the record's ID, as `Vector bad: ...`.

<br />

## ⚠️ Adding an ID that already exists

`add()` upserts by default. Re-adding an existing ID **replaces the whole record**, metadata included. Metadata is not merged, so a key you leave out of the new record is gone, and an overwrite with an empty metadata dict clears it entirely.

```python
index = vdb.create(dim=4)
index.add({"id": "doc1", "values": [0.1, 0.2, 0.3, 0.4], "metadata": {"text": "hello", "lang": "en"}})

# "lang" is not carried over
index.add({"id": "doc1", "values": [0.3, 0.4, 0.5, 0.6], "metadata": {"text": "goodbye"}})
print(index.get_records("doc1", return_vector=False))

# overwrite=False rejects the record instead, and counts it as an error
rejected = index.add({"id": "doc1", "values": [0.5, 0.6, 0.7, 0.8]}, overwrite=False)
print(rejected.total_inserted, rejected.total_errors)
print(rejected.errors)
```

*Output*
```text
[{'id': 'doc1', 'metadata': {'text': 'goodbye'}}]
0 1
["Vector doc1: ValueError: Vector with ID 'doc1' already exists"]
```

A rejected record is reported in the `AddResult`. It does not raise. The rejection is also logged at WARNING level, which is visible on stderr under the default development settings.

Every overwrite leaves a stranded node behind in the graph. `compact()` reclaims them, and `update_metadata()` changes a record's metadata without stranding one; see [Useful Utilities](../utilities.md).
