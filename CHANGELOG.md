# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-09-08

### Fixed
- **AST Identifier Duplicate Extraction**: Resolved double-extraction logic during AST node traversal (e.g., redundant registration of `'res'`), eliminating duplicate variable counts.
- **POS Structural Hash ($H_5$) & Frequency Dice ($H_7$) Mask Logic**: Fixed mask comparison logic in regression test cases to ensure consistent evaluation across components.
- **Deep Nesting Evaluation**: Addressed missing recursive evaluations in deeply nested AST structures (150+ levels), resolving $H_1$ detection failures.

### Changed
- **Default Threshold Retention**: Retained `jaccard_threshold = 0.50` and `freq_dice_threshold = 0.60` as production defaults to preserve v0 compatibility and prevent false positives in real-world codebases.
- **Calibration Results Documented**: Added grid search calibration notes confirming optimal separation performance ($F1 = 1.0000$) across a wide threshold range of 0.35 to 0.75 on synthetic benchmark datasets.