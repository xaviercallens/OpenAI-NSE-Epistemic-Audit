---
declaration: theorem
origin: cited
statement: draft
proof: draft
lean: NavierStokes.AtlasVerification.bkm_regularity_extension
---
# Beale-Kato-Majda Vorticity Criterion (BKM 1984)

> **Status (2026-09-17, v5.5.0): unverified draft — not a formalized proof.** The Lean declaration named above is in
> `src/drafts/AtlasReferenceVerification.lean`, which is not part of the verified set: the file contains a `sorry`
> and does not compile cleanly, and its definitions were written for the withdrawn "thermodynamic censorship"
> framing. The frontmatter previously read `proof: formalized`; that was incorrect. The cited paper's result is
> of course established in the literature; what is *not* established is this Lean rendering of it. The verified
> Lean files are listed in `03_Lean4_Topological_Censorship/README.md`.
> Note also that the statement as written is weaker than it looks and not the BKM theorem: a finite time
> integral of `‖ω‖∞` does not by itself exclude `‖ω‖∞ → ∞` as `t → T` (e.g. `(T − t)^{-1/2}`). The admissibility
> result this project actually proved on OpenAI's objects needed only an elementary periodic-cell lemma
> (`OpenAIAdmissibility.lean`).

BKM (1984) established that a smooth fluid solution extends beyond time $T$ if and only if the time integral of the $L^\infty$ norm of the vorticity field $\omega = \nabla \times u$ remains finite.

## Formal Theorem

```lean
theorem bkm_regularity_extension
    (v : ℝ³ → ℝ → ℝ³) (T : ℝ) (hBKM : BKM_VorticityIntegrable v T) :
    ¬ Tendsto (fun t => ⨆ x : ℝ³, vorticityNorm v x t) (𝓝[<] T) atTop
```
