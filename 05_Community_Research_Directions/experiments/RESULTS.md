# Experimental results: the paper's open questions, tested

**Date:** 2026-09-16
**Code:** this directory. **Data:** `results/*.json`.
**Dependencies:** `dualscale_solver` (`~/xdev/SocrateAI-Numeric-DualScale-Solver`) supplies the
RK4 integrator used for cross-validation and the `DyadicShellSolver` used for the wide-range
cascade test. Nothing in that repository was modified.

> **Update (2026-09-17, v5.4.0).** The "real test" called for in §2 below — reproducing a Re ≈ 1
> collapsing core with its own forcing — has since been built and run: see
> `../DIRECTION1_RESULTS.md`. At 32³ the barrier's engagement collapses onto one variable
> `α′/(ντ)`; at 96³ no run reaches `B/F = 1` (that detector proved ill-posed), but every core
> stalls at `ℓ ≈ 1.2–1.5 √α′` with exponents `ℓ +0.42`, `u −0.43…−0.47` approaching the law —
> not yet a converged arrest. The kinetic regime beneath `ℓ*` is covered by
> `results/lock_k_kinetic_spectrum.json` (linear) and `../kinetic_lock_rs/` (nonlinear: no arrest).
> The results in this file are unchanged.
>
> **Update (v5.5.0).** Compressibility and thermodynamics on the forced core: `compressible_core.py`,
> `../THERMO_COMPRESSIBLE_LOCK_STUDY.md` (no arrest before `ℓ*` at Re ≈ 1; Mach lock 0.70 for Re ≳ 16).
> The Leray-α comparisons below remain valid as model comparisons; the reading of Leray-α at `α = ℓ*`
> as the physical continuum limit is withdrawn.

This implements the five directions proposed in `../DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md`.
The headline outcome is a **negative result on the cutoff law**, obtained cleanly enough to say
precisely what would be required to test it properly.

---

## 1. The 3D solver (`spectral3d.py`) — built and validated

No 3D spectral Navier–Stokes solver existed in either source repository; the available one is
`PseudoSpectralNavierStokes2D`, and 2D Navier–Stokes is unconditionally globally regular, so it
cannot address a 3D regularity question at all. This is that solver.

| Check | Result | Verdict |
|---|---|---|
| V1 Taylor–Green invariants | `E(0)=0.1250000000` (exact 1/8), `Ω(0)=0.3750000000` (exact 3/8) | PASS |
| V3 Energy balance `dE/dt = −ε` | max relative imbalance `7.9e-4` (dominated by the finite-difference derivative) | PASS |
| V4 IFRK4 vs `dualscale_solver`'s RK4 | relative difference `4.5e-13` after 40 steps | PASS |
| V5 Grid convergence 32³→48³→64³ | successive differences `3.2e-7`, `1.9e-9` | converging |
| V6 TGV Re=1600 dissipation peak | **`1.339e-2` at `t=9.14`** vs published **`1.25e-2` at `t=9.0`** | peak time to 1.6% |

V6 is the real benchmark. The peak *time* matches published DNS to 0.14 time units; the peak
*magnitude* is 7% high, which is the expected signature of an under-resolved spectral run
(`k_max·η = 0.25 < 1` at 64³ — a converged DNS of this case needs ~256³). Reporting the
over-prediction rather than hiding it is the point: it is diagnostic, not embarrassing.

Design choices that mattered:
* **Rotational form.** `(u·∇)u = ω×u + ∇(|u|²/2)`; the Leray projector annihilates the gradient,
  so only `ω×u` is transformed — 9 FFTs per RHS instead of 12+.
* **Integrating-factor RK4.** The barrier operator `ν|k|²·max(1, α′|k|²)` is stiff: at `α′=0.1`,
  `n=32`, explicit RK4 needs `dt < 4.7e-3`, and the constraint worsens as `α′` grows. IFRK4
  integrates the linear part exactly, leaving only the advective CFL. Without this the sweep below
  is computationally impossible.

### The `1e-32` divergence figure, settled

| Field | Relative `‖∇·u‖` |
|---|---|
| Taylor–Green | `8.1e-32` |
| Generic random solenoidal | `8.3e-17` |
| float64 epsilon | `2.2e-16` |

Same solver, same code path. The Taylor–Green figure is an artifact of that initial condition's
binary representability (few modes, power-of-two coefficients, so `k·u` cancels exactly in
binary), **not** a property of the method. The generic-field number is the method's actual
divergence floor and is ordinary float64. A previously published benchmark in this program
reported the `1e-32` figure as "exact machine zero" evidence of a superior method; it is not.

---

## 2. The cutoff law — tested, and **not** confirmed

### Is the law wrong, or is its premise unreachable?

This distinction decides how the result reads, so it was settled explicitly
(`analyse_cutoff_law.py`, part A) rather than asserted.

**The law is arithmetically exact given its premise.** Granting a core on the diffusive scaling
(`Re_core = 1`), the arrest condition follows from the barrier operator itself rather than by
assumption: `ν k² max(1, α′k²)` exceeds the plain viscous rate at the core's own wavenumber exactly
when `ℓ_r < √α′`. Substituting back reproduces all four exponents **as identities to machine
precision**:

