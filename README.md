# Sieve Scope v1.3

**English** | [日本語](README.ja.md)

> **"See through the formatting, and look into the pure logic of the algorithm."**
> A fully local, zero-dependency, deterministic (100% reproducible) code plagiarism and structural similarity detection engine.
> Extends [Sieve-Core](https://github.com/neguseatama/sieve-core)'s deterministic similarity engine and [Sieve-Referee](https://github.com/neguseatama/sieve-referee)'s multi-hypothesis LUT judgment philosophy to the **source code domain**.

[![CI](https://github.com/neguseatama/sieve-scope/actions/workflows/test.yml/badge.svg)](https://github.com/neguseatama/sieve-scope/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)

---

## 💡 Concept & Philosophy

The starting point of this project is **Sieve-Core**, a core engine that applies the "sieve of set theory" design philosophy of **Sieve-AI**—inspired by the Sieve of Eratosthenes—to the more general domain of text and data processing.

Next, **Sieve Referee**, which adds a "sieve of combinatorics" to Sieve-Core, is a zero-dependency Python library that extracts reliable information from noise based on corroboration from multiple independent sources.

Then, **Sieve Scope** further adds a two-axis evaluation and redesigns the approach, making it an explainable code plagiarism detection engine that observes the **surface format** (variable names, comments, whitespace) and the **essential logic** (algorithm structure) separately.

Traditional string comparison and simple similarity measures struggle to distinguish between:
- Plagiarism by merely renaming variables (**variable laundering**)
- Coincidental matches due to shared templates (**boilerplate**)

`Sieve Scope` observes two axes independently:
- **AST (Abstract Syntax Tree)** — extracting the "logic skeleton" with identifiers removed
- **tokenize** — extracting "identifier vocabulary and order"

By inheriting the hypothesis mask (H1–H7) and LUT from Sieve-Referee, it fully explains why a judgment was made.

> The name "Sieve Scope" comes from the design philosophy of seeing through the surface of code (format) and comparing only the pure logic, like a microscope.

---

## 🔥 Key Features

- **7-bit Observation Space (H1–H7)**  
  Independently evaluates AST skeleton, identifier vocabulary, positional/order (g_POS), constants (g_CONST), and vocabulary context (g_FREQ).
- **v0_mask compatibility**  
  The legacy 4-bit v0_mask is preserved and regression-tested.
- **Strict Cluster Safety Invariant**  
  H4 is promoted to 1 only when the cluster size is at least 3 **and** there is direct similarity evidence (H2∨H3). Indirect "telephone game" chains are never mixed into direct judgments.
- **Short-Circuit Optimization**  
  Pairs with no structural or vocabulary similarity (H2=0 ∧ H3=0) are immediately returned as `1000-000`, skipping expensive hash computations.
- **Zero Dependencies & Deterministic**  
  Implemented using only the Python standard library. No external packages, no API costs, no probabilistic elements.

---

## 📐 7-bit Observation Space

The evaluation function `f_v1.3(C1, C2)` projects a code pair into seven boolean hypotheses `(H1, H2, H3, H4, H5, H6, H7)`.

| Hypothesis | Name | What it measures | Criterion / Threshold |
| :--- | :--- | :--- | :--- |
| **H1** | Parseability | Can both be parsed as Python syntax? | Success/failure of AST construction |
| **H2** | AST Skeleton | Do the AST node type sequences match exactly? | Exact match of skeleton strings |
| **H3** | Identifier Similarity | Jaccard + sequence similarity of identifiers | Score `> 0.50` |
| **H4** | Cluster Safety | Direct similarity + membership in a valid cluster (size ≥3) | Invariant condition satisfied |
| **H5** | g_POS | SHA-256 hash of recursive AST field representation | Exact hash match |
| **H6** | g_CONST | Constants / literals set match | Sorted constant list exact match |
| **H7** | g_FREQ | Weighted identifier bi-gram Dice coefficient | Score `>= 0.60` |

Mask notation is `v0_mask (4-bit) - extension (3-bit)`.
Example: `1100-011` → H1=1, H2=1, H3=0, H4=0 / H5=0, H6=1, H7=1

---

## 📊 Representative LUT Patterns

| v0_mask | Extended Example | Judgment Label | Description |
|:---:|:---:|:---|:---|
| `1110` | `1110-111` | `EXACT_CLONE` | Observation-space exact match |
| `1100` | `1100-110` | `VARIABLE_LAUNDERING` | Logic matches but surface differs |
| `1010` | `1010-011` | `COINCIDENTAL_FRAMEWORK_MATCH` | Logic differs but surface matches |
| `1000` | `1000-000` | `INDEPENDENT_LOGIC` | No direct similarity (short-circuit) |
| `1110` | `1110-101` | `CONSTANT_MODIFIED_CLONE` | Only constants differ |
| `1110` | `1110-011` | `PERMUTATED_CLONE` | Non-commutative order reversed |

---

## 💻 Quick Start

```python
from sieve_scope import SieveScopeEngineV1_3, SieveClusterAnalyzerV1_3

engine = SieveScopeEngineV1_3(jaccard_threshold=0.50, freq_dice_threshold=0.60)

code_a = "def calc_sum(a, b):\n    return a + b"
code_b = "def calc_sum(x, y):\n    return x + y"

result = engine.evaluate_pair(code_a, code_b)

print(result["v0_mask"])   # e.g., 1100
print(result["mask"])      # e.g., 1100-110

---

### Configuration / Thresholds

- `jaccard_threshold` (default: `0.50`): Threshold for H3 Multiset Jaccard + sequence similarity.
- `freq_dice_threshold` (default: `0.60`): Threshold for H7 Weighted identifier bi-gram Dice coefficient.

> **Note on Calibration & Defaults (v1.3)**:
> Exhaustive grid search experiments on synthetic benchmark datasets demonstrate optimal class separation ($F1 = 1.0000$) across a wide threshold range of `0.35` to `0.75`. However, the default threshold parameters are strictly maintained at **`0.50` / `0.60`** in order to preserve backwards compatibility with v0, maintain regression test stability, and prevent potential false positives caused by shared domain vocabulary in production codebases.

---

## 🔬 Testing & Verification
Cross-Python Validation Summary
24 regression cases (test_v1_3_full_suite.py): PASSED

5 compatibility tests (test_v1_3_regression.py): PASSED

6 edge-case & parallel determinism tests (test_v1_3_edge_cases.py): PASSED

81 synthetic threshold configurations (threshold_tuning.py): PASSED

All test suites and synthetic experiments passed completely without errors across Python 3.9, 3.10, 3.11, and 3.12.

Threshold Calibration & Synthetic Validation
The threshold parameters (H3 Multiset Jaccard: 0.50, H7 Weighted Bi-gram Dice: 0.60) were designed and calibrated using a synthetic validation pair set (Positive 6 pairs / Negative 3 pairs).
The engine's 1110-111 indicates an exact match in the current 7-dimensional observation space (Observation Clones), and does not guarantee complete semantic equivalence (Semantic Clones).

---

## 📚 Documentation

- 🏛️ Architecture Specification

- 🔌 API & Integration Guide

- 🚀 Deployment Guide

- 🔐 CI/CD & Security Guide

## 📄 License
MIT License. See LICENSE for details.

## 👤 Author
Kai IWASAKI