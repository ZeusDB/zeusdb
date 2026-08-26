# Logging

ZeusDB Vector Database includes enterprise-grade structured logging that works automatically out of the box while providing extensive customization for advanced users.

The logging system is designed to be invisible when you don’t need it and powerful when you do. Most users will never need to configure anything, while enterprise users get full control over observability.

## Basic Usage - it just works!

For most users, logging works automatically out of the box. No need to do anything.

<!-- zeusdb:skip -->
```python
from zeusdb import VectorDatabase
# Logging is automatically configured - no setup required!

vdb = VectorDatabase()
index = vdb.create("hnsw", dim=1536)

# Operations are automatically logged with structured data
result = index.add({"ids": ids, "embeddings": vectors})
results = index.search(query_vector, top_k=5)
```

**What you get automatically:**
- ✅ **Quiet by default** - Only errors and warnings outside development
- ✅ **Environment detection** - Appropriate defaults for dev/prod/testing/CI/notebooks
- ✅ **Structured JSON logs** in production environments  
- ✅ **Human-readable logs** in development environments
- ✅ **Operation timing** on index creation, additions, searches and saves
- ✅ **Cross-platform compatibility** 

`save()` and `load()` write their progress here too, at `debug`, so they print nothing on stdout. They used to print it directly, outside the logging system.


### Smart Environment Detection

The system automatically detects where your code is running and applies appropriate logging defaults.

- **🏭 Production** (`ENVIRONMENT=production`): ERROR level, JSON format, often file output
- **💻 Development** (default): WARNING level, human format, console output  
- **🧪 Testing** (`pytest`, `PYTEST_CURRENT_TEST`): CRITICAL level, minimal output
- **📓 Jupyter** (`JUPYTER_SERVER_ROOT`): INFO level, human format, clean output
- **🔄 CI/CD** (`CI`, `GITHUB_ACTIONS`): WARNING level, human format for readability

#### How Environment Detection Works

The system checks for these indicators, with an explicit `ENVIRONMENT` value winning over auto-detection:

| Environment | Detection Method | What It Finds |
|-------------|------------------|---------------|
| **Explicit** | `ENVIRONMENT=production` / `development` / `testing` | User explicitly set (short forms `prod`, `dev`, `test` also accepted) |
| **Testing** | `PYTEST_CURRENT_TEST` | pytest automatically sets this |
| **Testing** | `'pytest' in sys.modules` | pytest imported |
| **Jupyter** | `JUPYTER_SERVER_ROOT` | Jupyter server running |
| **Jupyter** | `JPY_PARENT_PID` | Jupyter kernel process |
| **Jupyter** | `'IPython' in sys.modules` | IPython/Jupyter imported |
| **CI/CD** | `CI` | Most CI systems set this |
| **CI/CD** | `GITHUB_ACTIONS` | GitHub Actions |
| **CI/CD** | `GITLAB_CI` | GitLab CI |
| **Production** | `KUBERNETES_SERVICE_HOST` | Running in Kubernetes |
| **Production** | `DOCKER_CONTAINER` | Running in Docker |

Environment variables always override the detected defaults.

#### Override Environment Detection

Set `ENVIRONMENT` before ZeusDB is first imported, since the defaults are applied at import time:

<!-- zeusdb:skip -->
```python
import os

# Force production mode
os.environ['ENVIRONMENT'] = 'production'
import zeusdb  # Will use ERROR level, JSON format

# Force development mode  
os.environ['ENVIRONMENT'] = 'development'  
import zeusdb  # Will use WARNING level, human format
```

<br />

## Intermediate Usage (Environment Variables)

Control logging behavior with environment variables.

**Quick Development Debugging**
```bash
export ZEUSDB_LOG_LEVEL=debug
python your_app.py
```

**Production JSON Logging**
```bash
export ZEUSDB_LOG_LEVEL=error
export ZEUSDB_LOG_FORMAT=json
export ZEUSDB_LOG_TARGET=file
export ZEUSDB_LOG_FILE=/var/log/zeusdb/app.log
python your_app.py
```

### Environment Variables Reference

