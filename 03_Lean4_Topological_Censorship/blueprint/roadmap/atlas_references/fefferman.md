---
declaration: theorem
origin: cited
statement: formalized
proof: formalized
lean: NavierStokes.AtlasVerification.ClayAlternativeD
---
# Clay Millennium Problem Statement (Fefferman 2000)

Fefferman (2000) formalizes the 3D Incompressible Navier-Stokes Equations and specifies Alternatives A, B, C, and D.

## Formal Statement

```lean
def ClayAlternativeD (nu : ℝ) (hnu : 0 < nu) (u₀ : ℝ³ → ℝ³) (hu₀ : PhysicallyReasonableInitialData u₀)
    (f : ℝ³ → ℝ → ℝ³) (hf : ContDiff ℝ ⊤ (fun (p : ℝ³ × ℝ) => f p.1 p.2)) : Prop :=
  ...
```

The OpenAI 2026 Lean 4 formalization claimed to resolve Alternative D by constructing a manufactured $C^\infty$ forcing field $f(x,t)$.
