---
name: academic-publication
description: Academic manuscript preparation, journal targeting, arXiv/alphaXiv preprint submission, and Zenodo certified archiving protocols for the MechanicaFluidorum Program at Socrate AI Lab.
---

# Academic Publication Skill

## Overview
This skill provides complete guidelines for drafting, polishing, and shepherding mathematical physics papers through peer review and open-science dissemination under Socrate AI Lab (French Association Loi 1901).

## Target Venues & Strategy
1. **Top Tier Mathematical Physics Journals**:
   - *Communications in Mathematical Physics (CMP)*
   - *Archive for Rational Mechanics and Analysis (ARMA)*
   - *Journal of Fluid Mechanics (JFM)*
   - *Communications on Pure and Applied Mathematics (CPAM)*
2. **Preprint Servers**:
   - **arXiv**: Primary categories `math.AP` (Analysis of PDEs) and `physics.flu-dyn` (Fluid Dynamics).
   - **alphaXiv**: Direct engagement and cross-referencing on discussion threads around OpenAI's `2609.navier-stokes`.
3. **Open-Science Archives**:
   - **Zenodo**: Permanent DOI deposit (`10.5281/zenodo.22696718`) with automated SHA-256 integrity verification (`zenodo_retriever.py`, `zenodo_push.py`).

## Manuscript Standards & Checklist
- [x] **Clear Problem Statement**: Distinguish between Millennium Prize Statements A/B (unforced) and Statements C/D (forced).
- [x] **Epistemic Tiering**: Explicitly demarcate machine-verified finite results (Tier A), numerical simulations (Tier B), and open conjectures (Tier C).
- [x] **No Hidden Axioms**: Lean 4 formalizations must use `sorry` or explicit hypothesis parameters (`HypothesisU`) rather than introducing unproven axioms into the Lean kernel.
- [x] **Literature Grounding**: Properly cite Fefferman (2000), Ladyzhenskaya (1967), Prodi (1959), Serrin (1962), Batchelor (1967), Landau & Lifshitz (1987), Roache (2002), and Tao (2016).
- [x] **Institutional Attribution**: Accurately cite Socrate AI Lab as a French non-profit research association under Loi 1901 for Neuro-Symbolic Scientific AI.

## Rebuttal & Reviewer Response Protocol
- When reviewers question the universality of the bound, clarify that the paper builds a *conditional reduction*: reducing global regularity to the verifiable asymptotic behavior of the 3D Leray projector on $\mathbb{Z}^3$.
- Emphasize that Lean 4 compilation guarantees the logical chain from `HypothesisU` to the Prodi-Serrin regularity criterion is completely free of calculus or algebraic errors.
