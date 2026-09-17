# 03 — Lean 4 formalization

*(The folder name "Topological Censorship" is kept for history; that framing has been withdrawn — see `../CHANGELOG.md`.)*

**Status at v5.5.0 (2026-09-17):** nine verified files, **74 declarations** checked with `#print axioms`, no `sorry`, no axioms beyond Lean's standard `propext`, `Classical.choice`, `Quot.sound`. Each file's header has a "what is proved / what is not proved" section; read it before citing a theorem.

## Verified files (`src/`)

| File | `#print axioms` checks | What it proves | What it does **not** prove |
|---|---|---|---|
| [`OpenAIAdmissibility.lean`](src/OpenAIAdmissibility.lean) | 15 | On OpenAI's **own** definitions (`VelocityField`, `spatialDerivative`, `CandidateProperties`, imported unchanged): any candidate has a bounded gradient on every $[0,1-\delta]$ (`gradient_bounded_before`), yet exceeds **every** gradient bound arbitrarily close to $t=1$ (`exits_admissible_near_one'`), so it is not admissible for any fluid $(c,\nu)$ in any units $(L,U)$ (`candidate_not_admissible'`, `candidate_not_admissibleScaled'`). The former hypothesis `BKMHypothesis` is proved as `bkmHypothesis_holds` via the periodic mean-velocity identity $d\langle u\rangle/dt = \langle f\rangle$, using OpenAI's `NavierStokes.PeriodicIntegration` and `PeriodicUniqueness`. | Anything about physical fluids beyond the definitional content of the bound; that the construction exists. `BKMHypothesis` is named for continuity but is **weaker than Beale–Kato–Majda** — an elementary periodic-cell lemma. The result is close to "velocity blow-up forces gradient blow-up". |
| [`CoreScaling.lean`](src/CoreScaling.lean) | 10 | Proposition 5.1 of the paper as identities on the diffusive scaling $\ell=\sqrt{\nu t}$, $u=\sqrt{\nu/t}$: $\mathrm{Re}_{\text{core}}=1$, Mach and Knudsen times, Eckert number one, and all limits meeting at $\ell_*=\nu/c$, $t_*=\nu/c^2$ (`one_scale`). | Nothing about the Navier–Stokes equations or any PDE; the coincidence at $\ell_*$ *is* this equality chain. |
| [`KineticSpectralCap.lean`](src/KineticSpectralCap.lean) | 6 | For a skew streaming operator plus projected BGK relaxation $-(1/\tau)(I-P)$: every eigenvalue satisfies $-1/\tau \le \operatorname{Re}\mu \le 0$ (`eigenvalue_damping_cap`); the discrete-velocity streaming is skew and the mean projection is an orthogonal projection. | The termination wavenumber $k\lambda=\sqrt{\pi/2}$ (computed numerically, not formalized); anything nonlinear. |
| [`BlowupRegimeMap.lean`](src/BlowupRegimeMap.lean) | 13 | The von Kármán relation $\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$; admissibility $u/\ell\le c^2/\nu \iff \mathrm{Ma}^2\le\mathrm{Re}$; the three routes to a singularity (diffusive: $\mathrm{Kn}=\mathrm{Ma}$, sonic at $\ell_*$; inertial: sonic at $\mathrm{Re}\,\ell_*$ with $\mathrm{Kn}<1$; bounded velocity: viscous scale $\ell_*/\mathrm{Ma}>\ell_*$); stage Reynolds number $\to\infty$ along a cascade with Tao's ratios; sign of the density-hole feedback; the atomistic bound $\lvert v\rvert\le\sqrt{2E/m}$. | Anything about solutions of a PDE: these are the algebraic facts that decide which physical assumption a scenario violates first. |
| [`LerayAlphaLinearization.lean`](src/LerayAlphaLinearization.lean) | 4 | For any bounded bilinear $B$ and bounded linear filter $F$, $u\mapsto B(Fu,u)$ has zero derivative at rest, so Leray-α, LANS-α and Navier–Stokes share one linearization for every α (`linearization_independent_of_filter`); $\nu k^2$ exceeds any finite cap $1/\tau$. This is the formal reason the "α = ℓ* physical anchor" claim is withdrawn. | That Leray-α is a bad turbulence closure (it is not); anything about its nonlinear dynamics or its global-regularity theorem. |
| [`LatticeBGKEntropy.lean`](src/LatticeBGKEntropy.lean) | 7 | Discrete BGK collision step: positivity, mass conservation, fixed point, and decrease of relative entropy (an H-theorem for the step). | Anything about the Boltzmann equation or Navier–Stokes. |
| [`NonlinearBGKEntropy.lean`](src/NonlinearBGKEntropy.lean) | 7 | The step used by the Rust solver: the entropic discrete Maxwellian minimizes $H$ under mass/momentum constraints; the BGK step conserves mass and momentum, preserves positivity and decreases $H$; exact-difference forcing conserves mass and momentum. | **Existence** of the entropic equilibrium (assumed); streaming, time splitting, or convergence of the solver. |
| [`LerayAlphaFilter.lean`](src/LerayAlphaFilter.lean) | 7 | The Leray-α filter symbol $\varphi=1/(1+\alpha^2k^2)$: positive, $\le 1$, $=1$ iff $k=0$, high-frequency decay, even, antitone, $\varphi^2\le\varphi$. | Well-posedness or regularity of Leray-α. |
| [`AlphaEnergyIdentity.lean`](src/AlphaEnergyIdentity.lean) | 5 | Finite-dimensional gate-versus-drain identity: a projected skew-adjoint term does no work (energy conserved), a dissipative term removes energy at first order in the step. | That the continuum operator $(\bar u\cdot\nabla)$ is skew-adjoint on the relevant function space. |

## Building

All files use Lean `v4.34.0-rc2` with Mathlib. The verified route is OpenAI's own project, which pins that toolchain:

```bash
git clone https://github.com/openai/NavierStokesAndEuler && cd NavierStokesAndEuler
lake exe cache get                                   # Mathlib oleans
lake build NavierStokes.PeriodicUniqueness           # 3 files; only OpenAIAdmissibility.lean needs it
lake env lean <path>/src/OpenAIAdmissibility.lean
lake env lean <path>/src/CoreScaling.lean            # likewise for the other five files
```

Do **not** build OpenAI's full library (~580 files); nothing here needs it. Expected: no errors, no warnings, every `#print axioms` line `[propext, Classical.choice, Quot.sound]`. (A `grep sorry` finds one hit per file: the docstring sentence stating there is none.)

