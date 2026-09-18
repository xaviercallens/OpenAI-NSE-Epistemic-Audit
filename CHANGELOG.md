# Changelog

## v5.8.0 — 2026-09-19 — A fixed-ambient-pressure test: the failed water-like prediction holds once the closed-box pressure rise is removed

- `md_run --baro auto`: a weak barostat on the box area, coupled to the far-ring pressure (study §12); two water-like slab runs.
- Far-field pressure held within +0.12 / +0.10 of target (uncontrolled: +0.45). The wall swirl plateaus at **0.842 / 0.841**
  (mean of the six highest windows) against the registered cap **0.824**: +2%, inside one per-window standard error.
  The prediction therefore **failed in the closed box (+14–24%) and held at fixed ambient pressure**; at the measured
  pressure the swirl reaches 0.97–1.01 of the bound at the plateau and never more than 0.94 in any window.
- Caveats: two runs, one state point, a slab; the barostat lags; the plateau statistic is biased upward; K and τ were tuned on one smoke test.
- Not done: a fixed-pressure test in 3D, an undriven liquid control for the axial diagnostic.
- Benchmark: four new checks (per run: barostat control; plateau vs the registered cap).
- DualScale-Enterprise `numerics/dualscale-md` gets the barostat in a follow-up PR.

## Unreleased — 2026-09-18 — Three corrections to how this project presents itself

No scientific claim changes. All three items are about the gap between what the repository
asserted and what a reader could actually check, which is the same class of defect this project
exists to find in other people's work.

### The continuous-integration badge was removed

The README carried a CI badge for a workflow named "Physical Censorship Audit Pipeline". Two
things were wrong with it. The name is the framing this project withdrew in September. And the
workflow has **never produced a job**: every run on record ends in `startup_failure`, which points
at a repository or account setting rather than at the workflow file. A badge for a gate that has
never executed is an advertisement for verification that did not happen, and it sits at the top of
the page where a skeptical reader looks first. Removed rather than fixed, because removing a false
signal does not require first solving the account problem.

### The kernel transcripts are now committed

Every "verified" Lean file ends in `#print axioms`, and the declaration counts quoted in the
README come from running those. Those transcripts existed only on the author's machine:
`.gitignore` excluded `benchmark_runs/`, and a global `*.log` rule excluded them a second time.
From GitHub, every count was therefore an unbacked self-report — precisely what this project
refuses to accept from the work it audits.

`benchmark_runs/v5.6.1/logs/` and `benchmark_runs/v5.7.0/logs/` are now tracked, 36 files and
about 180 KB. They contain the raw kernel output, for example:

```
'OpenAIAdmissibility.bkmHypothesis_holds' depends on axioms: [propext, Classical.choice, Quot.sound]
```

The README now also states plainly how to re-derive them, and what remains uncheckable from
GitHub alone.

### `LL.md` was rewritten

The previous version was an "Anti-Pattern Playbook" for public posting. Several of its lessons
were real and are kept: do not argue that a correct PDE proof is physically vacuous, do not ask
strangers to run your code, lead with a figure, read a venue's rules.

The rest was reputation management and has been removed, with the removal itemised in the file
itself. It contained a "Terminology Blacklist" mapping accurate descriptions of the work to casual
substitutes so that "We conducted a Physical Verification" would be presented as "I was playing
around with the equations"; a rule of zero links in an initial post and an instruction to say
nothing about the repository unless asked; an instruction to agree immediately with any
challenger regardless of whether they were right; an adopted persona of a curious explorer rather
than someone presenting an audit, which is what this is; and quotations of individual people by
account handle.

The replacement rule is: **disclose how the work was done, link the source, and let the work carry
it.** This project is AI-assisted, its history is mixed human and agent, and its subject is an
AI-generated proof. None of that is embarrassing. Concealing any of it would be, and in a project
whose whole subject is the gap between looking correct and being correct, a file optimising for
reception over correctness was the wrong instinct.

## v5.7.0 — 2026-09-18 — Three-dimensional boxes, a water-like liquid, a direct pressure test, and a prediction that failed

### What was run (paper §9.3, study §10–11)

- Gas ensemble completed: Re = 4 ×3 (target Mach 0.30/0.50/0.72: fitted local Mach 0.29 ± 0.02 / 0.40 ± 0.04 /
  0.50 ± 0.04 vs continuum 0.27 / 0.39 / 0.48), Re = 32 ×2 (dense gas 0.64–0.73 for target 0.75–3, fitted profile 0.63 → 0.47; the v5.6.1 single-run 0.62–0.71 is superseded).
- 3D gas box (170 × 170 × 60 σ, Re = 16): dense-gas local Mach ≤ 0.87 while the target reaches 3.1; axial density and
  centroid diagnostics show no fluctuation above an undriven vortex in the same box (control run).
- Liquid T = 1 ×2: cavitation at target u 1.49 in both; wall swirl 1.77–2.09 (± 0.03), at or below the cap 2.07 within one s.e.
- Water-like liquid (ρ 0.79, T 0.75, ν 2.95 ± 0.14): 2 slab runs and one 3D box (110 × 110 × 40 σ).

### A registered prediction that failed, and a measured reason

Registered before the data: cavitation waits for the tensile strength (**held**: onset at target u 0.95–0.97 slab,
1.17 in the box) and the wall swirl stays below √(2p∞/ρ) = 0.82 (**failed**: 0.94 at the half-density bin, 1.01–1.02
as the maximum over adjacent bins, 1.14 in the box; +14% to +38%).

