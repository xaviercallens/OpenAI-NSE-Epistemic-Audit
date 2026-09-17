# Contributing to OpenAI-NSE-Epistemic-Audit

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
- Lean 4 files added to the verified set must compile with no `sorry` and only the standard axioms
  (`propext`, `Classical.choice`, `Quot.sound`); drafts belong in `03_Lean4_Topological_Censorship/src/drafts/`.
- Simulation scripts must be reproducible with fixed random seeds, and any quoted number should be
  covered by `scripts/compare_benchmarks.py` (see `BENCHMARKS.md`). Run `python -m pytest -q` before a PR.
- Corrections are recorded, not silently rewritten: add a CHANGELOG entry saying what was wrong.

## Scope

This repository is a *physical reading* of the OpenAI Lean 4 proofs: where the constructed flows leave
the validity range of the model they are theorems about. It does **not** dispute the mathematical
correctness of those proofs, and nothing in it bears on Clay Statement A.

## Contact

For major contributions or collaboration inquiries: open a GitHub Issue.
