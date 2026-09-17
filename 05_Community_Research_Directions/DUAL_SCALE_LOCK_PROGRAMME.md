# The dual-scale lock: a programme

**Date:** 2026-09-16 · **Status:** proposal · **Builds on:** `LERAY_ALPHA_DUAL_SCALE_LOCK.md`,
`experiments/RESULTS.md`, paper §5, §9, §10.5

## 0. What "protect Navier–Stokes from blow-up in real physics" can mean

The phrase contains two different questions, and the programme only works if they are kept apart.

**Q-math.** Do the 3D incompressible Navier–Stokes equations blow up? Nothing *protects* the
equations; they do what they do. OpenAI has settled the forced case (C)/(D) in the affirmative. The
unforced case (A)/(B) is open. No lock, filter, or regularization bears on this question, because a
theorem about a modified equation is not a theorem about the original one. This programme does not
address Q-math and should never claim to.

**Q-phys.** Why does a real fluid not develop infinite gradients? This is *already answered* by the
flagship paper, and the answer is not a regularization: the incompressible model stops describing the
fluid at `ℓ* = ν/c_s`, and something else takes over — cavitation in liquids, the kinetic regime in
gases. The lock is physical, and it is a change of description, not a smoothing of the old one.

The productive question — the one this programme is about — is the one in between:

> **Q-lock.** What is the mathematical structure that connects the Navier–Stokes regime to the
> regime that replaces it at `ℓ*`, is it *derived* from physics or *posited*, and what does it
> predict that can be checked?

"Dual scale" is a good name for that structure. "T-duality" was a bad vehicle for it. Leray-α is a
better vehicle but is still *posited*. The claim of this proposal is that the structure already
exists in rigorous physics, that `ℓ*` is its scale, and that the way forward is to *derive* the
lock from it rather than to choose one.

## 1. The anchor: the lock already exists, and `ℓ*` is its scale

Kinetic theory gives `ν ≈ ½ c̄ λ` for a gas, with `c̄` the mean molecular speed and `λ` the mean
free path. Therefore

```
ℓ* = ν/c_s ≈ (c̄ / 2c_s) · λ.
```

For air at 300 K, `c̄/(2c_s) = 463/686 = 0.67`, and the paper's `ℓ* = 45 nm` against `λ = 68 nm`
gives `ℓ*/λ = 0.67`. **The validity scale of Proposition 5.1 is the mean free path, up to a
kinetic-theory constant that is derived, not fitted.** For water, `ℓ* ≈ 2.2` molecular diameters —
liquids have no mean free path, but the same order holds.

This changes what the programme is. The dual-scale structure connecting hydrodynamics to what lies
beneath is the **Chapman–Enskog hierarchy**: the Boltzmann equation at scale `λ`, the Navier–Stokes
equations as its `Kn → 0` limit, and `Kn = λ/L` as the parameter that locks the two. That hierarchy
comes with theorems:

* Global existence of renormalized solutions to Boltzmann (DiPerna–Lions 1989).
* The H-theorem: entropy is monotone along Boltzmann solutions.
* The rigorous incompressible Navier–Stokes–Fourier limit from Boltzmann (Golse–Saint-Raymond 2004).
* The incompressible limit of compressible flow as `Ma → 0` (Klainerman–Majda 1981).

So the honest statement of the intuition is: **a Navier–Stokes blow-up requires `Kn → ∞` locally;
that exits the regime in which Navier–Stokes is the limit of anything, and lands in a regime whose
governing equation has an H-theorem and global solutions.** No new physics is needed to say this.
What is needed is to make it *quantitative* and *checkable* — which is what the paper's §5 began
and what the rest of this programme continues.

One more number frames the fluctuation question. A `Re ≈ 1` core of size `ℓ*` carries kinetic
energy `ρν²ℓ*`: about **160 k_BT in water, 3200 k_BT in air**. Thermal fluctuations are therefore
8% and 2% of the core energy at the scale where the continuum ends — not negligible, not dominant.
That is the regime fluctuating hydrodynamics is for.

