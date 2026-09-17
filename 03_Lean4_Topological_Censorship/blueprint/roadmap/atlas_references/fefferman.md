---
declaration: theorem
origin: cited
statement: draft
proof: draft
lean: NavierStokes.AtlasVerification.ClayAlternativeD
---
# Clay Millennium Problem Statement (Fefferman 2000)

> **Status (2026-09-17, v5.5.0): unverified draft — not a formalized proof.** The Lean declaration named above is in
> `src/drafts/AtlasReferenceVerification.lean`, which is not part of the verified set: the file contains a `sorry`
> and does not compile cleanly, and its definitions were written for the withdrawn "thermodynamic censorship"
> framing. The frontmatter previously read `proof: formalized`; that was incorrect. The cited paper's result is
> of course established in the literature; what is *not* established is this Lean rendering of it. The verified
> Lean files are listed in `03_Lean4_Topological_Censorship/README.md`.

Fefferman (2000) formalizes the 3D Incompressible Navier-Stokes Equations and specifies Alternatives A, B, C, and D.

## Formal Statement

```lean
def ClayAlternativeD (nu : ℝ) (hnu : 0 < nu) (u₀ : ℝ³ → ℝ³) (hu₀ : PhysicallyReasonableInitialData u₀)
    (f : ℝ³ → ℝ → ℝ³) (hf : ContDiff ℝ ⊤ (fun (p : ℝ³ × ℝ) => f p.1 p.2)) : Prop :=
  ...
```

The OpenAI 2026 Lean 4 formalization claimed to resolve Alternative D by constructing a manufactured $C^\infty$ forcing field $f(x,t)$.
