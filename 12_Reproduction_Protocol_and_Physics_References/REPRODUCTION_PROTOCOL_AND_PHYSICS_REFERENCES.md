# 🔬 Protocol for Reproduction, Physical Principles, & Literature References

**How to reproduce this project's numerical and formal results, what physics they rest on, and the literature they cite**

*MechanicaFluidorum Program · SocrateAI Lab · September 2026 · rewritten for v5.5.0*

> **Status (v5.5.0).** Earlier versions of this document explained the results as "Thermodynamic
> Censorship" and presented `AtlasReferenceVerification.lean` as kernel-verified. Both are withdrawn: the
> censorship framing is replaced by a *physical reading* of a correct proof, and that Lean file is an
> unverified draft (it contains `sorry`) now in `03_Lean4_Topological_Censorship/src/drafts/`. The authoritative
> record of every number below is [`BENCHMARKS.md`](../BENCHMARKS.md), which regenerates them.

---

## 📌 1. What is being reproduced

OpenAI's Lean 4 proofs of finite-time blow-up (forced 3D Navier–Stokes; Euler) are **correct**. This project
does not dispute them. It asks what the constructed flow does physically, and answers:

- the Navier–Stokes core keeps a Reynolds number of order one, so its scales are diffusive; Mach, Knudsen and
  Eckert numbers all become order one together at $\ell_* = \nu/c_s$ (0.7 nm in water, 45 nm in air);
- in water that happens a few **picoseconds** before the singularity (Mach 0.3 about 6.7 ps before; core radius
  at molecular size about 90 fs before); heating there is hundreds of kelvin, not a plasma; cavitation comes
  earlier still;
- which physics a blow-up meets first depends on its route ($\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$), and what
  happens after has been simulated (kinetic, compressible, thermal) — with the outcomes summarised in §3.

Nothing here bears on Clay "Statement A" (unforced Navier–Stokes), which remains open.

---

## 🛠️ 2. Step-by-step reproduction

### Phase 1: environment
```bash
git clone https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit.git
cd OpenAI-NSE-Epistemic-Audit
pip install numpy scipy matplotlib sympy mpmath pytest
# optional: Rust (cargo) for 05_Community_Research_Directions/kinetic_lock_rs;
# Lean 4 v4.34.0-rc2 + OpenAI's NavierStokesAndEuler project for the Lean files
```

### Phase 2: everything at once (recommended)
```bash
scripts/run_benchmarks.sh          # tests, BGK spectrum, 32^3 forced core, Rust gates, all Lean files
scripts/run_benchmarks.sh --full   # adds the compressible/thermal physics ladder and the axial runs
```
It never overwrites committed results; it regenerates them in `benchmark_runs/` and checks every number
against the committed data (54/54 checks at v5.5.0). See [`BENCHMARKS.md`](../BENCHMARKS.md).

### Phase 3: individual pieces
```bash
python -m pytest -q                                   # full Python test suite
python scripts/directive5_mach_divergence.py         # Mach / Knudsen / boiling times (tau is dimensionless; t = T*tau)
python scripts/directive2_thermodynamic_paradox.py   # energy vs energy-density scalings
cd 05_Community_Research_Directions/experiments
python lock_k_kinetic_spectrum.py                    # exact BGK shear spectrum
python compressible_core_study.py                    # compressible / thermal forced core
```

### Phase 4: Lean 4
The verified files import OpenAI's `NavierStokes.*` modules and compile inside OpenAI's project:
```bash
cd NavierStokesAndEuler                               # OpenAI's repository, Mathlib oleans built
lake build NavierStokes.PeriodicUniqueness
lake env lean <path>/03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean
```
Nine verified files, 74 declarations, no `sorry`, standard axioms only — listed in
[`03_Lean4_Topological_Censorship/README.md`](../03_Lean4_Topological_Censorship/README.md).

---

## 🌌 3. The physics, stated as it now stands

### A. One validity scale on the construction's route
The incompressible equations assume constant density, a continuum, and a temperature decoupled from the flow.
For a core with $\mathrm{Re}=u\ell/\nu\approx1$ the Mach number $u/c_s$, the Knudsen number $\ell_*/\ell$ and the
Eckert number all reach order one at the same scale $\ell_*=\nu/c_s$. Equivalently the local bound
$|\nabla u|\lesssim c_s^2/\nu$ fails. Mach 0.3 is the usual onset of compressibility effects; Mach 1 is sonic.

### B. No law of thermodynamics is violated
Inside the idealised model, energy balance holds and dissipation is non-negative. What stops holding is the
model's idealisation: viscous heating $\Delta T\simeq u^2/c_p$ (an upper estimate — the v5.5.0 compressible
simulation measured a coefficient from 0.35 at Mach 0.4 to about 1 near Mach 1) is no longer negligible.

