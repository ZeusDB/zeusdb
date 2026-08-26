# Upgrading

`zeusdb` pins `zeusdb-vector-database` to one minor series at a time, so a breaking release of the vector database reaches you only when `zeusdb` moves its constraint. The constraint is `zeusdb-vector-database>=0.8.0,<0.9.0`, so installing or upgrading `zeusdb` brings in the 0.8.0 series. Read the section for the series you are coming from before upgrading.

## Upgrading to 0.8.0

The changes below are observable from an application written against `zeusdb-vector-database` 0.5.0, 0.6.0 or 0.7.0. Most saved indexes and most code keep working; the items that do not are listed first.

### Breaking

- **`dim` is required on `create()`.** It defaulted to 1,536. `create("hnsw")` without it raises `TypeError`. Pass the width your embedding model produces.
- **A metadata filter decides which records are ranked, not which results survive.** A filtered search returns the `top_k` nearest of the records the filter matches, where it used to return whatever survived the filter out of the `top_k` nearest overall. Code that raised `top_k` to compensate can stop, and a test that pinned a short page under a filter needs its expectation refreshed. See [Metadata Filtering](metadata_filtering.md).
- **`add()` raises on a malformed batch.** Parallel arrays of different lengths raise `ValueError`, and a parallel array that is not a `list`, such as a tuple or an ndarray of ids, raises `TypeError`. Both used to be absorbed silently. See [Add Data](usage/add.md).
- **`l1` cannot be quantized.** `create(space="l1", quantization_config=...)` raises, and `load()` refuses a saved directory pairing them, whatever release saved it. Use `l2` with the same configuration, or `l1` without quantization. See [Metrics that cannot be quantized](#metrics-that-cannot-be-quantized).
- **A quantized `cosine` index ranks and scores by cosine distance to the reconstruction**, where it ranked by the squared distance and reported that. Result order changes, in each measured case for the better, and a test that pinned scores or exact result sets from a quantized cosine index needs refreshing. A directory saved earlier opens and is scored by cosine distance from then on; loading it once with `ZEUSDB_LOAD_REBUILD_GRAPH=1` set and saving it again wires its graph on the new ordering.
- **A quantized `l2` index reports the rooted distance on every path.** The traversal used to return the squared sum. A threshold derived from the old traversal scores needs re-deriving on the rooted scale.
- **`dim`, `ef_construction`, `top_k` and `ef_search` have ceilings**: 65,536, 4,096, 65,536 and 131,072. None had one. A directory saved with a value outside these bounds does not open under this release.
- **`save()` and `load()` print nothing.** Both wrote progress lines to stdout. A script that read stdout for them has nothing to read. The steps are `debug` log records instead.
- **The saved graph is one file, `hnsw_index.zdbgraph`**, in place of `hnsw_index.hnsw.graph` and `hnsw_index.hnsw.data`, since 0.7.0. A directory holding the old pair opens, rebuilds its graph once, and writes the single file on the next `save()`. Code that lists the directory or reads `files_included` needs the new name.
- **One wheel per platform, built against the stable ABI**, since 0.6.0. A pinned wheel filename carrying an interpreter tag such as `cp312-cp312` no longer resolves, and PyPy and free-threaded CPython build from the source distribution.

### Changed

- **An unquantized index holds about half the memory it did**, because every raw vector was held twice. At 50,000 records of dimension 1,536 the index commits 325 MiB where it committed 632. `graph_memory_mb` and `total_memory_mb` both read lower on an index that has not changed. `quantized_with_raw` now holds more than an unquantized index at every record count, 1.08x at 50,000 records of dimension 1,536, which the earlier figures on this site had the other way round.
- **A save is atomic and verified.** A save writes a sibling directory and renames it into place, and `manifest.json` records a length and a digest for every other artefact, which `load()` checks before parsing them. `load()` also refuses a directory missing a file the manifest names. See [Persistence](persistence.md).
- **`list()` returns records in arrival order** and pages with `offset` and `after`, where it returned hash map iteration order that differed between processes.
- **Every spelling of a log level is accepted by both layers.** `warning`, `critical`, `warn`, `err`, `fatal` and `error` all work, where `warning` and `critical` were refused by the Rust layer and `warn` by the Python layer.
- **Records queued in the log file's writer at process exit are no longer lost.** The file is drained through an `atexit` hook, and `shutdown_logging()` drains it on demand.
- **The `quantized_only` break-even warning, the `quantized_with_raw` warning and the compression ratio warning attribute to your `create()` line**, and the low dimension warning is gone.

### Added

`space="dot"`. `$and`, `$or` and `$not` in the filter language, and the operators `nin`, `any`, `all`, `exists`, `is_missing` and `is_null`. `create(indexed_fields=[...])`. `len(index)`, `id in index` and `count()`. `remove_points()`, `remove_where()`, `delete()`, `clear()`, `update_metadata()`, `rebuild()` and `shrink_to_fit()`. `list(after=...)`. `get_records(strict=True)`. `AddResult.ids`. `index.space`, `index.m`, `index.ef_construction`, `index.expected_size` and `index.indexed_fields`. `shutdown_logging()`. Each is documented on the page for its operation.

## Upgrading from 0.4.x

`zeusdb-vector-database` 0.5.0 changed behaviour in ways an application written against the 0.4 releases can observe. Saved indexes and existing code largely keep working; the items below are the differences that matter, and the section above applies on top of them.

### Search results

**A reranked quantized search returns the raw-vector distance as the score, not the distance to the reconstruction.** Any threshold tuned against the old scores is wrong on a `quantized_with_raw` index. Pass `rerank=0` to restore the unreranked scores and ordering.

**Search on a quantized index over-fetches by default.** A `quantized_with_raw` index now fetches and rescores a calibrated number of candidates per query, which holds recall at the level of an unquantized index and costs query time above roughly 10,000 records. See [Product Quantization](product_quantization.md).

### Filters

- An unknown filter operator now raises `ValueError` rather than returning an empty result set.
- Numbers compare by magnitude across every operator, so an integer and an equal float now match under `eq`, `ne` and `in` as they already did under `lt` and `gte`.
- Array conditions now compare for equality rather than being silently dropped, so `{"tags": ["ai"]}` matches only records whose `tags` is exactly `["ai"]`.
- `ne` against a field a record does not have returns false, so a filter for "status is not archived" excludes records with no status at all.

### Add and overwrite

- `add()` with `overwrite=False` on an existing ID reports the collision through the returned `AddResult` rather than raising.
- Metadata is replaced wholesale on overwrite, never merged, so an overwrite with an empty metadata dict clears it.
- `summary()` returns a plain ASCII string; the emoji prefix is gone.

### Validation

- Vectors containing `NaN` or an infinity are rejected on `add()`, raise on `search()`, and are refused on `load()`.
- `m` must be at least 2. `expected_size` must be at most 100,000,000.

### Changed defaults

- The default `m` now scales with `expected_size`: 16 up to 25,000 and 32 above. Pass `m` explicitly to keep the old value.
- The default `subvectors` now scales with the dimension rather than being fixed at 8, holding compression at 128x from `dim=256` upward. Pass `subvectors: 8` explicitly to keep the old code size.
- The default `training_size` is derived, 10,000 at the default `bits`, rather than 1,000.
- The default `ef_search` is `max(2 × top_k, 150)` for `l1` and `l2`; `cosine` keeps `max(2 × top_k, 100)`.

### Removed entry points

Around a dozen entry points that were duplicate, dead or unsafe were removed, including `get_next_id`, which consumed an internal ID on every call. `HNSWIndex` can no longer be constructed directly; instances come from `VectorDatabase.create()` or `load()`. `get_stats()` lost `memory_savings` and gained `graph_memory_mb`, `total_memory_mb` and `raw_vectors_memory_mb`. `get_performance_info()` lost its insertion speedup fields, which described a parallel insert path that does not exist.

### Behaviour improvements you get without code changes

- **Persistence**: loading now reads the saved graph back rather than rebuilding it, so a load takes about a second at 50,000 records and returns identical results to the index that was saved. An index saved by 0.4.x still loads; its graph dump carries the old distance names, so the loader rebuilds it, with no user action required.
- **Deletion**: removed and overwritten records no longer consume result slots, so `top_k` no longer degrades with churn. A `compact()` method reclaims the stranded graph nodes.
- **Concurrency**: concurrent search now works and scales, measured at roughly seven times single-thread throughput at sixteen threads, and `add()` and `search()` can run concurrently.

### Logging

- `ZEUSDB_LOG_FILE` now writes exactly the path given rather than a dated sibling. Set `ZEUSDB_LOG_ROTATION=daily` for the previous behaviour.
- The disable flag is `ZEUSDB_DISABLE_AUTO_LOGGING` in both the Python and Rust layers, with the former Rust-only name accepted as a deprecated alias. Both require `true`, `1` or `yes`.

## Platform support

Wheels are published for Linux x86_64 and aarch64 (glibc and musl), macOS Apple Silicon, and Windows x86_64, for Python 3.10 through 3.14. macOS Intel, 32-bit x86, armv7, s390x and ppc64le are no longer published.

## The `zeusdb` package

`zeusdb` re-exports the full public surface of the vector database (`VectorDatabase`, `HNSWIndex`, `AddResult`, `init_logging`, `init_file_logging`, `is_logging_initialized`, `shutdown_logging`) and provides the `zeusdb.logging_config` helpers the integration packages import, documented under [Logging](logging.md). It pins `zeusdb-vector-database>=0.8.0,<0.9.0`, so a future breaking release will not reach you automatically.
