# Direction 1 — the forced-core test bed: results

**Date:** 2026-09-16 · **Status:** stage 1 complete at 32³; 96³ sweep in progress; stage 2 (axial) in progress
**Code:** `experiments/forced_core.py`, `experiments/plot_forced_core.py` · **Tests:** `tests/test_forced_core.py` (9)
**Data:** `experiments/results/forced_core_32_v3.{json,png}`

## The problem this bed solves

Every earlier test of the cutoff law (paper §9; `experiments/RESULTS.md`) failed at the same point:
generic initial data never produces a `Re ≈ 1` collapsing core, so the law's premise was never
met and its exponents were never actually tested. The remedy proposed in the paper's Direction 1
was to *manufacture* that core and sustain it with a forcing. This is that bed.

## The target, and why arrest is a clean event on it

A time-reversed Lamb–Oseen column: Gaussian vorticity `ω_z = Γ/(πℓ²) exp(−r²/ℓ²)` with fixed
circulation and core radius shrinking on the diffusive scaling `ℓ² = ντ`, `τ = T − t`. Fixed `Γ`
with `Γ = 2πν/0.638` gives `u_max·ℓ/ν = 1` exactly: **the cutoff law's premise, satisfied by
construction.** Peak vorticity is then `Γ/(πντ) ~ 1/τ` and peak velocity `~√(ν/τ)` — the
construction's own scalings.

The forcing is the residual of the target under the solver's own plain-NSE operators, evaluated at
the RK stage times. For the column `N(U)` is a pure gradient and projects to zero, so
`f = ∂ₜU − νΔU`; with `ℓ² = ντ` (a factor 4 tighter than diffusive Lamb–Oseen) the Gaussian obeys
`∂ₜω = −(ν/4)Δω`, so `f = −(5/4)νΔU` — time-reversed diffusion needs anti-diffusion.

With the barrier `ν|k|² max(1, α′|k|²)` switched on under the *same* forcing, the ratio of the
barrier's extra dissipation to the forcing's power is, by the scaling argument,
`B/F = C·α′/(ντ)`. Arrest is defined as the `B/F = 1` crossing — the argument's own definition —
not as a vorticity peak.

## Results (32³, ν = 0.01, ℓ₀ = 1.0, four values of α′)

### The control is exact

At `α′ = 0` the whole-field relative L2 error against the analytic target over the entire collapse
is **1.7×10⁻⁷**. The bed reproduces its target to discretization precision. (The 7.6% "error" in
`ω_max` is grid sampling of a Gaussian peak that falls between grid points, and is reported as
such rather than used.)

### The mechanism, measured — and the right statement about it is collapse

| quantity | value |
|---|---|
| pooled fit of `log(B/F)` vs `log(α′/ντ)`, initial transient excluded | slope **+0.85**, R² **0.94**, prefactor **C = 0.175** |
| per-run prefactor `C` across a 2.6× range of α′ | **0.188 ± 0.010 (5.2% spread)** |
| `B/F` across the four runs at a common abscissa `α′/(ντ) = 1` | 0.176, 0.198, 0.177, 0.197 — **5.6% spread** |
| per-run local slope, low → high α′ | 1.13, 0.82, 0.76, 0.56 |

**B/F is a single function of `α′/(ντ)` alone.** That collapse is the load-bearing statement, and
it was tested directly rather than inferred from one pooled R². Its consequence is exact: if
arrest (B/F = 1) happens at one fixed value `x*` of that variable, then `τ_c = α′/(νx*)`, hence
`ℓ_c ∝ √α′`, `u_c ∝ ν/√α′`, `ω_c ∝ ν/α′` — **all four predicted exponents follow from the collapse
with no assumption about the curve's slope.** Only the prefactor depends on its shape.

### The slope is 0.85, not 1, and that is physics — the wrong explanation was checked and refuted

Excluding the initial transient tightened the fit (R² 0.88 → 0.94) but pushed the slope *down*
(0.87 → 0.85 → 0.76 with more data cut), so the deficit is not an artifact. The tempting
explanation — the barrier makes the core lag the target, so it engages more slowly than the pure
law says — is **refuted**: refitting against the *measured* core size gives slope +2.4, the wrong
direction entirely. What B/F actually measures is the fraction of the *forcing's* injected Gaussian
spectrum lying above `k_α`, which is erfc-like in `α′/(ντ)`, not a power law; the falling per-run
local slopes (the curve is concave in log-log) are exactly what that predicts.

### Why no run crosses at 32³ — and why that is consistent

`C ≈ 0.18` puts the crossover at `τ_c ≈ 0.18·α′/ν`; for the largest α′ here that is `τ ≈ 11.5`,
below the resolved window floor `τ_min = 24`. The core lags the target by 63–123% at window end,
increasing monotonically with α′. The 96³ run with a 2.5-cell window reaches `α′/(ντ) ≈ 18` and
should cross for the upper half of its band — that is the direct test of the crossing exponents,
and it is running.

### A design flaw found by the figure, and fixed

