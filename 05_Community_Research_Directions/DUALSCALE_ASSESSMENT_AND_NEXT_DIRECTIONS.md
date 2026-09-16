# DualScale / LeanFlow assets: assessment and next research directions

**Date:** 2026-09-16
**Scope:** `~/xdev/SocrateAI-Numeric-DualScale-Solver`, `~/xdev/runux-ai-runtime`,
`~/xdev/SocrateAI-Scientific-MechanicaFluidorum`, `~/SocrateAI-Scientific-Agora-LeanMaster`,
`~/xdev/SocrateAI-Mathesis`
**Trigger:** a benchmark report (`report_navier_stokes_benchmark_openai_leanflow_openfoam`,
published to `runux-ai-runtime` release `v0.5.0-dualscale-nse` and to HuggingFace
`callensxavier/leanflow-dualscale-openfoam-nse-benchmark`) proposed to be used as the basis
for this project's next research directions.

This document records what in those repos is usable, what is not, and what programme
follows. It exists because adopting the report as-is would reverse the v5.0.0 corrections
(see `CHANGELOG.md`) and restate claims that are checkably false.

---

## 1. Claims that must not be carried forward

### 1.1 Claims about OpenAI's construction (all five of the report's "epistemic
deconstruction" points fail)

| Report claim | Status | Evidence |
|---|---|---|
| "Manufactured residual forcing `f ≠ 0`, therefore not the autonomous Clay problem"; "falsified as unforced NSE blowup" | **Wrong target** | Fefferman's statement *explicitly permits* a smooth external force in alternatives (C)/(D) — that is precisely what OpenAI claims. The unforced statements are (A)/(B), which they never claimed. The Euler paper is separately and genuinely unforced. Already withdrawn in this project's v2 errata. |
| "Compressible dilatational leakage: by relaxing `∇·u = 0`…" | **False** | `NavierStokesAndEuler/NavierStokes/ProblemStatement.lean:111` — `divergence_free : ∀ t ∈ Ico (0:ℝ) 1, ∀ x, spatialDivergence u t x = 0`. Enforced exactly as a hypothesis field. |
| "Suppressed viscous dissipation: `νk²` damping truncated at high wavenumbers" | **False** | The construction runs at viscosity one with the full Laplacian and rescales to any `ν > 0` (NS paper §3). |
| "Elimination of triadic phase frustration: replaced by a 1D scalar cascade with strictly positive couplings" | **Category error** | That describes *this project's own* 1D toy shell model, not OpenAI's construction, which is a 3D axisymmetric-with-swirl PDE construction. v2 errata: "A shell model is not the Euler equation." |
| "Engineered horizon cutoff: `T*` positioned before viscous relaxation" | **Misreading** | `T* = 1` is a normalisation. Any finite blowup time rescales to 1. |

### 1.2 Physical claims that are overclaims

- **"Incompressibility prohibits focal collapse."** Self-refuting in context: OpenAI's solution
  is incompressible *and* blows up. If incompressibility prohibited collapse, the Clay problem
  would be settled.
- **"Viscous damping unconditionally overtakes non-linear transport."** This is Statement (A) —
  the open problem. The `νk²` vs `k` scaling argument is heuristic; it ignores that the
  non-linear term's effective amplitude also grows.
- **"Triadic phase cancellation … severely inhibiting coherent energy transfer,"** attributed to
  incompressibility. This project's own corrected `02_Empirical_Observation/simu_frustration_Z3.py`
  decomposes `D = D_dot · D_leray_only` and finds total `D` median ≈ 2–3, of which the
  **incompressibility-specific factor has median ≈ 1.0–1.1** — a weak effect with a long right
  tail. The bulk is ordinary vector alignment (`|k·u| ≤ |k||u|`), which has nothing to do with
  the Leray projector. Reasserting the strong form reverses a v5.0.0 correction.
- **"T-duality / string-theoretic hyper-viscous barrier."** Withdrawn branding (v2 errata:
  "Nothing topological or string-theoretic is used… Names withdrawn"). The operator is a
  member of the Leray-α / Bessel-filter family and stands perfectly well on its own.
