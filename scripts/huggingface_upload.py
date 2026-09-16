#!/usr/bin/env python3
"""
huggingface_upload.py
======================
Synchronizes the HuggingFace dataset repo `callensxavier/OpenAI-NSE-Thermodynamic-Censorship`
with the current, corrected state of this project (v5.2.0).

NOTE (2026-09-15 remediation): this script, and the dataset card it used to
push, previously mirrored the withdrawn "Version 2" / Thermodynamic Censorship
framing -- including a directive-5 output log with the femtosecond/picosecond
unit bug this project's review caught and fixed. Anyone re-running this later
should re-check DATASET_CARD and FILES_TO_UPLOAD against the current paper
before uploading; do not assume this note stays accurate indefinitely.

Usage: HF_TOKEN=<token> python3 huggingface_upload.py
"""

import os
import sys
from huggingface_hub import HfApi

REPO_ID = "callensxavier/OpenAI-NSE-Thermodynamic-Censorship"
REPO_TYPE = "dataset"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES_TO_UPLOAD = [
    ("01_Verification_Paper/OpenAI_NSE_Verification.pdf", "paper/OpenAI_NSE_Verification.pdf"),
    ("01_Verification_Paper/OpenAI_NSE_Verification.tex", "paper/OpenAI_NSE_Verification.tex"),
    ("01_Verification_Paper/PEER_REVIEW_2026-09-15.md", "PEER_REVIEW_2026-09-15.md"),
    ("CHANGELOG.md", "CHANGELOG.md"),
    ("README.md", "PROJECT_README.md"),
    ("04_Thermodynamic_Censorship_Paper/Thermodynamic_Censorship_Navier_Stokes.pdf",
     "superseded/Thermodynamic_Censorship_Navier_Stokes.pdf"),
    ("03_Lean4_Topological_Censorship/src/drafts/ThermodynamicCensorship.lean",
     "superseded/lean4/ThermodynamicCensorship.lean"),
    ("05_Community_Research_Directions/WorkStream1_EntropyCondition/WorkStream1_EntropyCondition.pdf",
     "workstreams/WorkStream1_EntropyCondition.pdf"),
    ("05_Community_Research_Directions/WorkStream2_ThermalEquation/WorkStream2_ThermalEquation.pdf",
     "workstreams/WorkStream2_ThermalEquation.pdf"),
    ("05_Community_Research_Directions/WorkStream3_Turbulence/WorkStream3_Turbulence.pdf",
     "workstreams/WorkStream3_Turbulence.pdf"),
    ("05_Community_Research_Directions/WorkStream4_MechanicalCavitation/WorkStream4_MechanicalCavitation.pdf",
     "workstreams/WorkStream4_MechanicalCavitation.pdf"),
    ("05_Community_Research_Directions/WorkStream5_DivergenceFree/WorkStream5_DivergenceFree.pdf",
     "workstreams/WorkStream5_DivergenceFree.pdf"),
    ("05_Community_Research_Directions/WorkStream6_MeasureTheory/WorkStream6_MeasureTheory.pdf",
     "workstreams/WorkStream6_MeasureTheory.pdf"),
    ("scripts/directive5_mach_divergence.py", "scripts/directive5_mach_divergence.py"),
    ("scripts/directive2_thermodynamic_paradox.py", "scripts/directive2_thermodynamic_paradox.py"),
    ("scripts/directive_outputs/directive5_output.txt", "outputs/directive5_output.txt"),
    ("scripts/directive_outputs/directive2_output.txt", "outputs/directive2_output.txt"),
    # --- v5.2.0 additions ---
    ("03_Lean4_Topological_Censorship/src/CoreScaling.lean", "lean4/CoreScaling.lean"),
    ("03_Lean4_Topological_Censorship/src/LerayAlphaFilter.lean", "lean4/LerayAlphaFilter.lean"),
    ("03_Lean4_Topological_Censorship/src/LatticeBGKEntropy.lean", "lean4/LatticeBGKEntropy.lean"),
    ("03_Lean4_Topological_Censorship/src/AlphaEnergyIdentity.lean", "lean4/AlphaEnergyIdentity.lean"),
    ("05_Community_Research_Directions/DUAL_SCALE_LOCK_PROGRAMME.md", "research/DUAL_SCALE_LOCK_PROGRAMME.md"),
    ("05_Community_Research_Directions/DIRECTION1_RESULTS.md", "research/DIRECTION1_RESULTS.md"),
    ("05_Community_Research_Directions/LERAY_ALPHA_DUAL_SCALE_LOCK.md", "research/LERAY_ALPHA_DUAL_SCALE_LOCK.md"),
    ("05_Community_Research_Directions/WEEK1_LOCK_RESULTS.md", "research/WEEK1_LOCK_RESULTS.md"),
    ("05_Community_Research_Directions/DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md", "research/DUALSCALE_ASSESSMENT_AND_NEXT_DIRECTIONS.md"),
    ("05_Community_Research_Directions/RICCATI_THRESHOLD_CHECK.md", "research/RICCATI_THRESHOLD_CHECK.md"),
    ("05_Community_Research_Directions/experiments/RESULTS.md", "research/EXPERIMENTS_RESULTS.md"),
    ("05_Community_Research_Directions/experiments/spectral3d.py", "code/spectral3d.py"),
    ("05_Community_Research_Directions/experiments/forced_core.py", "code/forced_core.py"),
    ("05_Community_Research_Directions/experiments/forced_core_axial.py", "code/forced_core_axial.py"),
    ("05_Community_Research_Directions/experiments/shell_mach_cap.py", "code/shell_mach_cap.py"),
    ("05_Community_Research_Directions/experiments/shell_cutoff_law.py", "code/shell_cutoff_law.py"),
    ("05_Community_Research_Directions/experiments/analyse_cutoff_law.py", "code/analyse_cutoff_law.py"),
    ("05_Community_Research_Directions/experiments/results/cutoff_law_summary.png", "figures/cutoff_law_summary.png"),
    ("05_Community_Research_Directions/experiments/results/forced_core_32_v3.png", "figures/forced_core_32_v3.png"),
    ("05_Community_Research_Directions/experiments/results/lock_f_coherence.png", "figures/lock_f_coherence.png"),
    ("05_Community_Research_Directions/experiments/results/validation_3d.json", "data/validation_3d.json"),
    ("05_Community_Research_Directions/experiments/results/cutoff_law_shell.json", "data/cutoff_law_shell.json"),
    ("05_Community_Research_Directions/experiments/results/cutoff_law_analysis.json", "data/cutoff_law_analysis.json"),
    ("05_Community_Research_Directions/experiments/results/forced_core_32_v3.json", "data/forced_core_32_v3.json"),
    ("05_Community_Research_Directions/experiments/results/forced_core_axial_32.json", "data/forced_core_axial_32.json"),
    ("05_Community_Research_Directions/experiments/results/gate_leverage_vs_re.json", "data/gate_leverage_vs_re.json"),
    ("05_Community_Research_Directions/experiments/results/gate_barrier_crossover.json", "data/gate_barrier_crossover.json"),
    ("05_Community_Research_Directions/experiments/results/lans_vs_leray_vs_nse.json", "data/lans_vs_leray_vs_nse.json"),
    ("05_Community_Research_Directions/experiments/results/shell_mach_cap.json", "data/shell_mach_cap.json"),
    # --- v5.3.0 additions ---
    ("03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean", "lean4/OpenAIAdmissibility.lean"),
    ("05_Community_Research_Directions/experiments/lock_k_kinetic_spectrum.py", "code/lock_k_kinetic_spectrum.py"),
    ("05_Community_Research_Directions/experiments/results/lock_k_kinetic_spectrum.png", "figures/lock_k_kinetic_spectrum.png"),
    ("05_Community_Research_Directions/experiments/results/lock_k_kinetic_spectrum.json", "data/lock_k_kinetic_spectrum.json"),
]

