---
declaration: theorem
origin: cited
statement: formalized
proof: formalized
lean: NavierStokes.AtlasVerification.ess_no_blowup_under_l3_bound
---
# Escauriaza-Seregin-Sverak L3,infty Regularity (ESS 2003)

ESS (2003) proved that if the velocity field remains uniformly bounded in $L^3(\mathbb{R}^3)$ up to time $T$, no finite-time singularity can occur at $T$.

## Formal Theorem

```lean
theorem ess_no_blowup_under_l3_bound
    (v : ℝ³ → ℝ → ℝ³) (T : ℝ) (hESS : ESS_L3Bounded v T) :
    ¬ Tendsto (fun t => L3Norm v t) (𝓝[<] T) atTop
```
