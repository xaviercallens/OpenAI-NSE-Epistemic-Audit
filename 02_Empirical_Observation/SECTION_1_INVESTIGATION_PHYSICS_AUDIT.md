# 🔬 Section 1: Physical Metrics of the Official OpenAI Lean 4 Construction

**Reading OpenAI's Lean 4 code, extracting its scalings, and computing where the incompressible model stops describing a real fluid**

*MechanicaFluidorum Program · SocrateAI Lab · September 2026 · revised for v5.5.0*

> **Status (v5.5.0).** Earlier versions of this section said that "laws of physics forbid the blow-up", quoted a
> Mach-0.3 breach "67 femtoseconds" before blow-up, and described a "LeanFlow" engine whose theorem "blocks and
> refuses" OpenAI's proof. All three are withdrawn. The dimensionless time $\tau$ was misread as seconds (the correct
> figure is about 6.7 **picoseconds**); no law of thermodynamics is violated inside the model; and the old
> "interception" theorem rested on an underived global enstrophy bound and is an unverified draft. OpenAI's proofs
> are correct. See `../CHANGELOG.md` and Appendix A of the paper.

---

## 📌 1. Overview

In September 2026 an OpenAI multi-agent system produced Lean 4 proofs of finite-time blow-up for the forced 3D
Navier–Stokes equations and for Euler. (Press figures of "~10,000 agents" are not stated in OpenAI's own
publications.) The official code, [`openai/NavierStokesAndEuler`](https://github.com/openai/NavierStokesAndEuler),
compiles, and the proofs are correct theorems about the incompressible continuum model.

This section extracts the construction's scalings and computes when the constructed flow leaves the regime in which
that model describes a real fluid. It is a physical reading of a correct theorem, not a refutation, and it says
nothing about Clay "Statement A" (unforced flow), which remains open.

---

## 📥 2. The official code

```bash
git clone https://github.com/openai/NavierStokesAndEuler.git
cd NavierStokesAndEuler
lake build NavierStokes.ProblemStatement   # the full library is ~580 files; build only what you need
```

Lean checks that the theorems follow from the definitions of the incompressible equations. Sound speed and molecular
structure are not part of those definitions — correctly so: they are not part of the model the Clay problem is about.

---

## 📊 3. Scalings and validity times (Directives 2–5)

Times below: $\tau$ is the construction's **dimensionless** time to blow-up; physical time is $t=T\tau$ with
$T=L_0^2/\nu=100$ s for a 1 cm water vortex.

| Script | Quantity | Result | Reading |
| :--- | :--- | :--- | :--- |
| `directive2_thermodynamic_paradox.py` | global kinetic energy $E$ | $E\sim\tau^{+0.485}\to0$ | bounded; the core's energy vanishes |
| `directive2_thermodynamic_paradox.py` | local energy density | $e_{\text{local}}\sim\tau^{-1.010}\to\infty$ | the decoupled-temperature assumption fails |
| `directive2_thermodynamic_paradox.py` | enstrophy $\Omega$ | $\Omega\sim\tau^{-0.515}\to\infty$ | total dissipated energy stays finite |
| `directive2_thermodynamic_paradox.py` | $\|u\|_{L^3}$, $\|u\|_{H^{3/2}}$ | diverge ($\tau^{-0.0067}$, $\tau^{-0.51}$) | as required of any blow-up (Escauriaza–Seregin–Šverák); expected, not a defect |
| `directive3_jacobian_instability.py` | moment-matrix conditioning | $\kappa(B)\approx4.1\times10^5$ | the raw $\kappa\sim10^{28}$ was a units artifact |
| `directive4_gevrey_regularity.py` | cutoff regularity | Gevrey index $s=1.5$ | $C^\infty$, not analytic — required for a compactly supported force |
| `directive5_mach_divergence.py` | Mach 0.3 | $\tau=6.7\times10^{-14}$, **$t\approx6.7$ ps** | compressibility effects begin |
| `directive5_mach_divergence.py` | Mach 1 | $\tau=6.2\times10^{-15}$, $t\approx0.62$ ps | sonic |
| `directive5_mach_divergence.py` | core radius at molecular size ($\mathrm{Kn}\approx1$) | $\tau=9.0\times10^{-16}$, $t\approx90$ fs | continuum description ends |

All three limits are one: on the construction's diffusive route ($\mathrm{Re}\approx1$) Mach, Knudsen and Eckert
numbers reach order one together at $\ell_*=\nu/c_s$ (0.7 nm in water, 45 nm in air).

---

## 🌊 4. What a real fluid would do there

### A. Compressibility
Mach 0.3 is the onset of compressibility effects, reached near 450 m/s in water. Whether compressibility then stops
the collapse was tested (paper §9.3): in a compressible Navier–Stokes–Fourier simulation driven the same way, on this
route the core is slowed but **not stopped** before $\ell_*$. (On a high-Reynolds, inertial route, air stops following a
driven swirl at a local Mach number of about 0.70 — a lock on Mach number, not on velocity.)

### B. Heat — constitutive assumptions, not a Second-Law violation
Viscous heating is $\Delta T\simeq u^2/c_p$: about 48 K at Mach 0.3 and 540 K at Mach 1 in water — hot, nowhere near a
plasma. Inside the model, energy balance holds and dissipation is non-negative; what fails is the assumption that
temperature is decoupled from the flow. In water, **cavitation** comes before any of this.

### C. Molecules
At $\ell_*$ the hydrodynamic description itself ends (kinetic theory: the shear mode terminates at
$k\lambda=\sqrt{\pi/2}$). A nonlinear kinetic simulation of a driven core found no arrest there. Whether thermal noise
destroys the phase coherence the **Euler** construction needs is an open question.

---

## 💻 5. Reproduce

```bash
python scripts/directive5_mach_divergence.py         # Mach / Knudsen / boiling times (dimensionless tau and t = T*tau)
python scripts/directive2_thermodynamic_paradox.py   # energy, energy density, enstrophy exponents
python scripts/directive3_jacobian_instability.py    # conditioning after non-dimensionalization
python scripts/directive4_gevrey_regularity.py       # Gevrey index of the cutoffs
python scripts/directive7_pre_singularity_simulation.py
scripts/run_benchmarks.sh                             # regenerates and checks the newer results (BENCHMARKS.md)
```

---

## 🧠 6. Formal counterpart

The verified statement is on OpenAI's **own** definitions:
[`OpenAIAdmissibility.lean`](../03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean) proves, unconditionally and
with standard axioms only, that any object with OpenAI's `CandidateProperties` exceeds every velocity-gradient bound
arbitrarily close to the blow-up time, so it leaves $|\nabla u|\lesssim c_s^2/\nu$ for every fluid and choice of units.
That labels the construction; it does not block or refute it.

---

## 🔗 7. Links

- 📄 **Paper**: [`01_Verification_Paper/OpenAI_NSE_Verification.pdf`](../01_Verification_Paper/OpenAI_NSE_Verification.pdf)
- 🧠 **Model-validity layer proposal**: [`11_Proposed_Solution_NeuroSymbolic_Engine/PROPOSED_SOLUTION_NEUROSYMBOLIC_ENGINE.md`](../11_Proposed_Solution_NeuroSymbolic_Engine/PROPOSED_SOLUTION_NEUROSYMBOLIC_ENGINE.md)
- 🛠️ **PoC proposal**: [`10_OpenAI_PoC_Proposal/OPENAI_POC_PROPOSAL.md`](../10_OpenAI_PoC_Proposal/OPENAI_POC_PROPOSAL.md)
- 🧪 **Notebook**: [Open in Colab](https://colab.research.google.com/github/xaviercallens/OpenAI-NSE-Epistemic-Audit/blob/main/07_Tout_Public_Memo/Citizen_Science_Exploration.ipynb)
