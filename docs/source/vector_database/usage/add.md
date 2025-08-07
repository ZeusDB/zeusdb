# Add Data

Add vectors to your index for similarity search operations.

**HNSWIndex.<span style="color: #663399;">add</span>**(<br/>
&emsp;&emsp;**data: dict | list[dict] | dict[str, Union[list, np.ndarray]]**<br/>
) 

Inserts one or more vectors into the index. 

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

```


<br />

```{admonition} Returns
:class: tip

AddResult
:   Result object containing insertion statistics and error information:
    * `total_inserted` - Number of vectors successfully inserted or updated
    * `total_errors` - Number of failed records  
    * `errors` - List of detailed error messages for debugging
    * `vector_shape` - Shape of the processed vector batch
    * `summary()` - Human-readable summary string
    * `is_success()` - Boolean indicating if all records were processed successfully
```


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

print(add_result.summary())     # ✅ 1 inserted, ❌ 0 errors
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

print(add_result.summary())       # ✅ 2 inserted, ❌ 0 errors
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
print(add_result)  # AddResult(inserted=2, errors=0, shape=(2, 4))
```

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

print(result.summary())   # ✅ 2 inserted, ❌ 0 errors
```

<br />

**Format 5 – Separate Arrays with NumPy**

This format is highly performant and leverages NumPy's internal memory layout for efficient transfer of data.

```python
import numpy as np
add_result = index.add({
    "ids": ["doc1", "doc2"],
    "embeddings": np.array([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]], dtype=np.float32),
    "metadatas": [{"text": "hello"}, {"text": "world"}]
})
print(add_result)  # AddResult(inserted=2, errors=0, shape=(2, 4))
```

<br />










