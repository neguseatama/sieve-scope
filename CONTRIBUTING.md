# Contributing to Sieve Scope

Thank you for considering contributing to Sieve Scope!

## Design Principles

- **Determinism**: All outputs must be reproducible. Avoid non-deterministic functions.
- **Zero Dependencies**: Use only the Python standard library.
- **Explainability**: Every judgment must provide a clear reason and mask.

## How to Contribute

1. Fork the repository.
2. Create a feature branch.
3. Make changes with clear commit messages.
4. Ensure all tests pass: `python -m unittest discover -s tests -p "test_v1_3_full_suite.py" -v`
5. Submit a pull request.

## Reporting Issues

Please include:
- Python version
- Minimal code to reproduce
- Expected vs actual behavior