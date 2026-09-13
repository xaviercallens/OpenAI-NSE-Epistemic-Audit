# Contributing to OpenAI-NSE-Verification

Thank you for your interest in contributing to this Physical Verification of the OpenAI
Navier-Stokes / Euler blow-up formalization.

## How to Contribute

1. **Fork** the repository and create a feature branch from `main`.
2. Make your changes, following the guidelines below.
3. Open a **Pull Request** against `main`.
4. Your PR will be reviewed by the maintainer (@xaviercallens) before merging.

> ⚠️ Direct pushes to `main` are **not permitted**. All changes go through Pull Requests.

## Scientific Standards

- All mathematical claims must be verifiable or cited.
- LaTeX must compile cleanly with `pdflatex` (zero errors).
- Lean 4 additions must not introduce new `sorry` without explicit documentation.
- Simulation scripts must be reproducible with fixed random seeds.

## Scope

This repository audits the *physical realizability* of the OpenAI Lean 4 proofs.
It does **not** dispute the mathematical correctness of those proofs.

## Contact

For major contributions or collaboration inquiries: open a GitHub Issue.
