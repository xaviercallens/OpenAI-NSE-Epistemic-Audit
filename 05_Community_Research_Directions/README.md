# 🌐 Community Research Directions

Following the discussion on `r/FluidMechanics` (30,000+ views), this section develops the ideas, questions and intuitions brought forward by the community — and, since September 2026, the "dual-scale lock" research programme that grew out of them.

*Rendons à César ce qui appartient à César* — this work is driven by the collective curiosity of mathematicians, fluid dynamicists, and engineers. Thank you to everyone who contributed to the discussion, specifically `u/cowgod42`, `u/vibe0009`, `u/babainottawa`, `u/Little-Name9809`, and `u/brokebeany` for your sharp insights.

## Status at v5.5.0 (2026-09-17), in one paragraph

The construction necessarily passes the scale $\ell_* = \nu/c_s$ where the hydrodynamic description ends (proved in Lean on OpenAI's own objects, unconditionally, and on the construction's scalings). At that scale the kinetic (BGK) shear mode terminates at $k\lambda=\sqrt{\pi/2}$ with damping *below* viscous and capped at $1/\tau$ — but a nonlinear kinetic simulation of a forced collapse finds **no arrest** there, and a compressible, heat-conducting gas driven by the same force is not stopped before $\ell_*$ either (an arrest prediction of ours, Ma 0.36, failed). So on OpenAI's route nothing demonstrated here stops a driven collapse; the description ends. Which physics a blow-up meets first depends on its route, by $\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$: on the inertial route (Re ≳ 16, Tao-type) compressibility comes first, and there air **locks at local Mach 0.70** — a lock on Mach number, not on velocity or size, in a model with its own proved implosion singularities. A dissipative barrier stalls a manufactured Re ≈ 1 core near $\sqrt{\alpha'}$ (not yet converged); Leray-α/LANS-α are far weaker on such a core (a ranking of two *models*), and the claim that a Leray-α filter of width $\ell_*$ represents the fluid at its continuum limit is **withdrawn** ($\alpha$ is absent from the linearized dynamics). Nothing here bears on Clay Statement A.

## The lock programme — read in this order

| Document | What it is |
|---|---|
| [`DUAL_SCALE_LOCK_PROGRAMME.md`](DUAL_SCALE_LOCK_PROGRAMME.md) | The programme: six candidate locks (kinetic, compressibility, thermodynamic, fluctuation, α-model, geometric), the unifying claim stated so it can be wrong, **§8** (link 1 unconditional; link 4 nonlinear null) and **§9, current status at v5.5.0** (Locks C/T tested; Lock A answered negatively; open items) |
| [`DIRECTION1_RESULTS.md`](DIRECTION1_RESULTS.md) | The forced-core test bed: 32³ single-variable collapse of the barrier's engagement, the **96³ sweep** (no B/F crossing; core stall at ℓ ≈ 1.2–1.5 √α′), and stage 2 (gates vs barrier on an axial core) |
| [`THERMO_COMPRESSIBLE_LOCK_STUDY.md`](THERMO_COMPRESSIBLE_LOCK_STUDY.md) | **v5.5.0.** The regime map of blow-up scenarios (OpenAI, Tao 2016, forced Euler) via `Kn = Ma/Re`; the compressible/thermal forced core — a failed arrest prediction, and a thermodynamic **Mach lock at 0.70** for air on the inertial route; the formal withdrawal of the Leray-α "physical anchor" claim |
| [`kinetic_lock_rs/README.md`](kinetic_lock_rs/README.md) | The nonlinear kinetic test of link 4: Rust 2D-2V discrete-velocity BGK solver, its five validation gates, and the null result |
| [`LERAY_ALPHA_DUAL_SCALE_LOCK.md`](LERAY_ALPHA_DUAL_SCALE_LOCK.md) | The pivot from T-duality to Leray-α: gate (transport filter, conserves energy) vs drain (hyperviscosity). *Its "α = ℓ* physical anchor" reading is withdrawn (v5.5.0); kept as the record of the pivot* |
| [`WEEK1_LOCK_RESULTS.md`](WEEK1_LOCK_RESULTS.md) | First-week results: LANS-α, shell-model Mach cap, fluctuation coherence, first Lean files |
| [`experiments/RESULTS.md`](experiments/RESULTS.md) | The 3D spectral solver (Taylor–Green benchmark), cutoff-law tests on generic data (negative), thermal noise, validity monitor |
| [`RICCATI_THRESHOLD_CHECK.md`](RICCATI_THRESHOLD_CHECK.md) | Does the construction sit at the dyadic Riccati threshold? (coincidence, with an exact correspondence at α = 2/5) |
| [`DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md`](DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md) | Assessment of an external DualScale/OpenFOAM benchmark report (several claims do not hold) and the plan that led to the work above |