New diagnostic `md_run --stress on`: per-bin radial and isotropic pressure (kinetic part + per-particle virial share; the
tensor trace equals the pair virial to 1e-9, tested). In a further slab run the far-field pressure rises from 0.32 to
0.77 as the emptied core pushes liquid outward in the closed periodic box, and the wall swirl stays at 0.45–0.75 of the
cap at that pressure. **Post hoc, one run, not a passed test**; a fixed-pressure far field is needed. The earlier
cyclostrophic wall-tension estimate started from the initial pressure and is superseded.

### Also
- Axial diagnostic for the water-like box is inconclusive (an emptied core has no meaningful centroid; no undriven liquid control).
- Benchmark: four new checks (Re = 4 ensemble, 3D gas bound, water-like failed cap, measured-pressure reading).
### Published
- GitHub release v5.7.0 (paper PDF attached); Zenodo version DOI **10.5281/zenodo.22836538** (concept 10.5281/zenodo.22696717),
  66 files checksum-verified against the tagged tree before publishing; HuggingFace dataset synced to v5.7.0.
- DualScale-Enterprise `numerics/` (PR #1, merged) predates the stress diagnostic; not yet ported.

## v5.6.1 — 2026-09-18 — Full molecular-dynamics ensemble, a normalization correction, and a velocity bound from cavitation

### Correction to v5.6.0

v5.6.0 compared MD local Mach numbers formed with the ideal-gas sound speed `√(γT)` against continuum Mach
numbers normalized to the real-gas sound speed; `√(γT)` is 8.5% low at ambient density (1–2% in an evacuated
core). All MD local Mach numbers now use `c(ρ,T)` from the MD gas's own third-virial equation of state, bin by
bin. Two v5.6.0 statements change: free molecules on the emptied axis reach **0.84–0.95**, not "≈ 1.2" (that was
single raw bins with `√(γT)`); the surrounding dense gas does not "stay at 0.55–0.67" but **overshoots to 0.79 at
target Mach 1.5 and settles at 0.50–0.62**.

### Gas: full ensemble (paper §9.3, study §8)

- Re = 16, three runs, target Mach 1: fitted peak local Mach **0.538 ± 0.011** against the pre-registered 0.54;
  core density 0.33 ± 0.01 vs 0.36; core temperature 1.15 ± 0.02 vs 1.15.
- Re = 32 (one run): the dense gas stays at 0.62–0.71 while the target is driven to Mach 3, and falls to 0.47 by
  target Mach 6.3 (continuum 0.56–0.60). Re = 4 (one run): the target reaches only Mach 0.72 — unlocked, as in the
  continuum model.
- In every run the MD core density levels off near a quarter of ambient while the continuum core keeps
  evacuating: the one place the two descriptions differ.

### Liquid: cavitation and a capped wall speed (paper §9.3, study §9; one run, prediction registered first)

- Lennard-Jones liquid, ρ = 0.80, T = 1, Re = 4. Registered prediction (commit `4f59e04`): no cavitation before
  u_max ≈ 1.1 (ℓ ≈ 9σ). Outcome: cavitation at u_max ≈ 1.4–1.5 (ℓ ≈ 7σ), after the liquid held a tension of the
  order of its ambient pressure; core density 0.74 → 0.07 within one averaging window, then vapour.
- After cavitation the cavity grows to 7.5σ and **the swirl at its liquid wall levels off at 1.77–1.87 while the
  target rises from 1.6 to 2.8**, below the hollow-vortex bound √(2p∞/ρ) = 2.07: the one genuine velocity bound
  found in this work, supplied by a phase change. Vapour molecules inside the cavity keep following the force.

### Also

- Liquid run relaunched after the first attempt stopped at start-up (thermostat buffer did not fit the box).
- `analyse_md_core.py`: real-gas local sound speed, dense-bin estimator, figure with all Reynolds numbers, the
  pre-registered continuum curves, and the liquid density profiles.

### Published

- **Zenodo:** v5.6.1 published as **10.5281/zenodo.22828106** (concept DOI 10.5281/zenodo.22696717, verified to
  resolve to it), from a draft verified beforehand: 66/66 files with MD5s matching the tagged release, PDF
  byte-identical to the tag, description identical to the committed metadata. Benchmark 59/59.

## v5.6.0 — 2026-09-18 — A closure-free test of the Mach lock; the quantum-fluid counterpart

### Molecular dynamics of the forced core (paper §9.3; `md_core_rs/`; preliminary, two seeds)

- Lennard-Jones gas (ρ = 0.15, T = 2, mean free path 1.49σ, 107,584 particles), same per-unit-mass force,
  thermostat only beyond 3.2 core radii. No viscosity law, heat-conduction law or equation of state is put in.
- Gates: energy drift ≤ 4×10⁻⁵; pressure within 0.8% of the third-virial EOS; viscosity measured in situ
  1.71 ± 0.07 (shear waves, 14 runs) and 1.87 ± 0.18 (vortex decay) vs modified Enskog 1.83.
- **The continuum prediction was registered before the MD data existed** (commit `de1f539`). At Re = 16 and
  target Mach 1 (local Knudsen ≤ 0.2): MD local Mach 0.56–0.62, core density 0.34 ± 0.01, core temperature
  1.15 ± 0.03 vs continuum 0.54, 0.36, 1.15. **The lock is not an artefact of the Navier–Stokes–Fourier
  closure.**
- Beyond target Mach ≈ 1.5 the axis becomes free-molecular (tens of molecules at 8–10% density, mean free
  path larger than the core); those molecules reach local Mach ≈ 1.2 while the surrounding gas stays at
  0.55–0.67. The core crosses from the continuum into the free-molecular regime within one simulation.
- Limitations: two seeds; thin slab (no 3D instability); ideal-gas sound speed for local Mach numbers.
  Further seeds, Re = 4 and 32, and a liquid (cavitation) run are running and will be added in v5.6.1.

### The quantum-fluid counterpart (paper §9.5, new)

- A quantized vortex has `u r/(ħ/m) = 1` at every radius — a Reynolds-number-one core by theorem — with
  sonic radius `ħ/(mc) = √2 ξ` in the place of ℓ*. The GP vortex, its classical compressible twin, the air
  core and cavitating water all tolerate `u ∝ 1/r` by emptying the core.
- GP vortex dipole: every measured speed below c (fastest pair 0.50 c; annihilation pulses up to 0.92 c;
  point-vortex law recovered to 0.1% at large separation).
- Landau criterion as the tangent to the dispersion curve (c, 0, ≈ 58 m/s in He-4); Godfrin's roton in a 2D
  Fermi liquid as the warning not to carry the gas-kinetic termination over to water.
- Mass-independent estimate `ℓ* ≳ (√2/4π) a_B ≈ 6 pm` from published minimal-viscosity and maximal-sound-
  speed bounds (identity proved in Lean; the inputs are estimates).
- `QuantumVortexLink.lean` (11 declarations): **Lean total 85 declarations in ten files**, standard axioms.
- Moonshine (Mathieu/umbral) was examined and is *not* in the paper: no mechanism connects M₂₄ or K3 to
  fluids; the only shared object is the Dedekind η and SL(2,ℤ), which also fixes the hexagonal vortex lattice
  (`QUANTUM_FLUID_MICRO_MACRO_LINK.md` §4).

### Paper (31 pp, Version 5.6.0)

Abstract, §9.3 (molecular-dynamics paragraph), new §9.5, directions list; five new references.

### Published

- **Zenodo:** v5.6.0 published as **10.5281/zenodo.22823647** (concept DOI 10.5281/zenodo.22696717, verified
  to resolve to it), directly from a draft verified beforehand: 66/66 files with MD5s matching the tagged
  release, PDF byte-identical to the tagged commit, description identical to the committed metadata.

## v5.5.1 — 2026-09-17 — Repository-wide realignment with the v5.5.0 positions

No new results. Every tracked artefact was re-read against the current positions (proofs correct, physical
reading not refutation; regime map `Kn = Ma/Re`; link 1 unconditional; kinetic termination not drain; no
arrest on OpenAI's route; Mach lock 0.70 on the inertial route; Leray-α anchor withdrawn) and brought into
line. History is kept as dated notes, not rewritten.

- **Paper (29 pp, "Version 5.5.1").** Read end to end as one document: intro roadmap now covers §9;
  "lock" language for model regularizations replaced; §11.4 recast as the history and outcome of the
  dual-scale hypothesis instead of a live proposal; Lean status rewritten as nine files / 74 declarations;
  "thermal kinetic test" added as the most direct next experiment; conclusion covers all three routes;
  Table 7 no longer implies a physical cutoff would prevent blow-up; the "arrow and bullseye" simile removed.
- **Research and Lean docs.** Programme doc: Lock A answered negatively, Locks C/T tested, plan status
  (done / open). Leray-α document marked superseded. Blueprint atlas pages marked draft or withdrawn with
  their defects; the six `src/drafts/*.lean` carry an UNVERIFIED DRAFT header. The withdrawn
  "Thermodynamic Censorship" paper's notice now says "do not cite" and points to v5.5.0. WorkStream notes 1–4
  updated (measured heating coefficient; exact cavitation coefficient 1.70).
- **Public and educational material.** Memo (FR/EN/ZH), citizen-science and training notebooks (EN/FR/ZH),
  PoC proposal, neuro-symbolic engine proposal, reproduction protocols and `02_Empirical_Observation`:
  "censorship", "physically impossible", "intercepts/refutes" and LeanFlow/physlib-as-existing-tool claims
  removed or relabelled; "67 fs" corrected to 6.7 ps; a DNS page that described a synthetic field and a
  Gaussian filter as JHTDB queries and an ML-LES run now says what the script does. Two pre-existing notebook
  corruptions fixed (a vertical-tab character, a broken string literal).
- **Root, CI, code text.** README checked end to end (tree, commands, links, withdrawn labels);
  `dataset/README.md` to v5.5.0; historical working documents carry a status header. CI workflow now runs
  `pytest` and (on manual dispatch) checks the nine verified Lean files inside OpenAI's project. Legacy
  `zenodo_upload.py` (would have published the withdrawn framing) now refuses to run. Docstrings and labels in
  scripts/tests updated without behaviour changes.
- **Checks.** pytest 124/124; benchmark comparison 54/54; paper 0 errors / 0 undefined references; all
  notebooks validate; verified Lean files untouched.
- **Also in this tag (exploratory).** `05_Community_Research_Directions/QUANTUM_FLUID_MICRO_MACRO_LINK.md`: the
  micro-macro link through quantum fluids. A quantized vortex has `u r/(hbar/m) = 1` at every radius (a
  Reynolds-number-one core by theorem) and survives by emptying its axis, as the air core and cavitation do;
  Landau critical velocity as a tangent to the dispersion curve (c, 0, ~58 m/s for He-4); vortex-lattice
  energy `-log(sqrt(Im tau)|eta|^2)` minimal at the hexagonal point; a mass-independent floor
  `l* >= (sqrt2/4pi) a_B ~ 6 pm` (estimate); a GP vortex dipole never exceeds c. Moonshine: no mechanism
  links M24/K3 to fluids; the shared object is eta and SL(2,Z). `QuantumVortexLink.lean` (11 declarations);
  11 new tests. Not yet in the paper.
- **CI.** The updated workflow is parked at `.github/proposed/audit-pipeline.proposed.yml`; the live workflow
  is unchanged because pushing workflow files needs a token with the `workflow` scope.
- **Known and left as is.** GitHub Actions runs have been ending in `startup_failure` with zero jobs, which
  points at a repository/account setting rather than the workflow file. `openai_lean_audit_certificate.json`
  is signed and still carries old wording (its generator is fixed). `verify-physical-vacuity.sh` is kept
  unchanged because `zenodo_retriever.py` pins its checksum; the docs label it an older runner.

## v5.5.0 — 2026-09-17 — A regime map of blow-up scenarios; a thermodynamic Mach lock; the Leray-α anchor claim withdrawn

### Rereading Tao (2016) and a human-written forced Euler blow-up

`Kn = Ma/Re` (von Kármán) and `u/ℓ ≤ c²/ν ⇔ Ma² ≤ Re` put the three constructions in three places:
**diffusive route** (OpenAI NSE, `Re ≈ 1`): `Kn = Ma`, everything fails at `ℓ*` — Proposition 5.1 is this
case; **inertial route** (Tao: stages `(1+ε₀)` smaller and `(1+ε₀)^{5/2}` faster, `Re → ∞`): incompressibility
fails first, inside the continuum, at `Re·ℓ*`; **bounded-velocity route** (forced Euler with smooth force:
bounded velocity, unbounded gradients): neglected viscosity acts first, at `ℓ*/Ma > ℓ*`. Paper §9.4;
`BlowupRegimeMap.lean` (13 declarations, incl. the atomistic bound `|v| ≤ √(2E/m)`).

### Compressibility and thermodynamics on the forced core (paper §9.3)

- The kinetic null result of v5.4 excluded more than thermodynamics: constant collision time means
  `μ ∝ ρ`, constant ν. `kinetic_lock_rs` now has `--tau-law inv-rho` (physical gas) and `--force per-volume`.
- New `experiments/compressible_core.py`: 1D axisymmetric compressible Navier–Stokes–Fourier forced core,
  physics switched on one piece at a time; 8 tests; control tracks to 7e-6; grid-converged.
- **A prediction of ours failed**: quasi-steady arrest at Ma 0.36 (`ℓ_c = 2.76 Re ℓ*`) does not happen; at
  `Re ≈ 1` the collapse outruns its own density hole (needs `u_r/c ≈ 1.7 Ma³/Re`). On the diffusive route
  compressibility and heat only slow the core (+14% real-gas μ, +25% air, −5% constant ν at target Ma 2).
- **Positive result — a thermodynamic Mach lock on the inertial route**: for `Re ≳ 16` air does not follow
  the driven swirl past local **Ma = 0.70** (target Ma 4 and 8 alike; 0.81 with a per-volume force); the
  force's work goes into heat and evacuation (`T₀` 2.0, `ρ₀` 0.12, `ν₀` ×15 at target Ma 8). A lock on Mach
  number, not on velocity or core size; open-loop force; 1D ideal gas; and not a regularity statement
  (compressible NS has proved implosion singularities — MRRS 2022, Buckmaster–Cao-Labora–Gómez-Serrano 2025).
- Kinetic cross-check (`τ ∝ 1/ρ` vs constant τ): same direction, small at the resolvable Re ≤ 3
  (peak Ma 0.72 vs 0.77 at Re 3, target Ma 0.75; larger beyond the solver's validated Mach range); the BGK gas is isothermal, so the thermal kinetic test is still to be done.
- Refinements: measured heating coefficient vs `u²/c_p` is 0.35 (Ma 0.4) → 1 (Ma 1); exact Lamb–Oseen
  cavitation coefficient 1.70 moves the water threshold to u ≈ 7.6 m/s, 130 nm, 17 ns (paper §5.6).

### The Leray-α "physical anchor" claim is withdrawn (paper §9.5)

"α = ℓ* makes Leray-α a sound representation of the fluid at its continuum limit" is false. Formal reason
(`LerayAlphaLinearization.lean`, 4 declarations): for any bounded bilinear `B` and linear filter `F`,
`u ↦ B(Fu,u)` has zero derivative at rest, so α is absent from the linear dynamics, which stay `νk²` —
above any kinetic cap `1/τ`. Plus: wrong direction (kinetic theory reduces damping), none of Ma/Kn/Eckert
effects represented, and ℓ* is the relevant scale on one route only. The global-regularity theorem stands
as a theorem about a different equation.

### Also

- Lean total: 74 declarations in nine files. Benchmark extended to the new files and results.
- Write-up: `05_Community_Research_Directions/THERMO_COMPRESSIBLE_LOCK_STUDY.md`.

### Published

- **Zenodo:** v5.5.0 published as **10.5281/zenodo.22806767** (concept DOI **10.5281/zenodo.22696717**,
  verified to resolve to it). Published directly from a draft verified beforehand: 50/50 files, every
  MD5 matching the release commit, description identical to the committed metadata. One stale sentence
  ("57 Lean 4 declarations in seven files") was caught in that check and fixed before publishing.

## v5.4.1 — 2026-09-17 — Reproducibility benchmark; one figure corrected; documentation brought up to date

### Correction to v5.4.0

The paper (§9.2), this changelog and `DUAL_SCALE_LOCK_PROGRAMME.md` §8 quoted the Re = 0.25
grid-refinement endpoint of the kinetic collapse as **0.86λ**. That value belongs to a different
metric (minimum core size over the run); with the metric used for the other endpoints (core size at
the first 10% lag) it is **0.96λ**. The conclusion is unchanged: the apparent arrest moves with the
grid (0.96λ → 0.35λ). Found by the new benchmark's re-derivation check.

### Reproducibility benchmark

- `BENCHMARKS.md`, `scripts/run_benchmarks.sh`, `scripts/compare_benchmarks.py`: re-runs pytest (116),
  cargo tests (5), all seven Lean files (57 declarations, standard axioms), the exact BGK spectrum, the
  32³ forced-core and axial gate-vs-drain runs and the Rust solver gates G1–G5 (with the
  rusty-SUNDIALS CVODE cross-check), and re-derives the 96³ and kinetic-collapse numbers from the
  committed data. **44/44 checks pass; re-simulated numbers are bit-identical**; 6 min 39 s on a 4-core laptop CPU.

### Documentation

- Root `README.md`: current-status section with the lock-theory chain; stale BKM framing, a Kn = 1
  table row (now matching paper Table 6), overreaching LeanFlow claims and dead links fixed.
- `01_Verification_Paper/README.md` rewritten (it still cited the withdrawn Version-2 record and the
  wrong repository name); findings checked against the paper.
- `03_Lean4_Topological_Censorship/README.md`: all seven verified files, what each proves and does not,
  correct build instructions; legacy and draft files labelled honestly.
- `05_Community_Research_Directions/README.md` re-indexed; dated update notes in `experiments/RESULTS.md`,
  `LERAY_ALPHA_DUAL_SCALE_LOCK.md`, `WEEK1_LOCK_RESULTS.md`, `DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md`.
- `dataset/README.md` and `07_Tout_Public_Memo/MEMO.md` brought to v5.4; Lean toolchain version in
  `REPRODUCTION_PROTOCOL.md` corrected (v4.11.0 → v4.34.0-rc2).
- Zenodo and Hugging Face metadata updated; new files in both bundles: the two new Lean files, the
  kinetic solver README, kinetic and 96³ data, figure, and the benchmark.

## v5.4.0 — 2026-09-17 — Link 1 unconditional; the kinetic model does not arrest a driven collapse

### Lean 4: the admissibility bridge no longer has a hypothesis

- `OpenAIAdmissibility.lean` proves `bkmHypothesis_holds : BKMHypothesis` (the periodic mean-velocity
  lemma: `d⟨u⟩/dt = ⟨f⟩` on the unit cell via OpenAI's own `NavierStokes.PeriodicIntegration` and
  `PeriodicUniqueness`, bounded mean from `u(0) = 0`, oscillation `≤ √3·C`). New unconditional
  corollaries: `candidate_violates_every_gradient_bound'`, `candidate_not_admissible'`,
  `candidate_not_admissibleScaled'`, `exits_admissible_near_one'`. Definitions unchanged; 15
  declarations; standard axioms only.
- New files: `NonlinearBGKEntropy.lean` (7: discrete entropic equilibrium minimizes H; BGK step
  conserves mass/momentum, preserves positivity, decreases H; exact-difference forcing conserves
  mass/momentum) and `KineticSpectralCap.lean` (6: eigenvalues of skew streaming plus projected
  relaxation satisfy `−1/τ ≤ Re μ ≤ 0`).
- Count convention: 57 declarations checked by `#print axioms` across seven files (v5.3.0 quoted
  "45 theorems" under a different convention; by this one it was 36).

### Nonlinear test of the kinetic lock (link 4): null result

`05_Community_Research_Directions/kinetic_lock_rs/` — a Rust 2D-2V discrete-velocity BGK solver, gated
before use (moments 1e-15; conservation 2e-15 with monotone H; second-order agreement with
rusty-SUNDIALS CVODE; positivity to Mach 0.6; linear shear decay within 2% of exact BGK for kλ ≤ 1 at
dt = τ/20 — thin margin, fails at τ/10). Driven by the forced-core target:

- no arrest at `k_ωλ ≈ √(π/2)`; the kinetic core runs up to 12% *ahead* of the NSE target;
- the apparent stopping point moves with the grid, not with λ (λ = 0.065: Δx 0.67λ → 0.17λ moves it
  0.98λ → 0.52λ at Re 1, 0.96λ → 0.35λ at Re 0.25; core size at the first 10% lag); NSE control on the same grid tracks to 4e-4;
- robust within the validated range: no arrest at or above ≈ 0.9λ. Below it, runs exceed Mach 1 and
  the positivity gate. Isothermal model — no thermodynamic lock by construction.

### Direction 1: 96³ forced-core sweep

The v5.3.0 forecast of `B/F = 1` crossings **failed** (0/6; B/F saturates at 0.25–0.56 because the
barrier fattens the core). The core size shows the arrest instead: local collapse rate 0.04–0.16
(control 0.500) at `ℓ ≈ 1.2–1.5 √α′`; window-end exponents ℓ +0.42, u −0.43 to −0.47 against the
law's +0.5, −0.5. Not yet converged.

### Paper (25 pages)

Abstract, §9.1 (96³ result), §9.2 (nonlinear kinetic test paragraph), §10.3 (Lean status), Direction
1 and 2, conclusion, and a new "Forecasts not borne out" paragraph in Appendix A.

Not published to Zenodo or Hugging Face in this release; the latest DOI remains v5.3.0.

## v5.3.0 — 2026-09-16 — The kinetic lock is a termination, not a drain; first Lean bridge to OpenAI's objects

### Correction to v5.2.0

v5.2.0 said "the lock that operates where the continuum ends is dissipative, which is what kinetic
theory supplies", implying real physics at `ℓ*` acts like the hyperviscous barrier that §9.2 found to
be the stronger of two model regularizations. **That implication is withdrawn.** The exact shear-mode
spectrum of the BGK kinetic model (`experiments/lock_k_kinetic_spectrum.py`; two independent methods
agreeing to 3×10⁻¹²; numbers re-derived and re-verified from scratch) shows:

- damping `Γ = νk²[1 − (kλ)² + …]` — the first kinetic correction **reduces** damping (Burnett
  coefficient +1, derived and confirmed), the opposite sign to hyperviscosity; truncated at that order
  it becomes unstable for `kλ > 1` (Bobylev), the full mode does not;
- the damping never exceeds the collision rate `1/τ` — exact, since the linearized operator is skew
  advection plus `−(1/τ)(I − P)`, the spectral twin of the Lean H-theorem;
- the hydrodynamic shear mode **ceases to exist** at `kλ = √(π/2) ≈ 1.2533` (closed form);
- at `kλ = 1` the barrier damps 1.43× harder than kinetic theory.

BGK collisions are dissipative thermodynamically, but they are not a stronger drain on small scales.
**The lock at `ℓ*` is the end of the hydrodynamic description** — the paper's original §5 reading,
now with a mechanism. The gate-versus-drain comparison stands as a ranking of two *models*.

### Paper (24 pages)

- §9.2 "Which lock acts where the continuum ends" rewritten with the BGK dispersion relation
  (Eq. `bgk-shear`), the termination wavenumber (Eq. `bgk-termination`), and the corrected
  conclusion; a clause added that the gate–drain ranking is a model comparison. Abstract and
  conclusion corrected accordingly. New reference: Bobylev 1982.
- §10.3 Lean status: 45 theorems in five files, one now about OpenAI's actual objects.
- Direction 2 rewritten: the formal reduction is **done**, and its hypothesis is **not**
  Beale–Kato–Majda but an elementary periodic-cell lemma (cell mean obeys `d⟨u⟩/dt = ⟨f⟩`; a gradient
  bound `C` confines `u` within `√3·C` of it), unformalized only for want of torus integration by
  parts in Mathlib. The honest reading is stated: the result is close to "velocity blow-up forces
  gradient blow-up", valuable as the first bridge, not as new physics.

### Lean 4

- `OpenAIAdmissibility.lean` (7 theorems) imports OpenAI's `NavierStokes.ProblemStatement` unchanged.
  Unconditionally, a candidate's velocity gradient is bounded on every `[0, 1−δ]`; given the labelled
  hypothesis, any object with OpenAI's `CandidateProperties` exceeds every gradient bound in every
  window before `t = 1`, hence leaves the admissible set for every fluid and unit choice. Compiled
  inside OpenAI's project; independently re-verified (0 errors, 0 warnings, 0 `sorryAx`, standard
  axioms only). Build instructions in the module header.

### Also

- `DIRECTION1_RESULTS.md` and `DUAL_SCALE_LOCK_PROGRAMME.md` carry explicit correction notes rather
  than silent rewrites.
- HuggingFace card and Zenodo metadata brought to v5.3.0; the Zenodo push script retries 5xx
  responses and accepts `--draft-id`.

### Published

- **Zenodo:** v5.3.0 published as **10.5281/zenodo.22777467** (concept DOI
  **10.5281/zenodo.22696717**, which always resolves to the latest version). Published directly from a
  draft verified beforehand against the committed release: 32/32 files, every checksum matching,
  metadata and description checked. An earlier attempt had been delayed by a Zenodo-side 504 outage.
- **HuggingFace:** `callensxavier/OpenAI-NSE-Thermodynamic-Censorship` at v5.3.0, verified live (paper
  PDF byte-identical to the release). The card previously labelled record 22696718 as the "concept
  record"; that id is an earlier version record, and the card now cites the concept DOI.

### Pending

- The `96³` forced-core crossing sweep.

## v5.2.0 — 2026-09-16 — 3D solver, cutoff law tested, forced core, gate vs drain, 38 Lean theorems

### Paper (`01_Verification_Paper/`, 23 pages)

- **New §9, "Testing the Cutoff Regularization Hypothesis".** The cutoff law the Outlook stated as
  untested is tested. It is exact given its premise (all four exponents reproduced as identities to
  machine precision), but the premise — a `Re ≈ 1` diffusive core — is never produced by generic
  data: in a dyadic cascade the arrest-scale velocity follows `k^−0.345` (Kolmogorov `−1/3`), not
  the law's `k^+1`, with Re 5–1200 at the arrest scale. A 3D DNS resolution constraint
  `n > 3√(ω₀Re)` explains why earlier sweeps saw no effect at all.
- **Leray-α: gate, not drain.** Leray-α suppresses peak vorticity 3.3× while *retaining* more
  energy (its transport term does no work), where hyperviscosity dissipates. Distinguished
  explicitly from the hyperviscous barrier the earlier test used; the two had been conflated.
- **§9.1, a forced collapsing core.** A manufactured `Re = 1` collapse, sustained by its own
  Navier–Stokes residual, tracks the analytic target to `1.7×10⁻⁷`. The barrier's engagement
  `B/F` collapses onto the single variable `α′/(ντ)` (per-run prefactor `0.188 ± 0.010`), which is
  sufficient for all four arrest exponents. A lagging-core explanation of the sub-unity slope was
  tested and refuted.
- **§9.2, gate or drain on a `Re ≈ 1` collapse.** With axial structure, Leray-α and LANS-α lag the
  collapse by 0.2–0.4%; a barrier at the same scale lags it by 5–45%. Against the forcing, the
  nonlinearity is only ~5% of the dynamics, and a transport filter can act only through it. The
  gate–barrier crossover is an exact identity,
  `Re_× = ‖(L_barrier − L_ν)U‖ / ‖N_α(U) − N(U)‖`, ranging 8–142 and largest where arrest occurs.
- **Which lock acts where the continuum ends.** The validity scale is the mean free path with a
  derived constant (`ℓ*/λ = c̄/2c_s = 0.67` for air, matching the independent 45 nm / 68 nm).
  The operative lock at `ℓ*` is dissipative — collisional relaxation — not a Lagrangian-averaged
  transport filter. The LANS-α derivation conjecture is relocated to `Re ≳ 10–100`, not refuted.
- **§10.3 Lean status** updated; **Directions 1–3** updated with what is built, what is pending, and
  an uninformative first Lock-F attempt (`σ < 0`); abstract and conclusion updated. New references:
  Holm–Marsden–Ratiu 1998, Golse–Saint-Raymond 2004, Bhatnagar–Gross–Krook 1954.

### Code and data (`05_Community_Research_Directions/experiments/`)

- `spectral3d.py`: 3D pseudo-spectral NSE (rotational form, FFT Leray projection, 2/3 dealiasing,
  integrating-factor RK4); hyperviscous barrier; **Leray-α** (divergence form) and **LANS-α**
  (rotational form on `v`); Landau–Lifshitz noise with FDT calibration; runtime validity monitor;
  forcing hooks. Validated against the Taylor–Green Re=1600 benchmark (dissipation peak `t = 9.14`
  vs published `9.0`).
- `forced_core.py`, `forced_core_axial.py`, `plot_forced_core.py`: the forced-core test bed and its
  axial extension. `shell_mach_cap.py`, `lock_f_coherence.py`, `shell_cutoff_law.py`,
  `sweep_cutoff_law.py`, `analyse_cutoff_law.py`, `noise_and_monitor.py`, `validate_tgv3d.py`.
- Bugs fixed that the tests caught: a duplicated final time sample that made every
  `np.gradient`-based dE/dt diagnostic NaN; a key collision that overwrote the dissipation time
  series with the operator name; a vorticity-inversion sign error; a core-size estimator biased 12%
  by tail truncation.

### Lean 4 (`03_Lean4_Topological_Censorship/src/`, 38 theorems, standard axioms only)

- `CoreScaling.lean` — Proposition 5.1 as an equality chain from the diffusive core scalings.
- `LerayAlphaFilter.lean` — the Leray-α filter-symbol bounds.
- `LatticeBGKEntropy.lean` — H-theorem for the discrete BGK collision step.
- `AlphaEnergyIdentity.lean` — a projected skew term changes energy at second order; a dissipative
  term removes it at first order.
- Every `#print axioms` is exactly `[propext, Classical.choice, Quot.sound]`; zero `sorryAx`,
  independently re-verified. **None is connected to OpenAI's definitions yet** — stated in each file.

### Programme documents (`05_Community_Research_Directions/`)

`DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md`, `DUAL_SCALE_LOCK_PROGRAMME.md`,
`LERAY_ALPHA_DUAL_SCALE_LOCK.md`, `WEEK1_LOCK_RESULTS.md`, `DIRECTION1_RESULTS.md`,
`RICCATI_THRESHOLD_CHECK.md`, `experiments/RESULTS.md`.

### Pending

- The `96³` forced-core sweep that reaches the `B/F = 1` crossing (for the arrest exponents directly).
- A collapsing axial scale; azimuthal stability of the forced column; the construction's own profile
  with `h > 0`.
- The Zenodo draft for record 22696718 (new version 22777467) remains **unpublished** pending review.

## v5.1.0 — 2026-09-15 — Peer review response, table fixes, Zenodo record corrected

- Addressed an open peer review of the flagship paper (recorded verbatim in
  `01_Verification_Paper/PEER_REVIEW_2026-09-15.md`, with a point-by-point authors'
  response): consolidated "earlier drafts" meta-commentary out of the running text into
  a new Appendix A; moved individually-named Reddit commenters out of the main text
  into Acknowledgments and a new Appendix B preserving the full quotations; fixed a
  genuine LaTeX table overflow (Table 5, 106.7pt overfull hbox that was merging rows
  and truncating text) and rebuilt two other tables (`tabularx`, split columns) for
  robustness rather than relying on manually-sized `p{}` columns.
- **`zenodo_push.py` rewritten.** The script still targeted Zenodo record 22696718 with
  metadata and a file list from the withdrawn "Version 2" / Thermodynamic Censorship
  framing — a "10²⁸-digit structural instability", a global enstrophy-censorship axiom,
  "vacuous" physics, femtosecond-scale timings, and paths (`01_Challenger_Paper/...`)
  that no longer exist. Had this been run unmodified, it would have re-published
  already-withdrawn claims under a permanent DOI. Rewrote the title, description and
  `FILES_TO_PACKAGE` to match the current v5.0.0 paper, corrected the archive paths,
  and uploaded a corrected **draft** (record 22777467) for manual review; it has
  **not** been published (no DOI minted) — see the release notes for the review link.
- **HuggingFace dataset corrected.** The live dataset repo
  `callensxavier/OpenAI-NSE-Thermodynamic-Censorship` was found serving the withdrawn
  "Version 2" paper, an uncontextualized copy of `ThermodynamicCensorship.lean`, and a
  directive-5 output log with the exact femtosecond/picosecond unit bug this project's
  review caught (`Ma > 0.3 at tau ~ 6.7e-14 s`, twelve orders of magnitude off) --
  publicly live under a real name. Rewrote `scripts/huggingface_upload.py` (file list,
  dataset card, abort-before-upload safety check) and ran it: current paper,
  WorkStreams, CHANGELOG, peer review, regenerated directive outputs, and a corrected
  README are now live; the retracted paper and Lean file are kept under `superseded/`
  with the same withdrawal context as the Zenodo bundle.
  **Manual cleanup still needed:** a few stale duplicates remain live alongside the
  corrected files -- `REPO_README.md` (old card, still says "vacuity"), an old
  `paper/OpenAI_NSE_EpistemicAudit.pdf`/`.tex` copy, and an uncontextualized root-level
  `lean4/ThermodynamicCensorship.lean` -- because file deletion on that host was outside
  this session's permitted actions; delete them via the HuggingFace web UI or
  `huggingface_hub.HfApi.delete_file`.
- `deploy_huggingface.sh` (a *different*, unused script targeting a separate HF repo for
  the withdrawn Bi-Helmholtz/T-duality paper and `EulerCensorship.lean`, which has 7
  `sorry`s and a vacuous `True` conclusion per the v2 paper's own errata table) was left
  untouched and was not run.

## v5.0.0 — 2026-09-15 — Scientific review and remediation

This release is a full pass over every paper, script, Lean file and article in the
repository, with the aim of making each claim either derived, verified against the
OpenAI papers and Lean code, or explicitly labelled as a hypothesis. It supersedes the
"thermodynamic censorship" framing of v4.x.

### Headline scientific changes (papers)

- **One validity scale.** The physical reading is now organised around a unit-free
  result: the collapsing core has radial Reynolds number O(1), so ℓ_r ≃ √(νt) and
  u ≃ √(ν/t); compressibility, rarefaction and viscous heating all become order-one at
  the single length ℓ\* = ν/c_s (0.67 nm in water, 45 nm in air). The earlier "6.7 ps
  for a 1 cm vortex" numbers are recovered as special cases; the initial size ℓ₀ enters
  only as (ℓ₀²/νt)^h ≈ 1.2–1.3.
- **Viscous heating is u²/c_p.** Because ℓ_r² = νt exactly, ΔT = u²/c_p: 48 K at Ma = 0.3,
  540 K at Ma = 1 in water; boiling at Ma ≈ 0.37, ≈ 3–4.5 ps before blow-up. Earlier
  "plasma temperatures" and "45.6 ps" claims are withdrawn.
- **Cavitation comes first in liquids.** A vortex-core pressure deficit ρu² reaches 1 atm
  at u ≈ 14 m/s, ≈ 5 ns before blow-up (core ≈ 70 nm) — three decades before the Mach
  limit; even water's tensile strength (30–140 MPa) is reached at ≈ 17–4 ps.
- **Admissibility is a local vorticity bound.** |ω| ≲ c_s²/ν (2.2×10¹² s⁻¹ water,
  7.5×10⁹ s⁻¹ air) encodes Ma ≲ 1 and Kn ≲ 1 together; with it, "admissible on [0,T) ⇒
  no blow-up" is the Beale–Kato–Majda theorem. The constant Ω_max = 1.13×10¹³ s⁻² used
  since v4.x had no derivation anywhere in the repository and is withdrawn everywhere
  (papers, README, `physics_constants.py`, Lean draft doc-comments, table generator).
- **Lighthill "energy-budget check" removed as independent evidence.** Dimensionally,
  P_ac·t/E_core ~ Ma⁵ — it is the Mach criterion in disguise.
- **Synthetic figure removed.** `spectrum_comparison.png` drew the "OpenAI pre-singularity
  spectrum" as a hand-placed Gaussian; the flagship paper no longer presents it as a
  solver result. The unreproducible Taylor–Green/"certificate" section is removed and
  replaced by a statement of what a real numerical companion would need.
- **Citations corrected against the OpenAI PDFs.** The moment-matching system is
  Proposition B.8 / eqs. (5.10)–(5.11), not "Lemma 8.7"; "10,000 agents / 88 hours"
  appears in neither paper and is no longer stated as fact; the Euler datum is described
  as the stagewise shear-amplified packet iteration it is, with viscosity (not "Planck
  scale") as the missing physics. Bibliography entries for Schumacher et al. 2014,
  Donzis et al. 2008 and Luo–Hou 2014 corrected; Elgindi 2021, Chen–Hou 2022,
  Albritton–Brué–Colombo 2022, Foias–Holm–Titi 2001, Cheskidov et al. 2005, Bandak et al.
  2022, Zheng et al. 1991 and Caupin–Herbert 2006 added.
- **Priority-dispute paragraph reduced** to a neutral sentence (unverifiable claims about
  named individuals, sourced to Wikipedia, removed).
- Sept-12 "Thermodynamic Censorship" paper and the dual-scale/T-duality paper carry
  superseded/withdrawal notices with inline corrections; WorkStreams 1–6 rewritten to
  the positions above (WS1: BKM-based admissibility; WS2: u²/c_p; WS3: two-scale closure
  uses; WS4: cavitation first; WS5: bulk-modulus form; WS6: codimension question).

### Code

- `extract_openai_lean.py`: certificate verdict now derived from checks; Lean-4-anchored
  regexes; degraded-run flag. `directive6`: seeded RNG, result-dependent summary.
  `directive5`: analytic `tau_boil`, and the physical time unit T = ℓ₀²/ν restored in the
  heating estimate and in all printed times (τ is dimensionless). `directive2`:
  p\* = (3−2h)/(1+2h). `simu_sign_fragility_1D.py`, `simu_frustration_Z3.py`: rewritten so
  every printed verdict is computed. `thermal_derivation.py`: no magic constant.
  `zenodo_retriever.py`: frozen-snapshot vs `--live` API check. `zenodo_push.py`:
  `--publish` is opt-in with confirmation. Baseline outputs regenerated. 53/53 tests.
- Lean: 5 draft files fixed for mathlib v4.34.0-rc2 (`ContinuousMap.Basic`,
  `IntervalIntegral.Basic`), import-order bug fixed, doc-comments made honest
  (tautologies, toy types, stub demos labelled). `EulerCensorship.lean` marked superseded.

### Known limitations (unchanged in this release)

- `03_Lean4_Topological_Censorship` lemmas are not connected to OpenAI's definitions;
  only `lean_formalization/Validity/ModelValidity.lean` (v2 paper) compiles against them.
- `ThermodynamicAdmissibility.lean` still contains `sorry`; `ThermodynamicCensorship.lean`
  imports the external OpenAI package and does not build from this repository.
- No numerical realization of the OpenAI construction exists; all numerics here are
  exponent, unit and consistency checks.
- The v2 paper (`paper/where_the_continuum_ends.tex`) lives one directory above this
  repository and is not under version control here.
