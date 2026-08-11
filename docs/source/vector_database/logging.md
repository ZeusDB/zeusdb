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

Note that `save()` and `load()` print progress directly to stdout. That output is not part of the logging system and is not affected by any of the settings below.


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
| `ZEUSDB_LOG_LEVEL` | `trace`, `debug`, `info`, `error` | `warning` (dev), `error` (prod) | Controls log verbosity |
| `ZEUSDB_LOG_FORMAT` | `human`, `json` | `human` (dev), `json` (prod) | Output format |
| `ZEUSDB_LOG_TARGET` | `stdout`, `stderr`, `file` | `stderr` | Where logs go |
| `ZEUSDB_LOG_FILE` | `/path/to/file.log` | `zeusdb.log` | Log file path, written exactly as given (if target=file) |
| `ZEUSDB_LOG_ROTATION` | `daily`, `never` | `never` | With `daily`, a UTC date is appended to the file name |
| `ZEUSDB_LOG_CONSOLE` | `true`, `false` | Auto-detected | Force console output |
| `ZEUSDB_DISABLE_AUTO_LOGGING` | `true`, `1`, `yes` | unset | Skip automatic configuration entirely |
| `RUST_LOG` | standard `env_logger` syntax | unset | Overrides `ZEUSDB_LOG_LEVEL` for the Rust layer |

**⚠️ `warning` and `critical` are not accepted level names.** The Python layer accepts them, but the Rust layer rejects them and prints `ignoring 'zeusdb_vector_database=warning': invalid filter directive`. The bare `warn` is the opposite, accepted by Rust and rejected by Python. Use `trace`, `debug`, `info` or `error`, which both layers accept.

**Log rotation.** `ZEUSDB_LOG_FILE` writes exactly the path given. Under `ZEUSDB_LOG_ROTATION=daily` with `ZEUSDB_LOG_FILE=logs/app.log`, two files appear: `logs/app.log` and a dated `logs/app.log.2026-08-05`. Rotation applies to the Rust layer, which writes the dated one.

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

### 📊 Log Output Examples

#### Human-Readable (Development)
```text
2026-08-05T12:19:39.261318Z  INFO build: HNSW index created successfully operation="index_creation_complete" dim=8 space=cosine m=16 ef_construction=200 expected_size=10000 has_quantization=false duration_ms=0
2026-08-05T12:19:39.3491294Z  INFO add: Vector addition completed operation="add_vectors_complete" total_inserted=2 total_errors=0 success_rate=100.0 duration_ms=87 overwrite_mode=true final_storage_mode="raw_only"
```

#### Structured JSON (Production)
```json
{"timestamp":"2026-08-05T12:19:39.4853862Z","level":"INFO","fields":{"message":"HNSW index created successfully","operation":"index_creation_complete","dim":8,"space":"cosine","m":16,"ef_construction":200,"expected_size":10000,"has_quantization":false,"duration_ms":"0"},"target":"zeusdb_vector_database::hnsw_index","filename":"src\\hnsw_index.rs","line_number":1068,"threadId":"ThreadId(1)"}
```

### 🔍 Monitoring and Observability

#### Key Fields to Monitor
- **`operation`**: the operation name, for example `index_creation_complete`, `add_vectors_complete`, `search_complete`, `pq_training_complete`, `save_complete`, `compact_complete`
- **`duration_ms`**: timing on index creation, additions, searches, saves and compaction
- **`total_inserted`**, **`total_errors`**, **`success_rate`**: outcome of each `add()`
- **`final_storage_mode`**: whether an index is serving raw or quantized results
- **`results_count`**: results returned by a search

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

# Verify the level is one both layers accept
ZEUSDB_LOG_LEVEL=debug python -c "import zeusdb; print(zeusdb.is_logging_initialized())"
```

**File logging not working?**
```bash
# Check permissions
ls -la /path/to/log/directory

# Test with console first
ZEUSDB_LOG_TARGET=stderr ZEUSDB_LOG_LEVEL=info python your_app.py
```

**Want to see Rust logs specifically?**
```bash
# Enable trace level to see all Rust operations
ZEUSDB_LOG_LEVEL=trace python your_app.py
```

#### Performance Notes
- File logging is non-blocking: records are handed to a background writer rather than written on the calling thread.
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