- **"Ω ≤ 1/α′ ⇒ BKM finite ⇒ mathematical regularity certified."** Wrong object: this is global
  regularity of a *modified* equation, which says nothing about NSE. v2 errata already withdrew
  "a pathway to Statement A" for exactly this reason.

### 1.3 Numerical figures that are artifacts

- **`‖∇·u‖ = 4.40×10⁻³²` presented as "exact machine zero."** Not reproducible as a property of
  the method. The 2D Taylor–Green initial condition populates only 8 non-zero modes with
  coefficients `±1024 = N²/4`, a power of two, so `k·u` cancels *exactly* in binary. The same
  solver at the same amplitude on a generic random field gives relative divergence `5.6×10⁻¹⁵`
  — ordinary float64 (machine epsilon ≈ `2.2×10⁻¹⁶`). The figure is a property of the initial
  condition's binary representability, not of the projection.
- **`incompressibility_improvement_factor = 12955.99`.** This is
  `of_res["mean_continuity_error"] / max(spec_res["mean_divergence"], 1e-16)`, and the clamp
  binds: `1.2956×10⁻¹² / 1×10⁻¹⁶ = 12955.99` exactly. It divides by the clamp, not by the
  spectral divergence. Also compares an iterative **solver tolerance** (OpenFOAM) against a
  **round-off floor** (spectral) — different quantities.
- **"Eliminates 80% of computational runtime."** Asserted in prose only, and contradicted by the
  repo's own timing table: OpenFOAM 0.27 s (32×32) vs spectral 0.88 s (64×64). No timing
  benchmark supports it.
- **`linear_solver_speedup: "33 iters -> 0"`** contradicts `mean_pcg_iterations_per_step = 21.84`
  in the same JSON file.
- **The enstrophy ceiling is vacuously satisfied.** `enstrophy_upper_bound = 100.0` versus
  `standard_max_enstrophy = 4.5924` and `dualscale_max_enstrophy = 4.5906`. The barrier was never
  approached, and the regularisation changed the result by **0.04%**. A sweep of `α′` over five
  decades (1e-1 … 1e-5) moves max enstrophy from 1.0180 to 1.0182 — **0.02%**. Nothing is being
  arrested, so no arrest law is being demonstrated.
- **`epistemic_audit_conclusion`** is a hardcoded verdict string asserting the falsified claims
  of §1.1 — the same hardcoded-verdict defect class already fixed elsewhere in this project
  (see `CHANGELOG.md`, v5.0.0).

### 1.4 The structural problem

**The spectral solver is two-dimensional.**
`SocrateAI-Numeric-DualScale-Solver/src/dualscale_solver/numeric/fourier_spectral.py:10` —
`class PseudoSpectralNavierStokes2D`, "2D Incompressible Navier-Stokes Solver in a periodic
box `[0, 2π)²`", using `np.fft.fft2`. There is no 3D spectral NSE solver in either repo.

2D Navier–Stokes is **unconditionally globally regular** (classical). A 2D solver therefore
cannot bear on a 3D regularity question at all — favourably or unfavourably. The comparison
table's "LeanFlow / DualScale" column is not commensurable with the other two columns, and the
regularity row in particular is not a result about the problem under discussion.

Additionally, the report attributes the wrong dissipation operator to the solver: the 2D solver
uses `ν|k|²(1 + α′|k|²)` (`fourier_spectral.py:101`), whereas the `ν|k|² max(1, α′|k|²)` form the
report quotes appears only in the 1D shell model (`dyadic_cascade.py:58`).

---

## 2. What is genuinely good and should be credited

### 2.1 The Lean substrate is honest, careful work

This is the most important positive finding, and it runs contrary to the report that cites it.
`SocrateAI-Scientific-MechanicaFluidorum/lean_src/` appears to have already been through the
same correction process this project underwent, and its files warn *against* precisely the
extrapolation the report makes:

- `EnstrophyProductionBound.lean` — proves `S_N² ≤ 2·Ω_N³` for dyadic shells, sorry-free, with
  standard axioms only, **and includes negative controls** demonstrating its hypotheses are
  necessary. That is unusual discipline.
- `DyadicRiccati.lean` — exponent algebra for the Riccati threshold, sorry-free. Its own
  docstring: *"Claiming the theorem whole on the strength of this file would be exactly the
  D1-class overstatement the external audit of 2026-08-13 killed this programme's headline for."*