## 2. Why energy is not enough, and where the lock must live

A tempting version of the lock is "energy is conserved/bounded, so gradients cannot run away." It is
wrong, and Tao (2016) showed exactly how: an averaged Navier–Stokes system that **preserves the
energy identity** nonetheless blows up in finite time. The energy inequality is not a lock. Whatever
prevents blow-up must constrain the **structure of the nonlinear transfer**, not its energy budget.

This is precisely what §9's Leray-α measurement found from the other side. Leray-α suppresses peak
vorticity by 3.3× while *conserving* energy exactly (the transport term does no work on `u`), where
hyperviscosity suppresses gradients by *draining* energy. The lock that matters is a gate on
transfer, not a drain on energy — and Tao's result says it *had* to be, because a drain-free,
energy-preserving system can still blow up unless its transfer operator is constrained.

That gives the programme its ordering principle. Candidate locks, from weakest to most
discriminating:

| level | constrains | example | status |
|---|---|---|---|
| L0 | energy | Leray–Hopf inequality | **insufficient** (Tao 2016) |
| L1 | vorticity magnitude | `\|ω\| ≲ c_s²/ν` (paper §5.6) | dimensionally forced, blunt |
| L2 | transfer across a scale | Leray-α / LANS-α | posited; measured non-dissipative (§9) |
| L3 | vorticity direction | Constantin–Fefferman 1993 | a theorem about NSE itself |

The dual-scale intuition lives at L2. The deepest form of it may live at L3, since the construction's
fragile ingredient is *coherence*, which is a statement about direction.

## 3. The hierarchy of locks, each with its derivation status

Every lock below is stated with four things: what it is, whether it is derived or posited, what it
predicts, and what could be formalized. A lock without a test is a slogan.

### Lock K — kinetic (derived; the root)

*What.* Below `λ`, the Boltzmann equation replaces hydrodynamics; the H-theorem bounds entropy
production; no continuum gradient is defined.
*Status.* Derived. Rigorous limits exist (§1).
*Predicts.* Departure of a strained-vortex flow from Navier–Stokes at `Kn ~ 1`, i.e. at `ℓ*`.
*Test.* DSMC (direct simulation Monte Carlo) of a strained vortex against the spectral solver; measure
the scale of departure and compare to `ℓ*`. This is standard rarefied-gas methodology applied to a
new question.
*Formalize.* The H-theorem for a **discrete-velocity (lattice) Boltzmann BGK model** is
finite-dimensional and provable in Lean: `H(f)` decreases along the collision step. That is a
genuine lock theorem at the kinetic level, tractable now, and honest — it is about the discrete
model, and says so.

### Lock C — compressibility (derived)

*What.* Finite `c_s`; pressure cannot respond instantaneously; incompressible NSE is the `Ma → 0`
singular limit of the compressible system.
*Status.* Derived (Klainerman–Majda).
*Predicts.* A collapsing incompressible core is arrested when its velocity approaches `c_s`, at
`ℓ*`. Beyond that, compressible dynamics (possibly shocks) — a different singularity type that
viscosity regularizes into finite-width structures.
*Test.* Barotropic compressible pseudo-spectral solver (≈ 1–2 days from the existing 3D code) on
the shell-model and forced-core configurations; measure where the incompressible and compressible
trajectories separate. Cheap first version: a Mach cap in the dyadic shell model.
*Formalize.* The scaling chain of Proposition 5.1 as a formal theorem: from the hypotheses
`ℓ_r = √(νt)`, `u = √(ν/t)`, derive `t_Ma`, `t_Kn`, `ΔT` and their coincidence at `ℓ*`. Elementary
real arithmetic, and — unlike everything else in the repository — actually about the construction's
own scalings.

### Lock T — thermodynamic (derived; WorkStreams 2 and 4)

