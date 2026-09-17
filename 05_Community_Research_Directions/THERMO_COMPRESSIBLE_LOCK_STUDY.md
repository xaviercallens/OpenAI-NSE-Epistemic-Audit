# Compressibility, thermodynamics and the regime map — what stops a driven core, if anything does

**Date:** 2026-09-17 · **Status:** complete for the 1D continuum model; kinetic cross-check limited to Re ≤ 3, isothermal
**Code:** `experiments/compressible_core.py`, `compressible_core_study.py`, `compressible_core_re_sweep.py`,
`plot_compressible_core.py`; `kinetic_lock_rs` (`--tau-law inv-rho`, `--force per-volume`)
**Tests:** `tests/test_compressible_core.py` (8) · **Lean:** `BlowupRegimeMap.lean` (13), `LerayAlphaLinearization.lean` (4)
**Data:** `experiments/results/compressible_core_{study,re_sweep}.json`, `compressible_core.png`; `kinetic_lock_rs/runs/gas_*.json`

## 0. Where this starts

`DUAL_SCALE_LOCK_PROGRAMME.md` §8 ended with: the kinetic cutoff does not arrest a driven core; if anything
does, it is compressibility or thermodynamics; the kinetic solver was isothermal and could not say. Two
things were wrong with even that cautious sentence, and this study corrects both.

1. The kinetic null result excluded more than thermodynamics. The Rust solver used a **constant collision
   time**, which makes `μ ∝ ρ` and hence `ν` constant. A real gas has `τ ∝ 1/ρ`: dynamic viscosity
   independent of density, so `ν = μ/ρ` rises as the core evacuates. The main compressible feedback was
   switched off by construction.
2. "What stops a core at ℓ*" is the right question on one route to a singularity only (§1).

## 1. Rereading Tao and the human Euler proof: a regime map

For a feature of velocity `u` and size `ℓ`: `Re = uℓ/ν`, `Ma = u/c`, `Kn = ℓ*/ℓ`. Identically
**`Kn = Ma/Re`** (von Kármán), and the paper's admissibility bound `u/ℓ ≤ c²/ν` is **`Ma² ≤ Re`**.

| route | example | path in (Re, Ma) | first assumption to fail | at scale |
|---|---|---|---|---|
| diffusive | OpenAI NSE construction, `Re_r = O(1)` | `Re ≈ 1`, `Ma → ∞` | compressibility **and** rarefaction together | `ℓ*` |
| inertial | Tao 2016 averaged NSE: each stage `(1+ε₀)` smaller, `(1+ε₀)^{5/2}` faster, dissipation "negligible" ⇒ `u ~ ℓ^{-3/2}`, `Re ~ ℓ^{-1/2} → ∞` | `Re → ∞`, `Ma → ∞` | incompressibility, inside the continuum (`Kn = 1/Re`) | `Re·ℓ* ≫ ℓ*` |
| bounded velocity | forced Euler, smooth force (cims.nyu.edu/~tristanb/euler.pdf): `sup(‖Γ‖∞+‖u_r‖∞+‖u_z‖∞) < ∞`, `‖ω‖∞ → ∞` — "amplitudes can be small while their spatial derivatives increase" | `Ma` bounded, `ℓ → 0` so `Re → 0` | neglected viscosity | `ℓ*/Ma > ℓ*` |

So Proposition 5.1 of the paper (one scale, three limits) is the statement `Re = 1 ⇒ Kn = Ma`: a property of
the diffusive route, not of blow-up in general. All of this is proved in `BlowupRegimeMap.lean`.

Two further points from Tao's paper. His mechanism must be **"noise-tolerant"** to be realized in a fluid —
that is Lock F / Direction 3, in his words. And his theorem says the energy identity plus harmonic analysis
cannot exclude blow-up, so a regularization that *works* (hyperdissipation with exponent ≥ 5/4, Leray-α)
works by changing the equation at small scales, not by structure the equation already has.