| Variable | Options | Default | Description |
|----------|---------|---------|-------------|
| `ZEUSDB_LOG_LEVEL` | `trace`, `debug`, `info`, `warn`, `error` | `warn` (dev), `error` (prod) | Controls log verbosity. `warning` and `warn` are the same level, as are `critical`, `fatal`, `err` and `error`. An unrecognised name falls back to the default and logs a warning naming it |
| `ZEUSDB_LOG_FORMAT` | `human`, `json` | `human` (dev), `json` (prod) | Output format |
| `ZEUSDB_LOG_TARGET` | `stdout`, `stderr`, `file` | `stderr` | Where logs go |
| `ZEUSDB_LOG_FILE` | `/path/to/file.log` | `zeusdb.log` | Log file path, written exactly as given (if target=file) |
| `ZEUSDB_LOG_ROTATION` | `daily`, `never` | `never` | With `daily`, a UTC date is appended to the file name |
| `ZEUSDB_LOG_CONSOLE` | `true`, `false` | Auto-detected | Force console output |
| `ZEUSDB_DISABLE_AUTO_LOGGING` | `true`, `1`, `yes` | unset | Skip automatic configuration entirely |
| `RUST_LOG` | standard `env_logger` syntax | unset | Overrides `ZEUSDB_LOG_LEVEL` for the Rust layer |

**Every spelling of a level is accepted by both layers.** The Python layer and the Rust layer used to disagree, so `ZEUSDB_LOG_LEVEL=warning` was refused by the Rust layer with an `ignoring` line on stderr and `warn` was refused by the Python layer. Both now resolve `warn`, `warning`, `err`, `error`, `fatal` and `critical`.

**Log rotation.** `ZEUSDB_LOG_FILE` writes exactly the path given. Under `ZEUSDB_LOG_ROTATION=daily` with `ZEUSDB_LOG_FILE=logs/app.log`, two files appear: `logs/app.log` and a dated `logs/app.log.2026-08-26`. Rotation applies to the Rust layer, which writes the dated one.

<br />

## Advanced Usage (Programmatic Control)

For enterprise environments with existing logging infrastructure.

### Option 1: Disable Auto-Configuration
<!-- zeusdb:skip -->
```python
import os
os.environ["ZEUSDB_DISABLE_AUTO_LOGGING"] = "1"

# Now configure your own logging before importing ZeusDB
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from zeusdb import VectorDatabase  # Will respect your existing logging setup
```

### Option 2: Programmatic Initialization
<!-- zeusdb:skip -->
```python
import os
os.environ["ZEUSDB_DISABLE_AUTO_LOGGING"] = "1"

import zeusdb

# JSON to stdout
success = zeusdb.init_logging(level="info")

# OR JSON to a directory of daily rotating files. Pick one, not both.
# success = zeusdb.init_file_logging(
#     log_dir="/var/log/myapp",
#     level="debug", 
#     file_prefix="zeusdb"
# )

print("initialized:", success)

vdb = zeusdb.VectorDatabase()
```

**Only the first initializer to run takes effect.** Both functions return `True` if they installed the logging subscriber and `False` if one was already installed, so calling both leaves the second with no effect and a `False` return. `zeusdb.is_logging_initialized()` reports whether either has run.

### The file target is drained at exit

Records reach the file through a background writer, so a record emitted immediately before the process ends is still in flight when it ends. Importing the package registers the drain with `atexit`, which covers a normal exit and needs no call. `zeusdb.shutdown_logging()` runs the same drain on demand and returns `True` if it drained a file appender, or `False` if there was nothing to drain, which is the answer for the `stdout` and `stderr` targets and for a second call. It closes the file, so records emitted after it are discarded. Nothing runs on `os._exit()` or on a crash, and records still in flight at either are lost, so call it before such an exit.

<!-- zeusdb:skip -->
```python
import zeusdb

vdb = zeusdb.VectorDatabase()
index = vdb.create("hnsw", dim=1536)
# ... work that logs to the file target ...

print(zeusdb.shutdown_logging())   # True: the file is complete and closed
print(zeusdb.shutdown_logging())   # False: nothing left to drain
```

### Option 3: Custom Logger Integration
<!-- zeusdb:skip -->
```python
import logging
import os

# Disable auto-configuration
os.environ["ZEUSDB_DISABLE_AUTO_LOGGING"] = "1"

# Set up your own logger first
logger = logging.getLogger("myapp.zeusdb")
logger.setLevel(logging.INFO)

# Configure Rust logging to match
os.environ["ZEUSDB_LOG_LEVEL"] = "info"
os.environ["ZEUSDB_LOG_FORMAT"] = "json"

from zeusdb import VectorDatabase
# ZeusDB will integrate with your logging setup
```

