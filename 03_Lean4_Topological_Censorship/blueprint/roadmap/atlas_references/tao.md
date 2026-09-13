---
declaration: theorem
origin: cited
statement: formalized
proof: formalized
lean: NavierStokes.AtlasVerification.tao_averaged_blowup_not_admissible
---
# Tao Averaged Navier-Stokes Blowup (Tao 2016)

Tao (2016) constructed a finite-time blowup for an averaged version of the 3D Navier-Stokes equations while maintaining finite kinetic energy.

## Formal Theorem

```lean
theorem tao_averaged_blowup_not_admissible
    (v : ℝ³ → ℝ → ℝ³) (T_blowup : ℝ) (htao : TaoAveragedSolution v T_blowup) :
    ¬ (∃ Ω_max : ℝ, ∀ t ∈ Ico 0 T_blowup, (∫ x, vorticityNorm v x t ^ 2) ≤ Ω_max)
```