### C. The regime map
$\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$ (proved in `BlowupRegimeMap.lean`):
- **diffusive route** ($\mathrm{Re}\approx1$, OpenAI's construction): everything at $\ell_*$;
- **inertial route** ($\mathrm{Re}\to\infty$, Tao-type): compressibility first, inside the continuum, at $\mathrm{Re}\,\ell_*$;
- **bounded-velocity route** (forced Euler with bounded velocity): viscosity first, at $\ell_*/\mathrm{Ma}$.

### D. What happens after the model fails — measured, not assumed
- **Kinetic theory**: the hydrodynamic shear mode ends at $k\lambda=\sqrt{\pi/2}$; damping is *below* $\nu k^2$ and
  never exceeds the collision rate. A nonlinear kinetic simulation of a driven core finds **no arrest** there.
- **Compressibility and heat**: on OpenAI's route they slow the driven core but do not stop it before $\ell_*$.
  On the inertial route, air in a 1D compressible simulation stops following the driven swirl at a **local Mach
  number of about 0.70** — a lock on Mach number, not on velocity or size.
- **Liquids**: cavitation first — core pressure at vapour pressure at about 14 m/s with the $\tfrac12\rho u^2$
  estimate, about 7.6 m/s with the exact Gaussian-core coefficient 1.70.
- **Regularized models**: a Leray-α filter of width $\ell_*$ does **not** represent the fluid at its continuum
  limit — the filter width is absent from the linearized dynamics. Its global regularity is a theorem about a
  different equation.
- **Open**: whether molecular/thermal noise destroys the phase coherence the Euler construction needs.

---

## 📜 4. Literature (archived in `references/` where marked)

1. **Fefferman, C. (2000)**, *Existence and Smoothness of the Navier–Stokes Equation*, Clay Millennium Problem statement. 📄 `references/Fefferman_2000_Navier_Stokes.pdf`
2. **Leray, J. (1934)**, *Sur le mouvement d'un liquide visqueux emplissant l'espace*, Acta Math. 63, 193–248.
3. **Beale, J. T., Kato, T., Majda, A. (1984)**, *Remarks on the breakdown of smooth solutions for the 3-D Euler equations*, Comm. Math. Phys. 94, 61–66 (blow-up requires $\int_0^T\|\omega\|_{L^\infty}dt=\infty$).
4. **Escauriaza, L., Seregin, G., Šverák, V. (2003)**, *$L_{3,\infty}$-solutions of Navier–Stokes equations and backward uniqueness*, Russian Math. Surveys 58(2), 211. 📄 `references/ESS_2003_L3_Infinity_Backward_Uniqueness.pdf`
5. **Tao, T. (2016)**, *Finite time blowup for an averaged three-dimensional Navier–Stokes equation*, J. Amer. Math. Soc. 29(3), 601–674. 📄 `references/Tao_2016_Averaged_NSE_Blowup.pdf`
6. **Foias, C., Holm, D. D., Titi, E. S. (2001)** and **Cheskidov, A., Holm, D. D., Olson, E., Titi, E. S. (2005)** — the Leray-α / Navier–Stokes-α models.
7. **Merle, F., Raphaël, P., Rodnianski, I., Szeftel, J. (2022)**, *On the implosion of a compressible fluid II*, Ann. of Math. 196, 779–889; **Buckmaster, T., Cao-Labora, G., Gómez-Serrano, J. (2025)**, *Smooth imploding solutions for 3D compressible fluids*, Forum Math. Pi 13, e6.
8. *Blowup for the Euler equations with smooth forcing*, manuscript (2026), https://cims.nyu.edu/~tristanb/euler.pdf.

The full bibliography is in the paper.

---

## 🔗 5. Related resources

- 📄 **Paper**: [`01_Verification_Paper/OpenAI_NSE_Verification.pdf`](../01_Verification_Paper/OpenAI_NSE_Verification.pdf)
- 🧮 **Benchmarks**: [`BENCHMARKS.md`](../BENCHMARKS.md)
- 🧪 **Research programme**: [`05_Community_Research_Directions/README.md`](../05_Community_Research_Directions/README.md)
- 🧠 **Model-validity layer proposal**: [`11_Proposed_Solution_NeuroSymbolic_Engine/PROPOSED_SOLUTION_NEUROSYMBOLIC_ENGINE.md`](../11_Proposed_Solution_NeuroSymbolic_Engine/PROPOSED_SOLUTION_NEUROSYMBOLIC_ENGINE.md)
- 🧪 **Notebook**: [Open in Colab](https://colab.research.google.com/github/xaviercallens/OpenAI-NSE-Epistemic-Audit/blob/main/07_Tout_Public_Memo/Citizen_Science_Exploration.ipynb)
- Release v5.5.0 · Zenodo concept DOI [10.5281/zenodo.22696717](https://doi.org/10.5281/zenodo.22696717) (v5.5.0: [10.5281/zenodo.22806767](https://doi.org/10.5281/zenodo.22806767))
