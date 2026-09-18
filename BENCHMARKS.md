# Reproducibility benchmark

Every quantitative claim this project makes about its own simulations and proofs is paired below with a
regenerated value. `scripts/run_benchmarks.sh` re-runs the test suites, the Lean files, the kinetic
solver's validation gates and the fast simulations from scratch, and `scripts/compare_benchmarks.py`
checks each regenerated number against the committed result it came from. Long runs (the 96³ sweep,
about 6 h; the kinetic collapse runs, about 5 h) are not re-simulated; their headline numbers are
re-derived from the committed data, and that distinction is marked in the tables.

## Result for v5.8.0

**67 / 67 checks pass** (`--full` tier, 2026-09-19). Everything in the v5.7.0 table below reproduced again. New in this version,
per run (two runs): the barostat held the far-field pressure and the wall-swirl plateau against the registered cap.

| check | quoted | reproduced |
|---|---|---|
| water-like, barostat, run 1 / run 2: far pressure above target; box area change | ≤ +0.15; +5…+10% | +0.12, +6.9% / +0.10, +7.9% |
| water-like, barostat, run 1 / run 2: wall-swirl plateau (mean of the six highest windows) vs the registered cap 0.824 | within 5% (paper 0.842 / 0.841, +2%) | 0.842 (+2.2%) / 0.841 (+2.1%) |

The plateau statistic selects the highest windows and is biased upward; the ±5% tolerance is wider than the per-window standard error
(0.02–0.03) on purpose. About 2 further CPU-hours of MD are not re-run.

## Result for v5.7.0

**63 / 63 checks pass** (`--full` tier, 2026-09-18). The first full run gave 62 / 63: the Re = 32 check quoted the
v5.6.1 single-run range 0.62–0.71, and the two-run ensemble reads 0.64–0.73. The paper's sentence was
corrected to the ensemble value and the check to two runs; the comparison was then re-run against the same run
directory (simulations not repeated). New checks:

| check | quoted | reproduced |
|---|---|---|
| MD, Re = 32 (2 runs): dense-gas local Mach, target 0.75–3 | 0.64–0.73 | 0.64–0.73 |
| MD, Re = 4 (3 runs), target Mach 0.30 / 0.50 / 0.72: fitted local Mach | 0.29 / 0.40 / 0.50 (continuum 0.27 / 0.39 / 0.48) | 0.29 / 0.40 / 0.50 |
| MD 3D gas (Re = 16): local Mach, bins ρ ≥ 0.2 ρ∞, target passing 3 | ≤ 0.87 | 0.87, target 3.13 |
| MD water-like liquid: wall swirl vs the registered cap 0.82 | exceeded (prediction failed) | 0.94 |
| MD water-like, measured far-field pressure (post hoc, one run) | p_far 0.32 → 0.77; wall swirl ≤ 0.75 of the cap | 0.32 → 0.77; 0.75 |

Two of these check that a registered prediction *failed* and that a post-hoc reading holds; neither is a pass of
the original prediction. About 12 further CPU-hours of MD are not re-run.

## Result for v5.6.1

**59 / 59 checks pass** (`--full` tier, 2026-09-18). Everything in the v5.5.0 and v5.4.1 tables below reproduced
again; `pytest` runs 140 tests. New in this version:

| check | quoted | reproduced |
|---|---|---|
| `QuantumVortexLink.lean` | 11 declarations, standard axioms | 11, 0 errors, no `sorryAx` |
| Lean total | 85 declarations in ten files | 85 |
| MD, Re = 16 (3 runs), target Mach 1: fitted local Mach (real-gas c) | 0.538 ± 0.011 (continuum 0.54) | 0.538 |
| MD, Re = 16, target Mach 1: core density / temperature | 0.33 / 1.15 | 0.33 / 1.15 |
| MD, Re = 32: dense-gas local Mach for target Mach 0.75–3 | 0.62–0.71 | 0.62–0.71 |
| MD liquid: swirl at the cavity wall for target u ≥ 2 | 1.77–1.87, below 2.07 | 1.77–1.87 |

The MD numbers are re-derived from the committed analysis output and raw run files (about 7 CPU-hours of
simulation are not re-run). Writing these checks also caught a variable clash in the comparison script itself,
fixed before the run was recorded.

## Result for v5.5.0

