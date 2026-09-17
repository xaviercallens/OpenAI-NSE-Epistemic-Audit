# Meta ATLAS Formalization of Navier-Stokes References

This chapter documents **draft** Lean 4 renderings of five foundational reference papers, written under the project's earlier
"thermodynamic censorship" framing (withdrawn). None of the pages below is a verified formalization: the underlying file
`src/drafts/AtlasReferenceVerification.lean` contains a `sorry`, does not compile against the current toolchain
(38 errors, re-checked 2026-09-17), and is outside the verified set. They are kept for the
record and as a starting point. The verified Lean results of this project (nine files, 74 declarations, standard axioms
only) are listed in `03_Lean4_Topological_Censorship/README.md`.

## Articles
- [Clay Millennium Problem Statement (Fefferman 2000)](fefferman.md)
- [Viscous Energy Inequality (Leray 1934)](leray.md)
- [Enstrophy Blowup Criterion (Beale-Kato-Majda 1984)](bkm.md)
- [L3,infinity Regularity Criterion (Escauriaza-Seregin-Sverak 2003)](ess.md)
- [Averaged NSE Blowup (Tao 2016)](tao.md)
