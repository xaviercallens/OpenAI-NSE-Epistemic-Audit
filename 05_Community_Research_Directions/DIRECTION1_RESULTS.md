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
