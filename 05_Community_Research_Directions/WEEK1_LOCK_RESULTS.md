# Dual-scale lock programme — week 1 results

**Date:** 2026-09-16 · **Plan:** `DUAL_SCALE_LOCK_PROGRAMME.md` §5, "this week" items 1–4
**Code:** `experiments/spectral3d.py` (`alpha_model="lans"`), `experiments/shell_mach_cap.py`,
`experiments/lock_f_coherence.py`, `03_Lean4_Topological_Censorship/src/{CoreScaling,LerayAlphaFilter}.lean`
**Data:** `experiments/results/{lans_vs_leray_vs_nse,shell_mach_cap,lock_f_coherence}.json`

Four items were planned. Three produced positive, verified results; one produced an honest null
that redirects the work. Every verdict below is computed from the runs; none is asserted.

---

## 1. LANS-α implemented — the derivable member of the family

LANS-α (`∂_t v − u×(∇×v) + ∇π = νΔv`, `v = (1−α²Δ)u`) is the α-model obtained by Lagrangian
averaging, and therefore the one the programme conjectures could be *derived* from kinetic
fluctuations. Its invariant is the α-energy `½∫u·v`, not `½∫|u|²`.

**Verification.** Reduces to Navier–Stokes as `α→0` with the `O(α²)` scaling the filter predicts
(`1.9×10⁻⁷`, `1.9×10⁻⁵`, `1.9×10⁻³` at `α = 10⁻⁴, 10⁻³, 10⁻²`). Inviscid α-energy drift over
200 steps: `−2.6×10⁻¹⁶`; plain energy drifts by `2.7×10⁻⁴` in the same run — as it must, since it
is not the invariant. The pointwise identity `u·((∇×v)×u) = 0` is checked directly without time
stepping. Solenoidal to `2.4×10⁻¹⁷`. Five new tests.

**Three-way comparison** (Taylor–Green, `48³`, `Re = 200`, `t ∈ [0,8]`):

| model | peak `\|ω\|` | `t` at peak | own invariant lost | sub-α slope |
|---|---|---|---|---|
| Navier–Stokes | 10.42 | 5.69 | 55.1% (energy) | −5.7 |
| Leray-α, α=0.2 | 6.80 | 8.00 | 43.8% (energy) | −4.8 |
| **LANS-α, α=0.2** | **4.31** | 7.49 | 42.5% (α-energy) | −8.2 |
| Leray-α, α=0.4 | 3.18 | 8.00 | 34.7% (energy) | −5.3 |
| **LANS-α, α=0.4** | **2.48** | 8.00 | 35.6% (α-energy) | −7.2 |

Two findings. **LANS-α gates harder than Leray-α** at equal `α` (peak vorticity 2.48 vs 3.18 at
`α = 0.4`), while dissipating a comparable fraction of *its own* invariant — the gate-not-drain
character of the family holds for the derivable member too. And **the Graham et al. sub-α pileup
(`k⁺¹` "rigid bodies") is not seen**: sub-α slopes are steeply negative for every model. This is not
a refutation. At `Re = 200` there is no inertial range for `α` to sit inside, so the sub-α band is
simply viscosity-dominated and emptied; the pileup is a high-`Re`, α-in-the-inertial-range
phenomenon and remains **untested here**. Comparing Leray-α's α-energy loss (−3% at α=0.4, i.e. a
gain) to LANS-α's is meaningless, since α-energy is not Leray-α's invariant; each model is scored on
its own conserved quantity in the table.

## 2. Mach cap in the shell model — one cap, opposite ends

The cheapest Lock C: a phenomenological velocity saturation `s(u_n) = max(0, 1 − (u_n/c_s)²)` on
the nonlinear transfer into each shell (hard-zero form chosen so a forced shell cannot creep past
`c_s`). Reduces bit-identically to the base `DyadicShellSolver` at `c_s = ∞`.

**Forced cascade** (ν=10⁻⁶, 22 shells): uncapped `u ~ k^−0.334` over shells 2–10 — Kolmogorov
`−1/3` to 0.3%. Sweeping `c_s` from 0.05 to 10⁴: the maximum-Mach shell is **shell 0 in every run**,
and wherever the cap engages it engages at shell 0 first. In a cascade the Mach lock is a
**large-scale** constraint: it pins the forcing-scale velocity to `c_s` and leaves the small scales
to follow Kolmogorov downward.

**Imposed Re = 1 collapse** (arithmetic, not simulation): the `Ma = 1` crossing of
`u = √(ν/t)` lands at `ℓ/ℓ* = 1.000`, `t/t* = 1.000` for both water and air — reproducing
Proposition 5.1's `ℓ* = ν/c_s` to machine precision. On a collapse the same cap engages at the
**smallest** scale.

Computed verdict `same_cap_opposite_ends = True`. This is the shell-model version of §9's
conclusion: compressibility only locks a *collapsing* core, and generic cascades never present one.
Caveat carried in the JSON: velocity saturation only; no pressure, density, or acoustics.

## 3. Lock F coherent packet — an honest null that redirects

The programme's criterion is `σ·τ_decoh ≫ 1`: shear amplification against noise-driven
decoherence. A phase-definite single-mode packet (energy `10⁻⁴` of background) was seeded on
Taylor–Green at `32³`, `ν = 5×10⁻³`, with an 8-member noise ensemble at the FDT-calibrated
`θ = 2×10⁻⁵`.

