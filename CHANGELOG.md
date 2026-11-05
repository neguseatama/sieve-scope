# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-11-06

### Fixed
- **Empty/statement-less files no longer form false clones**: files whose
  `ast.parse` body is empty (empty files, comment-only files) are excluded
  from comparison and listed under the new `skipped` key with reason
  `not_applicable` — two empty `__init__.py` files no longer produce the
  `1110-110` false clone (and three no longer promote it to `1111-110`).
  Pair results for non-empty files are unchanged whether or not empty files
  are present in the corpus.
- **Parse failures are distinguishable from "no similarity"**: files that
  fail to parse are listed under `skipped` with reason `parse_failed`
  (their existing pair results are preserved), and an unparseable pair now
  carries `scores: null` instead of omitting the key — `null` means "no
  observation" (the pair could not be parsed).
- **Deeply nested code can no longer stop the whole corpus**: a file whose
  skeleton/position-tuple build hits a `RecursionError` is contained per
  file, listed under `skipped` (`parse_failed`), and the remaining files
  are evaluated normally. `sys.setrecursionlimit` is never called.
- **Parallel evaluation falls back to sequential**: when the
  `ProcessPoolExecutor` pool cannot be created or breaks (e.g. frozen
  apps), the analysis reruns sequentially and returns the byte-identical,
  deterministic result. Public API and arguments are unchanged.

### Changed
- **Removed the unused `sieve-core-engine` dependency** (measured: imported
  nowhere in code or tests; the engine is stdlib-only, so the dependency
  declaration now matches the "zero dependencies" design).
- **Version bumped to 1.3.1** (visibility and robustness fixes; no change
  to results for already-observable non-empty file pairs).

## [1.3.0] - 2026-09-08

### Fixed
- **AST Identifier Duplicate Extraction**: Resolved double-extraction logic during AST node traversal (e.g., redundant registration of `'res'`), eliminating duplicate variable counts.
- **POS Structural Hash ($H_5$) & Frequency Dice ($H_7$) Mask Logic**: Fixed mask comparison logic in regression test cases to ensure consistent evaluation across components.
- **Deep Nesting Evaluation**: Addressed missing recursive evaluations in deeply nested AST structures (150+ levels), resolving $H_1$ detection failures.

### Changed
- **Default Threshold Retention**: Retained `jaccard_threshold = 0.50` and `freq_dice_threshold = 0.60` as production defaults to preserve v0 compatibility and prevent false positives in real-world codebases.
- **Calibration Results Documented**: Added grid search calibration notes confirming optimal separation performance ($F1 = 1.0000$) across a wide threshold range of 0.35 to 0.75 on synthetic benchmark datasets.