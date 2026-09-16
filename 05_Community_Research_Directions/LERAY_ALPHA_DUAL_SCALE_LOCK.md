# The dual-scale lock, restated as Leray-α

**Date:** 2026-09-16 · **Status:** research note — intuition partly substantiated, formalization open
**Code:** `experiments/spectral3d.py` (`leray_alpha=`) · **Data:** `experiments/results/leray_alpha_vs_nse.json`
**Tests:** `tests/test_spectral3d.py::TestLerayAlpha` (6 cases)

## Why the pivot is right

The intuition behind the earlier "dual-scale" and T-duality drafts was that a physical fluid must
possess something that locks two scales together and so prevents unbounded gradient accumulation.
The friction those drafts met was with the vehicle, not the intuition: T-duality brings
quantum-gravity machinery that does no work in a fluid, and reviewers correctly said so.

Leray-α is the native language for the same idea, and it comes with real theorems. Instead of the
fluid transporting itself with its own velocity `u`, it is transported by a smoothed velocity:

```
∂_t u + (ū·∇)u = −∇p + νΔu,     ∇·u = 0,     ū = (1 − α²Δ)⁻¹ u   (equivalently ū − α²Δū = u)
```

Above the length `α` the filter is inert and `ū ≈ u`; below it the filter suppresses the
advecting field by `(αk)⁻²`. The two scales are locked by one parameter with units of length, and
the 3D system is **globally well-posed** — a theorem, not a conjecture
(Foias–Holm–Titi 2001; Cheskidov–Holm–Olson–Titi 2005).

## Three corrections, before this is built on

### 1. A theorem about Leray-α is not a theorem about Navier–Stokes

"The singularity is mathematically impossible" is true **in Leray-α**. It says nothing about the
Navier–Stokes equations, and in particular nothing about OpenAI's construction, which is a
Navier–Stokes solution. Global regularity of a *modified* equation does not constrain the
unmodified one. This project's v2 errata already withdrew a claim of exactly this shape
("A pathway to Statement A — Withdrawn"), and it would be easy to re-make it here without noticing,
because the new vehicle is so much more respectable than the old one. The respectability is real;
the inference is still invalid.

The correct framing: Leray-α shows that **one specific way** of locking the scales suffices to
exclude blow-up. Whether real fluids lock their scales **that way**, or at all, is a physical
question the theorem does not touch.

### 2. The test we ran was not Leray-α

The cutoff-law result in the paper (§9) was obtained with a **hyperviscous barrier**,
`ν|k|² → ν|k|² max(1, α′|k|²)`, which modifies *dissipation*. Leray-α modifies *transport*. They
are different models, conflated in earlier documents in this programme (including the v2 paper's
description of its filter as "in the Leray-α family" while applying it through a dissipation-like
estimate). The negative result of §9 therefore does not transfer to Leray-α automatically.

It does transfer in one respect, and it is worth being precise about which. The *kinematic* cutoff
law — arrest at the filter scale for a `Re ≈ 1` diffusive core, giving `t_c ~ α²/ν` and
`u_max ~ ν/α` — does not depend on the arrest mechanism, and neither does its obstruction: generic
data still does not produce a `Re ≈ 1` core. What does *not* transfer is the dissipation-balance
derivation of the arrest, since Leray-α adds no dissipation at all (below).

### 3. `α = ℓ*` is a falsifiable choice, not a representation of molecular physics

Setting the filter width to `ℓ* = ν/c_s ≈ 0.7 nm` is attractive, and it makes a checkable
prediction. It does **not** make Leray-α "a mathematically sound representation of the fluid
hitting its continuum limit." Leray-α was designed as a turbulence *closure*, with `α` placed in
the inertial range. At 0.7 nm no continuum PDE is a sound description; the physics there is kinetic
theory. Placing a filtered Navier–Stokes equation at the molecular scale and calling it a model of
molecular physics is precisely the over-extrapolation this project has spent its corrections
removing. The defensible version: *if* the continuum model is to be closed at `ℓ*`, Leray-α is a
closure with good mathematical properties, and its predictions can be compared against kinetic or
molecular-dynamics simulation. That is a hypothesis, and a good one.

## What was measured

Same solver, same Taylor–Green initial condition, `48³`, `Re = 200`, `t ∈ [0, 8]`:

| model | peak enstrophy | peak `\|ω\|` | `t` at peak | energy lost |
|---|---|---|---|---|
| Navier–Stokes | 1.285 | 10.42 | 6.07 | 55.1% |
| Leray-α, α = 0.05 | 1.237 | 10.12 | 6.30 | 54.0% |
| Leray-α, α = 0.1 | 1.127 | 9.22 | 6.61 | 50.8% |
| Leray-α, α = 0.2 | 0.907 | 6.80 | 6.96 | 43.8% |
| **Leray-α, α = 0.4** | **0.684** | **3.18** | **7.26** | **34.7%** |
| hyperviscous barrier, α′ = 0.01 | 1.211 | 9.67 | 6.07 | **55.4%** |

