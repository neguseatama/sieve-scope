# 🔐 CI/CD & Security Guide

Sieve Scope v1.3 has zero external runtime dependencies.

## CI Pipeline

`.github/workflows/test.yml` runs all test suites on Python 3.9–3.12.

## Security Considerations

- No third-party libraries
- Deterministic outputs (SHA-256, sorted results)
- Input validation catches SyntaxError and tokenization errors

## Reporting a Vulnerability

Follow `SECURITY.md`. Do not open a public issue. Email neguse.cat@gmail.com.