**54 / 54 checks pass.** Run 2026-09-17, `--full` tier (wall time 31 min on a machine also running two
kinetic production jobs; about 9 min unloaded). Everything in the v5.4.1 tables below reproduced again,
bit-identically, and `pytest` now runs 124 tests. New in this version (10 checks; the "Lean total" row is a
sum, not a separate check):

| check | committed / quoted | reproduced |
|---|---|---|
| `BlowupRegimeMap.lean` | 13 declarations, standard axioms | 13, 0 errors, no `sorryAx` |
| `LerayAlphaLinearization.lean` | 4 declarations, standard axioms | 4, 0 errors, no `sorryAx` |
| Lean total | 74 declarations in nine files | 74 |
| compressible core, low-Mach control: max lag (re-simulated) | 6.90e-6 | 6.90e-6 |
| Re = 1, real-gas μ, isothermal: max lag (re-simulated) | 0.1397 | 0.1397 |
| Re = 1, air, full thermodynamics: max lag (re-simulated) | 0.2464 | 0.2464 |
| grid convergence n = 400 vs 800, air (re-simulated) | < 1% | 0.5% |
| air Mach lock at target Ma = 4, Re = 16 / 64 (re-derived from `compressible_core_re_sweep.json`) | 0.70 | 0.700 / 0.700 |
| air Mach lock at target Ma = 8 | 0.70 | 0.701 |
| Mach lock, grid convergence n = 500 vs 1000 | < 0.5% | 0.002% |
| ν-constant isothermal control does not lock | 1.91 | 1.91 |

The Reynolds sweep itself (26 runs, about 40 min) is re-derived from its committed JSON rather than
re-simulated; the physics ladder (`compressible_core_study.py`, 14 runs) is re-simulated in the `--full` tier.

## Result for v5.4.1

**44 / 44 checks pass.** Run 2026-09-17 on the release commit, `--full` tier, 6 min 39 s wall time.
Every re-simulated quantity came back **bit-identical** to the committed value: the solvers are
deterministic on a fixed machine and library stack, so any difference in a future run is a real
change, not noise. Raw output: `benchmark_runs/v5.4.1/` (not committed; regenerate with the command
below).

Environment: Intel i7-4930MX (4 cores / 8 threads), Linux 6.8, Python with NumPy 1.26.4 and SciPy
1.17.1, rustc 1.97.1, Lean 4.34.0-rc2 with Mathlib v4.34.0-rc2 inside OpenAI's `NavierStokesAndEuler`
project. Bit-identity is expected on the same stack; across different BLAS/FFT builds or CPUs, expect
agreement to roughly 1e-12 relative on the simulation numbers. The comparison tolerances allow for that.

### Test suites

| check | reproduced |
|---|---|
| `pytest` (all Python tests) | 116 passed, 0 failed |
| `cargo test` (`kinetic_lock_rs`) | 5 passed |

### Lean 4 — every verified file compiles, no `sorry`, only the standard axioms

Each declaration's `#print axioms` output must be exactly `[propext, Classical.choice, Quot.sound]`.