*What.* Isothermal NSE cuts the coupling between dissipation and material state. Restoring the energy
equation gives `ΔT = u²/c_p` (Eckert ~ 1); restoring the equation of state gives cavitation at
`ρu² ≈ p_∞ − p_v`.
*Status.* Derived from the energy equation and the equation of state. In liquids this is the
*first* lock to engage — nanoseconds before compressibility (paper §5.5).
*Predicts.* In water, phase change at `u ≈ 14 m/s` (cavitation) or, under tension, at
`Ma ≈ 0.37` (boiling).
*Test.* Barotropic-with-cavitation or two-phase model driven by the forced core.
*Formalize.* Not a priority; the physics is settled and the arithmetic is in the paper.

### Lock F — fluctuation (derived; Direction 3)

*What.* Landau–Lifshitz stochastic stress, calibrated by the fluctuation–dissipation theorem (done:
equipartition and temperature-linearity both pass).
*Status.* Derived. Model validity itself limited to scales `≳ λ` — the one place this programme must
not over-extrapolate.
*Predicts.* Decoherence of phase-locked packets when the noise-driven decoherence rate exceeds the
shear amplification rate: `σ τ_decoh ≪ 1`.
*Test.* Seed phase-coherent packets (not random ones) on a shear background; measure `σ` and
`τ_decoh` directly. The conclusion available is about `t = 0` — realizability of the datum — which is
stronger than any statement about the approach to `t = 1`.
*Formalize.* Not near-term.

### Lock A — the α-model (posited → to be derived)

> **Status update (2026-09-16) — conjecture relocated, not refuted.** Measured on the forced-core
> bed (`DIRECTION1_RESULTS.md`, stage 2): on a Re ≈ 1 collapse a transport gate can only act
> through the nonlinear term, which is ~5% of the forcing, so Leray-α and LANS-α lag the collapse
> by 0.2–0.4% while a dissipative barrier at the same scale lags it by up to 45%. The Re at which a
> gate becomes as strong a lock as a barrier is exactly
> `‖(L_barrier − L_ν)U‖ / ‖N_α(U) − N(U)‖`: between 8 and 142 across nine configurations, and
> largest as α/ℓ → 1, which is where arrest happens. Since Proposition 5.1 puts a `Re_r = O(1)`
> core at `ℓ*`, **LANS-α cannot be the operative lock for the collapse at ℓ*.** The conjecture
> survives for Re ≫ 1 (cascades, where the gate is the stronger lock). At ℓ* the operative lock is
> a drain, which physics supplies through Lock K (collisional relaxation). Lock K moves from
> "the root" to "the lock that acts at ℓ*". The text below is retained as originally written.
>
> **Further correction (v5.3.0) to the note just above.** "A drain, which physics supplies through
> Lock K" is wrong in the sense it implies. The exact BGK shear spectrum
> (`experiments/lock_k_kinetic_spectrum.py`) gives damping `νk²[1 − (kλ)² + …]` — *less* than
> viscosity — capped at the collision rate `1/τ`, with the hydrodynamic mode ending at
> `kλ = √(π/2)`. Kinetic theory is not a stronger drain; it is the **termination** of the
> hydrodynamic mode. Lock K's role is therefore "the regime in which the gradient-based locks
> (barrier, gate) stop being defined", not "the strongest drain". Of the six locks, it remains the
> root; the barrier is now known not to model it.