The first band placed `√α′` up to `0.7ℓ₀`, so `k_α` sat *inside* the initial core's spectrum and
the barrier stripped its tail at `t = 0` — visible as a transient growth of `ℓ` and an early hook
in B/F. Fixed two ways: the default band is now capped at `√α′ ≤ 0.35ℓ₀` so the barrier starts
inert, and the fit excludes `τ > 0.7T` so a badly chosen band cannot contaminate it (the running
96³ sweep, launched with the old band, remains fully analysable from its saved series).

### Two defects caught by the tests

* A sign error in the vorticity → velocity inversion (`ψ̂ = +ω̂/k²` instead of `−ω̂/k²`). Harmless to
  the dynamics — a vortex of either sign collapses identically — but it made the core-size
  estimator read the periodization floor over the whole box (ℓ ≈ 2.6, i.e. `√⟨r²⟩` of the box).
* A core-size estimator that clipped at zero and truncated the Gaussian tail (12% low at ℓ = 1).
  Replaced by an enstrophy-weighted second moment with the periodization floor added back
  analytically; it recovers the analytic ℓ to 3%.

## Stage 2 — axial structure: the transport gates, measured against the barrier

**Code:** `experiments/forced_core_axial.py` · **Tests:** `tests/test_forced_core_axial.py` (9)
**Data:** `results/forced_core_axial_32.json`, `results/gate_leverage_vs_re.json`,
`results/gate_barrier_crossover.json`

### Setup

The swirl column plus an axisymmetric meridional cell from a Stokes streamfunction
`Ψ = W r² e^{−r²/ℓ²} sin z`, with `W = ν/(2ℓ)` so the axial peak velocity is `ν/ℓ` (axial Re = 1).
Solenoidal to 9×10⁻¹⁸ after projection. The forcing uses a central finite-difference time
derivative; two step sizes agree to 4×10⁻⁹. Control whole-field L2 error: **6.5×10⁻⁷**. The
α-model nonlinearities are no longer inert. Stated limitation: `k_z = 1`, so the axial scale does
not collapse with the core.

### Result: the gates barely touch a Re ≈ 1 collapse

Same target, same forcing, filter width matched to the barrier scale (`√α′ = α`), 32³:

| model | α | lag at window end | `dℓ/dt` vs target | meridional energy fraction (target 3.1%) |
|---|---|---|---|---|
| Leray-α | 0.25 / 0.35 / 0.50 | 0.17% / 0.23% / 0.31% | 1.00 | 3.1% |
| LANS-α | 0.25 / 0.35 / 0.50 | 0.26% / 0.32% / 0.37% | 1.00–1.01 | 3.1% |
| barrier | 0.25 / 0.35 / 0.50 | **4.8% / 19.2% / 45%** | 0.78 / 0.60 / 0.53 | 2.5% / 1.5% / **1.0%** |

### Why, measured in the right units

The first account of this result said the nonlinear term was "O(10⁻⁴) of the field scale". That
number was normalized by `|U|·k_max`, which makes every term small when ν = 0.01; it is not a
statement about the dynamics. Measured against the **forcing** instead, at `t = 0.3T` and `0.6T`:

| term, relative to the forcing | value |
|---|---|
| viscous `νΔU` | ~0.85 |
| nonlinear `P N(U)` | **0.04–0.05** |
| perturbation a gate makes (`N_α − N`), α = 0.25–0.5 | 0.014–0.027 |
| perturbation the barrier makes, same scale | 0.16–3.6 |

A Re ≈ 1 collapse is a balance between forcing and viscosity. The nonlinear term is about 5% of
it, and a transport gate can only act through that 5%. **A gate's leverage is bounded by the
nonlinear term's share, and that share is small precisely because Re ≈ 1.** The barrier acts on the
field directly, whatever sustains it, so it has 11× to 142× more leverage at the same scale.

### Leverage against Reynolds number, and the crossover

Scaling the target by λ multiplies the core Re by λ: linear terms scale as λ, the nonlinearity as
λ². This allows an exact Re scan with no time stepping (α = 0.35, `t = 0.4T`):

| Re | nonlinear / forcing | Leray gate | LANS gate | barrier | barrier / gate |
|---|---|---|---|---|---|
| 0.3 | 0.014 | 0.006 | 0.006 | 0.83 | 138 |
| 1 | 0.046 | 0.020 | 0.021 | 0.83 | 41 |
| 10 | 0.42 | 0.18 | 0.19 | 0.76 | 4.1 |
| 30 | 0.81 | 0.35 | 0.37 | 0.49 | 1.4 |
| 100 | 0.98 | 0.43 | 0.45 | 0.18 | 0.41 |
| 1000 | 1.00 | 0.44 | 0.46 | 0.018 | 0.04 |

Gate leverage grows as Re at low Re (fitted slope +1.00 — close to forced by the λ²/λ scaling, so
this is a consistency check rather than independent evidence) and saturates near 0.44. Barrier
leverage is flat at low Re and falls as 1/Re once the nonlinearity dominates the forcing.

**The crossover is an exact identity, not a fit.** Gate and barrier leverage share the same forcing
norm, which cancels in their ratio, so the Re at which they are equal is exactly
`Re_x = ‖(L_barrier − L_ν)U‖ / ‖N_α(U) − N(U)‖` — a property of the target and the filter alone.
A test pins this to ten decimal places.