<br />

## Logging from your own code with `zeusdb.logging_config`

`zeusdb.logging_config` is the umbrella package's own module, and it is what `langchain-zeusdb` and `llama-index-vector-stores-zeusdb` import. It provides two helpers.

**`get_logger(name=None)`** returns a `logging.LoggerAdapter` over the vector database's own `zeusdb.vector` logger, or over `zeusdb.vector.<name>` when a name is given. The adapter accepts arbitrary keyword fields and moves them into the record's `extra` mapping, which a plain `logging.Logger` rejects with `TypeError: Logger._log() got an unexpected keyword argument`. The fields appear in JSON output and are available to any handler as record attributes.

**`operation_context(operation_name, **context)`** is a context manager that logs an operation's lifecycle: a `debug` record on entry, an `info` record carrying `duration_ms` on success, and an `error` record carrying `duration_ms`, `error` and a traceback on failure, after which the exception is re-raised. Every record carries `operation` and the keyword fields you pass.

**The umbrella's logging and the vector database's are one system, not two.** The logger `get_logger()` hands back is the vector database's own, so it carries the handler, level and format the vector database configured at import, and every setting on this page applies to it. `ZEUSDB_LOG_LEVEL` decides which of these records appear and `ZEUSDB_LOG_FORMAT` decides how, exactly as for the records the vector database emits itself.

<!-- zeusdb:skip -->
```python
from zeusdb.logging_config import get_logger, operation_context

logger = get_logger("myapp")
logger.warning("Empty embedding received", operation="add_texts", text_count=0)

with operation_context("reindex", source="nightly"):
    pass  # the work being timed
```

Under the development defaults, WARNING level and human format on stderr, the warning prints and the `info` record from `operation_context` is below the level:

```text
2026-08-26 11:52:45 - zeusdb.vector.myapp - WARNING - Empty embedding received
```

Under `ZEUSDB_LOG_LEVEL=info ZEUSDB_LOG_FORMAT=json` both appear, with the keyword fields as top-level keys:

```json
{"level":"WARNING","logger":"zeusdb.vector.myapp","message":"Empty embedding received","module":"<string>","function":"<module>","line":5,"timestamp":"2026-08-26T01:52:45.363376Z","timestamp_epoch":1787709165.3633757,"taskName":null,"operation":"add_texts","text_count":0}
{"level":"INFO","logger":"zeusdb.vector","message":"reindex completed","module":"logging_config","function":"operation_context","line":125,"timestamp":"2026-08-26T01:52:45.363620Z","timestamp_epoch":1787709165.3636196,"taskName":null,"operation":"reindex","duration_ms":0.0015999539755284786,"source":"nightly"}
```

A block that raises produces an `error` record with `error` and `exception` fields and the exception propagates:

```json
{"level":"ERROR","logger":"zeusdb.vector","message":"reindex failed","module":"logging_config","function":"operation_context","line":116,"timestamp":"2026-08-26T01:52:45.549910Z","timestamp_epoch":1787709165.5499096,"exception":"Traceback (most recent call last):\n  ...\nValueError: boom","taskName":null,"operation":"reindex","duration_ms":0.009700015652924776,"error":"boom","source":"nightly"}
```

Do not pass a field named after a `logging.LogRecord` attribute, such as `message`, `name` or `module`, since the stdlib refuses to overwrite one.

Both helpers work when `zeusdb-vector-database` is not installed, falling back to the same `zeusdb.vector` logger names with no handler configured, so a package that imports them does not fail at import.

<br />

### 📊 Log Output Examples

#### Human-Readable (Development)
```text
2026-08-26T01:52:44.4292699Z  INFO build: HNSW index created successfully operation="index_creation_complete" dim=8 space=cosine m=16 ef_construction=200 expected_size=10000 has_quantization=false indexed_fields=0 duration_ms=0 indexed_fields=[] dim=8 space=cosine m=16 ef_construction=200 expected_size=10000 has_quantization=false
2026-08-26T01:52:44.5957415Z  INFO add: Vector addition completed operation="add_vectors_complete" total_inserted=2 total_errors=0 success_rate=100.0 duration_ms=166 overwrite_mode=true final_storage_mode="raw_only" overwrite=true has_quantization=false is_quantized=false
```