## 2. The experiment

The forced-core target (time-reversed Lamb–Oseen column, `ℓ² = ντ`, forcing = residual of the
*incompressible constant-ν* equations, as OpenAI's force is built for that model) applied to an
axisymmetric compressible Navier–Stokes–Fourier fluid, 1D in radius, with the physics switched on one
piece at a time: viscosity law (`μ ∝ ρ` | `μ` const | `μ ∝ T^0.76`), thermodynamics (isothermal | full
energy equation, Pr 0.71, γ 1.4 | no viscous heating), force convention (per mass | per volume).
Units `ℓ* = c = 1`; target Mach number `Re/ℓ`.

Gates: low-Mach control tracks to **1.3×10⁻⁴**; RHS reproduces the analytic target tendency; axis
operator exact to 2×10⁻⁵ (a 50% first-node error was found by the tests and fixed — results unchanged to
three digits); mass drift ≤ 7×10⁻⁵; **grid-converged** (n = 400/800 and 500/1000 agree to three digits).
The exact hole law `ln(ρ₀/ρ∞) = −(ln 2/0.638²) Ma² = −1.702 Ma²` was derived and the integral checked
(`= ln 2` to 10⁻¹⁵).

## 3. Results

### 3.1 A prediction that failed

Quasi-steady reasoning (hole law + the force's anti-diffusion `(5/4)ν` overtaken when `ν/ρ̂ > (5/4)ν`)
predicted arrest at `Ma = 0.36`, `ℓ_c = 2.76 Re ℓ*`. **No run arrests.** At `Re ≈ 1` the hole cannot form
fast enough: evacuating it quasi-steadily needs a radial outflow `u_r/c ≈ 1.7 Ma³/Re`, supersonic by
`Ma ≈ 0.8`. The collapse outruns its own compressible response. The prediction is kept here because its
failure is the explanation of why the diffusive route is special.

### 3.2 Re = 1 (the OpenAI route), target driven to Ma = 2

| model | lag in core size | core state |
|---|---|---|
| A · isothermal, ν const (continuum twin of constant-τ BGK) | **−5%** (ahead) | ρ₀ = 0.28 |
| B · isothermal, real-gas μ, force/mass | +14% | ρ₀ = 0.45 |
| C · as B, force/volume | −1.6% | ρ₀ = 0.28 |
| D · air, energy equation, μ(T), force/mass | **+25%** | T₀ = 1.44, ρ₀ = 0.47 |
| F · as D without viscous heating | +14% | T₀ = 0.96 (expansion cooling) |
| G · energy equation, μ fixed | +14% | T₀ = 1.49 |
| H · energy equation, ν const | −5.6% | T₀ = 1.64 |

Reading: heat acts on the collapse **only through the viscosity law** (D vs G, H); compressibility acts
through the density hole and its sign depends on the force convention (B vs C). Nothing arrests. A also
decomposes the kinetic result: of the constant-τ BGK core's 11–12% lead, about 5% is compressible and the
rest kinetic (Burnett).

### 3.3 The Mach lock (the positive result)

Peak **local** Mach number when the incompressible target has reached Ma = 4:

| model | Re 0.25 | 1 | 4 | 16 | 64 |
|---|---|---|---|---|---|
| ν const, isothermal, force/mass | 3.88 | 3.16 | 2.11 | 1.91 | 1.90 |
| real-gas μ, isothermal, force/volume | 4.16 | 4.66 | 4.95 | 4.98 | 4.98 |
| real-gas μ, isothermal, force/mass | 3.37 | 1.97 | 1.20 | 1.10 | 1.11 |
| **air, full thermodynamics, force/mass** | 1.11 | 0.92 | 0.74 | **0.70** | **0.70** |

Driving the target on to Ma = 8 (Re = 16): air stays at **0.70** (0.700 → 0.701); the isothermal real gas
creeps 1.10 → 1.22. With the energy equation the lock also survives the other force convention: air,
force/volume, Re = 16 gives **0.81**, where the isothermal per-volume case runs away to 4.98 and evacuates
its core to `ρ₀ = 10⁻⁴` (local Kn ≈ 670).

What the air core does instead of accelerating (Re = 16, target Ma 0.5 → 1 → 2 → 4 → 8):
local Ma 0.41 → 0.59 → 0.68 → 0.70 → 0.70; `T₀` 1.02 → 1.10 → 1.29 → 1.58 → 2.03; `ρ₀` 0.65 → 0.38 →
0.22 → 0.15 → 0.12; `ν₀/ν∞` 1.6 → 2.9 → 5.6 → 9.6 → 14.7; core size / target 1.08 → 1.22 → 1.54 → 2.15 →
3.04. The work of the force goes into heat and into evacuating the core; the hot, thin core is viscous and
fast-sounding, and the swirl Mach number stops rising. The velocity itself still creeps up, as `0.70·c(T₀)`
(`u/c∞` 0.88 → 1.00): **this is a lock on the Mach number, not a bound on velocity and not an arrest of the
core size** (collapse rate 0.24 against the unimpeded 0.50).

Measured by the way: the paper's heating estimate `ΔT ≈ u²/c_p` is an upper-order estimate; the measured
coefficient is 0.35 at Ma ≈ 0.4, 0.7 at Ma ≈ 0.7 and ≈ 1 near Ma ≈ 1.

### 3.4 Kinetic cross-check (Rust BGK, 2D, isothermal, λ = 0.065, N = 144, valid for ℓ ≳ 1.5λ)

`τ ∝ 1/ρ` versus constant τ, per-mass force. Same direction as the continuum runs, small at the Reynolds
numbers the grid allows: at Re = 3, target Ma 0.75: peak Ma **0.72 vs 0.77** (near the edge of the solver's validated Mach range; at target Ma 2 it is 1.66 vs 1.85, outside that range, negative populations 1.5×10⁻⁴), core-size lag −4% vs −8% (both still ahead of the target); at Re = 1 the two
are indistinguishable (Ma 0.92 vs 0.95 at target 0.67) and both cores remain ahead of the target. The BGK
gas is isothermal, so it has no energy-equation lock to show, and Re ≥ 4 is out of its resolvable range.
**The thermal kinetic test (BGK with temperature, or DSMC) remains undone** and is the next experiment.

## 4. What this does and does not establish

* On the **diffusive route** (`Re ≈ 1`, OpenAI's), neither compressibility nor heat arrests the driven
  core before `ℓ*`; they slow it (14–25% at 0.5 ℓ*), and the state they produce there has local Knudsen
  number 4–8, i.e. is outside the model that produced it. This agrees with, and gives numbers to, the
  paper's position: on this route the description ends; nothing locks.
* On the **inertial route** (`Re ≳ 16`), within the validity of the compressible continuum model
  (local Kn 0.25 at Re = 64), a real gas with an energy equation **does not follow a driven swirl past
  Ma ≈ 0.7**. This is the first positive "lock" result of the programme, and it is thermodynamic: it
  needs the energy equation to be robust.
* It is a statement about an **open-loop force built for the incompressible model**. A force designed
  knowing the gas law could do better; but it would have to grow without bound, which OpenAI's does not
  (theirs is smooth up to the blow-up time and seeds, rather than drives, the collapse — so this bed is
  harsher than the construction in that respect and different in mechanism).
* It is **not** a regularity statement. The compressible Navier–Stokes equations have their own proved
  finite-time singularities (implosions: Merle–Raphaël–Rodnianski–Szeftel; Buckmaster–Cao-Labora–
  Gómez-Serrano). Each model in the hierarchy hands its breakdown to the next: incompressible →
  compressible NSF → Boltzmann (open) → particles. Only the last carries an unconditional bound
  (`|v| ≤ √(2E/m)`, `atomistic_speed_bound`), and no continuum or kinetic equation inherits it.
* Limits: axisymmetric, z-invariant (no 3D instability, no axial flow); ideal gas with constant γ and Pr,
  Stokes hypothesis; T₀ reaches 2–5 T∞ in the extreme runs, beyond constant-γ air. Liquids are a
  different problem: there the first thermodynamic event is **cavitation**, and with the exact Lamb–Oseen
  pressure coefficient (`Δp = 1.702 ρu²`, not `ρu²/2`) it arrives at `u ≈ 7.6 m/s`, `ℓ ≈ 130 nm`,
  `t ≈ 17 ns` before blow-up for water at 1 atm (the paper's 14 m/s, 70 nm, 5 ns used `ρu²/2`). A
  hollow-core vortex then caps the swirl at `u ≈ √(2Δp/ρ) ≈ 14 m/s`. That is an estimate, not a
  simulation; a barotropic cavitating version of `compressible_core.py` is the natural follow-up.

## 5. The Leray-α anchor claim, formally re-examined

The claim: *(i) dual scale* — `ū = (1−α²Δ)⁻¹u`; *(ii) lock* — 3D Leray-α is globally regular, "the singularity
is mathematically impossible"; *(iii) physical anchor* — with `α = ℓ*` Leray-α is "a mathematically sound
representation of the fluid hitting its continuum limit".

(i) is a correct description of a model. (ii) is a correct theorem about a **different equation**, obtained
by leaving the supercritical class (two derivatives gained), which in the light of Tao's barrier is the
only way such a theorem could be obtained; on a Re ≈ 1 forced collapse the filter moves the core size by
0.2–0.4%, and on the swirl column it is exactly inert. **(iii) is false**, for four reasons:

1. **α is absent from the linear dynamics** (`LerayAlphaLinearization.lean`): for any bounded bilinear `B`
   and bounded linear filter `F`, `u ↦ B(Fu, u)` has zero derivative at rest, so Leray-α, LANS-α and
   Navier–Stokes share the linearization `νΔ` for every α. The gas relaxes at `νk²[1−(kλ)²+…] ≤ 1/τ` and
   not at all beyond `kλ = √(π/2)`; `νk²` exceeds any cap (`viscous_rate_exceeds_any_cap`). No α reconciles
   them.
2. It regularizes in the wrong direction: it removes small-scale transport and keeps small-scale damping;
   kinetic theory keeps transport and *reduces* damping.
3. At `ℓ*` the Mach, Knudsen and Eckert numbers are all order one; an incompressible, isothermal, Newtonian
   model represents none of them. §3 shows what two of them actually do.
4. `ℓ*` is the relevant scale on one route only (§1); on the others a filter at `ℓ*` sits below the scale
   where the model has already failed.

What survives of the dual-scale intuition is `Kn = Ma/Re`: every blow-up scenario has two scales, the
flow's and the molecules', and their ratio decides which physics arrives first. The "lock" is route-
dependent — termination of the description (diffusive), a thermodynamic Mach lock (inertial), plain
viscosity (bounded velocity) — and is a property of the fluid, not of a filter added to the equations.

## 6. Next

1. Thermal kinetic test: BGK with a temperature-dependent Maxwellian (or DSMC) on the forced core —
   does the Mach lock persist when the continuum closure is removed?
2. Energy budget of the locked core: fraction of the force's work going to heat vs kinetic energy.
3. Barotropic cavitating liquid core.
4. 3D: azimuthal stability of the hot evacuated core.

## Reproduce

```bash
cd 05_Community_Research_Directions/experiments
python3 compressible_core_study.py        # physics ladder, ~10 min on 6 cores
python3 compressible_core_re_sweep.py     # Reynolds sweep + convergence, ~40 min
python3 plot_compressible_core.py
cd ../kinetic_lock_rs && sh run_queue.sh jobs_stage4a.txt   # BGK with tau ~ 1/rho (and 4b)
```