**It is not universal.** Over nine configurations (three filter widths × three core sizes) it runs
from **8 to 142**, growing roughly as `(α/ℓ)^2.7`: barrier leverage rises steeply as the barrier
scale approaches the core, while gate leverage stays bounded by the filtered share of the
nonlinearity. The robust statement is that **Re_x ≫ 1 in every case measured** (minimum 8), and that
it is **largest where arrest actually happens**, as α/ℓ → 1 (142 at α/ℓ = 0.79, still rising).

### What this does to the programme's central conjecture

The programme conjectured that LANS-α with `α ≈ ℓ*` is the Lagrangian average over kinetic
fluctuations, and therefore a *derived* lock at the continuum limit. This result relocates that
conjecture rather than refuting it.

Proposition 5.1 places a `Re_r = O(1)` core at `ℓ*`, and arrest means α/ℓ → 1. That is exactly the
regime where a transport gate has two orders of magnitude less leverage than dissipation. **So
LANS-α cannot be the operative lock for an OpenAI-type collapse at ℓ*.** Transport gates are the
effective lock only for Re ≳ O(10–100), i.e. transfer-driven dynamics, which is the regime where the
cutoff law's premise fails. **Gate and cutoff law test opposite premises.**

The consistent reading gives each lock its own regime:

* **Re ≫ 1, cascades:** a transport gate (LANS-α) is the stronger lock. The derivation conjecture
  survives here, as a closure for inertial-range dynamics.
* **Re ≈ 1, the collapse at ℓ*:** of the two *model* regularizations, the drain is the stronger.

> **Correction (v5.3.0).** An earlier version of this note continued: "The drain that physics
> actually supplies there is the programme's own Lock K: collisional relaxation … the dual-scale
> lock that acts at ℓ* is kinetic and dissipative." The exact shear-mode spectrum of the BGK model
> (`experiments/lock_k_kinetic_spectrum.py`) refutes the implication that kinetic theory acts like
> the barrier. Its damping is `Γ = νk²[1 − (kλ)² + …]` — the first kinetic correction *reduces*
> damping — it never exceeds the collision rate `1/τ`, and the hydrodynamic shear mode ceases to
> exist at `kλ = √(π/2) ≈ 1.2533`. At `kλ = 1` the barrier damps 1.43× harder than kinetic theory.
> BGK collisions are dissipative in the thermodynamic sense (the H-theorem holds), but they are not
> a stronger drain on small scales.

The corrected reading: the gate-versus-drain comparison ranks two *models* against each other, and
says nothing by itself about what a real fluid does at ℓ*. What a real fluid does is neither: at a
scale fixed by the mean free path, the velocity gradient on which Navier–Stokes, the barrier and the
α-models all act stops having autonomous dynamics. The lock at ℓ* is the end of the hydrodynamic
description — which is the paper's original §5 reading, now with a mechanism rather than only a
scale. One of the programme's own experiments forced the gate-versus-drain result, and a second
forced this correction to how it was first interpreted.

### Limitations

* `k_z = 1`: the axial scale does not collapse. A collapsing `ℓ_z` needs a localized axial envelope.
* 32³, filter widths 0.25–0.5 below the window floor, so arrest `ℓ ~ α` itself is not observed for
  the gates. The leverage analysis is instantaneous and does not need the window.
* The `(α/ℓ)^2.7` trend is fitted over α/ℓ ∈ [0.28, 0.79]; the value at α/ℓ = 1 is a short
  extrapolation.

## What this bed cannot test, and stage 2

For the z-invariant column every α-model nonlinearity is a pure gradient and projects to zero
(`N_Leray`, `N_LANS` ≈ 10⁻⁷ relative, confirmed numerically). **Leray-α and LANS-α are inert on
this bed.** It tests the dissipative barrier only. Testing the transport gates — the family the
programme's central conjecture is about — needs axial structure (the construction's `ℓ_z`, `u_z`)
so that swirl–axial coupling makes `N(U) ≠ 0`. That is stage 2, in progress
(`forced_core_axial.py`).

## What this does and does not show

* It does not bear on Navier–Stokes regularity. The forced core is a manufactured solution; the
  forcing does the work of sustaining the collapse by construction, and the bed asks only whether a
  regularization can *resist* it.
* It shows, for the first time with the premise satisfied, that the barrier's engagement obeys the
  scaling argument's single-variable form. It does not yet show the crossing exponents; that needs
  the 96³ result.
* The prefactor `C ≈ 0.18` is a property of a Gaussian target's spectrum, not a universal number.

## Reproduction

```bash
cd 05_Community_Research_Directions/experiments
python3 forced_core.py --n 32 --nu 0.01 --l0 1.0 --points 4 --l-min-cells 2.5 \
        --sqrt-a-lo 0.5 --sqrt-a-hi 0.8 --tag v3      # ~3 min; reproduces the 32^3 table
python3 plot_forced_core.py results/forced_core_32_v3.json
```
