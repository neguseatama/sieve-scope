# Changelog

## [1.3.0] - 2026-09-08
### Added
- Tokenize-based pure identifier extraction
- Weighted Bi-gram Dice coefficient (H7)
- Parallel evaluation via ProcessPoolExecutor
- Indirect chain detection warning
- Full 24-case regression test suite
- Edge-case & parallel determinism tests

### Fixed
- v0/v1.2 v0_mask compatibility (IGNORED_WORDS, build_pos_tuple)
- Deterministic output ordering via sorted keys
- Strict greater-than operator for H3 threshold
- Unicode H5 expectation to match current build_pos_tuple()

### Changed
- Default thresholds: Jaccard=0.50, Dice=0.60
- Test structure unified under tests/
- Documentation updated with synthetic validation and observation-space semantics