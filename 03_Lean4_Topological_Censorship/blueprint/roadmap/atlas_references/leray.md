---
declaration: theorem
origin: cited
statement: formalized
proof: formalized
lean: NavierStokes.AtlasVerification.leray_energy_boundedness
---
# Viscous Energy Inequality (Leray 1934)

Leray (1934) proved that weak solutions to the 3D incompressible Navier-Stokes equations satisfy the viscous energy inequality.

## Formal Theorem

```lean
theorem leray_energy_boundedness
    (nu : ℝ) (hnu : 0 < nu) (u₀ : ℝ³ → ℝ³) (f : ℝ³ → ℝ → ℝ³) (v : ℝ³ → ℝ → ℝ³) (T : ℝ)
    (h_leray : LerayEnergyInequality nu u₀ f v T)
    (h_u0 : Integrable (fun x => ‖u₀ x‖^2) volume)
    (h_f_zero : f = fun _ _ => 0) :
    ∀ t ∈ Ico 0 T, (∫ x, ‖v x t‖^2) ≤ ∫ x, ‖u₀ x‖^2
```
