---
declaration: theorem
origin: cited
statement: draft
proof: draft
lean: NavierStokes.AtlasVerification.leray_energy_boundedness
---
# Viscous Energy Inequality (Leray 1934)

> **Status (2026-09-17, v5.5.0): unverified draft — not a formalized proof.** The Lean declaration named above is in
> `src/drafts/AtlasReferenceVerification.lean`, which is not part of the verified set: the file contains a `sorry`
> and does not compile cleanly, and its definitions were written for the withdrawn "thermodynamic censorship"
> framing. The frontmatter previously read `proof: formalized`; that was incorrect. The cited paper's result is
> of course established in the literature; what is *not* established is this Lean rendering of it. The verified
> Lean files are listed in `03_Lean4_Topological_Censorship/README.md`.

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
