# Changelog

## v5.3.0 — 2026-09-16 — The kinetic lock is a termination, not a drain; first Lean bridge to OpenAI's objects

### Correction to v5.2.0

v5.2.0 said "the lock that operates where the continuum ends is dissipative, which is what kinetic
theory supplies", implying real physics at `ℓ*` acts like the hyperviscous barrier that §9.2 found to
be the stronger of two model regularizations. **That implication is withdrawn.** The exact shear-mode
spectrum of the BGK kinetic model (`experiments/lock_k_kinetic_spectrum.py`; two independent methods
agreeing to 3×10⁻¹²; numbers re-derived and re-verified from scratch) shows:

- damping `Γ = νk²[1 − (kλ)² + …]` — the first kinetic correction **reduces** damping (Burnett
  coefficient +1, derived and confirmed), the opposite sign to hyperviscosity; truncated at that order
  it becomes unstable for `kλ > 1` (Bobylev), the full mode does not;
- the damping never exceeds the collision rate `1/τ` — exact, since the linearized operator is skew
  advection plus `−(1/τ)(I − P)`, the spectral twin of the Lean H-theorem;
- the hydrodynamic shear mode **ceases to exist** at `kλ = √(π/2) ≈ 1.2533` (closed form);
- at `kλ = 1` the barrier damps 1.43× harder than kinetic theory.

BGK collisions are dissipative thermodynamically, but they are not a stronger drain on small scales.
**The lock at `ℓ*` is the end of the hydrodynamic description** — the paper's original §5 reading,
now with a mechanism. The gate-versus-drain comparison stands as a ranking of two *models*.

### Paper (24 pages)

- §9.2 "Which lock acts where the continuum ends" rewritten with the BGK dispersion relation
  (Eq. `bgk-shear`), the termination wavenumber (Eq. `bgk-termination`), and the corrected
  conclusion; a clause added that the gate–drain ranking is a model comparison. Abstract and
  conclusion corrected accordingly. New reference: Bobylev 1982.
- §10.3 Lean status: 45 theorems in five files, one now about OpenAI's actual objects.
- Direction 2 rewritten: the formal reduction is **done**, and its hypothesis is **not**
  Beale–Kato–Majda but an elementary periodic-cell lemma (cell mean obeys `d⟨u⟩/dt = ⟨f⟩`; a gradient
  bound `C` confines `u` within `√3·C` of it), unformalized only for want of torus integration by
  parts in Mathlib. The honest reading is stated: the result is close to "velocity blow-up forces
  gradient blow-up", valuable as the first bridge, not as new physics.

### Lean 4

- `OpenAIAdmissibility.lean` (7 theorems) imports OpenAI's `NavierStokes.ProblemStatement` unchanged.
  Unconditionally, a candidate's velocity gradient is bounded on every `[0, 1−δ]`; given the labelled
  hypothesis, any object with OpenAI's `CandidateProperties` exceeds every gradient bound in every
  window before `t = 1`, hence leaves the admissible set for every fluid and unit choice. Compiled
  inside OpenAI's project; independently re-verified (0 errors, 0 warnings, 0 `sorryAx`, standard
  axioms only). Build instructions in the module header.

### Also

- `DIRECTION1_RESULTS.md` and `DUAL_SCALE_LOCK_PROGRAMME.md` carry explicit correction notes rather
  than silent rewrites.
- HuggingFace card and Zenodo metadata brought to v5.3.0; the Zenodo push script retries 5xx
  responses and accepts `--draft-id`.

### Published

- **Zenodo:** v5.3.0 published as **10.5281/zenodo.22777467** (concept DOI
  **10.5281/zenodo.22696717**, which always resolves to the latest version). Published directly from a
  draft verified beforehand against the committed release: 32/32 files, every checksum matching,
  metadata and description checked. An earlier attempt had been delayed by a Zenodo-side 504 outage.
- **HuggingFace:** `callensxavier/OpenAI-NSE-Thermodynamic-Censorship` at v5.3.0, verified live (paper
  PDF byte-identical to the release). The card previously labelled record 22696718 as the "concept
  record"; that id is an earlier version record, and the card now cites the concept DOI.

### Pending

- The `96³` forced-core crossing sweep.

