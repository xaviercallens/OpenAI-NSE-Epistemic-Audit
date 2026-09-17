# 01_Verification_Paper

## The OpenAI Navier–Stokes and Euler Blow-Up Proofs: A Physical Reading, Not a Physical Refutation
*(earlier title: "On the Physical Vacuity of Manufactured Singularities" — that framing has been withdrawn; see `../CHANGELOG.md` and Appendix A of the paper)*
**The MechanicaFluidorum Program | Socrate AI Lab**
*Non-Profit Research Organization (French Association Loi 1901 for Neuro-Symbolic Scientific AI)*

**Current version:** v5.4.1 (2026-09-17), 25 pages.

---

### Manuscripts & Artifacts
*   **Manuscript (PDF):** [`OpenAI_NSE_Verification.pdf`](OpenAI_NSE_Verification.pdf)
*   **LaTeX Source:** [`OpenAI_NSE_Verification.tex`](OpenAI_NSE_Verification.tex)
*   **Open peer review and authors' response:** [`PEER_REVIEW_2026-09-15.md`](PEER_REVIEW_2026-09-15.md)
*   **Reproduction Protocol:** [`REPRODUCTION_PROTOCOL.md`](REPRODUCTION_PROTOCOL.md) (step-by-step protocol for the original directives; for the solvers, Lean files and their expected numbers see [`../BENCHMARKS.md`](../BENCHMARKS.md))
*   **Check Script:** [`verify_openai.py`](verify_openai.py) (AST inspector for OpenAI Lean 4 source)
*   **Verification Script:** [`verify-physical-vacuity.sh`](verify-physical-vacuity.sh) (automated test runner; filename kept from the withdrawn framing)
*   **Zenodo Synchronizer:** [`zenodo_push.py`](zenodo_push.py)

---

### Core Findings

Every row below is checked against the current paper text.

| Topic | Mathematical status | Physical reading |
|---|---|---|
| **Lean 4 check of OpenAI's proof** | 0 `sorry`, 0 custom axioms | The proof is correct; nothing here disputes it |
| **Gevrey cutoffs** (§2.2) | $\exp(-1/q^2)$ cutoffs have Gevrey index $s = 1.5$: $C^\infty$, not real-analytic | A compactly supported nontrivial smooth force *requires* this gap; nothing improper about it |
| **Force** (§2.3, §6; `CandidateFromLimits.lean`) | `force_eq_activated_residual`: on $0\le t<1$ the force equals the Navier–Stokes residual of the final $(u,p)$ | The force is the smooth remainder left once shear-amplified pulses have cancelled the singular part of the residual; it *seeds* the pulses, it does not *drive* the collapse. A legitimate existence-proof technique, without independent physical origin |
| **Moment Jacobian** (§3) | $A = DBD$ (Prop. B.8 of the OpenAI paper) | $\kappa(B) \approx 4.11 \times 10^5$ for all $X_R$; the raw $\kappa \sim 10^{28}$ was an artifact of unscaled dimensions, not fine-tuning |
| **Global kinetic energy** | $E \sim \tau^{+0.485} \to 0$ | Bounded — Clay Alternative C's energy condition is respected |
| **Local energy density / enstrophy** | $e_{\text{local}} \sim \tau^{-1.010}$; $\Omega \sim \tau^{-0.515}$; $\lvert\omega\rvert^2 \sim \tau^{-2.010}$ | Viscous heating $\Delta T \simeq u^2/c_p$: 48 K at Ma 0.3 and 540 K at Ma 1 in water. The decoupled-temperature assumption fails; no thermodynamic law is violated |
| **Mach number** (§5.4, Table 6) | $\text{Ma} \to \infty$ as $\tau \to 0$ | Water, $\ell_0 = 1$ cm: Ma 0.3 at $t \approx 6.7$ ps before blow-up, Ma 1 at 0.6 ps; unit-free $t \simeq \nu/(0.3c)^2$ |
| **One scale** (Prop. 5.1) | Core Reynolds number stays 1 | Compressibility, rarefaction and heating become order one together at $\ell_* = \nu/c_s$: 0.67 nm (water), 45 nm (air) |
| **Cavitation (liquids)** (§5.6) | core pressure deficit $\sim \rho u^2$ | Vapour pressure reached at $u \approx 14$ m/s, $\approx 5$ ns before blow-up (core $\approx 70$ nm); if the liquid holds tension (30–140 MPa), at $\approx 17$–4 ps — before or with Ma 0.3 |
| **Admissibility** (§5.7; §11.5 Direction 2) | $\lvert\nabla u\rvert \lesssim c_s^2/\nu$; proved in Lean on OpenAI's own objects that every candidate exceeds every gradient bound near $t=1$ | Unconditional since v5.4.0; the formal content is close to "velocity blow-up forces gradient blow-up" — valuable as a bridge to the proof objects, not as new physics |
| **Cutoff regularization** (§9) | Cutoff law $u_{\max}\sim\nu/\sqrt{\alpha'}$ exact given a Re ≈ 1 core; generic data never supply one | On a manufactured core a dissipative barrier stalls the collapse near $(1.2$–$1.5)\sqrt{\alpha'}$ at 96³ (not yet converged); Leray-α/LANS-α act 1–2 orders more weakly there — a ranking of models |
| **Kinetic regime** (§9.2) | Exact BGK shear spectrum: damping below $\nu k^2$, capped at $1/\tau$, mode ends at $k\lambda=\sqrt{\pi/2}$ | A nonlinear discrete-velocity BGK simulation of the forced collapse finds **no arrest** there: the kinetic cutoff ends the hydrodynamic description, it does not stop a driven core |
| **Euler datum** | stagewise sum of shear-amplified oscillatory packets with unbounded frequencies | The missing physics is viscosity itself (and thermal noise); whether the packets' coherence survives thermal noise is open |

**Verdict:** The OpenAI proof is correct within Lean 4. Read physically, the construction leaves the domain of validity of the incompressible continuum model at $\ell_* \sim \nu/c_s$, a few picoseconds before the singularity. Whether unforced real fluids can develop finite-time singularities (Statement A) remains open; nothing here settles it.

---

- **Zenodo:** concept DOI [`10.5281/zenodo.22696717`](https://doi.org/10.5281/zenodo.22696717) (always resolves to the latest version); v5.3.0 is [`10.5281/zenodo.22777467`](https://doi.org/10.5281/zenodo.22777467). Versions 2.0.0 (`22725347`, `22727801`) carry withdrawn claims and should not be cited.
- **Hugging Face Dataset:** [`callensxavier/OpenAI-NSE-Thermodynamic-Censorship`](https://huggingface.co/datasets/callensxavier/OpenAI-NSE-Thermodynamic-Censorship) (repository name kept from the earlier framing)
- **GitHub Repository:** [`github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit`](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit)