| | `t_c` | `u_max` | `ω_max` | `ℓ_arrest` |
|---|---|---|---|---|
| computed | `+1.000000` | `−0.500000` | `−1.000000` | `+0.500000` |
| predicted | `+1.0` | `−0.5` | `−1.0` | `+0.5` |

So the experimental disagreement below is a statement about the **premise**, not about the law's
arithmetic. That is the difference between "this hypothesis is wrong" and "this hypothesis is
untestable with generic data" — and it is the latter.

### What was predicted

The flagship paper states as an untested hypothesis that a regularization arresting the collapse
at `ℓ_r ~ √α′` gives, via the diffusive core scaling `ℓ_r ≃ √(νt)`, `u ≃ √(ν/t)`:

```
t_c ~ α′/ν      u_max ~ ν/√α′      ω_max ~ ν/α′      ℓ_arrest ~ √α′
```

### Result (dyadic shell model, 3.6 decades in α′)

| Quantity | Predicted exponent | Fitted | 95% CI | R² | Consistent |
|---|---|---|---|---|---|
| `ω_max(α′)` | −1.00 | **−0.192** | [−0.22, −0.17] | 0.978 | **No** |
| `u(k_α)` | −0.50 | **+0.173** | [+0.16, +0.19] | 0.991 | **No** (wrong sign) |

These are tight fits over 3.6 decades, so this is a refutation, not noise.

### Why — the diagnosis is the useful part

Re-expressed in the barrier wavenumber `k_α = α′^(−1/2)`, the measured velocity scaling is

```
u(k_α) ~ k_α^(−0.345)      versus   Kolmogorov inertial range  k^(−1/3) = k^(−0.333)
                            versus   cutoff law  u ~ ν k_α = k_α^(+1)
```

**Agreement with Kolmogorov to 3.5%; disagreement with the cutoff law by a factor of 1200** at the
largest scale tested. The local Reynolds number at the arrest scale confirms it directly:

| `k_α` | 128 | 256 | 512 | 1024 | 2048 | 4096 | 8192 |
|---|---|---|---|---|---|---|---|
| `Re_a = u/(ν k_α)` | 1207 | 494 | 202 | 78 | 28 | 11 | **4.9** |

The cutoff law is a statement about a **Re ≈ 1, viscously-dominated collapsing core** — the special
property of the OpenAI construction. A forced cascade (or decaying turbulence) puts the arrest
scale in an **inertial range with Re ≫ 1**, where inertial-range scaling wins and the law's
premise simply does not hold. The exponents were never going to match, and this measures by how
much.

Note the trend: `Re_a` falls monotonically toward O(1) as `k_α` approaches the Kolmogorov scale.
So the cutoff-law regime is approached only as `√α′ → η` — at which point the barrier acts at the
same scale as ordinary viscosity and `α′` is no longer an independent parameter. **That is the
sharp form of the negative result:** for `√α′ ≫ η` inertial-range scaling dominates, and at
`√α′ ~ η` the barrier is redundant with viscosity.

### The 3D DNS resolution constraint, derived

The same test in the 3D DNS is bounded by a hard constraint. The barrier caps vorticity at
`ω_cap = ν/α′ = ν k_α²`, and `k_α` must stay inside the resolved band, so the largest achievable
cap is `ν k_max²` with `k_max = n/3`. Requiring the barrier to arrest a *growing* vorticity rather
than merely damp the initial field (`ω_cap > ω_0`) gives

```
    n  >  3 √(ω_0 · Re)
```

For the Taylor–Green vortex (`ω_0 = 2`): **n > 85 at Re=400, n > 170 at Re=1600.** This is exactly
why earlier 64³ attempts in this program saw max enstrophy move by 0.02% across five decades of
`α′` — the barrier was never engaged at all.

The completed 96³ run at Re=200 shows the squeeze is two-sided, and tighter than the resolution
constraint alone suggests. The band needs `√(ω_0/ν) < k_α < min(k_η, n/3)`; here the lower edge is
`20.0` while the **measured** `k_η = 17.6`, so the band is **empty** and no placement of the
barrier can work. All six runs excluded themselves — four with "viscosity bites first", two with
"dissipation does not peak at the barrier" — and `ω_max` varied by only **3.06%** across the whole
sweep, the quantitative signature of an inert barrier. The controls did their job: not one run
produced a number that could have been mistaken for a result.

A first 32³ run also correctly self-reported `Re_core = 1362` and flagged
**"premise DOES NOT HOLD → the exponent fits do not constitute a test of the law."**

### What would constitute a real test

Reproduce the construction's own viscously-dominated core, which requires its forcing. The law
cannot be tested with generic initial data at any resolution, because generic initial data does
not produce a Re ≈ 1 collapsing core. That is a sharper statement of the open question than the
paper currently makes, and it should replace the current phrasing.

---

