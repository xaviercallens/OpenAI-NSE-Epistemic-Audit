# 🚀 PoC: Physics-Informed Formal Proof Search (PI-FPS) — a model-validity layer

*MechanicaFluidorum Program · SocrateAI Lab · September 2026 · status note updated for v5.5.0*

> **Status (v5.5.0).** This folder is an **architectural proposal with illustrative stubs**, not a working
> system. OpenAI's Lean 4 blow-up proofs are correct theorems about the incompressible Navier–Stokes
> model; nothing here refutes, rejects or "intercepts" them. The earlier "thermodynamic censorship"
> framing of this proposal is withdrawn (see `../CHANGELOG.md`). The verified formal work of this
> project lives in [`../03_Lean4_Topological_Censorship/`](../03_Lean4_Topological_Censorship/README.md).

---

## 📌 Overview

The idea: a proof assistant that handles physically motivated PDEs could carry an explicit
**model-validity layer**, so that a kernel-checked result is labelled as a theorem about a model, with
the regime in which that model describes a real fluid stated alongside it. For the incompressible
equations the natural label is the local bound $|\nabla u| \lesssim c_s^2/\nu$, equivalently
$\mathrm{Ma}^2 \le \mathrm{Re}$: where it fails, the Mach, Knudsen and Eckert numbers are no longer small.

---

## 📂 Directory Contents

- **`OPENAI_POC_PROPOSAL.md`**: the proposal and its architecture, with what exists and what does not.
- **`pi_tactic_demo.lean`**: an **illustrative stub** (its header says so): its predicates do not depend on
  their inputs and its theorem proves `True`. It shows the *shape* of an admissibility structure only.
- **`openai_poc_pi_verifier.py`**: a small Python checker that labels a candidate state by Mach number,
  Knudsen number and sign of dissipation, and writes a JSON certificate. The two scenarios use
  hand-picked illustrative numbers.
- **`openai_phys_admissibility_certificate.json`**: example output of that script.
- **`OpenAI_PoC_Physics_Informed_Verification.ipynb`**: notebook walkthrough of the same checker.

The verdict strings `UNPHYSICAL_BLOWUP_REJECTED` / `PHYSICALLY_ADMISSIBLE` and the scenario keys are kept
as a stable interface for the tests. Read them as "outside / inside the incompressible model's validity
range".

---

## 🔬 What the verified counterpart shows

On OpenAI's **own** Lean definitions, [`OpenAIAdmissibility.lean`](../03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean)
proves, with no remaining hypothesis and standard axioms only, that any object with OpenAI's
`CandidateProperties` exceeds every velocity-gradient bound arbitrarily close to the blow-up time — so it
leaves the admissible set for every fluid and every choice of units. That is a bridge between the proof
objects and the physics ("velocity blow-up forces gradient blow-up"), not new physics and not a flaw in
the proof.

---

## 🚀 Quick Start

```bash
python openai_poc_pi_verifier.py     # writes openai_phys_admissibility_certificate.json
```

```json
{
  "poc_title": "OpenAI Physics-Informed Formal Proof Search (PI-FPS) Certificate",
  "scenarios": {
    "openai_unconstrained_sobolev_proof": { "verdict": "UNPHYSICAL_BLOWUP_REJECTED" },
    "leanflow_dual_scale_proof": { "verdict": "PHYSICALLY_ADMISSIBLE" }
  }
}
```

(Scenario 1 is an illustrative supersonic, sub-nanometre state; scenario 2 an illustrative subsonic,
continuum-scale state. Neither is output from OpenAI's construction or from a "LeanFlow" solver.)

Current release: v5.5.0 · Zenodo concept DOI [10.5281/zenodo.22696717](https://doi.org/10.5281/zenodo.22696717)
(v5.5.0: [10.5281/zenodo.22806767](https://doi.org/10.5281/zenodo.22806767)).
