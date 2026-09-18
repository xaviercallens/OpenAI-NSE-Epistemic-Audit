---
license: cc-by-4.0
task_categories:
  - text-generation
  - text-classification
tags:
  - navier-stokes
  - fluid-dynamics
  - formal-verification
  - lean4
  - millennium-prize
  - openai
  - kinetic-theory
  - model-validity
  - computational-physics
  - mathematical-physics
language:
  - en
size_categories:
  - n<1K
pretty_name: "The OpenAI Navier–Stokes and Euler Blow-Up Proofs: A Physical Reading (data and code)"
---

# The OpenAI Navier–Stokes and Euler Blow-Up Proofs: A Physical Reading — data and code

## Overview

This dataset accompanies the paper:
**"The OpenAI Navier–Stokes and Euler Blow-Up Proofs: A Physical Reading, Not a Physical Refutation"**, v5.5.0 (2026-09-17)
*The MechanicaFluidorum Program | Socrate AI Lab*
**Zenodo:** concept DOI [10.5281/zenodo.22696717](https://doi.org/10.5281/zenodo.22696717) (always the latest version); v5.7.0 is [10.5281/zenodo.22836538](https://doi.org/10.5281/zenodo.22836538)
**GitHub:** [xaviercallens/OpenAI-NSE-Epistemic-Audit](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit)

> **Earlier versions.** Versions 2.0.0 of this record (`10.5281/zenodo.22725347`, `22727801`) and the
> earlier paper title "On the Physical Vacuity of Manufactured Singularities" carry withdrawn claims
> (plasma temperatures, the raw condition number as fragility, "censorship", T-duality); v5.5.0 also withdraws the
> reading of a Leray-α filter of width $\ell_*$ as a representation of the fluid at its continuum limit. See
> `CHANGELOG.md` and Appendix A of the paper. `dataset/OpenAI_NSE_EpistemicAudit.pdf` is that
> superseded draft, kept for the record only.

## What the data support

OpenAI's Lean proof is correct. Read physically, the construction leaves the incompressible continuum model at $\ell_* = \nu/c_s$ (0.67 nm in water, 45 nm in air) a few picoseconds before the singularity. Beneath that scale, kinetic theory ends the hydrodynamic description ($k\lambda=\sqrt{\pi/2}$) but — in the nonlinear test included here — does not arrest a driven collapse. Which physics a blow-up meets first depends on its route ($\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$): on OpenAI's route ($\mathrm{Re}\approx1$) neither compressibility nor heat stops a driven core before $\ell_*$; on an inertial route ($\mathrm{Re}\gtrsim16$) a heat-conducting gas does not follow a driven swirl past local Mach 0.70 — a lock on Mach number, not on velocity or size. Nothing here bears on Clay Statement A.

## Key results

| Topic | Result | Data |
|---|---|---|
| Lean check of OpenAI's proof | 0 `sorry`, 0 custom axioms, $C^\infty$ force | `dataset/verification_results.json` |
| Local divergence | $e_{\text{local}} \sim \tau^{-1.010}$, $\Omega \sim \tau^{-0.515}$, $\|u\|_{L^3} \sim \tau^{-0.0067}$; global energy $\sim\tau^{+0.485}\to 0$ | `scripts/directive2_thermodynamic_paradox.py` |
| Moment matrix | $A = DBD$, $\kappa(B) \approx 4.11\times10^5$ for all $X_R$ (raw $10^{28}$ is a units artifact) | paper §3 |
| Gevrey cutoffs | index $s = 1.5$: $C^\infty$, not real-analytic | paper §2.2 |
| Mach limit (water, $\ell_0 = 1$ cm) | Ma 0.3 at $\approx 6.7$ ps and Ma 1 at $\approx 0.6$ ps before blow-up | `scripts/directive5_mach_divergence.py` |
| Admissibility in Lean (link 1) | every object with OpenAI's `CandidateProperties` exceeds every gradient bound near $t=1$ — **unconditional** | `lean4/OpenAIAdmissibility.lean` |
| 3D solver benchmark | Taylor–Green Re 1600 dissipation peak at $t = 9.14$ (published 9.0) | `data/validation_3d.json` |
| Cutoff law on generic data | premise (Re ≈ 1 core) never produced; arrest scale follows cascade scaling | `data/cutoff_law_shell.json`, `data/cutoff_law_analysis.json` |
| Forced core, 32³ | barrier engagement collapses onto $\alpha'/(\nu\tau)$ (per-run $C = 0.188 \pm 0.010$) | `data/forced_core_32_v3.json` |
| Forced core, 96³ | 0/6 runs reach $B/F = 1$; cores stall at $\ell \approx 1.2$–$1.5\sqrt{\alpha'}$, exponents $\ell$ +0.42, $u$ −0.43…−0.47 (law +0.5, −0.5); not yet converged | `data/forced_core_96_v3.json` |
| Gates vs barrier (axial core) | Leray-α/LANS-α lag 0.2–0.4%, barrier 5–45% — a ranking of models | `data/forced_core_axial_32.json`, `data/gate_*.json` |
| Linear kinetic spectrum | damping $\nu k^2[1-(k\lambda)^2+\dots]$, capped at $1/\tau$, mode ends at $k\lambda = \sqrt{\pi/2}$ | `data/lock_k_kinetic_spectrum.json` |
| Nonlinear kinetic test (link 4) | 2D-2V discrete-velocity BGK, five gates passed; **no arrest** at $k\lambda\approx\sqrt{\pi/2}$ — the apparent stopping point follows the grid; NSE control tracks to $4\times10^{-4}$ | `data/kinetic_lock_gates.json`, `data/kinetic_lock_collapse.json`, `figures/kinetic_lock.png` |
| Regime map (v5.5.0) | $\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$: diffusive route (OpenAI) meets everything at $\ell_*$; inertial route (Tao 2016) meets compressibility first at $\mathrm{Re}\,\ell_*$; bounded-velocity route (forced Euler) meets viscosity first at $\ell_*/\mathrm{Ma}$ | `lean4/BlowupRegimeMap.lean` |
| Compressible / thermal forced core (v5.5.0) | on OpenAI's route the driven core lags 14–25% but is not stopped before $\ell_*$ (a quasi-steady arrest prediction failed); for $\mathrm{Re}\gtrsim16$ air locks at local Mach **0.70** (target Mach 4 and 8); 1D ideal gas, open-loop force | `data/compressible_core_study.json`, `data/compressible_core_re_sweep.json`, `figures/compressible_core.png` |
| Kinetic cross-check with a physical-gas collision law | $\tau\propto1/\rho$ vs constant $\tau$: same direction, small where the solver is valid (peak Mach 0.72 vs 0.77 at Re 3) | `data/kinetic_lock_gas_law.json` |
| Leray-α anchor claim (v5.5.0) | **withdrawn**: the filter width does not appear in the linearized dynamics of any α-model | `lean4/LerayAlphaLinearization.lean` |

## Contents

- `paper/`: the paper (PDF and LaTeX source), v5.5.0 (29 pages).
- `lean4/`: verified Lean 4 files (`OpenAIAdmissibility`, `CoreScaling`, `KineticSpectralCap`, `LatticeBGKEntropy`, `NonlinearBGKEntropy`, `LerayAlphaFilter`, `AlphaEnergyIdentity`, `BlowupRegimeMap`, `LerayAlphaLinearization`; 74 `#print axioms` checks, standard axioms only). `superseded/` holds withdrawn drafts.
- `code/`: the 3D pseudo-spectral solver, forced-core test beds, the 1D compressible Navier–Stokes–Fourier core, kinetic-spectrum computation, analysis and benchmark scripts.
- `data/` and `figures/`: result JSON files and plots, including `forced_core_96_v3.json`, `kinetic_lock_gates.json`, `kinetic_lock_collapse.json`, `kinetic_lock.png` (v5.4) and `compressible_core_study.json`, `compressible_core_re_sweep.json`, `kinetic_lock_gas_law.json`, `compressible_core.png` (v5.5.0).
- `research/`: the lock programme and results notes (`DUAL_SCALE_LOCK_PROGRAMME.md` §8–9 and `THERMO_COMPRESSIBLE_LOCK_STUDY.md` have the current status).
- `scripts/`: the original directive scripts (SymPy, NumPy, SciPy).
- The Rust kinetic solver (`kinetic_lock_rs/`) lives in the GitHub repository.

Exact file lists depend on the upload (Zenodo bundle or Hugging Face); every verdict in the JSON files is computed from the runs, not hardcoded.

## Citation

```bibtex
@misc{callens2026nse,
  author    = {Callens, Xavier and {MechanicaFluidorum Program}},
  title     = {The OpenAI Navier-Stokes and Euler Blow-Up Proofs:
               A Physical Reading, Not a Physical Refutation},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22696717},
  url       = {https://doi.org/10.5281/zenodo.22696717},
  note      = {Concept DOI; resolves to the latest version. v5.7.0: 10.5281/zenodo.22836538}
}
```