*What.* `ū = (1 − α²Δ)⁻¹u` (Leray-α) or the Lagrangian-averaged variant (LANS-α, Holm–Marsden–Ratiu
1998). Global 3D well-posedness is a theorem for both.
*Status.* **Posited.** `α` is a free parameter. This is the weakness the T-duality drafts shared:
the lock was chosen, not derived.
*The central open problem of this programme.* Derive `α`. LANS-α is obtained by averaging over
Lagrangian fluctuations of correlation length `α`. In a real fluid at the continuum limit, the
fluctuations are kinetic/thermal with correlation length `~ λ ≈ ℓ*`. **Conjecture: LANS-α with
`α ≈ ℓ*` is the Lagrangian-averaged description of a gas near `Kn ~ 1`, and therefore a
*consequence* of Lock K rather than an independent assumption.** If true, the α-model stops being
a closure and becomes a derived intermediate between Boltzmann and Navier–Stokes.
*Predicts.* Then `α` is not free: `α = ℓ*` with a computable `O(1)` constant, and the α-model's
predictions (arrested peak velocity `u_max ~ ν/α ~ c_s`; the `k^{+1}` sub-α energy spectrum
reported by Graham et al. 2007–08) must match DSMC at `Kn ~ 1`.
*Test.* Three-way comparison — Navier–Stokes / LANS-α at `α = ℓ*` / DSMC — on the same strained
vortex. Agreement of LANS-α with DSMC where NSE fails would be the first evidence the lock is
derived. Disagreement would show the α-model is a closure and nothing more — equally worth knowing.
*Known hazard.* LANS-α is documented to accumulate energy in "rigid-body" structures below `α`
(Graham et al.); whether that is an artifact or the correct sub-`λ` behaviour is exactly what the
DSMC comparison decides.
*Formalize.* (i) Filter bounds `0 < (1+α²k²)⁻¹ ≤ 1`; (ii) the finite-truncation energy identity —
the formal content of "gate, not drain," already tested numerically; (iii) the conditional reduction
on OpenAI's `VelocityField` with the regularity theorem as a labelled hypothesis. Full
well-posedness is not a near-term target.

### Lock G — geometric (a theorem about NSE itself; Direction 2)

*What.* Constantin–Fefferman: regularity follows from Lipschitz coherence of the vorticity direction
in regions of large `|ω|`.
*Status.* Theorem — and, uniquely on this list, about the unmodified equations.
*Why it matters here.* The construction's essential and fragile ingredient is coherent phase
alignment maintained to arbitrarily fine scales. Lock F attacks that coherence physically; Lock G
says that coherence is what the mathematics needs. A criterion at L3 would discriminate exactly
where an L1 magnitude bound does not.
*Test.* Measure the vorticity-direction Lipschitz constant along the construction's scalings (from
the leading-order profile) and along a Lock-F noisy run; ask whether noise breaks the
Constantin–Fefferman condition before the Mach limit is reached.
*Formalize.* Stating the Constantin–Fefferman hypothesis as a predicate on OpenAI's `VelocityField`
is tractable; the theorem itself is not.

## 4. The unifying claim, stated so it can be wrong

> All six locks are one lock seen at different levels of description, and `ℓ* = ν/c_s` is its
> scale. Lock K is the root. Locks C and T are its hydrodynamic shadows (the `Ma` and `Kn` and
> `Ec` conditions of Proposition 5.1 all coincide at `ℓ*` because they are all `Kn ~ 1` in
> disguise). Lock F is its fluctuation shadow. Lock A is its *Lagrangian-averaged* shadow — if the
> conjecture in §3 holds — and Lock G is the geometric property that makes the whole thing bite on
> the construction specifically.

Falsifiers: (a) DSMC departs from NSE at a scale unrelated to `ℓ*`; (b) LANS-α at `α = ℓ*` fails to
track DSMC where NSE fails; (c) the vorticity-direction coherence of the construction survives Lock-F
noise to scales below `ℓ*`. Any one of these breaks the unification. None of them is known.

## 5. Staged plan

> **Week 1 done (2026-09-16) — see `WEEK1_LOCK_RESULTS.md`.** Items 1, 2 and 4 delivered and
> verified (LANS-α gates harder than Leray-α; the Mach cap is large-scale in a cascade and lands
> on `ℓ*` for a collapse; 17 Lean theorems on the three standard axioms). Item 3 returned an
> honest null: a plane-wave packet on Taylor–Green is not amplified (`σ < 0`), so Lock F is now
> formally blocked on Direction 1. Three of six locks wait on the same object — the forced-core
> test bed is the next step, and it is over-determined.

**This week (existing code).**
1. LANS-α alongside Leray-α in `spectral3d.py` (different nonlinearity; ~hours). Repeat the
   drain-vs-gate comparison; check the sub-α spectrum for the Graham et al. pileup.
