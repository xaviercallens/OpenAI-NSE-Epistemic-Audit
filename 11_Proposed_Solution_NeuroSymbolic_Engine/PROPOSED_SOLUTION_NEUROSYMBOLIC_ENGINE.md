# 🧠 Proposed Solution: A Neuro-Symbolic Model-Validity Layer for Physical PDEs

**Labelling kernel-checked results with the regime in which the model describes a real fluid**

*MechanicaFluidorum Program · SocrateAI Lab · September 2026 · rewritten for v5.5.0*

> **Status and history (v5.5.0).** Earlier versions of this document were titled "The Neuro-Symbolic
> Physics Engine (LeanFlow): Intercepting and Rejecting Unphysical Mathematical Singularities". That
> framing is **withdrawn**. The "interception theorem" it presented
> (`openai_physical_invalidation_master`, in `src/drafts/PhysicalInvalidationProof.lean`) takes a
> *global bounded-enstrophy* condition as part of its admissibility definition — the withdrawn
> "thermodynamic censorship" axiom with no derivation — so it proves only that a divergent quantity is
> not bounded; it now sits in `drafts/`, does not compile against the current toolchain, and is not a verified result. A "LeanFlow" engine and a `physlib`
> tactic library do not exist as verified tools here. OpenAI's Lean proofs are correct, and nothing in
> this project refutes, rejects or intercepts them. See `../CHANGELOG.md` and Appendix A of the paper.

---

## 📌 1. The problem, stated correctly

