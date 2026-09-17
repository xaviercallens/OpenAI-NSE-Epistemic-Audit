# 🚀 Proof of Concept Proposal: Physics-Informed Formal Proof Search (PI-FPS)

**Labelling formal results about physical PDEs with the regime in which the model is valid**

*Prepared by the MechanicaFluidorum Program & SocrateAI Lab · September 2026 · revised for v5.5.0*
*Audience: teams working on automated theorem proving for PDEs in Lean 4*

> **Status (v5.5.0).** A proposal with illustrative stubs. It does not claim that OpenAI's proofs are
> wrong, unphysical in a sense that invalidates them, or rejected by any Lean tactic. The earlier
> "thermodynamic censorship" and "physlib guardrail" framing is withdrawn (`../CHANGELOG.md`); no
> `physlib` or `LeanFlow` tool exists as verified software in this repository.

---

## 📌 Executive Summary

OpenAI's Lean 4 formalizations of finite-time blow-up for the forced 3D Navier–Stokes equations and for
Euler are correct, and a real achievement in automated reasoning. They are theorems about the
incompressible continuum model — which is what the Clay problem asks about. They are not claims about
how a real fluid behaves, and the Clay "Statement A" for unforced Navier–Stokes remains open.

Read physically, the Navier–Stokes construction keeps a core Reynolds number of order one, so its
scales are diffusive and its velocity diverges. Compressibility, rarefaction and viscous heating all
become order-one effects together at the single length $\ell_* = \nu/c_s$ (about 0.7 nm in water, 45 nm
in air), a few picoseconds before the mathematical singularity in water. Heating there is hundreds of
kelvin, not a plasma; in water, cavitation comes earlier still. None of this is a flaw in the proof.

We propose a **model-validity layer** for formal proof search on physical PDEs: alongside the kernel
check, attach explicit statements of the regime in which the modelled equations describe a real fluid,
so that results are labelled as mathematical, physical, or both.

---

## 🏛️ Proposed architecture

```
+-----------------------------------------------------------------------+
|              FORMAL PROOF SEARCH ON A PHYSICAL PDE (any prover)        |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                 KERNEL CHECK (Lean 4): is the theorem true?            |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|     MODEL-VALIDITY LAYER: in which regime does the model hold?        |
|     e.g. |grad u| <= c_s^2/nu  <=>  Ma^2 <= Re  (Mach, Knudsen,       |
|     Eckert all small)                                                 |
+-----------------------------------------------------------------------+
                  |                                   |
                  v                                   v
   "theorem about the model; the          "theorem about the model, and the
    solution leaves the model's            solution stays in its validity
    validity range at scale l*"            range: also a physical statement"
```

The layer labels; it never blocks a true theorem.

---

## 🛠️ What exists, and what does not

| Component | Status |
|---|---|
| Admissibility on OpenAI's own objects — [`OpenAIAdmissibility.lean`](../03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean) | **Verified.** Any object with OpenAI's `CandidateProperties` exceeds every gradient bound near $t=1$; unconditional, standard axioms only. A bridge, not new physics. |
| Regime map — [`BlowupRegimeMap.lean`](../03_Lean4_Topological_Censorship/src/BlowupRegimeMap.lean) | **Verified.** $\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$; which assumption a blow-up scenario violates first (see below). |
| `pi_tactic_demo.lean` | **Illustrative stub**: predicates ignore their inputs; the theorem proves `True`. |
| `openai_poc_pi_verifier.py` | **Illustrative checker** of Mach, Knudsen and dissipation sign on hand-picked states; not connected to any prover or solver. |
| A `physlib` tactic library, a "LeanFlow" neural operator | **Do not exist** as verified tools here. Earlier drafts described them as if they did. |

---

## 🧭 Why the label depends on the blow-up route

The relation $\mathrm{Kn} = \mathrm{Ma}/\mathrm{Re}$ (proved in `BlowupRegimeMap.lean`) says a single
validity scale is special to one kind of blow-up:

- **Diffusive route** ($\mathrm{Re}\approx1$; OpenAI's Navier–Stokes construction): Mach and Knudsen fail
  together, at $\ell_*$.
- **Inertial route** ($\mathrm{Re}\to\infty$; e.g. Tao's averaged-equation blow-up): compressibility
  fails first, still inside the continuum, at $\mathrm{Re}\,\ell_*$. In a one-dimensional compressible
  simulation driven the same way, air stops following the driven swirl at a local Mach number of about
  0.70 — a lock on Mach number, not on velocity or size.
- **Bounded-velocity route** (e.g. forced Euler blow-up with bounded velocity and diverging gradients):
  the neglected viscosity acts first, at $\ell_*/\mathrm{Ma}$.

A useful validity layer should therefore report *which* assumption fails first, not a single pass/fail.

---

## ⚠️ What not to build into it

- **No regularized model as a stand-in for the physics.** A Leray-α filter of width $\ell_*$ is not a
  representation of the fluid at its continuum limit: the filter width does not appear in the linearized
  dynamics at all (`LerayAlphaLinearization.lean`), whereas kinetic theory changes exactly those dynamics
  at that scale. Global regularity of Leray-α is a theorem about a different equation.
- **No expectation that kinetic theory "stops" the collapse.** The hydrodynamic description ends at
  $k\lambda = \sqrt{\pi/2}$, but a nonlinear kinetic simulation of a driven core found no arrest there.

---

## 🤝 Next steps

1. Run `python 10_OpenAI_PoC_Proposal/openai_poc_pi_verifier.py` to see the labelling format.
2. Replace the stubs with predicates stated on a real proof object, following `OpenAIAdmissibility.lean`.
3. Report the first-failing assumption by route (Mach, Knudsen, Eckert, viscosity) rather than one verdict.

Current release v5.5.0 · Zenodo concept DOI [10.5281/zenodo.22696717](https://doi.org/10.5281/zenodo.22696717).
The "~10,000 agents" figure circulating in press coverage is not stated in OpenAI's own publications and
is not used here.