2. Mach cap in the dyadic shell model: cheapest possible Lock C.
3. Coherent-packet seeding for Lock F: measure `σ` and `τ_decoh`.
4. Lean: Proposition 5.1 as a formal scaling theorem; the Leray-α filter bounds.

**This month.**
5. Barotropic compressible 3D solver from the existing code (Lock C properly).
6. The forced-core test bed of Direction 1 — needed by Locks A, C, F alike.
7. Lean: lattice-Boltzmann BGK H-theorem; the finite-truncation α-energy identity.

**This year.**
8. DSMC comparison (Lock K) — the decisive experiment for the §3 conjecture. External code (SPARTA
   or dsmcFoam) on a strained vortex; the spectral solver supplies the NSE and LANS-α sides.
9. Vorticity-direction diagnostics (Lock G) on the forced core and under noise.
10. Lean: the conditional reduction on OpenAI's `VelocityField`.

## 6. What to stop saying

* "The lock protects Navier–Stokes from blow-up." It does not; it replaces Navier–Stokes.
* "The singularity is mathematically impossible" — true in Leray-α, and irrelevant to Q-math.
* "`α = ℓ*` makes the model a sound representation of the continuum limit." It makes it a
  *falsifiable closure* pending Lock K. Sound representations at `ℓ*` are kinetic.
* "T-duality." The duality here is `Kn`, and it needs no string.

## 7. What is new in this proposal

Two things, and both are checkable. First, that the validity scale is the mean free path with a
derived kinetic constant (`ℓ*/λ = c̄/2c_s = 0.67` for air), which relocates the dual-scale
structure from speculation into the Chapman–Enskog hierarchy. Second, the conjecture that LANS-α
with `α ≈ ℓ*` is the Lagrangian average over kinetic fluctuations — which, if true, turns the
α-model from a chosen closure into a derived intermediate, and if false, settles that the
dual-scale lock is a modelling convenience. Either outcome is worth the DSMC run that decides it.

## 8. Status update (2026-09-17): the chain after the nonlinear kinetic test

* **Link 1 is now unconditional.** The periodic mean-velocity lemma (formerly named
  `BKMHypothesis`) is proved in `OpenAIAdmissibility.lean` on OpenAI's own definitions and
  periodic-integration library: any object with OpenAI's `CandidateProperties` exceeds every
  velocity-gradient bound arbitrarily close to `t = 1`. Standard axioms only.
* **Link 4, nonlinear test: null result for the lock as an arrest.** A 2D-2V discrete-velocity
  BGK solver in Rust (`kinetic_lock_rs/`, gates G1–G5 passed, CVODE cross-check via
  rusty-SUNDIALS) driven by the forced-core target shows **no arrest at `k_ωλ ≈ √(π/2)`**. The
  kinetic core runs slightly *ahead* of the Navier–Stokes target (lag down to −11 to −12%;
  kinetic damping is weaker than viscous, as the linear Burnett sign predicts), and its apparent
  stopping point moves with the grid — at λ = 0.065, refining `Δx` from 0.67λ to 0.17λ moves it
  from 0.98λ to 0.52λ (Re = 1) and from 0.86λ to 0.35λ (Re = 0.25), with `k_ωλ` rising to 4–5 —
  while the NSE control on the same grid tracks the target to |lag| ≤ 4×10⁻⁴. Robustly, within
  the solver's validated range: no arrest at or above ≈ 0.9λ. Below that the runs reach
  Mach 1–3, 20–98% density holes and negative `f` beyond the G5 limit, so they bound, rather
  than measure, what happens there.
* **Reading.** This is what Lock K's correction (§ Lock K, v5.3.0) implies rather than a
  surprise: kinetic theory terminates the hydrodynamic *mode* at `kλ = √(π/2)` and caps damping
  at `1/τ`, so it supplies no extra resistance a body force must overcome. A driven core is
  stopped, if at all, by something else (compressibility, thermodynamics — Locks C, T), not by
  the kinetic cutoff. Limits: 2D, isothermal BGK (no energy equation, so Lock T is absent by
  construction), `Δx ≥ λ/6`, forcing taken from the incompressible solution.