DATASET_CARD = """---
license: cc-by-4.0
task_categories:
  - other
tags:
  - navier-stokes
  - euler-equations
  - fluid-dynamics
  - formal-verification
  - lean4
  - millennium-prize
  - openai
  - model-validity
  - beale-kato-majda
  - forced-core
  - leray-alpha
  - lans-alpha
  - kinetic-theory
language:
  - en
size_categories:
  - n<1K
pretty_name: "OpenAI NSE Blow-Up Proofs: A Physical Reading (v5.3.0)"
---

# The OpenAI Navier-Stokes and Euler Blow-Up Proofs: A Physical Reading, Not a Physical Refutation

**Socrate AI Lab / MechanicaFluidorum Program** &middot; Lead: Xavier Callens
**GitHub:** [xaviercallens/OpenAI-NSE-Epistemic-Audit](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit) (release [v5.3.0](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/releases/tag/v5.3.0))
**Zenodo:** concept record [10.5281/zenodo.22696718](https://doi.org/10.5281/zenodo.22696718)

## What this is

In September 2026, an OpenAI multi-agent system produced Lean 4-verified proofs of finite-time
blow-up for the forced 3D Navier-Stokes equations (Millennium Prize Alternatives C and D) and for
the unforced Euler equations: zero `sorry`s, zero custom axioms, no weakened norms. **This dataset
does not dispute that proof.** The Millennium Prize problems ask precise questions about a specific
continuum model; they were never claims about how real fluids behave. This project is a *physical
reading* of the specific solution OpenAI constructed: how far it travels from the regime the
incompressible model is normally trusted to describe.

## Headline result

Because the collapsing core keeps a radial Reynolds number of order one, its scales are diffusive
(&#8467;<sub>r</sub> &asymp; &radic;(&nu;t), u &asymp; &radic;(&nu;/t)), essentially independent of
the initial vortex size. Compressibility, rarefaction and viscous heating all become order-one
effects at a **single length** &#8467;* = &nu;/c<sub>s</sub> (0.7&nbsp;nm in water, 45&nbsp;nm in
air), a few **picoseconds** (water) or nanoseconds (air) before the mathematical singularity --
expressible as one local vorticity bound |&omega;| &lesssim; c<sub>s</sub><sup>2</sup>/&nu; that the
Beale-Kato-Majda theorem turns into a genuine admissibility criterion. For liquids, cavitation is
reached three decades earlier still.

## Results added in v5.2.0 and v5.3.0

- **3D solver validated.** Pseudo-spectral Navier-Stokes solver reproduces the Taylor-Green
  Re = 1600 benchmark: dissipation peak at t = 9.14 against the published t = 9.0.
- **Cutoff law tested.** Exact given its premise, but the premise (a Re ~ 1 diffusive core) is not
  produced by generic data: in a cascade the arrest-scale velocity scales as k^-0.345 (Kolmogorov
  -1/3), where the law predicts k^+1.
- **Forced collapsing core.** A manufactured Re = 1 collapse is tracked to 1.7e-7; the barrier's
  engagement collapses onto the single variable alpha'/(nu tau) (per-run prefactor 0.188 +/- 0.010).
- **Gate vs drain.** On that collapse, Leray-alpha / LANS-alpha lag it by 0.2-0.4%, a hyperviscous
  barrier by 5-45%. The crossover Reynolds number
  Re_x = ||(L_barrier - L_nu) U|| / ||N_alpha(U) - N(U)|| ranges 8-142.
- **Kinetic anchor.** l*/lambda = cbar/(2 c_s) = 0.67 for air: the validity scale is the mean free
  path, with a derived constant.
- **Kinetic lock (v5.3.0) -- a correction to v5.2.0.** The exact BGK shear-mode spectrum damps small
  scales LESS than viscosity (Gamma = nu k^2 [1 - (k lambda)^2 + ...]), never exceeds the collision
  rate 1/tau, and the hydrodynamic mode ceases to exist at k lambda = sqrt(pi/2) = 1.2533. At
  k lambda = 1 the barrier damps 1.43x harder than kinetic theory. So the lock at l* is the end of the
  hydrodynamic description, not a stronger drain; v5.2.0's "the lock at l* is dissipative, supplied by
  kinetic theory" is withdrawn in that sense.
- **Lean 4.** 45 theorems on the three standard axioms: scaling chain, Leray-alpha filter bounds,
  discrete BGK H-theorem, gate/drain energy identity, and (v5.3.0) the first statements on OpenAI's
  own `ProblemStatement` objects -- any object with their CandidateProperties exceeds every gradient
  bound before t = 1, given an elementary periodic-cell lemma (not Beale-Kato-Majda) that is stated as
  a labelled hypothesis because Mathlib lacks the needed torus integration by parts.

## What changed from earlier releases (important)

An earlier version of this dataset (still visible in this repo's commit history) asserted a
different framing: a global "Thermodynamic Censorship" enstrophy axiom, "plasma temperatures", and
a Mach-limit timeline that misread the model's own dimensionless time parameter as seconds
directly (off by twelve orders of magnitude -- **femtoseconds instead of picoseconds**). Those
claims are withdrawn. See `CHANGELOG.md` and Appendix A of the paper for the itemized list, and
`PEER_REVIEW_2026-09-15.md` for an open peer review and the authors' point-by-point response.
`superseded/` in this repo holds the retracted paper and Lean file, kept for the historical record
with inline withdrawal notices -- **do not cite them for their original claims.**

## Contents

- `paper/`: current flagship paper (PDF + LaTeX source)
- `workstreams/`: six community-research-direction notes (admissibility, turbulence-modeling
  closure, thermal response, cavitation, divergence-free vs. incompressible, genericity/codimension)
- `scripts/`: the two verified analytical scripts referenced in the paper's physical-scale tables
- `outputs/`: their console output logs (regenerated 2026-09-15; times are explicitly labelled
  dimensionless &tau; vs. physical seconds t = T&tau;)
- `superseded/`: the retracted paper and Lean file, with withdrawal notices, for the historical record
- `lean4/`: the v5.2.0 Lean 4 files (standard axioms only)
- `research/`: programme notes and experiment write-ups
- `code/`: the 3D solver and forced-core test beds
- `figures/`, `data/`: figures and JSON outputs of the v5.2.0 experiments
- `CHANGELOG.md`, `PEER_REVIEW_2026-09-15.md`, `PROJECT_README.md`: project documentation

## Citation

Cite the GitHub release or the Zenodo record above, not this dataset card directly. Please do not
cite `superseded/Thermodynamic_Censorship_Navier_Stokes.pdf` for its original conclusions.
"""


