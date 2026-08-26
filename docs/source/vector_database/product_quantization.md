# Product Quantization

Product Quantization (PQ) is a vector compression technique that reduces memory usage by dividing each vector into subvectors and quantizing them independently. A record's compressed form is one byte per subvector, whatever the dimension, so an index over 1536-dimensional vectors with 8 subvectors stores 8 bytes per code in place of 6144 bytes of float32.

ZeusDB Vector Database's PQ implementation features:

✅ Automatic training, triggered on the `add()` call that reaches the configured threshold

✅ Compact codes, one byte per subvector per record

✅ Asymmetric Distance Computation (ADC) for fast search against the codes

✅ Automatic switch from raw to quantized storage once training completes

Compression is not free, and the accuracy cost is much larger than the memory saving suggests. Read [Quantized search accuracy](#quantized-search-accuracy) before choosing a storage mode, and [Metrics that cannot be quantized](#metrics-that-cannot-be-quantized) before choosing a space.

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
    * `"quantized_only"` - Stores only quantized codes once trained. The memory mode. Results cannot be reranked, so recall is far below an unquantized index.
    * `"quantized_with_raw"` - Keeps raw vectors alongside the codes. The accuracy mode. Search reranks against the raw vectors by default and matches unquantized recall, and the index holds more memory than an unquantized one.
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

Quantization is available under `cosine` and `l2` only. `create()` refuses `l1` and `dot` together with a `quantization_config`; see [Metrics that cannot be quantized](#metrics-that-cannot-be-quantized).

<br/>

## 📦 Storage modes

| Mode | What it stores | Rerank available | Memory |
|------|----------------|------------------|--------|
| `quantized_only` | Codes for every record; the raw vectors collected for training are released when training completes | No | Lowest. Below an unquantized index from a break-even record count that `create()` names |
| `quantized_with_raw` | Codes and raw vectors for every record | Yes | Highest. It adds the codes and the trained tables to everything an unquantized index holds, so it is above an unquantized index at every record count |

A raw vector is held once, in a store the graph reads. `quantized_only` replaces it with a code and holds a second code in the map that finds a record by id, so it saves `dim × 4 - 2 × subvectors` bytes per record against a codebook and a centroid distance table it holds whatever the record count. `quantized_with_raw` keeps the raw vector and adds both codes and both tables to it.

Measured resident, one index per interpreter, 50,000 records of real embeddings in each mode over the same data:

| dataset | dim | unquantized | `quantized_only` | `quantized_with_raw` |
|---|---:|---:|---:|---:|
| dbpedia-openai | 1,536 | 334.4 MiB | 69.1 MiB, 0.21x | 361.7 MiB, 1.08x |
| sift-128 | 128 | 66.6 MiB | 50.5 MiB, 0.76x | 76.1 MiB, 1.14x |

**Pick `quantized_only` when memory is the constraint and `quantized_with_raw` when accuracy is.** What `quantized_only` saves is set by the share of a record that is the vector, and that share falls with the dimension: 37% at `dim=128` and 88% at `dim=1,536` on the rows above. `get_stats()` prices your own index on your own records, which is the figure to size against.

`create()` warns when `quantized_only` cannot repay its fixed tables at the `expected_size` you declared, naming the record count above which it starts saving, which is 1,297 records at `dim=1536` and 4,626 at `dim=64` with the default `subvectors` and `bits`. Raise `expected_size` if your estimate was low, or drop `quantization_config`. `quantized_with_raw` never repays them, so it gets a warning that names the mode instead. A separate warning fires when `expected_size` is below `training_size`, because an index that never reaches its training threshold never trains.

Two consequences of `quantized_only` are worth knowing before you pick it.

**The training records are held at full width only until training completes.** Records collected before the threshold is reached are stored raw so the quantizer has something to train on. The moment training completes they are encoded and their raw copies are released, so a trained index in this mode holds no raw vector for any record, and `get_stats()["raw_vectors_stored"]` reads zero.

**Once training completes every record exists only as a code, so the vector you read back is an approximation.** `get_records(..., return_vector=True)` and `search(..., return_vector=True)` reconstruct the vector from its code, so what they hand back is close to the value supplied rather than equal to it. Only `quantized_with_raw` reads back exactly.

**Recall cannot be recovered.** Without raw vectors there is nothing to rerank against, so no tuning restores the accuracy the codes discard. See the next section.

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

**A quantized index scores on the metric it declared.** A quantized `cosine` index ranks by the cosine distance to each record's reconstruction and reports it, and a quantized `l2` index reports the euclidean distance to the reconstruction on every path. A reconstruction is assembled from independently trained per-subspace centroids, so it is not a unit vector even where the record it stands for was; measured on 25,000 OpenAI embeddings at `dim=1,536` with 48 subvectors, reconstructed norms ran 0.85 to 0.96 against a stored norm of 1.0. Ranking by cosine rather than by the squared distance to the reconstruction measured better on every corpus tried, by 0.0015 to 0.0518 of recall at 10.

**How deep a search has to fetch to hold recall depends on your data, not on the record count.** Measured on three real datasets at 100,000 records with the default `subvectors`, the fetch that reaches mean recall at 10 of 0.99:

| dataset | dim | compression | fetch for 0.99 | share of corpus |
|---|---:|---:|---:|---:|
| dbpedia-openai (ada-002) | 1,536 | 128x | 494 | 0.49% |
| sift-128 | 128 | 64x | 426 | 0.43% |
| glove-100 | 100 | 40x | 5,143 | 5.14% |

No formula in the record count fits those three, so ZeusDB measures the fetch on your data instead. On data with no resolvable structure no fetch works, so measure recall on your own data before you rely on quantization.

### The `rerank` argument

`search()` takes a `rerank` argument on a quantized index:

- `rerank` omitted uses a fetch calibrated on your own data. When a `quantized_with_raw` index finishes training it measures how deep a search has to fetch into the code ordering to reach recall at 10 of 0.99 on the training records, how that depth grows with the record count, and how it grows with `top_k`. `get_stats()` reports the calibration under the `rerank_` keys, and `rerank_default_fetch` is the number of candidates a search at `top_k=10` fetches and rescores at the current record count.
- `rerank=N` for N of 1 or more fetches `top_k × N` candidates, a fixed multiple that does not move with the corpus. Use it to override the default deliberately, for example to trade recall for query time.
- `rerank=0` turns reranking off and returns the distances to the reconstructions and their ordering.
- `rerank` has no effect on an unquantized index or on a `quantized_only` one. Both ignore it.
- With rerank on, the scores you get back are exact distances to the raw vectors. With it off, they are distances to the reconstructions. Both are on the scale the index's own space reports, so a page is on one scale whichever you asked for, but the two are not equal and the difference is the quantization error.

An index trained before the calibration existed, and any index loaded from a directory saved by one, carries no calibration and falls back to a fixed fetch of 2% of the record count. `get_stats()` reports `rerank_calibrated: false` for it. Rebuild the index to calibrate it.

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

The result IDs and scores depend on the data, so they are not shown. Production indexes use a much larger `training_size`; 1,000 is the minimum the validator accepts and keeps this example quick. `create()` emits a `UserWarning` for `quantized_with_raw` naming it as the accuracy mode and pricing what it adds, and another when a `subvectors` value you passed implies a ratio above 50x, as the explicit 8 here does at `dim=1536`.

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

(metrics-that-cannot-be-quantized)=
## 🚫 Metrics that cannot be quantized

`create()` refuses `space="l1"` and `space="dot"` together with `quantization_config`, and `load()` refuses a saved directory that pairs them.

```python
try:
    VectorDatabase().create(
        "hnsw", dim=16, space="l1", expected_size=20000,
        quantization_config={"type": "pq", "subvectors": 4, "bits": 8, "training_size": 1000},
    )
except RuntimeError as exc:
    print(str(exc).split(".")[0])
```

*Output*
```text
Failed to create HNSW index: space='l1' cannot be quantized
```

A quantized graph works from tables of squared L2 distances to the codebook. `l2` and `cosine` can both be recovered from those, using the codebook's own centroid norms where the conversion needs them. The two below are refused, each for its own reason.

- **`l1`.** Against the query `[0, 0]`, the point `[2, 0]` is at L1 2.0 and squared L2 4.0, while `[1.1, 1.1]` is at L1 2.2 and squared L2 2.42. The two rank that pair in opposite orders. L1 tables over the codebook are buildable, since Manhattan distance is separable across subvectors, and were measured over the shipped codebook and over a k-medians codebook fitted to absolute error. By brute force over their own reconstructions at 100,000 records on three corpora, ranking by L1 to a k-medians reconstruction reached recall at 10 of 0.17 to 0.65 against an exact L1 ranking, 0.03 to 0.08 below what quantized `l2` reaches against exact L2 on the same records and code length, and at the default `subvectors` below the squared L2 ordering it would replace on every corpus. The codebook objective moved recall by under 0.01 anywhere. Use `l2` if squared distance suits your data, or drop `quantization_config`.
- **`dot`.** The codebook is fitted by squared L2, and a codebook fitted that way cannot rank by the inner product. Measured by brute force over its own reconstructions at the default configuration, recall at 10 against an exact inner product ranking never exceeded 0.37, at least 0.35 below an unquantized `dot` index on the same data, across three corpora and stored length spreads up to three orders of magnitude. Use `cosine` with normalised vectors where only direction should count, or `dot` without `quantization_config` where length must count.

**A directory saved by 0.7.0 or earlier that pairs `l1` with quantization no longer loads.** `load()` raises `ValueError` naming the path. Open it under the release that saved it, read the records back with `get_records()`, and add them to an index created under `l2` or without quantization.

<br />

## ⚙️ Configuration Guidelines

For a memory saving, where recall can be traded for it:
```python
quantization_config = {
    'type': 'pq',
    'storage_mode': 'quantized_only'  # Default. No raw vectors, no reranking
}
# Measured 0.21x the resident memory of an unquantized index at 50,000
# records of real embeddings at dim=1536, returning roughly half the
# correct results.
```

For quantization with accuracy, where memory is not the constraint:
```python
quantization_config = {
    'type': 'pq',                         # subvectors and training_size derived
    'storage_mode': 'quantized_with_raw'  # Keep raw vectors so search can rerank
}
# Matches unquantized recall through reranking, and holds 1.08x the
# resident memory of an unquantized index at 50,000 records of dim=1536.
# It is the only mode that reads back the vector you inserted.
```

Leave `subvectors` and `bits` at their defaults unless you have measured a reason to move them. Raising `subvectors` lowers the compression ratio, costs memory and build time, and returns almost nothing on recall at the default rerank. Lowering `bits` shrinks only the fixed tables and costs recall.

### 📊 Performance Characteristics

- **Training**: happens once, on the `add()` call that reaches `training_size`. That call takes noticeably longer than the others. Measured on random vectors at `dim=768` with the default `subvectors`, the `add()` that trained took 1.8 s for 1,000 records and 26.7 s for 10,000, against 0.1 s and 4.0 s for the same records into an unquantized index. On `quantized_with_raw` it also calibrates the rerank fetch, which `get_stats()["rerank_calibration_ms"]` prices, at 0.8 s for the 10,000 record case.
- **Memory**: a record's code is `subvectors` bytes against `dim × 4` for a raw vector, and a raw vector is held once. `quantized_only` saves and `quantized_with_raw` costs. The table in Storage modes prices both at `dim=128` and `dim=1,536`.
- **Search speed**: an unreranked quantized search is faster than a raw search, and far less accurate. A reranked one matches unquantized recall, is faster below roughly 10,000 records, and is slower above, with the gap widening as the index grows. Measured on real 1536-dimensional embeddings, paired against an unquantized index over the same records, a reranked quantized search ran at 0.95x the unquantized query time at 10,000 records, 1.23x at 25,000, 1.32x at 50,000 and 1.79x at 100,000.
- **Build speed**: a quantized build is faster than an unquantized one, because the graph compares codes rather than vectors, and it slows as `subvectors` rises. At 100,000 records of `dim=768` it is 137 s against 231 s at the default `subvectors`.
- **Accuracy**: see [Quantized search accuracy](#quantized-search-accuracy). Treat quantization as a memory decision that costs accuracy or query time, not as a free win.

Quantization pays best on large, high-dimensional datasets where memory is the constraint. Measure recall on your own data before you rely on it.


<br/>