Code: `experiments/` (Python: `spectral3d.py`, `forced_core.py`, `forced_core_axial.py`, `lock_k_kinetic_spectrum.py`, …; data in `experiments/results/`) and `kinetic_lock_rs/` (Rust). Tests: `../tests/`. Lean: `../03_Lean4_Topological_Censorship/`. Every check with its expected number: [`../BENCHMARKS.md`](../BENCHMARKS.md).

## Work Streams (community-inspired notes)

### 1. The "Augmented Navier-Stokes" & Entropy Condition (Inspired by `u/cowgod42`)
Exploring the idea that 3D Navier-Stokes requires an augmented admissibility condition (similar to the Lax entropy condition for inviscid Burgers) to filter out unphysical weak solutions. The paper's Direction 2 (§11.5) develops this; the formal admissibility statement is now proved on OpenAI's objects.
* [WorkStream 1 Folder](./WorkStream1_EntropyCondition) (LaTeX note; its `ThermodynamicAdmissibility.lean` is a draft, not a verified result)

### 2. Deriving the Thermal Energy Equation (Inspired by `u/vibe0009` & `u/Little-Name9809`)
Addressing how viscous heating follows from the scalings: because the core keeps Re ≈ 1, $\Delta T = u^2/c_p$ — about 48 K at Ma 0.3 and 540 K at Ma 1 in water (boiling a few picoseconds before blow-up; a few hundred kelvins at most, not plasma). The v5.5.0 compressible simulation measured the actual coefficient: 0.35 at Ma ≈ 0.4 rising to ≈ 1 near Ma ≈ 1, so $u^2/c_p$ is an upper-order estimate.
* [WorkStream 2 Folder](./WorkStream2_ThermalEquation) (Python visualization and LaTeX derivation)

### 3. Pre-Singularity Journey & Turbulence (Inspired by `u/babainottawa`)
Analyzing the trajectory *before* incompressibility breaks ($Ma < 0.3$) to extract insights for Large Eddy Simulation (LES) and subgrid-scale stress models.
* [WorkStream 3 Folder](./WorkStream3_Turbulence)

### 4–6. Mechanical cavitation, divergence-free structure, measure theory
WorkStream 4's cavitation figures use a core pressure deficit of ½ρu²; for a Gaussian core the exact deficit is 1.70 ρu², which moves the water threshold to ≈ 7.6 m/s (paper §5.6, v5.5.0).
* [WorkStream 4](./WorkStream4_MechanicalCavitation) · [WorkStream 5](./WorkStream5_DivergenceFree) · [WorkStream 6](./WorkStream6_MeasureTheory)

### The Dual-Framework for AI PDE Verification
A "Dual-Framework" combines mathematical validity (the theorem) and physical validity (Mach, Knudsen and Eckert bounds — equivalently the local bound $|\nabla u| \lesssim c^2/\nu$), so AI-generated mathematical-physics results can be labelled as theorems about a model versus statements about real fluids. It labels; it does not reject or "intercept" correct proofs. The Lean statement of that bound on OpenAI's own definitions is [`OpenAIAdmissibility.lean`](../03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean). The older `03_Lean4_Topological_Censorship/src/drafts/` files are not verified physics.

### Positive Scientific Roadmap: Leveraging OpenAI's Formalization
How the community can leverage OpenAI's Lean 4 Sobolev libraries, Gevrey bounds and proof tactics — as this project now does, reusing their periodic-integration library for its own admissibility proof.
* **Document**: [Positive Scientific Directions & Roadmap](./POSITIVE_FUTURE_DIRECTIONS.md) · manifesto: [TAO_NEUROSYMBOLIC_SCIENTIFIC_AI_MANIFESTO.md](./TAO_NEUROSYMBOLIC_SCIENTIFIC_AI_MANIFESTO.md)

---
*We invite further PRs, issues, and discussions. The gap between pure math and physical fluids is an open frontier!*
