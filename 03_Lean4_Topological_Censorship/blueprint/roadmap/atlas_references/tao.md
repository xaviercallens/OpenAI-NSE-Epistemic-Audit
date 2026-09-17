---
declaration: theorem
origin: cited
statement: draft
proof: draft
lean: NavierStokes.AtlasVerification.tao_averaged_blowup_not_admissible
---
# Tao Averaged Navier-Stokes Blowup (Tao 2016)

> **Status (2026-09-17, v5.5.0): unverified draft — not a formalized proof.** The Lean declaration named above is in
> `src/drafts/AtlasReferenceVerification.lean`, which is not part of the verified set: the file contains a `sorry`
> and does not compile cleanly, and its definitions were written for the withdrawn "thermodynamic censorship"
> framing. The frontmatter previously read `proof: formalized`; that was incorrect. The cited paper's result is
> of course established in the literature; what is *not* established is this Lean rendering of it. The verified
> Lean files are listed in `03_Lean4_Topological_Censorship/README.md`.
> On Tao (2016) this project's current reading is different: his blow-up is an *inertial-route* scenario (stage
> Reynolds number → ∞), so the first physical assumption it would violate is incompressibility, at `Re·ℓ*`, inside
> the continuum — formalized as algebra in `BlowupRegimeMap.lean` (verified), paper §9.4.

Tao (2016) constructed a finite-time blowup for an averaged version of the 3D Navier-Stokes equations while maintaining finite kinetic energy.

## Formal Theorem

```lean
theorem tao_averaged_blowup_not_admissible
    (v : ℝ³ → ℝ → ℝ³) (T_blowup : ℝ) (htao : TaoAveragedSolution v T_blowup) :
    ¬ (∃ Ω_max : ℝ, ∀ t ∈ Ico 0 T_blowup, (∫ x, vorticityNorm v x t ^ 2) ≤ Ω_max)
```