## v5.2.0 — 2026-09-16 — 3D solver, cutoff law tested, forced core, gate vs drain, 38 Lean theorems

### Paper (`01_Verification_Paper/`, 23 pages)

- **New §9, "Testing the Cutoff Regularization Hypothesis".** The cutoff law the Outlook stated as
  untested is tested. It is exact given its premise (all four exponents reproduced as identities to
  machine precision), but the premise — a `Re ≈ 1` diffusive core — is never produced by generic
  data: in a dyadic cascade the arrest-scale velocity follows `k^−0.345` (Kolmogorov `−1/3`), not
  the law's `k^+1`, with Re 5–1200 at the arrest scale. A 3D DNS resolution constraint
  `n > 3√(ω₀Re)` explains why earlier sweeps saw no effect at all.
- **Leray-α: gate, not drain.** Leray-α suppresses peak vorticity 3.3× while *retaining* more
  energy (its transport term does no work), where hyperviscosity dissipates. Distinguished
  explicitly from the hyperviscous barrier the earlier test used; the two had been conflated.
- **§9.1, a forced collapsing core.** A manufactured `Re = 1` collapse, sustained by its own
  Navier–Stokes residual, tracks the analytic target to `1.7×10⁻⁷`. The barrier's engagement
  `B/F` collapses onto the single variable `α′/(ντ)` (per-run prefactor `0.188 ± 0.010`), which is
  sufficient for all four arrest exponents. A lagging-core explanation of the sub-unity slope was
  tested and refuted.
- **§9.2, gate or drain on a `Re ≈ 1` collapse.** With axial structure, Leray-α and LANS-α lag the
  collapse by 0.2–0.4%; a barrier at the same scale lags it by 5–45%. Against the forcing, the
  nonlinearity is only ~5% of the dynamics, and a transport filter can act only through it. The
  gate–barrier crossover is an exact identity,
  `Re_× = ‖(L_barrier − L_ν)U‖ / ‖N_α(U) − N(U)‖`, ranging 8–142 and largest where arrest occurs.
- **Which lock acts where the continuum ends.** The validity scale is the mean free path with a
  derived constant (`ℓ*/λ = c̄/2c_s = 0.67` for air, matching the independent 45 nm / 68 nm).
  The operative lock at `ℓ*` is dissipative — collisional relaxation — not a Lagrangian-averaged
  transport filter. The LANS-α derivation conjecture is relocated to `Re ≳ 10–100`, not refuted.
- **§10.3 Lean status** updated; **Directions 1–3** updated with what is built, what is pending, and
  an uninformative first Lock-F attempt (`σ < 0`); abstract and conclusion updated. New references:
  Holm–Marsden–Ratiu 1998, Golse–Saint-Raymond 2004, Bhatnagar–Gross–Krook 1954.

### Code and data (`05_Community_Research_Directions/experiments/`)

- `spectral3d.py`: 3D pseudo-spectral NSE (rotational form, FFT Leray projection, 2/3 dealiasing,
  integrating-factor RK4); hyperviscous barrier; **Leray-α** (divergence form) and **LANS-α**
  (rotational form on `v`); Landau–Lifshitz noise with FDT calibration; runtime validity monitor;
  forcing hooks. Validated against the Taylor–Green Re=1600 benchmark (dissipation peak `t = 9.14`
  vs published `9.0`).
- `forced_core.py`, `forced_core_axial.py`, `plot_forced_core.py`: the forced-core test bed and its
  axial extension. `shell_mach_cap.py`, `lock_f_coherence.py`, `shell_cutoff_law.py`,
  `sweep_cutoff_law.py`, `analyse_cutoff_law.py`, `noise_and_monitor.py`, `validate_tgv3d.py`.
- Bugs fixed that the tests caught: a duplicated final time sample that made every
  `np.gradient`-based dE/dt diagnostic NaN; a key collision that overwrote the dissipation time
  series with the operator name; a vorticity-inversion sign error; a core-size estimator biased 12%
  by tail truncation.

### Lean 4 (`03_Lean4_Topological_Censorship/src/`, 38 theorems, standard axioms only)

