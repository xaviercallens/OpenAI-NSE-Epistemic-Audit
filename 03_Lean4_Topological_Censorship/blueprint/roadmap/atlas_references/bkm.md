---
declaration: theorem
origin: cited
statement: formalized
proof: formalized
lean: NavierStokes.AtlasVerification.bkm_regularity_extension
---
# Beale-Kato-Majda Vorticity Criterion (BKM 1984)

BKM (1984) established that a smooth fluid solution extends beyond time $T$ if and only if the time integral of the $L^\infty$ norm of the vorticity field $\omega = \nabla \times u$ remains finite.

## Formal Theorem

```lean
theorem bkm_regularity_extension
    (v : ℝ³ → ℝ → ℝ³) (T : ℝ) (hBKM : BKM_VorticityIntegrable v T) :
    ¬ Tendsto (fun t => ⨆ x : ℝ³, vorticityNorm v x t) (𝓝[<] T) atTop
```
