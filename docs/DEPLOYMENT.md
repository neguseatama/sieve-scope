# 🚀 Deployment Guide

Sieve Scope core has no external runtime dependencies.

## Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY sieve_scope.py ./
COPY tests/ ./tests/
RUN pip install --no-cache-dir .
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_v1_3_full_suite.py"]
```

## Resource Sizing

The core library requires no external runtime package. Actual memory and
CPU requirements depend on corpus size because pair evaluation is O(N²);
capacity must be benchmarked against the target corpus.