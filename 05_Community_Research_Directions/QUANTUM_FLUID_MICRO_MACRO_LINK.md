# The micro–macro link through quantum fluids — and what moonshine can and cannot add

**Date:** 2026-09-18 · **Status:** exploratory study; all calculations and simulations verified
**Code:** `experiments/quantum_fluid_link.py` (A–D), `experiments/gp_vortex_dipole.py` (E) · **Tests:** `tests/test_quantum_fluid_link.py` (5), `tests/test_gp_vortex_dipole.py` (6)
**Lean:** `03_Lean4_Topological_Censorship/src/QuantumVortexLink.lean` (11 declarations, standard axioms)
**Data:** `experiments/results/quantum_fluid_link.{json,png}`, `gp_vortex_dipole.{json,png}`

## 0. The question, and the discipline

The intuition behind this programme is that the microscopic and the macroscopic descriptions of a fluid
are *linked*: that the parameter which stops a collapsing vortex should be readable from the microscopic
structure — "from the geometry". Earlier versions tried to carry that link through string theory
(T-duality, K3×T²); that claim was reviewed and withdrawn because nothing in it was load-bearing (its
central Lean theorem ended in `True`). This study asks the same question where the answer is known
exactly: **quantum fluids**, in which the microscopic scale is built into the equation of motion. It
then asks, separately and without enthusiasm, what the Mathieu/umbral moonshine literature the question
was framed with could contribute.

Sources read for this study: H. Godfrin & E. Krotscheck, *The Dynamics of Quantum Fluids*,
arXiv:2206.06039 (2022); H. Godfrin et al., *Roton collective mode observed in a two-dimensional Fermi
liquid*, Nature 483, 576 (2012), HAL hal-00920422; M. R. Gaberdiel, C. A. Keller & H. Paul, *Mathieu
Moonshine and Symmetry Surfing*, arXiv:1609.09302; A. Taormina & K. Wendland, *A twist in the M24 moonshine
story*, arXiv:1303.3221 (INSPIRE 1223650); K. Trachenko & V. V. Brazhkin, *Minimal quantum viscosity from
fundamental physical constants*, Sci. Adv. 6, eaba3747 (2020); K. Trachenko, B. Monserrat, C. J. Pickard &
V. V. Brazhkin, *Speed of sound from fundamental physical constants*, Sci. Adv. 6, eabc8662 (2020);
R. J. Donnelly & C. F. Barenghi, J. Phys. Chem. Ref. Data 27, 1217 (1998).

## 1. What the quantum-fluid sources establish (read, not computed here)

* **The dispersion curve decides.** Godfrin & Krotscheck: "the particular shape of the dispersion relation
  leads to the superfluid behavior"; with a linear low-k branch an immersed object cannot create
  excitations below a critical velocity; "in a Bose gas, where the dispersion relation is parabolic, the
  critical velocity is zero"; interactions (Bogoliubov) make the branch linear.
* **The roton is a property of a dense, strongly interacting liquid, not of quantum statistics.** Godfrin
  et al. 2012 observe a roton-like collective mode in a *Fermi* liquid (a ³He monolayer): the density mode
  "reappears as a well-defined excitation at momentum transfers larger than twice the Fermi momentum",
  inside a regime long believed incoherent. They cite Pines (common origin: strong interactions) and
  Nozières (incipient localization).
* **Consequence for normal liquids.** A dense liquid keeps a collective density mode down to the
  interparticle scale. That is the opposite of the dilute gas, whose hydrodynamic shear mode terminates at
  `kλ = √(π/2)` (paper §9.2). It sharpens a gap this programme already listed: *liquids are not dilute
  gases*, and the "termination" picture of link 4 must not be carried to water.

## 2. Four exact calculations (`quantum_fluid_link.py`, verified)

### (A) A quantized vortex *is* a Reynolds-number-one core — and it survives by emptying its axis

Around one circulation quantum `u = ħ/(m r)`, so `u r/(ħ/m) = 1` at **every** radius (Lean:
`quantum_reynolds_eq_one`). With `ħ/m` in the place of `ν`, this is exactly the condition `Re_r = O(1)`
that defines the OpenAI construction's diffusive route. The Gross–Pitaevskii (GP) equation is, via the
Madelung transform, compressible Euler with a barotropic pressure plus a quantum-pressure term; its sonic
radius `u = c` is `r_s = ħ/(m c) = √2 ξ` (Lean: `sonic_radius`, `sonic_radius_eq_sqrt_two_xi`), the
superfluid analogue of `ℓ* = ν/c` (`lstar_analogue`).