REPO_README_POINTER = (
    "# REPO_README\n\n"
    "This file previously held an outdated dataset card. The current card is README.md; "
    "see CHANGELOG.md for what changed.\n"
)


def main():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        print("[-] Error: set HF_TOKEN (or HUGGINGFACE_TOKEN).", file=sys.stderr)
        sys.exit(1)

    api = HfApi(token=token)
    print(f"[*] Syncing corrected v5.2.0 content to {REPO_TYPE} repo: {REPO_ID}")

    missing = [rel for rel, _ in FILES_TO_UPLOAD if not os.path.exists(os.path.join(REPO_ROOT, rel))]
    if missing:
        print("[-] Missing local files, aborting before any upload:", file=sys.stderr)
        for m in missing:
            print(f"    - {m}", file=sys.stderr)
        sys.exit(1)

    for rel_path, path_in_repo in FILES_TO_UPLOAD:
        local_path = os.path.join(REPO_ROOT, rel_path)
        print(f"  -> {path_in_repo} ({os.path.getsize(local_path):,} bytes)")
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="v5.3.0: kinetic spectrum correction, first Lean bridge to OpenAI objects",
        )

    print("  -> README.md (dataset card)")
    api.upload_file(
        path_or_fileobj=DATASET_CARD.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        commit_message="v5.3.0: update dataset card",
    )

    print("  -> REPO_README.md (pointer replacing outdated card)")
    api.upload_file(
        path_or_fileobj=REPO_README_POINTER.encode("utf-8"),
        path_in_repo="REPO_README.md",
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        commit_message="v5.2.0: replace outdated REPO_README with pointer to README.md",
    )

    # Optional extras: directive_outputs/, audit certificate, animations, if present.
    outputs_dir = os.path.join(REPO_ROOT, "scripts", "directive_outputs")
    if os.path.isdir(outputs_dir):
        api.upload_folder(
            folder_path=outputs_dir,
            repo_id=REPO_ID,
            path_in_repo="outputs/directive_outputs",
            repo_type=REPO_TYPE,
            commit_message="v5.2.0: refresh all directive output logs",
        )
        print("  -> outputs/directive_outputs/ (full refresh)")

    anim_dir = os.path.join(REPO_ROOT, "dataset", "animations")
    if os.path.isdir(anim_dir):
        api.upload_folder(
            folder_path=anim_dir,
            repo_id=REPO_ID,
            path_in_repo="animations",
            repo_type=REPO_TYPE,
            commit_message="v5.2.0: refresh animations",
        )
        print("  -> animations/")

    print(f"\n[+] Done. https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