The folder's own `lakefile.lean` builds only the legacy roots below (`NSECensorship`, `LeanMasterBridge`, `TopologicalCensorship`); it does not include the verified files, and `OpenAIAdmissibility.lean` cannot compile under it because it imports OpenAI's modules.

## Legacy files (`src/`) — compile, but are toys

- `TopologicalCensorship.lean` — elementary bounds on the free-standing formula $k_{\text{eff}}=\min(|k|, 1/(\alpha'|k|)) \le 1/\sqrt{\alpha'}$. Its `bkm_regularity_censorship` restates its hypothesis as its conclusion and does **not** invoke Beale–Kato–Majda (its docstring says so). No connection to OpenAI's types.
- `LeanMasterBridge.lean` — arithmetic facts about `Nat`-valued toy records; not connected to any PDE (see its "Reader Caution").
- `NSECensorship.lean` — package root re-exporting the two above.

Both `TopologicalCensorship.lean` and `LeanMasterBridge.lean` compile with 0 errors in OpenAI's environment (re-checked 2026-09-17). The earlier "Open Challenges" framed around them (a dual-scale metric "censoring" blow-up via BKM) are withdrawn: a regularized metric changes the equations, and a bound on it says nothing about Navier–Stokes.

## Drafts (`src/drafts/`) — not verified

`AtlasReferenceVerification`, `BallIdentity`, `ThermodynamicAdmissibility`, `ThermodynamicCensorship` contain `sorry`; `PhysLibThermodynamicCensorship` declares a custom `axiom` and has a `True` placeholder; `PhysicalInvalidationProof` claims "0 sorry" in prose but belongs to the withdrawn "physical invalidation" framing. Do not cite any of them as results.

---
*Maintained by the MechanicaFluidorum Program | Socrate AI Lab (French Non-Profit Association Loi 1901 for Neuro-Symbolic Scientific AI)*
