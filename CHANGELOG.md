# Changelog

## v5.0.0 — 2026-09-15 — Scientific review and remediation

This release is a full pass over every paper, script, Lean file and article in the
repository, with the aim of making each claim either derived, verified against the
OpenAI papers and Lean code, or explicitly labelled as a hypothesis. It supersedes the
"thermodynamic censorship" framing of v4.x.

### Headline scientific changes (papers)

- **One validity scale.** The physical reading is now organised around a unit-free
  result: the collapsing core has radial Reynolds number O(1), so ℓ_r ≃ √(νt) and
  u ≃ √(ν/t); compressibility, rarefaction and viscous heating all become order-one at
  the single length ℓ\* = ν/c_s (0.67 nm in water, 45 nm in air). The earlier "6.7 ps
  for a 1 cm vortex" numbers are recovered as special cases; the initial size ℓ₀ enters
  only as (ℓ₀²/νt)^h ≈ 1.2–1.3.
- **Viscous heating is u²/c_p.** Because ℓ_r² = νt exactly, ΔT = u²/c_p: 48 K at Ma = 0.3,
  540 K at Ma = 1 in water; boiling at Ma ≈ 0.37, ≈ 3–4.5 ps before blow-up. Earlier
  "plasma temperatures" and "45.6 ps" claims are withdrawn.
- **Cavitation comes first in liquids.** A vortex-core pressure deficit ρu² reaches 1 atm
  at u ≈ 14 m/s, ≈ 5 ns before blow-up (core ≈ 70 nm) — three decades before the Mach
  limit; even water's tensile strength (30–140 MPa) is reached at ≈ 17–4 ps.
- **Admissibility is a local vorticity bound.** |ω| ≲ c_s²/ν (2.2×10¹² s⁻¹ water,
  7.5×10⁹ s⁻¹ air) encodes Ma ≲ 1 and Kn ≲ 1 together; with it, "admissible on [0,T) ⇒
  no blow-up" is the Beale–Kato–Majda theorem. The constant Ω_max = 1.13×10¹³ s⁻² used
  since v4.x had no derivation anywhere in the repository and is withdrawn everywhere
  (papers, README, `physics_constants.py`, Lean draft doc-comments, table generator).
- **Lighthill "energy-budget check" removed as independent evidence.** Dimensionally,
  P_ac·t/E_core ~ Ma⁵ — it is the Mach criterion in disguise.
- **Synthetic figure removed.** `spectrum_comparison.png` drew the "OpenAI pre-singularity
  spectrum" as a hand-placed Gaussian; the flagship paper no longer presents it as a
  solver result. The unreproducible Taylor–Green/"certificate" section is removed and
  replaced by a statement of what a real numerical companion would need.
- **Citations corrected against the OpenAI PDFs.** The moment-matching system is
  Proposition B.8 / eqs. (5.10)–(5.11), not "Lemma 8.7"; "10,000 agents / 88 hours"
  appears in neither paper and is no longer stated as fact; the Euler datum is described
  as the stagewise shear-amplified packet iteration it is, with viscosity (not "Planck
  scale") as the missing physics. Bibliography entries for Schumacher et al. 2014,
  Donzis et al. 2008 and Luo–Hou 2014 corrected; Elgindi 2021, Chen–Hou 2022,
  Albritton–Brué–Colombo 2022, Foias–Holm–Titi 2001, Cheskidov et al. 2005, Bandak et al.
  2022, Zheng et al. 1991 and Caupin–Herbert 2006 added.
- **Priority-dispute paragraph reduced** to a neutral sentence (unverifiable claims about
  named individuals, sourced to Wikipedia, removed).
- Sept-12 "Thermodynamic Censorship" paper and the dual-scale/T-duality paper carry
  superseded/withdrawal notices with inline corrections; WorkStreams 1–6 rewritten to
  the positions above (WS1: BKM-based admissibility; WS2: u²/c_p; WS3: two-scale closure
  uses; WS4: cavitation first; WS5: bulk-modulus form; WS6: codimension question).

### Code

- `extract_openai_lean.py`: certificate verdict now derived from checks; Lean-4-anchored
  regexes; degraded-run flag. `directive6`: seeded RNG, result-dependent summary.
  `directive5`: analytic `tau_boil`, and the physical time unit T = ℓ₀²/ν restored in the
  heating estimate and in all printed times (τ is dimensionless). `directive2`:
  p\* = (3−2h)/(1+2h). `simu_sign_fragility_1D.py`, `simu_frustration_Z3.py`: rewritten so
  every printed verdict is computed. `thermal_derivation.py`: no magic constant.
  `zenodo_retriever.py`: frozen-snapshot vs `--live` API check. `zenodo_push.py`:
  `--publish` is opt-in with confirmation. Baseline outputs regenerated. 53/53 tests.
- Lean: 5 draft files fixed for mathlib v4.34.0-rc2 (`ContinuousMap.Basic`,
  `IntervalIntegral.Basic`), import-order bug fixed, doc-comments made honest
  (tautologies, toy types, stub demos labelled). `EulerCensorship.lean` marked superseded.

### Known limitations (unchanged in this release)

- `03_Lean4_Topological_Censorship` lemmas are not connected to OpenAI's definitions;
  only `lean_formalization/Validity/ModelValidity.lean` (v2 paper) compiles against them.
- `ThermodynamicAdmissibility.lean` still contains `sorry`; `ThermodynamicCensorship.lean`
  imports the external OpenAI package and does not build from this repository.
- No numerical realization of the OpenAI construction exists; all numerics here are
  exponent, unit and consistency checks.
- The v2 paper (`paper/where_the_continuum_ends.tex`) lives one directory above this
  repository and is not under version control here.
