# Sieve Scope v1.3 — Review Fixes

## 1. Full regression suite

`tests/test_v1_3_full_suite.py` is corrected to match the actual v1.3
observation semantics rather than forcing the implementation to satisfy
incorrect expectations.

Corrected cases:

| Case | Old | Corrected |
|---|---|---|
| Basic 1-3 | `1100-110` | `1100-010` |
| Boundary 2-2 | mixed comment/docstring | comment-only pair; `1110-111` |
| Boundary 2-3 | `1110-011` | `1110-111` |
| Boundary 2-7 | `1000-000` | `1010-011` |
| 4Q 2 | `1100-110` | `1100-010` |
| 4Q 3 | `1010-011` | `1010-010` |
| 4Q 6 | `1010-011` | `1010-010` |
| Q3-1 | `1010-011` | `1010-010` |
| Q3-2 | `1010-011` | `1010-010` |
| Q3-3 | `1010-011` | `1010-101` |

Important semantic corrections:

- H2=0 and H3=1 is a similarity case, not a short-circuit case.
- H5 follows the current `build_pos_tuple()` implementation. In
  particular, binding names represented by `ast.arg.arg` currently affect
  the positional hash.
- H7 is `>= 0.60`; extra identifiers can therefore lower H7 below the
  threshold even when H3 remains 1.
- A docstring is an AST constant/expression and is not equivalent to a
  comment.

## 2. ARCHITECTURE.md

Change the H2 description from:

    AST node-type sequence after excluding Load, Store, Del

to:

    AST node-type sequence emitted by ASTSkeletonVisitor.generic_visit().
    The current implementation includes Load, Store, Del and operator
    nodes such as Add, Sub, Mult, etc.

Change H5 description from:

    Pure AST structure hash excluding values and attributes

to:

    SHA-256 hash of the recursive AST field representation produced by
    build_pos_tuple(). The current representation excludes fields named
    value, id, and attr, but retains other scalar AST fields. It is
    therefore not a complete identifier-erased semantic representation.

Change the non-commutative example:

    a - b vs b - a is distinguished by H5

to:

    a - b vs b - a can be distinguished by H7 (identifier order/context);
    H5 alone does not distinguish them because Name.id is excluded.

Clarify H4:

    evaluate_pair() always returns H4=0 because cluster context is
    unavailable at pair-evaluation time. SieveClusterAnalyzerV1_3 promotes
    H4 only after corpus-level cluster validation.

## 3. README.md / README.ja.md

Avoid the absolute claim "100% backward compatibility".

Use:

    v0_mask compatibility
    The legacy 4-bit v0_mask is preserved and regression-tested.

Avoid calling H5 simply "pure AST structure" or implying that it is
identifier-free.

Also qualify benchmark numbers:

    The published benchmark figures are measurements of the supplied
    synthetic 100-file pair benchmark on a particular execution
    environment. They are not universal performance guarantees.

Do not state that the benchmark measures ProcessPoolExecutor/corpus
analysis; the current benchmark measures evaluate_pair() only.

The statement "F1=1.0" should similarly be qualified as a result on the
synthetic threshold-tuning dataset, not as production accuracy.

## 4. benchmark_v1_3.py

Improve measurement quality:

- use `time.perf_counter()` rather than `time.time()`;
- rename `generate_random_code()` to `generate_synthetic_code()` because
  the generator is deterministic;
- report the benchmark as a pair-engine benchmark;
- add an optional warm-up before timing;
- do not claim it benchmarks corpus parallelism.

A corpus-level benchmark should be added separately if ProcessPoolExecutor
performance is to be reported.

## 5. .github/workflows/test.yml

Remove:

    python -m pip install --upgrade pip

The project has no runtime dependencies, so the CI job does not need pip
at all. Removing it makes the CI path more faithfully match the
zero-dependency design and removes an unnecessary network operation.

Keep the Python 3.9–3.12 matrix and the three existing test commands.

## 6. CHANGELOG.md

Replace the placeholder release date:

    2026-09-XX

with the actual release date when publishing the tag. Do not publish the
placeholder.

## 7. INTEGRATION.md / DEPLOYMENT.md

Separate "core library has zero runtime dependencies" from optional
integration examples that install FastAPI/Uvicorn.

Replace unsupported deployment language such as "512MB/1vCPU is more than
sufficient" with a bounded statement:

    The core library requires no external runtime package. Actual memory
    and CPU requirements depend on corpus size because pair evaluation is
    O(N²); capacity must be benchmarked against the target corpus.

## 8. H4 safety invariant

Keep the invariant exactly as implemented:

    H4 = 1 only if:
      - both items belong to the same valid cluster,
      - cluster size >= min_cluster_size (default 3),
      - the pair itself has direct H2 or H3 evidence.

Indirect paths must never manufacture direct H4 evidence.

## 9. No algorithmic expansion

These fixes deliberately do NOT add semantic execution analysis, ML models,
embeddings, or probabilistic similarity. The Sieve Scope v1.3 observation
model remains deterministic and zero-dependency.
