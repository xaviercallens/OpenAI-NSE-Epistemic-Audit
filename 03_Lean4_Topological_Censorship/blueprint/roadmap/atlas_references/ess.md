---
declaration: theorem
origin: cited
statement: draft
proof: draft
lean: NavierStokes.AtlasVerification.ess_no_blowup_under_l3_bound
---
# Escauriaza-Seregin-Sverak L3,infty Regularity (ESS 2003)

> **Status (2026-09-17, v5.5.0): unverified draft — not a formalized proof.** The Lean declaration named above is in
> `src/drafts/AtlasReferenceVerification.lean`, which is not part of the verified set: the file contains a `sorry`
> and does not compile cleanly, and its definitions were written for the withdrawn "thermodynamic censorship"
> framing. The frontmatter previously read `proof: formalized`; that was incorrect. The cited paper's result is
> of course established in the literature; what is *not* established is this Lean rendering of it. The verified
> Lean files are listed in `03_Lean4_Topological_Censorship/README.md`.

ESS (2003) proved that if the velocity field remains uniformly bounded in $L^3(\mathbb{R}^3)$ up to time $T$, no finite-time singularity can occur at $T$.

## Formal Theorem

```lean
theorem ess_no_blowup_under_l3_bound
    (v : ℝ³ → ℝ → ℝ³) (T : ℝ) (hESS : ESS_L3Bounded v T) :
    ¬ Tendsto (fun t => L3Norm v t) (𝓝[<] T) atTop
```