Solving the stationary GP vortex and comparing it with its classical twin — isothermal compressible Euler
with the *same* velocity field, whose cyclostrophic density is exactly `ρ = exp(−r_s²/2r²)`:

| quantity (units ħ = m = c = 1) | GP (quantum) | isothermal Euler (classical) |
|---|---|---|
| `u r / (ħ/m)` | 1.000 everywhere | 1.000 everywhere |
| radius where `ρ = ρ∞/2` | 1.10 (= 1.55 ξ) | 0.85 |
| behaviour at the axis | `ρ ≈ (0.825 r)²` | `ρ → 0` with an essential singularity |
| far field | `ρ ≈ 1 − r_s²/2r²` | same leading term (difference 7% of the deficit at r = 5, falling as 1/r²) |
| peak mass current `ρu` | 0.46 at r = 1.28 | — |

**Reading.** Neither fluid stops the velocity from diverging at the axis. Both make the divergence
harmless by removing the mass that would carry it. This is the same answer the compressible simulation
gave for air (`THERMO_COMPRESSIBLE_LOCK_STUDY.md`: hot, evacuated core, Mach locked at 0.70) and the same
answer cavitation gives for a liquid. In three unrelated microphysics — quantum pressure, heat, phase
change — a fluid "survives" `u ∝ 1/r` by evacuating the core. That is the most robust micro–macro link
found in this programme, and it is a statement about *density*, not about a filter on velocity.

### (B) The critical velocity is read off the geometry of the dispersion curve

Landau: a body at speed `v` can create an excitation `(p, ε)` only if `ε(p) − p v < 0`, so
`v_c = inf ε(p)/p`, the slope of the tangent from the origin to the curve (Lean: `landau_no_excitation`).

| spectrum | `v_c` |
|---|---|
| Bogoliubov, `ε = √(c²k² + (k²/2)²)` | **exactly `c`** (numerical 1.000000000000; Lean: `bogoliubov_ratio_ge`, `bogoliubov_vc_is_c`) |
| free Bose gas, `ε = k²/2` | **0** (Lean: `free_gas_vc_zero`) |
| He-4, phonon + roton (Δ/k_B ≈ 8.62 K, k₀ ≈ 1.92 Å⁻¹, μ ≈ 0.16 m₄, c ≈ 238 m/s; approximate standard values) | **≈ 58 m/s = 0.24 c**, set by the roton minimum |

This is the precise, non-metaphorical form of "the parameter comes from the geometry": a single number
of the fluid (its critical velocity) is a geometric property (a tangent) of its excitation spectrum.
Normal fluids have no condensate and no Landau criterion — viscosity dissipates at any speed — so this does
not transfer as a bound on a normal fluid. What transfers is the *method*: in the dilute gas the analogous
geometric feature of the spectrum is the termination point `kλ = √(π/2)` of the shear mode (§9.2).

### (C) Modular geometry fixes the shape of a vortex lattice

