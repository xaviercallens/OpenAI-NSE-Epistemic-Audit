<div align="center">

# 🌊 OpenAI NSE / Euler Physical Verification

### *A Physical Reading, Not a Physical Refutation*

[![CI Pipeline](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/actions/workflows/audit-pipeline.yml/badge.svg)](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/actions/workflows/audit-pipeline.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22696717.svg)](https://doi.org/10.5281/zenodo.22696717)
[![HuggingFace](https://img.shields.io/badge/🤗%20HuggingFace-Dataset-yellow)](https://huggingface.co/datasets/callensxavier/OpenAI-NSE-Thermodynamic-Censorship)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Discussions](https://img.shields.io/github/discussions/xaviercallens/OpenAI-NSE-Epistemic-Audit)](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/blob/main/.github/CONTRIBUTING.md)

**Non-Profit Citizen Science Initiative for Neuro-Symbolic Science · MechanicaFluidorum Program · September 2026**

[📄 Read the Paper (PDF)](01_Verification_Paper/OpenAI_NSE_Verification.pdf) · [💬 Join Discussions](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions) · [🏛️ Zenodo](https://doi.org/10.5281/zenodo.22696717) · [🤗 HuggingFace](https://huggingface.co/datasets/callensxavier/OpenAI-NSE-Thermodynamic-Censorship) · [⚖️ Legal Notice](LEGAL_NOTICE_AND_CITIZEN_SCIENCE_DISCLAIMER.md)

<br>

![Turbulent Energy Cascade & Kolmogorov Microscales](./dataset/animations/turbulence_energy_cascade.jpg)

</div>

> **Note (2026-09-15 pivot):** This document predates a project-wide reframing away from "physical vacuity"/"censorship" framing and away from string-theory/T-duality claims, after community and scientific feedback identified problems with both. See `REVIEW_AND_NEW_DIRECTION.md` and `paper/where_the_continuum_ends.tex` for the corrected position and specific retractions. Read what follows with that context — several claims below (plasma/vaporization framing, the condition-number figure, specific timing figures, and any string-theory/T-duality/K3×T² material) have since been corrected or withdrawn.

---

## 📌 TL;DR

In September 2026, an OpenAI multi-agent system produced a **Lean 4 formalized proof** of finite-time blow-up for the 3D Navier-Stokes and Euler equations — claiming Millennium Prize Alternatives C and D.

**The proof is mathematically sound within abstract Sobolev spaces. However, the singularity bypasses physical admissibility.**

This project presents a comprehensive physical verification, demonstrating how the mathematical construction diverges from real-world thermodynamic constraints, bounded by the continuum hypothesis and standard physical limits.

---

## 🛸 Tout Public & Citizen Science (General Public Section)

**Welcome!** If you are not a physicist or mathematician, start here. We have translated this complex scientific audit into accessible, highly visual materials to help everyone understand the clash between abstract AI mathematics and physical reality.

- 🌌 **[Read the "Tout Public" Memo](07_Tout_Public_Memo/MEMO.md):** An accessible, cyberpunk-styled visual memo explaining the mathematical singularity vs. physical turbulence, our claims, and our proposals for Neuro-Symbolic AI.
- 💻 **[Launch the Google Colab Notebook](07_Tout_Public_Memo/Citizen_Science_Exploration.ipynb):** A fully interactive environment where you can visualize where the continuum model stops describing a real fluid, and why a mathematical blow-up is not a physical event. No installation required!

![Cyberpunk Singularity & Turbulence](07_Tout_Public_Memo/assets/cyber_singularity_turbulence_1789311421687.jpg)

---

## 🔬 The Five Epistemic Disconnects

| # | Finding | Key Metric / Exponent |
|---|---|---|
| **1** | **Intensive Local Energy Density Divergence**: $e_{\text{local}} = \frac{1}{2}\rho\|u\|^2 \sim \tau^{-1.010}$ and global enstrophy $\Omega \sim \tau^{-0.515}$ diverge without bound | **$\Delta T = u^2/c_p \sim \tau^{-1.010}$** — about 48 K at $Ma = 0.3$ and 540 K at $Ma = 1$ (not plasma): the decoupled-temperature assumption fails, no thermodynamic law is violated |
| **2** | **Mach Number Self-Invalidation**: incompressible NSE invalidate themselves when $Ma \ge 0.3$ | about **6.7 picoseconds** before mathematical blow-up (dimensionless $\tau \approx 6.7 \times 10^{-14}$, physical $t = T\tau$ with $T = \ell_0^2/\nu = 100$ s; unit-free estimate $\nu/(0.3\,c)^2 \approx 5$ ps). Compressibility, rarefaction and heating all become order one at a single scale $\ell_* = \nu/c \approx 0.7$ nm in water |
| **3** | **Teleological Causality Reversal**: force $f$ is reverse-engineered from a pre-specified singular similarity profile | **MMS inversion** — shooting an arrow and painting a bullseye around it |
| **4** | **Matrix Scaling & Non-Dimensionalization**: moment-matching matrix $A = D B D$ has bounded non-dimensional condition number $\kappa(B) \approx 4.11 \times 10^5$ | **$\kappa(B) \sim O(10^5)$** — raw $\kappa \sim 10^{28}$ was an unscaled dimensional artifact |
| **5** | **Sub-Molecular Coherent Fine-Tuning** *(open question, see pivot note)*: Euler initial conditions would require implausibly fine-tuned coherence far below the molecular mean-free-path scale (~10⁻¹⁰–10⁻⁷ m), i.e. far below anything physically meaningful — not, as earlier drafts claimed, at the Planck scale (~10⁻³⁵ m, a quantum-gravity scale unrelated to fluid discreteness) | Whether such phased fluctuations survive molecular/thermal noise is an open question, not a demonstrated result |

### The Proposed Resolution: Dual-Framework

> **Model-validity (admissibility) condition** — The continuum, incompressible description of a real fluid holds only while the *local* vorticity stays below $|\omega| \lesssim c^2/\nu$ (about $2 \times 10^{12}\ \text{s}^{-1}$ in water, $8 \times 10^{9}\ \text{s}^{-1}$ in air): this single bound is equivalent to $Ma \lesssim 1$ together with $Kn \lesssim 1$. A solution that satisfies it on $[0,T)$ cannot blow up at $T$ — that is the Beale–Kato–Majda theorem, not a new axiom. The AI's construction has $|\omega| \sim \tau^{-1.005} \to \infty$ and crosses this bound a few picoseconds before the singularity. (An earlier version of this README quoted a global enstrophy ceiling "$\Omega_{\max} \approx 1.13 \times 10^{13}$"; that constant has no derivation and has been withdrawn.)

This analysis uses a **Dual-Framework**: Lean 4 for the mathematics, and explicit physical-validity predicates (Mach, Knudsen, Eckert bounds) for the physics. While the formal derivation is flawless, the flow it describes leaves the constitutive assumptions of the incompressible model (low Mach, continuum, decoupled temperature) a few picoseconds before the blow-up time.

---

## ✅ Lean 4 Physical Verification Telemetry

| Criterion | Expected | Found |
|---|---|---|
| `sorry` / `admit` in core proof | 0 | ✅ 0 |
| Custom `axiom` bypasses in physics | 0 | ✅ 0 (Non-vacuous flow explicitly checked) |
| Force smoothness type | `ContDiff ℝ ∞` | ✅ `ContDiff ℝ ∞` |
| Sobolev weakening | None | ✅ None |
| Global *L²* energy bound | Uniform | ✅ ∃ E, ∀ t, kineticEnergy u t ≤ E |

**Conclusion:** The AI accurately and brilliantly navigated the Millenium Prize rulebook. The gap highlighted here is strictly physical, shedding light on the boundary between abstract mathematical exploration and real-world fluid dynamics.

---

## 📁 Repository Structure

```
OpenAI-NSE-Epistemic-Audit/
├── 01_Verification_Paper/               # Peer-reviewed LaTeX paper + PDF
│   ├── OpenAI_NSE_Verification.pdf
│   ├── OpenAI_NSE_Verification.tex
│   └── zenodo_push.py
├── 02_Empirical_Observation/            # Python, Rust, & DNS Turbulence Simulations
│   ├── simu_sign_fragility_1D.py
│   ├── simu_frustration_Z3.py
│   ├── euler_counterdetonation/
│   └── DNS_Turbulence_Verification/     # JHTDB & OpenFOAM dataset empirical proofs
├── 03_Lean4_Topological_Censorship/     # Lean 4 Implementation with `physlib`
│   └── src/
│       ├── PhysLibThermodynamicCensorship.lean
│       ├── ThermodynamicCensorship.lean
│       ├── TopologicalCensorship.lean
│       └── NSECensorship.lean
├── 04_Thermodynamic_Censorship_Paper/   # Sept-12 draft, SUPERSEDED (see 01_Verification_Paper and paper/where_the_continuum_ends.tex)
├── 05_Community_Research_Directions/    # Extensible Workstreams & Terence Tao Manifesto
│   ├── POSITIVE_FUTURE_DIRECTIONS.md
│   └── TAO_NEUROSYMBOLIC_SCIENTIFIC_AI_MANIFESTO.md # The Neuro-Symbolic Scientific AI Modus Operandi
├── LEGAL_NOTICE_AND_CITIZEN_SCIENCE_DISCLAIMER.md # Legal protections & Fair Use disclaimers
├── autoform-bot/                        # Submodule: Dual-Framework Meta-Heuristics 
├── scripts/                             # Directives 2–7 analyses & Extractors
│   ├── extract_limits_to_latex.py       # Automated physical limit LaTeX extractor
│   ├── directive2_thermodynamic_paradox.py
│   ├── directive3_jacobian_instability.py
│   ├── directive4_gevrey_regularity.py
│   ├── directive5_mach_divergence.py
│   ├── directive6_thermal_instability.py
│   └── directive7_pre_singularity_simulation.py
├── dataset/                             # Dataset artifacts
│   └── animations/                      # Pre-singularity vortex animations
├── AUDIT_AND_IMPROVEMENT_PLAN.md        # Living roadmap for verification CI
└── .github/                             # CI/CD Workflows for automated physical testing
```

---

## 🚀 Quick Start

### Read the Paper
```
👉 01_Verification_Paper/OpenAI_NSE_Verification.pdf
```

### Reproduce the Simulations
```bash
git clone https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit
cd OpenAI-NSE-Epistemic-Audit/scripts
pip install numpy scipy sympy mpmath matplotlib
python directive5_mach_divergence.py             # Mach number trajectory (Ma = 0.3 about 6.7 ps before blow-up)
python directive2_thermodynamic_paradox.py       # Intensive scaling (-1.010 exponent)
python directive3_jacobian_instability.py        # Non-dimensionalization (kappa ~ 4.11e5)
python directive4_gevrey_regularity.py           # Analytical Gevrey index (s = 1.5)
python directive7_pre_singularity_simulation.py  # Pre-singularity animated plots
```

### Lean 4 Challenges
```bash
cd 03_Lean4_Topological_Censorship
lake build  # Requires Lean 4 + Mathlib
```

---

## 📊 Key Computational Results

<div align="center">
  <img src="02_Empirical_Observation/DNS_Turbulence_Verification/enstrophy_falsification.png" alt="Enstrophy Falsification vs Kolmogorov Dissipation" width="48%">
  <img src="dataset/animations/pre_singularity_vortex.gif" alt="Pre-Singularity Vortex Contraction" width="48%">
</div>

### Mach Number Self-Invalidation
| Dimensionless τ (physical time $t = T\tau$, $T = \ell_0^2/\nu = 100$ s for water, $\ell_0 = 1$ cm) | Velocity |u| (m/s) | Mach Ma | Regime |
|---|---|---|---|
| 10⁰ (t = 100 s) | 10⁻⁴ | 6.7×10⁻⁸ | ✅ Incompressible |
| 10⁻¹² (t = 100 ps) | 115 | 0.077 | ✅ Incompressible |
| **6.7×10⁻¹⁴ (t ≈ 6.7 ps)** | **450** | **0.30** | ❌ **Limit breached** |
| 6.2×10⁻¹⁵ (t ≈ 0.6 ps) | 1500 | 1.00 | ❌ Transonic |
| 9.0×10⁻¹⁶ (t ≈ 90 fs) | 4100 | 2.73 | ❌ Core radius ≈ molecular spacing (Kn ≈ 1) |

The velocity and Mach columns depend on $\ell_0$ only through a factor $(\ell_0^2/\nu t)^{1/200} \approx 1.2$; in unit-free form $u \simeq \sqrt{\nu/t}$, so $Ma = 0.3$ is reached at $t \simeq \nu/(0.3\,c)^2 \approx 5$ ps whatever the initial vortex size.

### Moment Matrix Non-Dimensionalization
| X_R | κ(A) [Raw Unscaled] | κ(B) [Non-Dimensionalized] | Status |
|---|---|---|---|
| 1 | 4.11 × 10⁵ | 4.11 × 10⁵ | Bounded |
| 100 | 2.36 × 10²⁰ | 4.11 × 10⁵ | Bounded |
| 1000 | 1.78 × 10²⁸ | **4.11 × 10⁵** | **Bounded & Scale-Invariant** |

### 🌪️ DNS & Empirical CFD Verification: The Ultraviolet Bomb vs. Real Turbulence

To illustrate the dual-framework, we contrast the AI's scaling limits with a physical turbulence spectrum. The figures below are schematic: the "OpenAI snapshot" curve is a hand-placed spike drawn from the scaling exponents, not a computed spectrum of the construction (no numerical implementation of the 166-page construction exists).

<div align="center">
  <img src="dataset/animations/turbulence_energy_cascade.jpg" alt="Energy Spectrum Comparison" width="48%">
  <img src="dataset/animations/smooth_vortex_dissipation.jpg" alt="Phase Fragility" width="48%">
</div>

#### 1. The Ultraviolet Bomb vs. The Kolmogorov Cascade (Left)
* **The Physics:** Real physical turbulence (JHTDB DNS, blue line) adheres strictly to the classical Kolmogorov $k^{-5/3}$ cascade, smoothly dissipating kinetic energy at the viscous microscale. 
* **The AI Singularity (schematic):** The red curve sketches where the construction's energy sits as $\tau \to 0$: at ever higher wavenumbers ($k_{\text{peak}} \sim \tau^{-1/2}$), eventually below the molecular scale. Note that the *total* kinetic energy of the core actually vanishes ($E \sim \tau^{+0.485}$); what diverges is the velocity and the energy *density*, not the amount of energy. (Earlier drafts called this an "Ultraviolet Bomb" at "sub-Planckian" scales; both phrasings were wrong — the relevant physical cutoff is the molecular scale, about $\ell_* = \nu/c \approx 0.7$ nm in water, not the Planck length.)

#### 2. Phase Fragility and Structural Instability (Right) *(hypothesis, not an established result — see pivot note)*
* **The Thermal Noise Test (open question):** Whether the AI's Euler singularity requires "Forced Coherence" between interacting wave packets that could not survive real molecular/thermal noise is one of the open questions identified in `REVIEW_AND_NEW_DIRECTION.md` (Q3: thermal noise survival), not a settled result.
* **The Hypothesis:** In a 1D dyadic *toy* model (`simu_sign_fragility_1D.py`), wide random phase jitter *delays* the cascade but does not arrest it; only a complete local decoupling of one shell arrests it. So the toy model does not, by itself, support the claim that thermal noise destroys the mechanism. Whether it does in the real construction (under Landau–Lifshitz fluctuating hydrodynamics) remains open and is not yet established.

---

## 🧠 Beyond Syntactic Truth: A Roadmap for Scientific AI

OpenAI's multi-agent formalization of the Navier-Stokes blow-up is a staggering computational achievement. It proves that Reinforcement Learning (RL) agents can navigate hyper-dimensional combinatorial search spaces and act as flawless syntactic compilers in Lean 4. **They brilliantly solved the mathematician's problem.**

However, unconstrained optimization in abstract mathematics will happily explore the edges of a model — producing theorems that hold for the equations while lying outside the equations' domain of physical validity. To advance from **Automated Mathematics** to true **Scientific AI**, we must anchor these massive theorem solvers to the phenomenological constraints of physical reality. 

Inspired by Fields Medalist **Terence Tao's vision of AI as a collaborative "gadgeteer"** rather than an infallible oracle, we propose upgrading the current *Bipartite* (Neural ↔ Symbolic) loop to a **Tripartite Neuro-Symbolic Architecture**:

1. **Neural (The Intuition Engine):** LLMs/RL agents propose physical models, flow geometries, and proof strategies.
2. **Symbolic (The Logic Engine):** Lean 4 (`mathlib`) verifies topological limits, norm bounds, and $C^\infty$ syntax.
3. **Empirical (The Physics Engine):** A deterministic CFD kernel (`physlib` / `LeanFlow`) acts as a strict semantic grounding node.

**The Modus Operandi:** If a proposed mathematical step compiles in Lean 4 but leaves the validity range of the model (Mach, Knudsen or Eckert bounds — equivalently $|\omega| \lesssim c^2/\nu$), the Empirical Engine flags the proof state as **"Physically Ill-Typed,"** forcing the AI to search for *physically admissible* mathematics. 

### 🔭 Open Research Directions for Frontier AI Labs
We invite OpenAI, DeepMind, and the open-source community to pivot these massive multi-agent swarms toward physically grounded challenges:

* **Direction A (Automated Epistemic "Red Teaming"):** Deploy specialized AI swarms to automatically audit abstract proofs for thermodynamic and physical loopholes (automating the exact epistemic audit performed in this repository).
* **Direction B (Global Regularity via Censorship):** Task the "10,000-agent" swarm (reported figure, not confirmed in OpenAI's own technical writeup) to attack Millennium Prize Alternative A (Global Regularity), which remains open. Note what is *not* a research problem: under the local admissibility bound $|\omega| \lesssim c^2/\nu$ on $[0,T)$, regularity on $[0,T]$ is already the Beale–Kato–Majda theorem. The real questions are the codimension of the blow-up, the cutoff law $u_{\max} \sim \nu/\sqrt{\alpha'}$, and thermal noise (see `REVIEW_AND_NEW_DIRECTION.md`).
* **Direction C (AI-Generated Turbulence Closures):** Invert the Method of Manufactured Solutions (MMS). Instead of reverse-engineering a singular residual into a phantom force, prompt the AI to discover exact, non-linear subgrid-scale (SGS) closure relationships for CFD, revolutionizing aerospace engineering and climate modeling.

*(Read our full strategic manifesto: [TAO_NEUROSYMBOLIC_SCIENTIFIC_AI_MANIFESTO.md](05_Community_Research_Directions/TAO_NEUROSYMBOLIC_SCIENTIFIC_AI_MANIFESTO.md))*

---

## 🦞 Visualizations, CFD, and The Thermodynamic Lobster

To make our scientific audit more tangible (and entertaining), we've built a suite of visual tools and conceptual CFD simulations.

* **Section 1 Investigation (Empirical Physics Audit of OpenAI Lean 4 Code):** Read Section 1 of our empirical investigation showing how physical metrics (Mach divergence, intensive energy scaling) self-invalidate official OpenAI Lean 4 code: **[Section 1: Empirical Investigation & Physics Audit](02_Empirical_Observation/SECTION_1_INVESTIGATION_PHYSICS_AUDIT.md)**.
* **Reproduction Protocol & Scientific Literature References:** Follow our step-by-step reproduction guide, physics deep-dive, literature bibliography (Fefferman, Leray, BKM, ESS, Tao), and Lean 4 formalization: **[Reproduction Protocol & Literature References](12_Reproduction_Protocol_and_Physics_References/REPRODUCTION_PROTOCOL_AND_PHYSICS_REFERENCES.md)**.
* **Proposed Solution (Neuro-Symbolic Engine & Lean 4 Interception):** Read our technical demonstration showing how physical predicates in Lean 4 intercept and refuse OpenAI unphysical blowup proofs: **[The Neuro-Symbolic Engine (LeanFlow)](11_Proposed_Solution_NeuroSymbolic_Engine/PROPOSED_SOLUTION_NEUROSYMBOLIC_ENGINE.md)**.
* **OpenAI PoC Proposal (Physics-Informed Proof Search):** Explore our working Proof of Concept designed for OpenAI research & reasoning teams: **[OpenAI PoC Proposal](10_OpenAI_PoC_Proposal/OPENAI_POC_PROPOSAL.md)**. Demonstrating how to embed physical domain tactics (`physlib`) into Lean 4 multi-agent proof search architectures.
* **Empirical DNS and OpenFOAM Telemetry:** Analyze full direct numerical simulations and Taylor-Green Vortex benchmarks comparing LeanFlow and OpenFOAM against mathematical blow-up profiles in **[Section 1: Investigation & Physics Audit](02_Empirical_Observation/SECTION_1_INVESTIGATION_PHYSICS_AUDIT.md)**.
* **Superseded draft (historical record):** the Sept-12 **[Thermodynamic Censorship Paper](04_Thermodynamic_Censorship_Paper/Thermodynamic_Censorship_Navier_Stokes.pdf)** has been superseded by the current paper and by `paper/where_the_continuum_ends.tex`; it is kept for the record and should not be cited for its "censorship" or "plasma" claims. The dual-scale idea survives only as a Leray-α/Bessel-filter regularization with a testable cutoff law $u_{\max} \sim \nu/\sqrt{\alpha'}$ — no string-theory claim.
* **PyFR & CFD Integration:** We advocate for using awesome Python CFD libraries like **[PyFR](https://www.linkedin.com/pulse/pyfr-awesome-python-cdf-library-dmitry-buzolin/)** to act as the "Empirical Engine." See our visualization scripts (e.g., `scripts/pyfr_lobster_visualization.py`) demonstrating how the physics engine shields reality from infinite mathematical blow-ups.
* **Navier-Stokes Masterclass (2-Hour Training):** Dive deep into the fluid equations with our interactive Jupyter Notebook course. Learn the math, write a CFD solver in Python, and visualize where the incompressible model stops describing a real fluid, using the LeanFlow dual-scale approach. Available in **[English](08_Training_Course/Navier_Stokes_Training_EN.ipynb)**, **[Français](08_Training_Course/Navier_Stokes_Training_FR.ipynb)**, and **[中文](08_Training_Course/Navier_Stokes_Training_ZH.ipynb)**.

---

## 💬 Join the Discussion

**Discussions are open to everyone** — mathematicians, physicists, engineers, students, science journalists, and curious minds.

Whether you want to debate the boundary between abstract Sobolev spaces and fluid mechanics, report a local GPU simulation run, or ask a question about Lean 4 formal logic, you are welcome here!

| Thread Category | Discussion Thread | Focus & Topics |
|---|---|---|
| 🚀 **Welcome** | [🚀 Welcome Post & Overview](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions/1) | Research overview, resources, & paper links |
| 💬 **Community** | [💬 Community Introductions](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions/2) | Introduce yourself & your research background |
| ❓ **Q&A** | [❓ Q&A Megathread (Reddit & Community FAQs)](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions/3) | Community feedback (r/physics, r/math, r/MachineLearning) & answers |
| 💡 **Challenges** | [💡 Open Challenges: Thermodynamic Censorship](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions/4) | Lean 4 challenge: physical bounds vs blow-up |
| 🎉 **Showcase** | [🎉 Show & Tell: Reproductions & OpenFOAM Runs](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions/5) | Share local GPU benchmarks, certificates, & visualizations |

*All community members are invited to participate in the open GitHub Discussions above.*

---

## 📝 Cite This Work

```bibtex
@misc{callens2026nse,
  author       = {Callens, Xavier and {MechanicaFluidorum Program}},
  title        = {The OpenAI Navier-Stokes and Euler Blow-Up Proofs:
                  A Physical Reading, Not a Physical Refutation},
  year         = {2026},
  month        = sep,
  version      = {5.3.0},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.22777467},
  url          = {https://doi.org/10.5281/zenodo.22777467},
  note         = {SocrateAI Lab, MechanicaFluidorum Program. Concept DOI
                  10.5281/zenodo.22696717 resolves to the latest version.
                  Versions 2.0.0 (10.5281/zenodo.22725347, 22727801) carry
                  withdrawn claims; see CHANGELOG.md}
}
```

---

## 📜 License

This work is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt the material for any purpose, provided appropriate credit is given.

---

<div align="center">

*"The AI has not solved the physicist's problem. It has solved the mathematician's problem and, in doing so, illuminated the precise location of the gap between them."*

**MechanicaFluidorum Program · SocrateAI Lab · 2026**

</div>