In September 2026 an OpenAI multi-agent system produced Lean 4-verified proofs of finite-time blow-up
for the forced 3D incompressible Navier–Stokes equations and for Euler. (Press figures such as
"~10,000 agents over 88 hours" are not stated in OpenAI's own publications and are not used here.)
The proofs are correct theorems about the incompressible continuum model — the model the Clay problem
is about. The Clay "Statement A" for unforced flow remains open.

Read physically, the constructed Navier–Stokes core keeps a Reynolds number of order one, so its
scales are diffusive and its velocity diverges. Compressibility, rarefaction and viscous heating all
become order-one effects at one length, $\ell_* = \nu/c_s$ (about 0.7 nm in water, 45 nm in air),
a few picoseconds before the singularity in water. No law of thermodynamics is violated inside the
model; what stops holding is its constitutive idealisation (incompressible, isothermal, continuum).

So the gap is not an error to be blocked. It is a **missing label**: a kernel-checked theorem about a
model says nothing, by itself, about whether the model describes the flow it produces.

---

## 🏛️ 2. Architecture: label, don't block

```
[ AI-assisted formal proof search on a physical PDE ]
                     |
                     v
[ Lean 4 kernel ]  ---->  is the theorem true?            (untouched)
                     |
                     v
[ MODEL-VALIDITY LAYER ]  in which regime does the model hold for this object?
     |grad u| <= c_s^2/nu   <=>   Ma^2 <= Re
     Kn = Ma / Re           (which assumption fails first)
                     |
          +----------+-----------+
          v                      v
 "a theorem about the model;    "a theorem about the model, and
  the object leaves the model's  the object stays in the model's
  validity range, at scale X,    validity range: a physical
  first through assumption Y"    statement as well"
```

---

## 💻 3. The verified part: statements on OpenAI's own objects

[`03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean`](../03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean)
imports OpenAI's `NavierStokes.ProblemStatement`, `PeriodicIntegration` and `PeriodicUniqueness`
unchanged and proves, with no `sorry`, no remaining hypothesis, and only Lean's standard axioms:

- `gradient_bounded_before`: any candidate has a uniformly bounded velocity gradient on every
  $[0, 1-\delta]$;
- `bkmHypothesis_holds`: a uniformly bounded gradient on $[0,1)$ excludes unbounded speed (the
  periodic mean-velocity lemma $d\langle u\rangle/dt = \langle f\rangle$ — weaker than Beale–Kato–Majda);
- `exits_admissible_near_one'`, `candidate_not_admissible'`, `candidate_not_admissibleScaled'`: any
  object with OpenAI's `CandidateProperties` exceeds **every** gradient bound arbitrarily close to
  $t = 1$, hence leaves $|\nabla u| \lesssim c_s^2/\nu$ for every fluid and every choice of units.

```lean
def GradientBoundedOn (u : VelocityField) (T C : ℝ) : Prop :=
  ∀ t ∈ Ico (0 : ℝ) T, ∀ x : Space, ‖spatialDerivative u t x‖ ≤ C

theorem exits_admissible_near_one' (hc : CandidateProperties u p f) :
    ∀ C δ : ℝ, 0 < δ → ∃ t ∈ Ioo (1 - δ) 1, ∃ x : Space, C < ‖spatialDerivative u t x‖
```

What this is: a bridge between the proof objects and the physics — roughly, "velocity blow-up forces
gradient blow-up". What it is not: new physics, or a defect in OpenAI's proof.

---

## 🧭 4. What the layer should report: the first assumption to fail

[`BlowupRegimeMap.lean`](../03_Lean4_Topological_Censorship/src/BlowupRegimeMap.lean) proves
$\mathrm{Kn} = \mathrm{Ma}/\mathrm{Re}$ and its consequences. Different blow-up routes meet different
physics first:

| route | example | first assumption to fail | at scale |
|---|---|---|---|
| diffusive, $\mathrm{Re}\approx1$ | OpenAI's Navier–Stokes construction | compressibility and rarefaction together | $\ell_*$ |
| inertial, $\mathrm{Re}\to\infty$ | Tao's averaged-equation blow-up | compressibility, inside the continuum | $\mathrm{Re}\,\ell_*$ |
| bounded velocity | forced Euler blow-up with bounded velocity | the neglected viscosity | $\ell_*/\mathrm{Ma}$ |

What happens after that point has been measured, not assumed (paper §9):

- **Kinetic theory** ends the hydrodynamic shear mode at $k\lambda=\sqrt{\pi/2}$ and never damps faster
  than the collision rate; a nonlinear kinetic simulation of a driven core found **no arrest** there.
- **Compressibility and heat**, on OpenAI's route, slow the driven core but do not stop it before
  $\ell_*$. On the inertial route, air in a one-dimensional compressible simulation stops following the
  driven swirl at a **local Mach number of about 0.70** — a lock on Mach number, not on velocity or size,
  inside equations that have their own proved implosion singularities.
- **Liquids**: cavitation comes first (core pressure deficit reaches vapour pressure at about 14 m/s with
  the $\tfrac12\rho u^2$ estimate, about 7.6 m/s with the exact Gaussian-core coefficient 1.70).

---

## 🚫 5. What the layer must not do

- **Block or "refuse" a true theorem.** Validity of a model is a separate question from truth.
- **Substitute a regularized equation for the physics.** A "dual-scale" or Leray-α regularization with
  width $\ell_*$ does not represent the fluid at its continuum limit: the filter width is absent from the
  linearized dynamics ([`LerayAlphaLinearization.lean`](../03_Lean4_Topological_Censorship/src/LerayAlphaLinearization.lean)),
  while kinetic theory changes exactly those dynamics at that scale. Global regularity of Leray-α is a
  theorem about a different equation. The earlier "LeanFlow Dual-Scale Regularization" section of this
  document, including its sketched `leanflow_dual_scale_global_smoothness` statement (never compiled), is
  withdrawn.
- **Use an underived global bound.** The global enstrophy ceiling ($\Omega_{\max}\approx1.13\times10^{13}$)
  of earlier drafts had no derivation and is withdrawn in favour of the local bound above.

---

## ⚡ 6. Illustrative Python labelling

[`10_OpenAI_PoC_Proposal/openai_poc_pi_verifier.py`](../10_OpenAI_PoC_Proposal/openai_poc_pi_verifier.py)
labels a candidate state by Mach number, Knudsen number and sign of dissipation and writes a JSON
certificate. Its two scenarios use hand-picked numbers (an illustrative supersonic sub-nanometre state and
an illustrative subsonic continuum state). Its verdict strings, e.g. `UNPHYSICAL_BLOWUP_REJECTED`, are kept
as a test interface and mean "outside the incompressible model's validity range".

---

## 🔗 7. Sources

- Verified Lean: [`03_Lean4_Topological_Censorship/README.md`](../03_Lean4_Topological_Censorship/README.md)
  (74 declarations in nine files, standard axioms)
- The paper: [`01_Verification_Paper/OpenAI_NSE_Verification.pdf`](../01_Verification_Paper/OpenAI_NSE_Verification.pdf)
- Compressible/thermal study: [`05_Community_Research_Directions/THERMO_COMPRESSIBLE_LOCK_STUDY.md`](../05_Community_Research_Directions/THERMO_COMPRESSIBLE_LOCK_STUDY.md)
- PoC proposal: [`10_OpenAI_PoC_Proposal/OPENAI_POC_PROPOSAL.md`](../10_OpenAI_PoC_Proposal/OPENAI_POC_PROPOSAL.md)
- Notebook: [Open in Colab](https://colab.research.google.com/github/xaviercallens/OpenAI-NSE-Epistemic-Audit/blob/main/07_Tout_Public_Memo/Citizen_Science_Exploration.ipynb)
- Release v5.5.0 · Zenodo concept DOI [10.5281/zenodo.22696717](https://doi.org/10.5281/zenodo.22696717)
