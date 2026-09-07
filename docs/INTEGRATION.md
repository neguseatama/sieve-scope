# 🔌 API & Integration Guide

## 1. Python Library Integration

```python
from sieve_scope import SieveScopeEngineV1_3, SieveClusterAnalyzerV1_3

engine = SieveScopeEngineV1_3()
analyzer = SieveClusterAnalyzerV1_3(engine, min_cluster_size=3)

corpus = {
    "A.py": "def calc(a, b): return a + b",
    "B.py": "def calc(x, y): return x + y",
    "C.py": "def calc(p, q): return p + q",
}

analysis = analyzer.analyze_corpus(corpus, max_workers=4)
print(analysis["valid_clusters"])

## 2. FastAPI Example

from fastapi import FastAPI
from pydantic import BaseModel
from sieve_scope import SieveScopeEngineV1_3

app = FastAPI(title="Sieve Scope API", version="1.3.0")
engine = SieveScopeEngineV1_3()

class EvaluateRequest(BaseModel):
    code1: str
    code2: str

@app.post("/api/v1/evaluate")
def evaluate(payload: EvaluateRequest):
    return engine.evaluate_pair(payload.code1, payload.code2)

Note: FastAPI/Uvicorn are optional integration dependencies and are not
part of the core zero-dependency design.