## 3. Thermal noise — implemented and calibrated

Landau–Lifshitz fluctuating hydrodynamics, with the prefactor **verified rather than assumed**:

| Check | Expected | Measured | Verdict |
|---|---|---|---|
| FDT1 equipartition (per-mode energy flat in k) | spread ≈ 0 | **0.233** | PASS |
| FDT2 equilibrium energy vs temperature | log-log slope 1.00 | **1.000** | PASS |

Both can fail, and a wrong prefactor would fail them. Only after they pass is the noise
thermodynamically meaningful.

**First probe of Q2.** A seeded pulse at `k=8` with amplitude `1e-3` on a Taylor–Green background:

| | shell energy |
|---|---|
| pulse, no noise, final | `4.1e-5` |
| thermal floor in the same shell | `6.0e-3` |

The pulse ends up **~150× below the thermal floor** — buried. This is a modest result and is
labelled as such in the code: it is not the OpenAI pulses, which are phase-coherent and
shear-amplified by a specific arrangement. It establishes the measurement method and one data
point, not an answer to Q2.

---

## 4. Runtime model-validity monitor — implemented

Instruments any run with the paper's local admissibility bound `|ω| ≲ c_s²/ν` (equivalently
`Ma ≲ 1` and `Kn ≲ 1`): water `2.25e12 s⁻¹`, air `7.54e9 s⁻¹`.

The same simulation, interpreted at two physical scales:

| Interpretation | worst Ma | worst Kn | worst `|ω|`/bound | admissible |
|---|---|---|---|---|
| 1 m/s over 1 cm (laboratory) | `6.7e-4` | `5.1e-8` | `1.6e-10` | yes |
| 300 m/s over 10 nm (extreme) | `0.20` | `5.1e-2` | `4.7e-2` | yes, but 8 orders closer |

The numerics are byte-identical in both rows; only the physical interpretation differs. That is
the point — **model validity is not a property of the discretization**, and a solver can be
perfectly stable while describing a state no real fluid can occupy. This is the honest form of the
"deploy a regularization in LES" recommendation: not a regularization that hides the excursion,
but a diagnostic that reports it.

---

## 5. Riccati threshold — coincidence, with a better finding alongside

Full working in `../RICCATI_THRESHOLD_CHECK.md`.

**Verdict: coincidence.** The `α` in `DyadicRiccati.lean` is the model's *dissipation index*, not
a temporal exponent. The comparable quantity is `ρ(α) = 3 − 1/α`; the file's threshold `α ≥ 1/2`
is `ρ ≥ 1`, whereas our enstrophy exponent is `ρ = 1/2 + 3h ≈ 0.515`. Matching would need
`h = 1/6`, and the construction requires `h < 1/100`.

**But the check found an exact correspondence worth more than the one asked about.** The Lean file
contains `example : rhoExp (2/5) = 1/2`, and `α = 2/5` is the value its source singles out as
carrying *the same enstrophy estimate as 3D Navier–Stokes*. Our enstrophy exponent at `h → 0` is
exactly `1/2`. At that `α`, the Riccati is `Ω′ ≲ Ω³` with saturating rate `Ω ~ τ^(−1/2)` — i.e.
**the construction blows up at precisely the rate that saturates the NSE-critical dyadic
estimate**, with `h > 0` the small excess.

Two cautions, both recorded: it is a numerical agreement and not a theorem (the shell model's
single length scale versus `ℓ_r ≠ ℓ_z` actively obstructs a derivation), and it is *independent*
of the known ESS marginality, which pulls the opposite way — `h → 0` makes the construction
exactly Riccati-critical but makes it **fail** ESS.

Also confirmed: `S² ≤ 2Ω³` is super-linear and therefore *permits* Riccati blowup. It cannot be
cited as an enstrophy ceiling, and the benchmark report that did so inverted its content.

---

## Reproduction

```bash
cd 05_Community_Research_Directions/experiments
python3 validate_tgv3d.py                 # V1-V6, ~1 min + TGV benchmark
python3 shell_cutoff_law.py --n-shells 22 --nu 1e-6 --points 8 \
        --shell-lo 7 --shell-hi 15 --t-end 30 --dt 5e-4
python3 noise_and_monitor.py              # FDT checks + monitor demo
python3 sweep_cutoff_law.py --n 96 --nu 5e-3 --ic tgv --points 6 \
        --t-end 7 --k-lo 14 --k-hi 30     # slow; thin band by construction
```

All verdicts in the JSON outputs are computed from the runs. None are hardcoded — a defect class
this project has had to fix twice before.

## What none of this shows

* Nothing here bears on whether the OpenAI proof is correct. It is correct.
* The shell-model result is not a Navier–Stokes result. A shell model has no geometry, no vortex
  stretching in the real sense, and one scalar per octave.
* The 3D DNS runs are at modest Reynolds number and do not resolve a Kolmogorov-scale cascade.
* The Q2 pulse probe is not the construction's pulses.
* Nothing here tests the codimension question, which needs eigenvalue analysis in similarity
  variables rather than forward integration.
