# Logging

ZeusDB Vector Database includes enterprise-grade structured logging that works automatically out of the box while providing extensive customization for advanced users.

The logging system is designed to be invisible when you don’t need it and powerful when you do. Most users will never need to configure anything, while enterprise users get full control over observability.

## Basic Usage - it just works!

For most users, logging works automatically out of the box. No need to do anything.

```python
from zeusdb import VectorDatabase
# Logging is automatically configured - no setup required!

vdb = VectorDatabase()
index = vdb.create("hnsw", dim=1536)

# Operations are automatically logged with structured data
result = index.add({"vectors": vectors, "ids": ids})
results = index.search(query_vector, top_k=5)
```

**What you get automatically:**
- ✅ **Silent by default** - Only errors and warnings in production
- ✅ **Environment detection** - Appropriate defaults for dev/prod/testing
- ✅ **Structured JSON logs** in production environments  
- ✅ **Human-readable logs** in development environments
- ✅ **Performance timing** on all operations
- ✅ **Cross-platform compatibility** 


### Smart Environment Detection

This amazing feature automatically detects where your code is running and applies appropriate logging defaults!

- **🏭 Production** (`ENVIRONMENT=production`): ERROR level, JSON format, often file output
- **💻 Development** (`ENVIRONMENT=development`): WARNING level, human format, console output  
- **🧪 Testing** (`pytest`, `PYTEST_CURRENT_TEST`): CRITICAL level, minimal output
- **📓 Jupyter** (`JUPYTER_SERVER_ROOT`): INFO level, human format, clean output
- **🔄 CI/CD** (`CI`, `GITHUB_ACTIONS`): WARNING level, human format for readability

#### How Environment Detection Works

The system automatically checks for these indicators:

| Environment | Detection Method | What It Finds |
|-------------|------------------|---------------|
| **Testing** | `PYTEST_CURRENT_TEST` | pytest automatically sets this |
| **Testing** | `'pytest' in sys.modules` | pytest imported |
| **Jupyter** | `JUPYTER_SERVER_ROOT` | Jupyter server running |
| **Jupyter** | `JPY_PARENT_PID` | Jupyter kernel process |
| **Jupyter** | `'IPython' in sys.modules` | IPython/Jupyter imported |
| **CI/CD** | `CI=true` | Most CI systems set this |
| **CI/CD** | `GITHUB_ACTIONS=true` | GitHub Actions |
| **CI/CD** | `GITLAB_CI=true` | GitLab CI |
| **Production** | `KUBERNETES_SERVICE_HOST` | Running in Kubernetes |
| **Production** | `DOCKER_CONTAINER` | Running in Docker |
| **Explicit** | `ENVIRONMENT=production` | User explicitly set |

#### Real-World Examples

**🧪 In pytest:**
```bash
$ pytest test_my_app.py
# Environment detected: 'testing'
# Applied: CRITICAL level, no console output, minimal format
# Result: Your tests run clean without log spam!
```

**📓 In Jupyter:**
```python
# Cell 1
import zeusdb
# Environment detected: 'jupyter' (via JUPYTER_SERVER_ROOT)
# Applied: INFO level, human format, clean timestamps
# Result: Nice readable logs for exploration!

# Cell 2  
vdb = zeusdb.VectorDatabase()
# Logs: "Index created: dim=1536, vectors=0" (clean, readable)
```

**🏭 In Docker production:**
```bash
$ docker run my-app
# Environment detected: 'production' (via KUBERNETES_SERVICE_HOST)
# Applied: ERROR level, JSON format, structured output
# Result: Production-ready structured logs!
```

**💻 On your laptop:**
```bash
$ python my_script.py
# Environment detected: 'development' (default)
# Applied: WARNING level, human format, console output
# Result: Clean development experience!
```

#### Test Environment Detection Yourself

```python
# See what environment is detected
import zeusdb.logging_config as lc
env = lc._detect_environment()
print(f"Detected environment: {env}")

config = lc._get_smart_defaults(env)
print(f"Applied config: {config}")
```

#### Override Environment Detection

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

**Machine Learning Pipeline Debugging**
```bash
# For ML workflows where you want detailed progress tracking
export ZEUSDB_LOG_LEVEL=info
export ZEUSDB_LOG_FORMAT=human
export ZEUSDB_LOG_CONSOLE=true
python train_embeddings.py

# Example output you'll see:
# 2025-01-15 14:30:15 - INFO - Starting PQ training: 5000 vectors
# 2025-01-15 14:30:19 - INFO - PQ training completed: 4.2s (compression: 192x)
# 2025-01-15 14:30:20 - INFO - Vector addition completed: 10000 vectors in 2.1s
```

