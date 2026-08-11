# Upgrading from 0.4.x

`zeusdb-vector-database` 0.5.0 changed behaviour in ways an application written against 0.4.x can observe. `zeusdb` 0.1.0 installs it automatically, so read this page before upgrading. Saved indexes and existing code largely keep working; the items below are the differences that matter.

## Search results

**A reranked quantized search returns the raw-vector distance as the score, not the ADC estimate.** Any threshold tuned against the old scores is wrong on a `quantized_with_raw` index. Pass `rerank=0` to restore the ADC scores and ordering.

**Search on a quantized index over-fetches by default.** A `quantized_with_raw` index now fetches and rescores a calibrated number of candidates per query, which holds recall at the level of an unquantized index and costs query time above roughly 10,000 records. See [Product Quantization](product_quantization.md).

## Filters

- An unknown filter operator now raises `ValueError` rather than returning an empty result set.
- Numbers compare by magnitude across every operator, so an integer and an equal float now match under `eq`, `ne` and `in` as they already did under `lt` and `gte`.
- Array conditions now compare for equality rather than being silently dropped, so `{"tags": ["ai"]}` matches only records whose `tags` is exactly `["ai"]`.
- `ne` against a field a record does not have returns false, so a filter for "status is not archived" excludes records with no status at all.

## Add and overwrite

- `add()` with `overwrite=False` on an existing ID reports the collision through the returned `AddResult` rather than raising.
- Metadata is replaced wholesale on overwrite, never merged, so an overwrite with an empty metadata dict clears it.
- `summary()` returns a plain ASCII string; the emoji prefix is gone.

## Validation

- Vectors containing `NaN` or an infinity are rejected on `add()`, raise on `search()`, and are refused on `load()`.
- `m` must be at least 2. `expected_size` must be at most 100,000,000.

## Changed defaults

- The default `m` now scales with `expected_size`: 16 up to 25,000 and 32 above. Pass `m` explicitly to keep the old value.
- The default `subvectors` now scales with the dimension rather than being fixed at 8, holding compression at 128x from `dim=256` upward. Pass `subvectors: 8` explicitly to keep the old code size.
- The default `training_size` is derived, 10,000 at the default `bits`, rather than 1,000.
- The default `ef_search` is `max(2 × top_k, 150)` for `l1` and `l2`; `cosine` keeps `max(2 × top_k, 100)`.

## Removed entry points

Around a dozen entry points that were duplicate, dead or unsafe were removed, including `get_next_id`, which consumed an internal ID on every call. `HNSWIndex` can no longer be constructed directly; instances come from `VectorDatabase.create()` or `load()`. `get_stats()` lost `memory_savings` and gained `graph_memory_mb`, `total_memory_mb` and `raw_vectors_memory_mb`. `get_performance_info()` lost its insertion speedup fields, which described a parallel insert path that does not exist.

## Behaviour improvements you get without code changes

- **Persistence**: loading now reads the saved graph back rather than rebuilding it, so a load takes about a second at 50,000 records and returns identical results to the index that was saved. An index saved by 0.4.x still loads; its graph dump carries the old distance names, so the loader rebuilds it, with no user action required.
- **Deletion**: removed and overwritten records no longer consume result slots, so `top_k` no longer degrades with churn. A new `compact()` method reclaims the stranded graph nodes.
- **Concurrency**: concurrent search now works and scales, measured at roughly seven times single-thread throughput at sixteen threads, and `add()` and `search()` can run concurrently.

## Logging

- `ZEUSDB_LOG_FILE` now writes exactly the path given rather than a dated sibling. Set `ZEUSDB_LOG_ROTATION=daily` for the previous behaviour.
- The disable flag is `ZEUSDB_DISABLE_AUTO_LOGGING` in both the Python and Rust layers, with the former Rust-only name accepted as a deprecated alias. Both require `true`, `1` or `yes`.
- `warning` and `critical` are not accepted by the Rust layer as `ZEUSDB_LOG_LEVEL` values; use `trace`, `debug`, `info` or `error`.

## Platform support

Wheels are published for Linux x86_64 and aarch64 (glibc and musl), macOS Apple Silicon, and Windows x86_64, for Python 3.10 through 3.14. macOS Intel, 32-bit x86, armv7, s390x and ppc64le are no longer published.

## The `zeusdb` package

`zeusdb` 0.1.0 re-exports the full public surface of the vector database (`VectorDatabase`, `HNSWIndex`, `AddResult`, `init_logging`, `init_file_logging`, `is_logging_initialized`) and provides the `zeusdb.logging_config` helpers the integration packages import. It pins `zeusdb-vector-database>=0.5.0,<0.6.0`, so a future breaking release will not reach you automatically.