- `CoreScaling.lean` — Proposition 5.1 as an equality chain from the diffusive core scalings.
- `LerayAlphaFilter.lean` — the Leray-α filter-symbol bounds.
- `LatticeBGKEntropy.lean` — H-theorem for the discrete BGK collision step.
- `AlphaEnergyIdentity.lean` — a projected skew term changes energy at second order; a dissipative
  term removes it at first order.
- Every `#print axioms` is exactly `[propext, Classical.choice, Quot.sound]`; zero `sorryAx`,
  independently re-verified. **None is connected to OpenAI's definitions yet** — stated in each file.

### Programme documents (`05_Community_Research_Directions/`)

`DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md`, `DUAL_SCALE_LOCK_PROGRAMME.md`,
`LERAY_ALPHA_DUAL_SCALE_LOCK.md`, `WEEK1_LOCK_RESULTS.md`, `DIRECTION1_RESULTS.md`,
`RICCATI_THRESHOLD_CHECK.md`, `experiments/RESULTS.md`.

### Pending

- The `96³` forced-core sweep that reaches the `B/F = 1` crossing (for the arrest exponents directly).
- A collapsing axial scale; azimuthal stability of the forced column; the construction's own profile
  with `h > 0`.
- The Zenodo draft for record 22696718 (new version 22777467) remains **unpublished** pending review.

## v5.1.0 — 2026-09-15 — Peer review response, table fixes, Zenodo record corrected

- Addressed an open peer review of the flagship paper (recorded verbatim in
  `01_Verification_Paper/PEER_REVIEW_2026-09-15.md`, with a point-by-point authors'
  response): consolidated "earlier drafts" meta-commentary out of the running text into
  a new Appendix A; moved individually-named Reddit commenters out of the main text
  into Acknowledgments and a new Appendix B preserving the full quotations; fixed a
  genuine LaTeX table overflow (Table 5, 106.7pt overfull hbox that was merging rows
  and truncating text) and rebuilt two other tables (`tabularx`, split columns) for
  robustness rather than relying on manually-sized `p{}` columns.
- **`zenodo_push.py` rewritten.** The script still targeted Zenodo record 22696718 with
  metadata and a file list from the withdrawn "Version 2" / Thermodynamic Censorship
  framing — a "10²⁸-digit structural instability", a global enstrophy-censorship axiom,
  "vacuous" physics, femtosecond-scale timings, and paths (`01_Challenger_Paper/...`)
  that no longer exist. Had this been run unmodified, it would have re-published
  already-withdrawn claims under a permanent DOI. Rewrote the title, description and
  `FILES_TO_PACKAGE` to match the current v5.0.0 paper, corrected the archive paths,
  and uploaded a corrected **draft** (record 22777467) for manual review; it has
  **not** been published (no DOI minted) — see the release notes for the review link.
- **HuggingFace dataset corrected.** The live dataset repo
  `callensxavier/OpenAI-NSE-Thermodynamic-Censorship` was found serving the withdrawn
  "Version 2" paper, an uncontextualized copy of `ThermodynamicCensorship.lean`, and a
  directive-5 output log with the exact femtosecond/picosecond unit bug this project's
  review caught (`Ma > 0.3 at tau ~ 6.7e-14 s`, twelve orders of magnitude off) --
  publicly live under a real name. Rewrote `scripts/huggingface_upload.py` (file list,
  dataset card, abort-before-upload safety check) and ran it: current paper,
  WorkStreams, CHANGELOG, peer review, regenerated directive outputs, and a corrected
  README are now live; the retracted paper and Lean file are kept under `superseded/`
  with the same withdrawal context as the Zenodo bundle.
  **Manual cleanup still needed:** a few stale duplicates remain live alongside the
  corrected files -- `REPO_README.md` (old card, still says "vacuity"), an old
  `paper/OpenAI_NSE_EpistemicAudit.pdf`/`.tex` copy, and an uncontextualized root-level
  `lean4/ThermodynamicCensorship.lean` -- because file deletion on that host was outside
  this session's permitted actions; delete them via the HuggingFace web UI or
  `huggingface_hub.HfApi.delete_file`.
- `deploy_huggingface.sh` (a *different*, unused script targeting a separate HF repo for
  the withdrawn Bi-Helmholtz/T-duality paper and `EulerCensorship.lean`, which has 7
  `sorry`s and a vacuous `True` conclusion per the v2 paper's own errata table) was left
  untouched and was not run.

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