- `MillenniumReduction.lean` — a conditional reduction for the Katz–Pavlović shell model, with
  `hAL`/`hPS` explicitly undischarged and labelled: *"**This proves no analytic content.**"*
- `LocalDualScale.lean` — `Reff α R := max R (α/R)`, sorry-free, and it documents that an
  earlier revision declared `axiom alpha_prime` while claiming zero axioms, and repaired it.
- `scripts/verify.sh` — a genuine two-gate harness (exact-rational Python checks, then a Lean
  kernel gate with a mandatory `#print axioms` footprint).

**However**, no file in any of the three Lean repos states `Ω ≤ 1/α′`, a BKM bound `≤ T√(2/α′)`,
or any Navier–Stokes regularity result; none imports OpenAI's definitions; and none uses real
function spaces (no `EuclideanSpace`, no `Lp`, no Sobolev space — "Sobolev" appears only as
shell-model Fourier weights `k_n^{2s}`, and is labelled as such). The report's
"Mathematical Regularity: Formally certified in Lean 4" is therefore not supported by anything
in these repos. `LeanMaster/…/NavierStokesBridge.lean` is `Nat`-valued throughout (its "Master
Theorem" reduces to `Nat.sub_le`), and should not be cited as fluid mechanics.

### 2.2 A finding that inverts the report's use of the Lean work

`S² ≤ 2Ω³` is **super-linear**. It therefore *permits* Riccati-type finite-time blowup
(`Ω′ ~ Ω^{3/2}`) in shell models — it is the bound that makes blowup possible, not an enstrophy
ceiling. `DyadicRiccati.lean`'s `α = 1/2` threshold is exactly where the blowup rate stops being
integrable. Citing these files as certifying regularity inverts their actual content.

### 2.3 Numerics that are real

- **The OpenFOAM run is genuine.** `/usr/bin/icoFoam` and `/usr/share/openfoam/etc/bashrc` are
  installed; `blockMesh` and `icoFoam` are actually invoked via subprocess and the log parsed.
  `3276` total PCG iterations / `21.84` per step is a real measurement. (Caveat: at 32×32,
  against a 64×64 spectral run — the grids differ, so cross-column comparisons need care.)
- **FFT-based Leray projection with Orszag 2/3 dealiasing** is correctly implemented. It is
  standard practice for periodic boxes rather than novel, but it is right, and it is the correct
  foundation for the 3D solver proposed below.
- **The numerical-diffusion argument is correct and useful to this project.** Second-order FVM
  face interpolation carries a leading truncation diffusion `ν_num ≈ ½|u|Δx`, which on coarse
  grids can exceed the physical `ν` by orders of magnitude. This *supports* the paper's position:
  a conventional CFD code cannot resolve the regime in question, so the absence of such events in
  routine simulation is not evidence either way. (State it for upwind/limited schemes
  specifically; for pure central differencing the leading error is dispersive, not diffusive.)

---

## 3. Research directions that follow

Ordered by value per unit effort. The unifying theme: **use these assets to answer the questions
this project has posed and left open, rather than to re-litigate OpenAI's proof.**

### A. Enabling infrastructure

**A1. A 3D pseudo-spectral NSE solver.** *(≈1–2 days; the 2D solver is a sound template.)*
Nothing below is possible without it, and no existing asset substitutes. Reuse the FFT Leray
projection and 2/3 dealiasing verbatim, extended to `fftn`. Validate against the 3D Taylor–Green
vortex, whose dissipation-peak history is a standard benchmark with published reference data.

**A2. An `α′` sweep harness with an initial condition that actually reaches the barrier.**
The current probe shows 0.02% variation across five decades of `α′` — the barrier never bites,
so nothing is measured. This needs a collapsing initial condition (Hou–Luo-type axisymmetric
configuration, or a truncation of the construction itself) and a sweep driver recording
`u_max(α′)`, `t_c(α′)`, and the enstrophy history.

### B. Experiments that answer this project's open questions

**B1. The cutoff law — the highest-value experiment available.**
The flagship paper states as an explicitly untested hypothesis: if collapse is arrested when
`ℓ_r ~ √α′`, then since `ℓ_r ≃ √(νt)` and `u ≃ √(ν/t)`,
```
    u_max ~ ν/√α′ ,        t_c ~ α′/ν ,
```
and setting `√α′ = ℓ* = ν/c_s` predicts `u_max ~ c_s`, consistent with Proposition 5.1. Sweeping
`α′` over several decades and fitting these exponents would convert a stated open question into a
measured result — and a *negative* result (e.g. pulses de-cohering before `ℓ_r` reaches `√α′`)
would be equally publishable. This is a far stronger contribution than another critique.

**B2. Thermal noise under fluctuating hydrodynamics.**
Add a Landau–Lifshitz stochastic stress of size `√(2νk_BT/ρ)` to the 3D solver and ask whether
the exponentially small seeded pulses survive, or whether shear amplification of the noise still
produces stress with the required sign and anisotropy. Spectral methods make the
fluctuation–dissipation-consistent covariance straightforward to impose correctly.

**B3. A runtime model-validity monitor — novel and immediately useful.**
Instrument any solver with the admissibility bound derived in the paper,
```
    |ω| ≲ c_s²/ν     (equivalently  Ma ≲ 1  and  Kn ≲ 1),
```
≈ `2.2×10¹² s⁻¹` in water, `7.5×10⁹ s⁻¹` in air, and flag cells that leave it. This reports when
a simulation has left the regime in which incompressible NSE is a valid model *of a real fluid* —
distinct from, and complementary to, a numerical stability check. This is the honest and more
useful form of the report's "deploy DualScale regularisation in LES" recommendation: not a
regularisation that hides the excursion, but a diagnostic that reports it.

### C. Theory connections that use the Lean work for what it proves

**C1. Does the OpenAI construction sit at the shell-model Riccati threshold?**
This project's exponents give integrated enstrophy `Ω ~ τ^{-1/2-3h} = τ^{-0.515}` and
`‖ω‖_∞ ~ τ^{-1-2h} = τ^{-1.005}`. `DyadicRiccati.lean` formalises an integrability threshold at
`α = 1/2`. Checking whether these coincide — and whether the coincidence is structural or
numerical — is cheap, uses the existing sorry-free Lean work correctly, and would connect the
shell-model formalisation to the actual construction. Note the construction is already known to
be marginal in an independent sense: `‖u‖_{L³} ~ τ^{-4h/3}` diverges *only* because `h > 0`, so at
`h = 0` the Escauriaza–Seregin–Šverák criterion would forbid the blowup outright.

**C2. Use `S² ≤ 2Ω³` correctly.** As the shell-model statement of why blowup is *possible*
(§2.2), not as a regularity certificate. A short note correcting its citation in downstream
material would prevent the inversion from propagating.

### D. Corrections to already-published material

The report is live at `runux-ai-runtime` release `v0.5.0-dualscale-nse` and at HuggingFace
`callensxavier/leanflow-dualscale-openfoam-nse-benchmark`. Recommended, in order:

1. Correct or withdraw the five-point "epistemic deconstruction" (§1.1) — all five points fail,
   and two are contradicted by a single line of OpenAI's Lean source.
2. Remove `4.4×10⁻³²`, the `12955.99` improvement factor, the "80% runtime" claim, and the
   `Ω ≤ 1/α′` regularity claim (§1.3).
3. Label the solver column as 2D, and drop the regularity row — or replace the solver with A1.
4. Fix the harness defects: the hardcoded `epistemic_audit_conclusion`, the `max(…, 1e-16)` clamp,
   the 32×32-vs-64×64 grid mismatch, and the internally inconsistent `33 iters -> 0`.
5. Keep and strengthen what survives: the OpenFOAM iteration measurements, the numerical-diffusion
   argument, and the Leray-projection implementation (§2.3).

---

## 4. One-line summary

The numerical report cannot be built on, but the Lean substrate underneath it is careful,
sorry-free, honestly-scoped work whose own authors warn against the extrapolation the report
makes — and the most valuable thing these assets enable is not another critique of OpenAI's
proof, but the first actual test of this project's own cutoff-law prediction, which requires a
3D solver that does not yet exist.
