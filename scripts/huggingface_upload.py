#!/usr/bin/env python3
"""
huggingface_upload.py
======================
Synchronizes the HuggingFace dataset repo `callensxavier/OpenAI-NSE-Thermodynamic-Censorship`
with the current, corrected state of this project (v5.1.0).

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
language:
  - en
size_categories:
  - n<1K
pretty_name: "OpenAI NSE Blow-Up Proofs: A Physical Reading (v5.1.0)"
---

# The OpenAI Navier-Stokes and Euler Blow-Up Proofs: A Physical Reading, Not a Physical Refutation

**Socrate AI Lab / MechanicaFluidorum Program** &middot; Lead: Xavier Callens
**GitHub:** [xaviercallens/OpenAI-NSE-Epistemic-Audit](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit) (release [v5.1.0](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/releases/tag/v5.1.0))
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
- `CHANGELOG.md`, `PEER_REVIEW_2026-09-15.md`, `PROJECT_README.md`: project documentation

## Citation

Cite the GitHub release or the Zenodo record above, not this dataset card directly. Please do not
cite `superseded/Thermodynamic_Censorship_Navier_Stokes.pdf` for its original conclusions.
"""


def main():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        print("[-] Error: set HF_TOKEN (or HUGGINGFACE_TOKEN).", file=sys.stderr)
        sys.exit(1)

    api = HfApi(token=token)
    print(f"[*] Syncing corrected v5.1.0 content to {REPO_TYPE} repo: {REPO_ID}")

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
            commit_message="v5.1.0: correct dataset card and paper, withdraw superseded claims",
        )

    print("  -> README.md (dataset card)")
    api.upload_file(
        path_or_fileobj=DATASET_CARD.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        commit_message="v5.1.0: rewrite dataset card, withdraw superseded claims",
    )

    # Optional extras: directive_outputs/, audit certificate, animations, if present.
    outputs_dir = os.path.join(REPO_ROOT, "scripts", "directive_outputs")
    if os.path.isdir(outputs_dir):
        api.upload_folder(
            folder_path=outputs_dir,
            repo_id=REPO_ID,
            path_in_repo="outputs/directive_outputs",
            repo_type=REPO_TYPE,
            commit_message="v5.1.0: refresh all directive output logs",
        )
        print("  -> outputs/directive_outputs/ (full refresh)")

    anim_dir = os.path.join(REPO_ROOT, "dataset", "animations")
    if os.path.isdir(anim_dir):
        api.upload_folder(
            folder_path=anim_dir,
            repo_id=REPO_ID,
            path_in_repo="animations",
            repo_type=REPO_TYPE,
            commit_message="v5.1.0: refresh animations",
        )
        print("  -> animations/")

    print(f"\n[+] Done. https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
