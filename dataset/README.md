---
license: cc-by-4.0
task_categories:
  - text-generation
  - text-classification
tags:
  - navier-stokes
  - fluid-dynamics
  - formal-verification
  - lean4
  - millennium-prize
  - openai
  - epistemic-audit
  - thermodynamic-censorship
  - computational-physics
  - mathematical-physics
language:
  - en
size_categories:
  - n<1K
pretty_name: "OpenAI NSE Epistemic Audit — Thermodynamic Censorship Dataset"
---

# OpenAI Navier-Stokes Epistemic Audit: Thermodynamic Censorship Dataset

## Overview

This dataset accompanies the paper **"Thermodynamic Censorship of Navier-Stokes Singularities: Why Mathematical Blow-ups Are Physically Unrealizable"** — an independent epistemic audit of OpenAI's Lean 4 formalized proof of finite-time blow-up for the forced 3D incompressible Navier-Stokes equations (Alternatives C & D of the Clay Millennium Prize Problem).

## Key Findings

| Directive | Title | Verdict |
|---|---|---|
| 1 | Lean 4 Formal Audit | ✅ CLEAN — 0 sorry, 0 axioms |
| 2 | Thermodynamic Paradox | 🔴 DIVERGENT — enstrophy → ∞ |
| 3 | Jacobian Instability | 🔴 κ ~ 10²⁸ |
| 4 | Gevrey Regularity | ✅ No loophole — Gevrey-2 ⊂ C∞ |
| 5 | Mach Number Divergence | 🔴 Ma > 0.3 at τ ~ 10⁻¹⁴ s |
| 6 | Thermal Noise Decoupling | 🔴 Cancellation fails at X_R > 500 |

## Dataset Contents

### `audit_results.json`
Structured results from all 6 computational directives, including:
- Formal verification findings (sorry count, axiom count, type checks)
- Scaling exponents for energy, enstrophy, L^p norms
- Condition number tables for the 5-moment Jacobian
- Gevrey index measurements
- Mach number trajectory data
- Thermal noise Monte Carlo results

### `scripts/`
Python scripts (SymPy, NumPy, SciPy) implementing each computational directive:
- `directive2_thermodynamic_paradox.py` — Energy density divergence analysis
- `directive3_jacobian_instability.py` — Condition number computation
- `directive4_gevrey_regularity.py` — Gevrey index measurement
- `directive5_mach_divergence.py` — Mach number trajectory
- `directive6_thermal_instability.py` — Monte Carlo thermal noise simulation

### `03_Lean4_Topological_Censorship/src/`
- `ThermodynamicCensorship.lean` — Lean 4 formalization of the bounded enstrophy axiom

### `04_Thermodynamic_Censorship_Paper/`
- `paper.tex` — Full LaTeX paper

### `01_Challenger_Paper/`
- `OpenAI_NSE_EpistemicAudit.tex` — Original epistemic audit paper

## Citation

```bibtex
@article{callens2026thermodynamic,
  title={Thermodynamic Censorship of Navier-Stokes Singularities: Why Mathematical Blow-ups Are Physically Unrealizable},
  author={Callens, Xavier},
  journal={Preprint},
  year={2026},
  note={Socrate AI Lab, MechanicaFluidorum Program}
}
```

## License

CC-BY-4.0