The fields after the operation's own are the enclosing span's, repeated on every record inside it.

#### Structured JSON (Production)
```json
{"timestamp":"2026-08-26T01:52:44.8264153Z","level":"INFO","fields":{"message":"HNSW index created successfully","operation":"index_creation_complete","dim":8,"space":"cosine","m":16,"ef_construction":200,"expected_size":10000,"has_quantization":false,"indexed_fields":0,"duration_ms":"0"},"target":"zeusdb_vector_database::hnsw_index::construct","filename":"src\\hnsw_index\\construct.rs","line_number":709,"span":{"dim":8,"ef_construction":200,"expected_size":10000,"has_quantization":false,"indexed_fields":"[]","m":16,"space":"cosine","name":"build"},"spans":[{"dim":8,"ef_construction":200,"expected_size":10000,"has_quantization":false,"indexed_fields":"[]","m":16,"space":"cosine","name":"build"}],"threadId":"ThreadId(1)"}
```

### 🔍 Monitoring and Observability

#### Key Fields to Monitor
- **`operation`**: the operation name, for example `index_creation_complete`, `add_vectors_complete`, `search_complete`, `pq_training_complete`, `save_complete`, `compact_complete`
- **`duration_ms`**: timing on index creation, additions, searches, saves and compaction
- **`total_inserted`**, **`total_errors`**, **`success_rate`**: outcome of each `add()`
- **`final_storage_mode`**: whether an index is serving raw or quantized results
- **`results_count`**: results returned by a search
- **`filter_field_not_indexed`**: the `operation` of the warning logged once when a filter names a field left out of `indexed_fields`

#### Production Alerting Examples
```bash
# Monitor error rates
grep '"level":"ERROR"' /var/log/zeusdb/app.log | wc -l

# Track search latency
grep '"operation":"search_complete"' /var/log/zeusdb/app.log | jq '.fields.duration_ms'

# Watch quantization training
grep '"operation":"pq_training' /var/log/zeusdb/app.log
```

### 🛠️ Troubleshooting

#### Common Issues

**Logs not appearing?**
```bash
# Check if auto-logging is disabled
echo $ZEUSDB_DISABLE_AUTO_LOGGING

# Check the level
ZEUSDB_LOG_LEVEL=debug python -c "import zeusdb; print(zeusdb.is_logging_initialized())"
```

**File logging not working?**
```bash
# Check permissions
ls -la /path/to/log/directory

# Test with console first
ZEUSDB_LOG_TARGET=stderr ZEUSDB_LOG_LEVEL=info python your_app.py
```

A process that ends through `os._exit()` or a crash skips the exit drain, so its final records never reach the file. Call `zeusdb.shutdown_logging()` before such an exit.

**Want to see Rust logs specifically?**
```bash
# Enable trace level to see all Rust operations
ZEUSDB_LOG_LEVEL=trace python your_app.py
```

#### Performance Notes
- File logging is non-blocking: records are handed to a background writer rather than written on the calling thread. The exit drain waits for that writer to finish.
- `trace` and `debug` are verbose enough to dominate runtime on a hot loop. Leave production at `error`.

### Best Practices

#### Development
```bash
export ZEUSDB_LOG_LEVEL=debug
export ZEUSDB_LOG_FORMAT=human
```

#### Staging  
```bash
export ZEUSDB_LOG_LEVEL=info
export ZEUSDB_LOG_FORMAT=json
export ZEUSDB_LOG_TARGET=file
export ZEUSDB_LOG_FILE=logs/zeusdb-staging.log
export ZEUSDB_LOG_ROTATION=daily
```

#### Production
```bash
export ENVIRONMENT=production
export ZEUSDB_LOG_LEVEL=error  
export ZEUSDB_LOG_FORMAT=json
export ZEUSDB_LOG_TARGET=file
export ZEUSDB_LOG_FILE=/var/log/zeusdb/production.log
export ZEUSDB_LOG_ROTATION=daily
```

Logging stays out of the way when you don’t need it, but delivers full power and flexibility when you do. Most users never need to touch the settings, while enterprise teams can fine-tune every aspect of observability.

<br/>
