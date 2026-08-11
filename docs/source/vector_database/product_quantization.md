# Product Quantization

Product Quantization (PQ) is a vector compression technique that reduces memory usage by dividing each vector into subvectors and quantizing them independently. A record's compressed form is one byte per subvector, whatever the dimension, so an index over 1536-dimensional vectors with 8 subvectors stores 8 bytes per code in place of 6144 bytes of float32.

ZeusDB Vector Database's PQ implementation features:

✅ Automatic training, triggered on the `add()` call that reaches the configured threshold

✅ Compact codes, one byte per subvector per record

✅ Asymmetric Distance Computation (ADC) for fast search against the codes

✅ Automatic switch from raw to quantized storage once training completes

Compression is not free, and the accuracy cost is much larger than the memory saving suggests. Read [Quantized search accuracy](#quantized-search-accuracy) before choosing a storage mode.

<br />


```{admonition} Quantization Configuration Parameters
:class: note

type : *str, required*
:   Quantization algorithm type. Currently only supports `"pq"` for Product Quantization.

subvectors : *int, default derived from the dimension*
:   Number of vector subspaces (must divide dimension evenly). The vector is split into this many subvectors for independent quantization. Valid range: 1 to dimension. The default is `dim / 32`, clamped to between 8 and 192 and snapped to a divisor of `dim`, which holds the compression ratio at 128x from `dim=256` upward.

bits : *int, default 8*
:   Bits per quantized code, which sets the centroids per subvector to 2^bits. Valid range: 1-8. Lowering it shrinks the fixed codebook and centroid distance table but not the per-record code, which is one byte per subvector at every value, and it costs recall.

training_size : *int, default derived, 10,000 at the default bits*
:   Records collected before training is triggered. When passed explicitly it must be at least 1000, the minimum for stable k-means clustering.

max_training_vectors : *int, default None*
:   Maximum vectors used during training (optional limit). When specified, must be ≥ training_size.

storage_mode : *str, default "quantized_only"*
:   Storage strategy for vectors. Options:
    * `"quantized_only"` - Stores only quantized codes once trained. Lowest memory, and results cannot be reranked, so recall is far below an unquantized index.
    * `"quantized_with_raw"` - Keeps raw vectors alongside the codes. Search reranks against them by default and matches unquantized recall.
```

**The compression ratio is `dim × 4 / subvectors`.** More subvectors means a longer code, so it lowers the compression ratio and raises accuracy. Fewer subvectors means the opposite. At `dim=1536`, 8 subvectors gives 768x and 48 subvectors gives 128x. Do not quote a ratio without the dimension, since the default `subvectors` scales with it:

| `dim` | default `subvectors` | compression |
|-------|----------------------|-------------|
| 64 | 8 | 32x |
| 128 | 8 | 64x |
| 256 | 8 | 128x |
| 768 | 24 | 128x |
| 1536 | 48 | 128x |
| 3072 | 96 | 128x |

<br/>

## 📦 Storage modes

| Mode | What it stores | Rerank available | Memory |
|------|----------------|------------------|--------|
| `quantized_only` | Codes for every record; the raw vectors collected for training are released when training completes | No | Lowest of the three |
| `quantized_with_raw` | Codes and raw vectors for every record | Yes | Between `quantized_only` and no quantization |

Measured resident memory, 50,000 records of real 1536-dimensional OpenAI embeddings, one process each:

| Configuration | Resident | Against unquantized |
| --- | --- | --- |
| No quantization | 806 MiB | 1.00x |
| `quantized_with_raw` | 475 MiB | 0.59x |
| `quantized_only` | 181 MiB | 0.22x |

Two consequences of `quantized_only` are worth knowing before you pick it.

**Once training completes every record exists only as a code, so the vector you read back is an approximation.** `get_records(..., return_vector=True)` and `search(..., return_vector=True)` reconstruct the vector from its code, so what they hand back is close to the value supplied rather than equal to it. Only `quantized_with_raw` reads back exactly. `get_stats()["raw_vectors_stored"]` reports zero once a `quantized_only` index has trained.

**Recall cannot be recovered.** Without raw vectors there is nothing to rerank against, so no tuning restores the accuracy the codes discard. See the next section.

Quantization saves little at low dimension, because the vectors are a small share of what an HNSW index holds there. Below roughly `dim=256` the saving falls under a fifth of what an unquantized index holds, and `create()` warns when a configuration cannot repay its fixed cost at the declared `expected_size`.

<br/>

(quantized-search-accuracy)=
## 🎯 Quantized search accuracy

**Quantized search without reranking is far less accurate than raw search, and `quantized_only` cannot be repaired by tuning.** ADC scores candidates against the codes, and a code discards most of the information in a vector. Reranking fixes this by over-fetching candidates and rescoring them against raw vectors, which is only possible under `quantized_with_raw`.

Measured on 50,000 real OpenAI embeddings at `dim=1536`, recall at 10 was roughly 0.49 for `quantized_only` against 0.99 unquantized, and no setting recovers it. On 6,000 clustered 128-dimensional vectors with 8 subvectors, recall at 10 against exact search:

| Configuration | Recall@10 |
|---------------|-----------|
| No quantization | 1.00 |
| `quantized_only` | 0.16 |
| `quantized_with_raw`, `rerank=0` | 0.15 |
| `quantized_with_raw`, default rerank | 1.00 |

The exact figures depend on your data, but the shape does not. If you need quantization and you need accuracy, use `quantized_with_raw` and leave rerank on.

### The `rerank` argument

`search()` takes a `rerank` argument on a quantized index:

- `rerank` omitted uses a fetch calibrated on your own data. When a `quantized_with_raw` index finishes training it measures how deep a search has to fetch into the code ordering to reach recall at 10 of 0.99 on the training records, how that depth grows with the record count, and how it grows with `top_k`. `get_stats()` reports the calibration under the `rerank_` keys, and `rerank_default_fetch` is the number of candidates a search at `top_k=10` fetches and rescores at the current record count.
- `rerank=N` for N of 1 or more fetches `top_k × N` candidates, a fixed multiple that does not move with the corpus. Use it to override the default deliberately, for example to trade recall for query time.
- `rerank=0` turns reranking off and returns the ADC scores and ordering.
- `rerank` has no effect on an unquantized index or on a `quantized_only` one. Both ignore it.
- With rerank on, the scores you get back are raw-vector distances. With it off, they are ADC estimates. The two are not comparable, so a threshold tuned against one does not carry to the other.

An index trained before the calibration existed, including any index loaded from a directory saved by an earlier release, carries no calibration and falls back to a fixed fetch of 2% of the record count, floored at 250 candidates and at `5 × top_k`. `get_stats()` reports `rerank_calibrated: false` for it. Rebuild the index to calibrate it.

### `ef_search` does nothing on a reranked quantized search

The graph traversal is widened to the rerank fetch, and the fetch already exceeds any `ef_search` a caller is likely to set, so a smaller value is discarded. Raising it above the fetch buys no recall either, because the candidates are limited by the code ordering rather than by the traversal, and it costs query time. Change `rerank` instead. On an unquantized search, and on a quantized search with `rerank=0`, `ef_search` applies normally.

<br/>


**🗜️ Usage Example 1**

```python
from zeusdb import VectorDatabase
import numpy as np

vdb = VectorDatabase()

quantization_config = {
    'type': 'pq',                        # `pq` for Product Quantization
    'subvectors': 8,                     # 8 subvectors of 192 dims each
    'bits': 8,                           # 256 centroids per subvector (2^8)
    'training_size': 1000,               # Train once 1,000 records are collected
    'storage_mode': 'quantized_with_raw' # Keep raw vectors so results can be reranked
}

index = vdb.create(
    index_type="hnsw",
    dim=1536,                                # OpenAI `text-embedding-3-small` dimension
    expected_size=2500,
    quantization_config=quantization_config
)

# Add vectors. Training triggers automatically at the threshold.
rng = np.random.default_rng(0)
documents = {
    "ids": [f"doc_{i}" for i in range(2500)],
    "embeddings": rng.random((2500, 1536), dtype=np.float32),
    "metadatas": [{"category": "tech", "year": 2026} for _ in range(2500)],
}

result = index.add(documents)
print("inserted:", result.total_inserted)

# Check quantization status
print("training progress:", f"{index.get_training_progress():.1f}%")
print("storage mode:", index.get_storage_mode())
print("is quantized:", index.is_quantized())

# Get compression statistics
quant_info = index.get_quantization_info()
print("compression ratio:", f"{quant_info['compression_ratio']:.1f}x")
print("codebook memory:", f"{quant_info['memory_mb']:.1f} MB")

# Search works the same way on a quantized index
query_vector = rng.random(1536, dtype=np.float32)
results = index.search(vector=query_vector, top_k=3)
print("results:", len(results), "| keys:", sorted(results[0].keys()))
```

*Output*
```text
inserted: 2500
training progress: 100.0%
storage mode: quantized_active
is quantized: True
compression ratio: 768.0x
codebook memory: 1.5 MB
results: 3 | keys: ['id', 'metadata', 'score']
```

The result IDs and scores depend on the data, so they are not shown. Production indexes use a much larger `training_size`; 1,000 is the minimum the validator accepts and keeps this example quick. `create()` emits a `UserWarning` for `quantized_with_raw` describing the memory trade, and another when a `subvectors` value you passed implies a ratio above 50x, as the explicit 8 here does at `dim=1536`.

`index.info()` reports the quantization state as well:

```python
print(index.info())
```

*Output*
```text
HNSWIndex(dim=1536, space=cosine, m=16, ef_construction=200, expected_size=2500, vectors=2500, quantization=pq(subvectors=8, bits=8, trained, active, compression=768.0x))
```

<br />

**🗜️ Usage Example 2 - with explicit storage mode**

```python
from zeusdb import VectorDatabase

vdb = VectorDatabase()

quantization_config = {
    'type': 'pq',
    'subvectors': 8,
    'bits': 8,
    'training_size': 10000,
    'max_training_vectors': 50000,
    'storage_mode': 'quantized_only'    # Drop raw vectors once training completes
}

index = vdb.create(
    index_type="hnsw",
    dim=3072,                           # OpenAI `text-embedding-3-large` dimension
    expected_size=100000,
    quantization_config=quantization_config
)
```

<br />

## ⚙️ Configuration Guidelines

For accuracy with a memory saving (recommended):
```python
quantization_config = {
    'type': 'pq',                         # subvectors and training_size derived
    'storage_mode': 'quantized_with_raw'  # Keep raw vectors so search can rerank
}
# Matches unquantized recall through reranking.
# Measured 0.59x the resident memory of an unquantized index at 50,000
# records of dim=1536.
```

For maximum memory saving, where recall does not matter:
```python
quantization_config = {
    'type': 'pq',
    'storage_mode': 'quantized_only'  # Default. No raw vectors, no reranking
}
# Measured 0.22x the resident memory of an unquantized index at 50,000
# records of dim=1536, returning roughly half the correct results.
```

Leave `subvectors` and `bits` at their defaults unless you have measured a reason to move them. Raising `subvectors` lowers the compression ratio, costs memory and build time, and returns almost nothing on recall at the default rerank. Lowering `bits` shrinks only the fixed tables and costs recall.

### 📊 Performance Characteristics

- **Training**: happens once, on the `add()` call that reaches `training_size`. That call takes noticeably longer than the others. Training alone is roughly linear in the training set, measured at 3.1 s for 1,000 vectors and 40.6 s for 10,000 at `dim=768`. On `quantized_with_raw` it also calibrates the rerank fetch.
- **Memory**: a record's code is `subvectors` bytes against `dim × 4` for a raw vector, and the graph's internal copy of every point shrinks by the same factor, which is why both storage modes hold less than an unquantized index once past their break-even record count.
- **Search speed**: an unreranked quantized search is faster than a raw search, and far less accurate. A reranked one matches unquantized recall, is faster below roughly 10,000 records, and is slower above, with the gap widening as the index grows. Measured on real 1536-dimensional embeddings, a reranked quantized search ran at 0.96x the unquantized query time at 10,000 records, 1.56x at 25,000 and 2.42x at 100,000.
- **Build speed**: a quantized build is faster than an unquantized one, because the graph compares codes rather than vectors.
- **Accuracy**: see [Quantized search accuracy](#quantized-search-accuracy). Treat quantization as a memory decision that costs accuracy or query time, not as a free win.

Quantization pays best on large, high-dimensional datasets where memory is the constraint. Measure recall on your own data before you rely on it.


<br/>