Rotating superfluids and BECs form vortex lattices. For equal vortices at fixed density, the lattice-
dependent part of the renormalized energy is `W(τ) = −log(√Im τ · |η(τ)|²)`, `τ` the shape of the unit
cell and `η` the Dedekind eta function (Kronecker's first limit formula). Verified here:

* modular invariance `W(τ+1) = W(−1/τ) = W(τ)` to 9×10⁻¹⁶;
* the minimum over the fundamental domain is at the hexagonal point `τ = e^{iπ/3}` (grid minimum at the
  equivalent point `−½ + 0.871 i`); `W_square − W_hex = 0.0106`;
* independent check by a direct lattice sum (Epstein zeta, s = 2, unit cell area): hexagonal 5.783 <
  square 6.027 < rectangular 7.391.

The hexagonal minimum is classical mathematics (Rankin, Cassels, Ennola, Diananda; Sandier–Serfaty for the
renormalized energy) and is observed (triangular vortex lattices in rotating BECs, Abo-Shaeer et al.,
Science 2001). **This is the one exact place where a modular form fixes a fluid parameter from geometry
alone.**

### (D) A floor on the validity length from fundamental constants

Two published estimates — the minimal kinematic viscosity `ν_m = ħ/(4π√(m_e m))` and the maximal speed of
sound `v_u = α c √(m_e/2m_p)/√A` — combine into an identity in which the molecular mass cancels exactly
(Lean: `lstar_floor_identity`):

`ν_m / v_u = (√2/4π) · ħ/(m_e c α) = (√2/4π) a_B ≈ 5.96 pm`,

numerically identical for hydrogen, helium, water and mercury (to 10⁻¹²). Any fluid obeying both
estimates therefore has `ℓ* = ν/c ≥ 6 pm` (`lstar_floor`). Water's `ℓ* = 0.67 nm` is 113 times the floor.
**Status:** the identity is exact; the inputs are order-of-magnitude bounds from the literature, not
theorems, so the floor is an estimate. It is the micro–macro statement in its cleanest form: the scale at
which any continuum description of a fluid must end cannot be smaller than a fixed fraction of the Bohr
radius, whatever the fluid. (Superfluid He II is exempt from the viscosity estimate; its analogue of `ν` is
`ħ/m ≈ 1.6×10⁻⁸ m²/s`.)

## 3. The vortex-dipole velocity lock (E) — `gp_vortex_dipole.py`

A classical point-vortex pair of separation `d` translates at `U = κ/(2πd)`, which diverges as `d → 0`:
the two-vortex version of a collapse with no microscopic lock. In GP the same pair is simulated with a
split-step Fourier solver (Bogoliubov dispersion reproduced to 10⁻⁵ for `kξ ≤ 2`, norm drift ≤ 2×10⁻¹²,
energy drift ≤ 8×10⁻⁷; the step size is set from the stability limit `dt·k_max²/2 ≤ 1.5`, after an
instability at a larger step was caught by the energy check and fixed).

| `d₀/ξ` | state | speed `/c` |
|---|---|---|
| 1.5, 2.0, 2.5 | annihilates → rarefaction pulse | 0.919, 0.906, 0.830 |
| 3.0, 3.5 | annihilates → rarefaction pulse | 0.715, 0.595 |
| 4.0 (measured separation 2.75 ξ) | surviving pair, **fastest** | **0.498** |
| 8, 14, 20, 28, 40 | surviving pair | 0.205, 0.117, 0.081, 0.040 |

**Every speed measured, pair or pulse, is below `c`** — verified directly from the run records. The pair
branch ends near 0.5 c at a separation of about 2.75 ξ; below it the vortices annihilate into a sound
pulse whose speed rises towards `c` but never reaches it. This brackets the Jones–Roberts picture (a
dipole branch terminating near 0.6 c and a rarefaction branch continuing to `c`), with the caveat that
the initial state here is an ansatz plus relaxation, not their exact travelling solution, so the
annihilation threshold (3.5–4 ξ) belongs to this initial condition rather than to GP itself.

*How to read the ratios.* Measured `U` exceeds the free-space law `1/d₀` by ~14% at large `d`, which is
**not** a physical excess: the box scales with `d`, so periodic images contribute a constant factor, and
the pair contracts slightly while shedding the ansatz's sound. Against the point-vortex speed of the
*same periodic four-vortex lattice* at the *measured* separation, GP agrees to 0.1% for `d ≥ 14 ξ`
(`U/U_per` = 1.024, 1.012, 1.007, 1.004 at `d₀` = 14, 20, 28, 40 and 1.000 when the measured separation is
used). Refining `dx` from 0.35 ξ to 0.25 ξ moves `U` by < 0.2%; doubling the box moves absolute `U` by
4–8.5% but the ratio by ≤ 1%.

**Core state at the fastest surviving pair.** Minimum density 3.5×10⁻³ ρ∞ (an essentially empty core),
bounded mass current (max 0.373), maximum speed 0.674 c where ρ > ρ∞/2, and a local Mach number of 0.92 on
the half-density contour. The same picture as (A) and as the compressible air core: the fluid carries a
velocity singularity by removing the mass around it.

## 4. Moonshine: what can be said, precisely

**What moonshine is.** Mathieu moonshine is the observation that the coefficients of the K3 elliptic genus,
decomposed into N = 4 superconformal characters (20, −2, 90, 462, 1540, …), are dimensions of
representations of the sporadic group M₂₄. Its existence has been proved abstractly (Gannon), but "a
conceptual understanding in terms of a representation of the Mathieu group on the BPS states is missing"
(Gaberdiel–Keller–Paul). No single K3 sigma model has M₂₄ symmetry. Taormina and Wendland obtain M₂₄
representations only by *symmetry surfing* — combining the geometric symmetry groups of different points in
the moduli space — and their 45-dimensional representation carries a twist that cannot be undone for the
combined group. Umbral moonshine extends this to 23 Niemeier lattices with mock modular forms.

**What connects to fluids, exactly.** One mathematical object is shared: the Dedekind eta function and the
modular group SL(2,ℤ). η builds the K3 elliptic genus and the M₂₄ twining genera; η also gives the energy of a
vortex lattice (§2C). The reason is the same in both cases — a torus has a shape parameter `τ`, and physics
on it must be invariant under SL(2,ℤ) — and it involves **no sporadic group**. The vortex lattice's
symmetry is the hexagonal lattice's point group, not M₂₄.

**What does not connect.** There is no known mechanism by which M₂₄, K3 geometry, BPS state counting, or
mock modular forms enter the dynamics of a classical or quantum fluid, and nothing in this study creates
one. The Navier–Stokes problem OpenAI solved is posed on a torus, but its shape is fixed (a cube), so even
the SL(2,ℤ) moduli play no role there. Any statement that moonshine "explains" a fluid scale would repeat the
error the T-duality version made.

**What survives as an analogy — labelled as one.** Symmetry surfing has a structural parallel in this
programme: no single route to a singularity shows all the physics (diffusive → kinetic termination;
inertial → compressibility and heat; bounded velocity → viscosity; quantum → evacuated core), and the full
picture is only visible by combining routes (`BlowupRegimeMap.lean`). That is a way of organising results,
not evidence, and it should not be cited as one.

## 4b. The correspondence, in one table

| | classical fluid (this project) | quantum fluid (this study) |
|---|---|---|
| microscopic constant | kinematic viscosity `ν` | quantum of circulation `ħ/m` |
| core with `u ℓ / (const) = 1` | the construction's diffusive core (`Re_r = O(1)`, a *property* of the solution) | every quantized vortex (a *theorem*: `u r/(ħ/m) ≡ 1`) |
| validity length | `ℓ* = ν/c_s` | `ħ/(m c) = √2 ξ` (sonic radius = healing length up to √2) |
| what happens at that scale | hydrodynamic mode terminates (gas); nothing arrests a driven core | the core is empty; the velocity singularity is topological and harmless |
| velocity bound | none; Mach locks at 0.70 on the inertial route (air, measured) | pair speed < `c` always; fastest pair 0.50 `c`; pulses → `c` |
| critical velocity | none (viscous dissipation at any speed) | `v_c = inf ε(p)/p`: `c` (Bogoliubov), ≈ 58 m/s (He-4 roton), 0 (free gas) |
| lower bound on the validity length | `ℓ* ≳ (√2/4π) a_B ≈ 6 pm` (estimate, mass-independent) | same identity; He II is exempt (no viscosity) |

## 5. What this adds to the programme

1. **The robust micro–macro link is the evacuated core.** Quantum pressure (GP), heat (air), and phase change
   (water) all let a fluid tolerate `u ∝ 1/r` by removing mass from the axis. None does it by capping
   velocity with a filter. This reinforces the withdrawal of the Leray-α anchor.
2. **"Parameters from geometry" has two exact, testable forms in fluids:** the Landau tangent to the
   dispersion curve (critical velocity) and the modular minimum of lattice energy (vortex-lattice shape).
   Neither involves M₂₄.
3. **A universal floor** `ℓ* ≳ (√2/4π) a_B` (estimate) bounds from below the scale at which any continuum
   fluid description ends.
4. **For liquids,** Godfrin's result argues that collective modes survive to the interparticle scale, so
   the gas-kinetic termination at `kλ = √(π/2)` is not the right picture for water; the next kinetic test
   for liquids is generalized hydrodynamics or molecular dynamics, not BGK.

## 6. Next

* Quantum-turbulence analogue of the forced core: a GP vortex ring or dipole driven by a prescribed force
  against quantization — does the force produce phonons (Mach-type lock) or reconnection?
* Molecular dynamics of a Lennard-Jones liquid vortex at the interparticle scale (liquids gap).
* Thermal kinetic test for the air Mach lock (unchanged from `THERMO_COMPRESSIBLE_LOCK_STUDY.md`).

## Reproduce

```bash
cd 05_Community_Research_Directions/experiments
python3 quantum_fluid_link.py      # A-D, ~1 min
python3 gp_vortex_dipole.py        # E
cd ../.. && python3 -m pytest -q tests/test_quantum_fluid_link.py tests/test_gp_vortex_dipole.py
```