### The lock is real

Peak vorticity falls monotonically, **by a factor of 3.3** from `α = 0` to `α = 0.4`, and the
cascade is delayed (`t` at peak moves from 6.07 to 7.26). In the regime tested, Leray-α does exactly
what the intuition asked of a dual-scale lock: it suppresses gradient growth, continuously and
controllably in `α`.

### The lock is non-dissipative — this is the finding

As `α` increases, the flow **retains more energy**, not less: 55.1% lost for Navier–Stokes, 34.7%
for `α = 0.4`. The hyperviscous barrier does the opposite and removes slightly *more* energy than
Navier–Stokes.

These are two different kinds of lock:

* **Hyperviscosity** destroys energy that reaches small scales. It is a drain.
* **Leray-α** stops energy reaching small scales in the first place. It is a gate.

The reason is exact rather than empirical. The Leray-α nonlinearity does no work on `u`:

```
∫ u·(ū·∇)u dx = ∫ ū·∇(|u|²/2) dx = −∫ (∇·ū)|u|²/2 dx = 0,
```

because `ū` is solenoidal (the filter is radial in `k` and commutes with the Leray projector). So
inviscid Leray-α conserves `½∫|u|²` exactly — verified numerically to a drift of `−2.8×10⁻¹⁶` over
200 steps, and checked directly without time stepping in the test suite. Energy is not removed; it
is kept at scales where ordinary viscosity acts slowly, which is why more of it survives.

For the dual-scale intuition this is the more interesting of the two mechanisms. A drain is what
any viscous fluid already has. A gate that blocks *transfer* across a scale, while conserving
energy, is a genuinely distinct structural claim about how scales couple.

### Implementation checks

* **Reduces to Navier–Stokes** as `α → 0`, with the difference scaling as `α²` exactly (two
  decades per decade of `α`: `1.8×10⁻⁷`, `1.8×10⁻⁵`, `1.8×10⁻³`), as the `O(α²k²)` filter
  correction predicts.
* **Divergence form, not rotational form.** The rotational identity
  `(u·∇)u = ω×u + ∇(|u|²/2)` requires the advecting and advected fields to coincide; in Leray-α they
  do not, so the nonlinearity is computed as `∇·(ū⊗u)`. Using the rotational form here would have
  been a silent error.

## What this does not show

* Nothing about Navier–Stokes regularity (correction 1).
* Nothing at high Reynolds number: `Re = 200` at `48³`, where plain Navier–Stokes does not blow up
  either. The comparison is of magnitudes in a regime where both are regular, not of a singular
  versus a regular outcome.
* Nothing about whether real fluids behave like Leray-α at any scale.
* Nothing yet about the cutoff law in Leray-α specifically; the kinematic obstruction still applies.

## The Lean 4 path — what is actually tractable

Full 3D global well-posedness of Leray-α is a major formalization project (Sobolev spaces,
compactness, Gronwall-type arguments, and much of it not yet in Mathlib). It is not a near-term
target, and presenting partial progress toward it as a result would repeat the overclaiming
pattern the MechanicaFluidorum Lean files are careful to avoid.

Three statements are tractable now, in increasing difficulty, and each is worth having:

1. **Filter bounds.** For `α > 0` and all `k`: `0 < (1 + α²|k|²)⁻¹ ≤ 1`, with equality iff `k = 0`;
   and the high-frequency decay `(1 + α²|k|²)⁻¹ ≤ (α|k|)⁻²`. Elementary real analysis; a day.
2. **The energy identity, algebraically.** On a finite Fourier truncation, with `ū` defined by the
   filter and the solenoidal constraint as hypothesis, the nonlinear power `Σ conj(û)·N(û)` vanishes.
   This is the exact statement the test suite checks numerically, and it is the formal content of
   "the lock is a gate, not a drain." Finite-dimensional, so no function-space machinery.
3. **The reduction, conditional.** On OpenAI's own `VelocityField`: *if* a Leray-α-type bound holds
   on `[0, T)`, then not `SpeedUnboundedAtOne`, with the analytic regularity theorem entering as an
   explicitly labelled hypothesis. This connects to the actual proof objects, which nothing in the
   repository yet does — and labelling which part is assumed is the whole point.

The existing `MechanicaFluidorum/lean_src/` work is a good model for tone: its files state plainly
when they "prove no analytic content," and that honesty is what makes the rest credible.

## Where it goes next

This sharpens the paper's Direction 2. The admissibility question has three candidate forms of
increasing discrimination: a bound on vorticity **magnitude** (the current `|ω| ≲ c_s²/ν`), a bound
on **transfer** across a scale (what Leray-α enforces, and now measured as non-dissipative), and a
bound on vorticity **direction** coherence (Constantin–Fefferman). The Leray-α result places the
dual-scale intuition squarely in the middle term — which is the most distinctive of the three, and
the one this note gives the first quantitative evidence for.