**No amplification exists to compete with.** `σ` is negative for every orientation tried —
generic `k=(6,4,2)`: `−2.49`; strain-aligned `k=(0,7,0)`: `−1.49` (`R²=0.95`); the
extension-aligned case is identical by the TGV `x↔y` symmetry. Decay is ~6× faster than `νk²`
alone, because a fixed-`k` amplitude leaks by scattering to `k±(1,1,1)`. **A global plane wave on a
Taylor–Green background is not a shear-amplified pulse**, and the rate competition the criterion
describes cannot occur in this configuration. Computed verdict: *criterion moot for this
packet/background.*

**`τ_decoh` is unconstrained** (`1.90`, bootstrap 95% CI `[0.55, 15.0]`, fit `R² = 0.05`): the
packet sits at 0.23 of the thermal floor in its own mode from `t = 0`, so the coherent fraction
collapses immediately and then fluctuates — algebraic decay, as additive noise predicts, not
exponential. Controls behaved: `θ = 0` preserves coherence to `5.6×10⁻¹⁶` (asserted in tests);
doubling `θ` shortens `τ` by 0.78× (diffusive expectation 0.5; direction right, magnitude
unconstrained by a fit this poor).

**What this fixes for next time.** (i) The measurement needs a *localized* packet in a *locally
strained* region — which is exactly the Direction 1 forced-core test bed; Lock F is now formally
blocked on it, as the programme's dependency table already said. (ii) The packet must start at or
above the thermal floor for a fair `τ`. (iii) The exponential fit should be replaced by the
additive-noise form `f = |p|²/(|p|² + σ_n²t)`. All three are recorded in the script and JSON.

## 4. Lean 4 — two files, seventeen theorems, three axioms

Both in `03_Lean4_Topological_Censorship/src/`, compiled with `lake env lean` against mathlib
v4.34.0-rc2; every theorem's `#print axioms` is exactly `[propext, Classical.choice, Quot.sound]`.
Independently re-verified: zero `sorryAx` in the compile output (the one grep hit for "sorry" in
each file is the docstring sentence stating there is none — the same prose false-positive this
project's own audit tooling was fixed for).

**`CoreScaling.lean`** — Proposition 5.1 as a formal theorem about the construction's own scalings.
From `ℓ t = √(νt)`, `u t = √(ν/t)`: `Re_core` (= 1 exactly), `mach_time`/`mach_radius`,
`knudsen_time`, `heating` (Eckert = 1: `ε·t/c_p = u²/c_p`), and `one_scale` — at `t* = ν/c²`,
`ℓ = ℓ*`, `Ma = 1`, and with the kinetic relation `ν = ½c̄λ`, `c̄ = c` as explicit hypotheses,
`Kn = 2`. The docstring says what it should: the coincidence of the three limits at `ℓ*` *is* this
equality chain and nothing deeper. It is the first Lean statement in this repository that is about
the construction's scalings rather than about a free-standing toy.

**`LerayAlphaFilter.lean`** — `φ α k = 1/(1+α²k²)`: positive, `≤ 1`, `= 1 ↔ k = 0`, high-frequency
decay `≤ 1/(α²k²)`, even, antitone on `k ≥ 0`, and `φ² ≤ φ`. These are the only facts about the
filter a formalization of "the lock is a gate" needs, and they say nothing about well-posedness —
the docstring says so.

One thing worth keeping: the first compile of both files failed with `invalid 'import' command`
because the module docstring preceded the imports — precisely the defect the v2 errata records for
the earlier "kernel-verified" drafts. The convention is now fixed in these files.

---

## Where this leaves the programme

| lock | week-1 status |
|---|---|
| K kinetic | anchor confirmed (`ℓ*/λ = 0.67` derived and measured); DSMC not started *(see update below)* |
| C compressibility | shell-model version done; large-scale in cascades, `ℓ*` on collapse |
| T thermodynamic | unchanged (paper §5) |
| F fluctuation | **blocked on Direction 1**: needs a localized packet in local strain |
| A α-model | LANS-α implemented and verified; gates harder than Leray-α; Graham pileup untested |
| G geometric | not started |

The single most valuable next step is unchanged and now over-determined: **the forced-core test bed
(Direction 1)**. Lock A's derivation conjecture, Lock C's collapse regime, and Lock F's rate
competition all require a `Re ≈ 1` collapsing core that generic data does not supply. Three of six
locks are waiting on the same object.

> **Update (2026-09-17, v5.4.0).** Since week 1: the forced-core bed was built (`DIRECTION1_RESULTS.md`;
> 96³ cores stall near `√α′`, not yet converged). **Lock K** was tested twice: the exact linear BGK
> spectrum shows a *termination* at `kλ = √(π/2)` with damping below viscous (v5.3.0), and a nonlinear
> Rust discrete-velocity BGK simulation of the forced collapse (`kinetic_lock_rs/`, used instead of
> DSMC or lattice-Boltzmann) finds **no arrest** at that scale — a null result for Lock K as an arrest
> mechanism. The magnitude-based admissibility bound is now formal on OpenAI's own objects and
> unconditional (`OpenAIAdmissibility.lean`); **Lock G** (Constantin–Fefferman direction coherence)
> is still not started.
> Current status of every link: `DUAL_SCALE_LOCK_PROGRAMME.md` §8.

## Tests

`python3 -m pytest tests/ -q` — includes 5 new LANS-α, 5 Mach-cap, and 3 Lock-F cases.