### Environment Variables Reference

| Variable | Options | Default | Description |
|----------|---------|---------|-------------|
| `ZEUSDB_LOG_LEVEL` | `trace`, `debug`, `info`, `warning`, `error`, `critical` | `warning` (dev), `error` (prod) | Controls log verbosity |
| `ZEUSDB_LOG_FORMAT` | `human`, `json` | `human` (dev), `json` (prod) | Output format |
| `ZEUSDB_LOG_TARGET` | `stdout`, `stderr`, `file` | `stderr` | Where logs go |
| `ZEUSDB_LOG_FILE` | `/path/to/file.log` | `zeusdb.log` | Log file path (if target=file) |
| `ZEUSDB_LOG_CONSOLE` | `true`, `false` | Auto-detected | Force console output |

<br />

## Advanced Usage (Programmatic Control)

For enterprise environments with existing logging infrastructure.

### Option 1: Disable Auto-Configuration
```python
import os
os.environ["ZEUSDB_DISABLE_AUTO_LOGGING"] = "1"

# Now configure your own logging before importing ZeusDB
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from zeusdb_vector_database import VectorDatabase  # Will respect your existing logging setup
```

### Option 2: Programmatic Initialization
```python
import os
os.environ["ZEUSDB_DISABLE_AUTO_LOGGING"] = "1"

import zeusdb

# Initialize with JSON to console 
success = zeusdb.init_logging(level="info")

# OR initialize with file logging
success = zeusdb.init_file_logging(
    log_dir="/var/log/myapp",
    level="debug", 
    file_prefix="zeusdb"
)

# Then use normally
vdb = zeusdb.VectorDatabase()
```

### Option 3: Custom Logger Integration
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
```
2025-01-15 10:30:15 - zeusdb.vector - INFO - Index created: dim=1536, vectors=0
2025-01-15 10:30:16 - zeusdb.vector - INFO - Added 1000 vectors in 45ms
2025-01-15 10:30:16 - zeusdb.vector - DEBUG - Search completed: 5 results in 2ms
```

#### Structured JSON (Production)
```json
{"timestamp":"2025-01-15T10:30:15.123Z","level":"INFO","operation":"index_creation","dim":1536,"space":"cosine","duration_ms":12}
{"timestamp":"2025-01-15T10:30:16.456Z","level":"INFO","operation":"vector_addition","total_inserted":1000,"duration_ms":45}
{"timestamp":"2025-01-15T10:30:16.789Z","level":"DEBUG","operation":"search_complete","results_count":5,"duration_ms":2}
```

### 🔍 Monitoring and Observability

#### Key Metrics to Monitor
- **`operation`**: Type of operation (index_creation, vector_addition, search, etc.)
- **`duration_ms`**: Performance timing for all operations
- **`total_inserted`**, **`total_errors`**: Success/failure rates
- **`compression_ratio`**: Memory efficiency with quantization
- **`training_progress`**: Quantization training status

#### Production Alerting Examples
```bash
# Monitor error rates
grep '"level":"ERROR"' /var/log/zeusdb/app.log | wc -l

# Track performance degradation  
grep '"operation":"search"' /var/log/zeusdb/app.log | jq '.duration_ms' | avg

# Watch quantization training
grep '"operation":"pq_training"' /var/log/zeusdb/app.log | tail -f
```

### 🛠️ Troubleshooting

#### Common Issues

**Logs not appearing?**
```bash
# Check if auto-logging is disabled
echo $ZEUSDB_DISABLE_AUTO_LOGGING

# Verify log level
ZEUSDB_LOG_LEVEL=debug python -c "import zeusdb; print('Logging active')"
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

#### Performance Impact
- **Minimal overhead**: Structured logging adds <1% performance impact
- **Async file writing**: File logging doesn't block operations
- **Smart buffering**: Logs are efficiently batched for performance

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
```

#### Production
```bash
export ENVIRONMENT=production
export ZEUSDB_LOG_LEVEL=error  
export ZEUSDB_LOG_FORMAT=json
export ZEUSDB_LOG_TARGET=file
export ZEUSDB_LOG_FILE=/var/log/zeusdb/production.log
```

Logging stays out of the way when you don’t need it, but delivers full power and flexibility when you do. Most users never need to touch the settings, while enterprise teams can fine-tune every aspect of observability.

<br/>