| file | declarations | errors | `sorryAx` | non-standard axioms |
|---|---|---|---|---|
| `CoreScaling.lean` | 10 | 0 | no | 0 |
| `LerayAlphaFilter.lean` | 7 | 0 | no | 0 |
| `LatticeBGKEntropy.lean` | 7 | 0 | no | 0 |
| `AlphaEnergyIdentity.lean` | 5 | 0 | no | 0 |
| `NonlinearBGKEntropy.lean` | 7 | 0 | no | 0 |
| `KineticSpectralCap.lean` | 6 | 0 | no | 0 |
| `OpenAIAdmissibility.lean` (imports OpenAI's `ProblemStatement`, `PeriodicIntegration`, `PeriodicUniqueness`) | 15 | 0 | no | 0 |
| **total** | **57** | | | |

### Link 4, linear — exact BGK shear spectrum (re-simulated)

| claim (paper §9.2) | committed | reproduced |
|---|---|---|
| hydrodynamic mode ends at `kλ = √(π/2) = 1.2533141373155` | 1.2533141373147 (bisection) | 1.2533141373147 |
| first kinetic correction `Γ = νk²[1 − c(kλ)²]`, `c = 1` | 0.99999892 | 0.99999892 |
| damping never exceeds the collision rate `1/τ` | true | true |
| barrier / kinetic damping at `kλ = 1` | 1.4339607 | 1.4339607 |
| two independent methods agree (q ≤ 0.5) | 2.6e-12 | 2.6e-12 |

### Direction 1 — forced collapsing core, 32³ (re-simulated)

| claim (paper §9.1–9.2) | committed | reproduced |
|---|---|---|
| control tracks analytic target, whole-field relative L2 error | 1.722e-7 | 1.722e-7 |
| B/F pooled prefactor C | 0.17523 | 0.17523 |
| B/F pooled slope | 0.85093 | 0.85093 |
| per-run C spread | 5.25% | 5.25% |
| B/F collapses onto α′/(ντ) | true | true |
| axial control L2 error | 6.502e-7 | 6.502e-7 |
| lag at end, Leray-α (α = 0.25 / 0.35 / 0.5) | 0.17% / 0.23% / 0.31% | identical |
| lag at end, LANS-α (α = 0.25 / 0.35 / 0.5) | 0.26% / 0.32% / 0.37% | identical |
| lag at end, hyperviscous barrier (α = 0.25 / 0.35 / 0.5) | 4.8% / 19.2% / 45.0% | identical |

This is the source of "the gates lag 0.2–0.4%, the barrier 5–45%".

### Direction 1 — 96³ sweep (re-derived from `forced_core_96_v3.json`)

| claim (paper §9.1) | quoted | re-derived |
|---|---|---|
| runs crossing B/F ≥ 1 | 0 of 6 | 0 |
| window-end exponent of ℓ vs α′ (clean band) | +0.42 | +0.423 |
| window-end exponent of u_max vs α′ (clean band) | −0.43 | −0.429 |
| control collapse rate d ln ℓ / d ln τ | 0.500 | 0.500 |

### Link 4, nonlinear — Rust discrete-velocity BGK solver

Gates re-run (`gates --dt-over-tau 0.05`, including the rusty-SUNDIALS CVODE cross-check G3):

| gate | criterion (from `kinetic_lock_rs/README.md`) | reproduced |
|---|---|---|
| G1 | Newton equilibrium matches target moments | pass |
| G2 | mass/momentum conserved, discrete H non-increasing | pass |
| G3 | agreement with CVODE; second-order convergence | pass |
| G4 | shear decay within 2% of exact BGK for kλ ≤ 1 | pass (thin margin, 1.97%; fails at dt = τ/10) |
| G5 | positivity in Taylor–Green flows to Mach 0.6 | pass |
| — | lattice vs exact BGK reference points, max rel. diff | 5.6e-12 (identical) |

Collapse results (re-derived from `kinetic_lock_collapse.json`):

| claim (paper §9.2) | quoted | re-derived |
|---|---|---|
| apparent arrest moves with grid, λ = 0.065, Re = 1 (Δx 0.67λ → 0.34λ → 0.17λ; core size at first 10% lag) | 0.98λ → 0.52λ | 0.98 → 0.70 → 0.52 |
| same, Re = 0.25 | 0.96λ → 0.35λ | 0.96 → 0.54 → 0.35 |
| NSE control on the same grid, max \|lag\| through the kinetic event | ≤ 4e-4 | 3.7e-4 |
| kinetic core ahead of NSE target | up to 12% | 12.2% |

## What the benchmark caught

Building the re-derivation checks exposed one wrong figure in the v5.4.0 paper, CHANGELOG and
programme document: the Re = 0.25 grid-refinement endpoint was quoted as 0.86λ, a value of a different
metric (minimum core size over the run), while the other three endpoints used the core size at the
first 10% lag. With one metric throughout it is 0.96λ. Corrected in v5.4.1.

## What this benchmark does not do

- It does not re-run the 96³ sweep or the kinetic collapse runs; it re-derives their quoted numbers
  from the committed data. A full re-simulation needs about 11 CPU-hours.
- It does not check the older analytical directive scripts beyond what `pytest` covers.
- It checks that the Lean files compile with standard axioms; it does not check that their statements
  mean what the prose says. For that, read each file's header, which states what it does not prove.
- Passing it shows the committed numbers are what the code produces. It does not show the models are
  the right models.

## Run it

```bash
scripts/run_benchmarks.sh          # quick tier: tests, spectrum, 32^3 forced core, Rust gates, Lean
scripts/run_benchmarks.sh --full   # adds the 32^3 axial gate-vs-drain runs
# options: BENCH_OUT=<dir>  OPENAI_LEAN=<path to NavierStokesAndEuler>  RAYON_NUM_THREADS=<n>
```

The script never writes under `experiments/results/`; it copies the experiment scripts into the run
directory and compares from there. It exits non-zero if any check fails.
