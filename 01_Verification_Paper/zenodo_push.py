#!/usr/bin/env python3
"""
zenodo_push.py
==============
A Physical Reading of the OpenAI Navier-Stokes/Euler Blow-Up Proofs
MechanicaFluidorum Program | Socrate AI Lab (French Association Loi 1901)

Automated Zenodo synchronizer and bundle packager for Record 22696718.
- Validates SHA-256 integrity of all certified assets.
- Packages distribution archive (zenodo_bundle_v5.zip).
- Synchronizes with Zenodo REST API and publishes the updated deposit.

NOTE (2026-09-15 remediation): the file list and metadata below were rewritten
from scratch. The version this script previously pushed (labelled "2.0.0")
asserted claims -- a 10^28-digit "structural instability", a global
enstrophy-censorship axiom, "vacuous" physics, femtosecond-scale timings --
that this project's own scientific review subsequently withdrew (see
CHANGELOG.md and 01_Verification_Paper/PEER_REVIEW_2026-09-15.md). Anyone
re-running this script should re-check FILES_TO_PACKAGE and METADATA against
the current paper before publishing; do not assume this note stays accurate
indefinitely.
"""

import os
import sys
import json
import zipfile
import hashlib
import argparse
import requests

RECORD_ID = "22696718"
ZENODO_BASE_URL = "https://zenodo.org/api"

FILES_TO_PACKAGE = [
    ("01_Verification_Paper/OpenAI_NSE_Verification.pdf", "OpenAI_NSE_Verification.pdf"),
    ("01_Verification_Paper/OpenAI_NSE_Verification.tex", "OpenAI_NSE_Verification.tex"),
    ("01_Verification_Paper/PEER_REVIEW_2026-09-15.md", "PEER_REVIEW_2026-09-15.md"),
    ("CHANGELOG.md", "CHANGELOG.md"),
    ("README.md", "README.md"),
    ("04_Thermodynamic_Censorship_Paper/Thermodynamic_Censorship_Navier_Stokes.pdf",
     "SUPERSEDED_Thermodynamic_Censorship_Navier_Stokes.pdf"),
    ("05_Community_Research_Directions/WorkStream1_EntropyCondition/WorkStream1_EntropyCondition.pdf",
     "WorkStream1_EntropyCondition.pdf"),
    ("05_Community_Research_Directions/WorkStream2_ThermalEquation/WorkStream2_ThermalEquation.pdf",
     "WorkStream2_ThermalEquation.pdf"),
    ("05_Community_Research_Directions/WorkStream3_Turbulence/WorkStream3_Turbulence.pdf",
     "WorkStream3_Turbulence.pdf"),
    ("05_Community_Research_Directions/WorkStream4_MechanicalCavitation/WorkStream4_MechanicalCavitation.pdf",
     "WorkStream4_MechanicalCavitation.pdf"),
    ("05_Community_Research_Directions/WorkStream5_DivergenceFree/WorkStream5_DivergenceFree.pdf",
     "WorkStream5_DivergenceFree.pdf"),
    ("05_Community_Research_Directions/WorkStream6_MeasureTheory/WorkStream6_MeasureTheory.pdf",
     "WorkStream6_MeasureTheory.pdf"),
    ("scripts/directive5_mach_divergence.py", "directive5_mach_divergence.py"),
    ("scripts/directive2_thermodynamic_paradox.py", "directive2_thermodynamic_paradox.py"),
    ("dataset/README.md", "dataset_README.md"),
    # --- v5.2.0: dual-scale lock programme, forced core, Lean 4 ---
    ("05_Community_Research_Directions/DUAL_SCALE_LOCK_PROGRAMME.md", "DUAL_SCALE_LOCK_PROGRAMME.md"),
    ("05_Community_Research_Directions/DIRECTION1_RESULTS.md", "DIRECTION1_RESULTS.md"),
    ("05_Community_Research_Directions/LERAY_ALPHA_DUAL_SCALE_LOCK.md", "LERAY_ALPHA_DUAL_SCALE_LOCK.md"),
    ("05_Community_Research_Directions/experiments/RESULTS.md", "EXPERIMENTS_RESULTS.md"),
    ("05_Community_Research_Directions/experiments/spectral3d.py", "spectral3d.py"),
    ("05_Community_Research_Directions/experiments/forced_core.py", "forced_core.py"),
    ("05_Community_Research_Directions/experiments/forced_core_axial.py", "forced_core_axial.py"),
    ("05_Community_Research_Directions/experiments/results/cutoff_law_summary.png", "figure_cutoff_law_summary.png"),
    ("05_Community_Research_Directions/experiments/results/forced_core_32_v3.png", "figure_forced_core.png"),
    ("03_Lean4_Topological_Censorship/src/CoreScaling.lean", "CoreScaling.lean"),
    ("03_Lean4_Topological_Censorship/src/LerayAlphaFilter.lean", "LerayAlphaFilter.lean"),
    ("03_Lean4_Topological_Censorship/src/LatticeBGKEntropy.lean", "LatticeBGKEntropy.lean"),
    ("03_Lean4_Topological_Censorship/src/AlphaEnergyIdentity.lean", "AlphaEnergyIdentity.lean"),
    # --- v5.3.0 ---
    ("03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean", "OpenAIAdmissibility.lean"),
    ("05_Community_Research_Directions/experiments/lock_k_kinetic_spectrum.py", "lock_k_kinetic_spectrum.py"),
    ("05_Community_Research_Directions/experiments/results/lock_k_kinetic_spectrum.png", "figure_lock_k_kinetic_spectrum.png"),
    # --- v5.4.x: unconditional Lean bridge, nonlinear kinetic test, 96^3 sweep, benchmarks ---
    ("03_Lean4_Topological_Censorship/src/NonlinearBGKEntropy.lean", "NonlinearBGKEntropy.lean"),
    ("03_Lean4_Topological_Censorship/src/KineticSpectralCap.lean", "KineticSpectralCap.lean"),
    ("05_Community_Research_Directions/kinetic_lock_rs/README.md", "KINETIC_LOCK_RS_README.md"),
    ("05_Community_Research_Directions/experiments/results/kinetic_lock.png", "figure_kinetic_lock.png"),
    ("05_Community_Research_Directions/experiments/results/kinetic_lock_gates.json", "kinetic_lock_gates.json"),
    ("05_Community_Research_Directions/experiments/results/kinetic_lock_collapse.json", "kinetic_lock_collapse.json"),
    ("05_Community_Research_Directions/experiments/results/forced_core_96_v3.json", "forced_core_96_v3.json"),
    # --- v5.5.0: regime map, compressible/thermal forced core, Leray-alpha linearization ---
    ("03_Lean4_Topological_Censorship/src/BlowupRegimeMap.lean", "BlowupRegimeMap.lean"),
    ("03_Lean4_Topological_Censorship/src/LerayAlphaLinearization.lean", "LerayAlphaLinearization.lean"),
    ("05_Community_Research_Directions/THERMO_COMPRESSIBLE_LOCK_STUDY.md", "THERMO_COMPRESSIBLE_LOCK_STUDY.md"),
    ("05_Community_Research_Directions/experiments/compressible_core.py", "compressible_core.py"),
    ("05_Community_Research_Directions/experiments/results/compressible_core_study.json", "compressible_core_study.json"),
    ("05_Community_Research_Directions/experiments/results/compressible_core_re_sweep.json", "compressible_core_re_sweep.json"),
    ("05_Community_Research_Directions/experiments/results/kinetic_lock_gas_law.json", "kinetic_lock_gas_law.json"),
    ("05_Community_Research_Directions/experiments/results/compressible_core.png", "figure_compressible_core.png"),
    # --- v5.6.0: molecular dynamics of the forced core, quantum-fluid counterpart ---
    ("03_Lean4_Topological_Censorship/src/QuantumVortexLink.lean", "QuantumVortexLink.lean"),
    ("05_Community_Research_Directions/QUANTUM_FLUID_MICRO_MACRO_LINK.md", "QUANTUM_FLUID_MICRO_MACRO_LINK.md"),
    ("05_Community_Research_Directions/experiments/quantum_fluid_link.py", "quantum_fluid_link.py"),
    ("05_Community_Research_Directions/experiments/gp_vortex_dipole.py", "gp_vortex_dipole.py"),
    ("05_Community_Research_Directions/experiments/results/quantum_fluid_link.json", "quantum_fluid_link.json"),
    ("05_Community_Research_Directions/experiments/results/quantum_fluid_link.png", "figure_quantum_fluid_link.png"),
    ("05_Community_Research_Directions/experiments/results/gp_vortex_dipole.json", "gp_vortex_dipole.json"),
    ("05_Community_Research_Directions/experiments/results/gp_vortex_dipole.png", "figure_gp_vortex_dipole.png"),
    ("05_Community_Research_Directions/md_core_rs/README.md", "MD_CORE_RS_README.md"),
    ("05_Community_Research_Directions/experiments/analyse_md_core.py", "analyse_md_core.py"),
    ("05_Community_Research_Directions/experiments/compressible_core_md_match.py", "compressible_core_md_match.py"),
    ("05_Community_Research_Directions/experiments/results/md_core_gates.json", "md_core_gates.json"),
    ("05_Community_Research_Directions/experiments/results/md_core_runs.json", "md_core_runs.json"),
    ("05_Community_Research_Directions/experiments/results/md_core.png", "figure_md_core.png"),
    ("05_Community_Research_Directions/experiments/results/compressible_core_md_match_preregistered.json", "compressible_core_md_match_preregistered.json"),
    ("05_Community_Research_Directions/experiments/results/compressible_core_md_match.json", "compressible_core_md_match.json"),
    ("BENCHMARKS.md", "BENCHMARKS.md"),
    ("scripts/run_benchmarks.sh", "run_benchmarks.sh"),
    ("scripts/compare_benchmarks.py", "compare_benchmarks.py"),
]

METADATA = {
    "metadata": {
        "title": "The OpenAI Navier-Stokes and Euler Blow-Up Proofs: A Physical Reading, Not a Physical Refutation (v5.6.1)",
        "upload_type": "publication",
        "publication_type": "preprint",
        "description": (
            "<p>In September 2026, an OpenAI multi-agent system produced Lean 4-verified proofs of "
            "finite-time blow-up for the forced 3D Navier-Stokes equations (Millennium Prize "
            "Alternatives C and D) and for the unforced Euler equations. The proofs are syntactically "
            "flawless: zero <code>sorry</code>s, zero custom axioms, no weakened norms. This is not a "
            "refutation of that result. The Clay Millennium Prize problems ask precise questions about "
            "a specific continuum model; they were never claims about how real fluids behave.</p>"
            "<p>This paper is a physical reading. Because the collapsing core keeps a radial Reynolds "
            "number of order one, its scales are diffusive (&#8467;<sub>r</sub> &#8776; &radic;(&nu;t), "
            "u &#8776; &radic;(&nu;/t)), essentially independent of the initial vortex size or choice "
            "of units. Compressibility, rarefaction and viscous heating all become order-one effects at "
            "a single length &#8467;* = &nu;/c<sub>s</sub> (0.7 nm in water, 45 nm in air), a few "
            "picoseconds (water) or nanoseconds (air) before the mathematical singularity -- one scale, "
            "expressible as a single local vorticity bound |&omega;| &lesssim; c<sub>s</sub><sup>2</sup>/&nu; "
            "that the Beale-Kato-Majda theorem turns into a genuine admissibility criterion. For liquids "
            "at ambient pressure, cavitation is reached three decades earlier still. Also shown: the "
            "moment-matching system's apparent 10<sup>28</sup> condition number is a non-dimensionalization "
            "artifact (&kappa; &asymp; 4.1&times;10<sup>5</sup> once properly scaled); the acoustic "
            "radiation \"check\" used in earlier drafts is the Mach criterion in disguise, not an "
            "independent one; the external force has no independent physical origin, by construction; "
            "and the Euler datum requires coherent structure below the molecular length, where the "
            "missing physics is viscosity itself, not any exotic short-distance cutoff.</p>"
            "<p><strong>New in v5.2.0 to v5.6.1.</strong> The cutoff-regularization hypothesis the paper previously "
            "stated as untested is tested with a validated 3D pseudo-spectral solver (Taylor-Green "
            "Re=1600 dissipation peak at t=9.14 against a published 9.0). It is exact given its premise, "
            "but the premise -- a Re~1 diffusive core -- is not produced by generic data. A manufactured "
            "Re=1 collapse, sustained by its own Navier-Stokes residual, is tracked to 1.7e-7; on it the "
            "barrier's engagement reduces to a single variable, and transport-filtering regularizations "
            "of the Leray-alpha and LANS-alpha type are one to two orders of magnitude weaker than "
            "dissipation, because they can act only through a nonlinearity that is a few percent of the "
            "dynamics (the gate-drain crossover Reynolds number is an exact norm ratio, 8 to 142). At 96^3 "
            "the barrier stalls the forced core near 1.2-1.5 sqrt(alpha') with exponents approaching the "
            "cutoff law (0.42 and -0.43 against 0.5 and -0.5), not yet converged; a forecast that the "
            "barrier/forcing ratio would cross one was not borne out and is recorded as such. The "
            "continuum validity scale is the mean free path with a derived kinetic-theory constant (0.67 "
            "for air). The exact BGK shear-mode spectrum shows that kinetic theory is not a stronger drain: "
            "its damping is below viscosity, capped at the collision rate, and the hydrodynamic mode ends "
            "at k lambda = sqrt(pi/2). A nonlinear test with a validated discrete-velocity BGK solver in "
            "Rust, driven by the same manufactured collapse, finds no arrest there: the kinetic core runs "
            "up to 12% ahead of Navier-Stokes and its apparent stopping point moves with the grid, not the "
            "mean free path (a null result for the kinetic lock as an arrest mechanism, robust down to "
            "about 0.9 mean free paths). The bundle's Lean 4 files use only the three standard axioms; "
            "among them is the statement, proved on OpenAI's own ProblemStatement "
            "definitions and periodic-integration library with no remaining hypothesis, that any object "
            "with their candidate properties exceeds every velocity-gradient bound arbitrarily close to "
            "the singular time. A reproducibility benchmark (BENCHMARKS.md, run_benchmarks.sh) re-runs "
            "the tests, Lean files, solver gates and fast simulations and compares every regenerated "
            "number with the committed results. v5.4.1 corrects one figure in the v5.4.0 paper (a "
            "grid-refinement endpoint quoted as 0.86 instead of 0.96 mean free paths). v5.5.0 rereads Tao's "
            "averaged-equation blow-up and a human-written forced Euler blow-up through the relation "
            "Kn = Ma/Re: the three scenarios meet different physics first (kinetic termination at l*, "
            "compressibility inside the continuum at Re l*, plain viscosity at l*/Ma). A one-dimensional "
            "compressible Navier-Stokes-Fourier simulation of the forced core finds that on OpenAI's route "
            "neither compressibility nor heat stops the core before l* (an arrest prediction of ours failed), "
            "while on the inertial route (Re of 16 or more) air does not follow the driven swirl past a local "
            "Mach number of 0.70 -- a lock on Mach number, not on velocity or size, in a model whose own "
            "equations have proved implosion singularities. The claim that a Leray-alpha filter of width l* "
            "represents the fluid at its continuum limit is withdrawn, with a formal reason: the filter width "
            "does not appear in the linearized dynamics. Lean: 85 declarations in ten files. v5.6.0 tests the Mach lock with no continuum closure at all: molecular dynamics of a "
            "Lennard-Jones gas driven by the same force, with viscosity measured in situ, reproduces the continuum prediction "
            "registered beforehand where the gas is still a continuum (local Mach 0.56-0.62 against 0.54, core density 0.34 "
            "against 0.36, core temperature 1.15 against 1.15), and shows the core emptying into a "
            "free-molecular region beyond it. v5.6.1 completes the ensemble (Re 16: local Mach 0.538 +- 0.011 against 0.54 "
            "with a consistent real-gas sound speed, correcting a normalization in v5.6.0; Re 32: 0.62-0.71) and adds a "
            "liquid: the core cavitates, after holding a tension of the order of its ambient pressure, and the swirl at the "
            "cavity wall then levels off at 1.77-1.87 below the hollow-vortex bound 2.07 -- the one velocity bound found, "
            "supplied by a phase change. A new section gives the quantum-fluid counterpart: a quantized vortex is a "
            "Reynolds-number-one core by theorem, and quantum pressure, heat and cavitation all let a fluid carry a velocity "
            "singularity by emptying the core rather than by bounding the velocity.</p>"
            "<p>This version supersedes all previous public drafts of this project, including "
            "one previously deposited under this same Zenodo record. Claims withdrawn in this revision "
            "-- \"plasma temperatures\", a global enstrophy-censorship axiom with no stated derivation, "
            "the acoustic check treated as independent, femtosecond-scale timings, and the framing of "
            "this result as \"physically vacuous\" -- are documented individually in the accompanying "
            "CHANGELOG.md and in Appendix A of the main paper. The bundle also includes an open peer "
            "review received 2026-09-15 and the authors' point-by-point response "
            "(PEER_REVIEW_2026-09-15.md), and the six community-authored WorkStream notes developing "
            "specific follow-on research directions (an admissibility condition, subgrid-scale closure "
            "benchmarking, a derived thermal response, mechanical cavitation, the divergence-free/"
            "incompressible distinction, and measure-theoretic genericity). The earlier "
            "\"Thermodynamic Censorship\" paper is included for the historical record with an inline "
            "withdrawal notice; it should not be cited for its original claims.</p>"
        ),
        "creators": [
            {
                "name": "Callens, Xavier",
                "affiliation": "Socrate AI Lab, MechanicaFluidorum Program"
            },
            {
                "name": "Socrate AI Lab",
                "affiliation": "Non-Profit Research Organization (French Association Loi 1901 for Neuro-Symbolic Scientific AI)"
            }
        ],
        "keywords": [
            "Navier-Stokes",
            "Euler Equations",
            "Millennium Prize Problem",
            "Lean 4",
            "Formal Verification",
            "Fluid Dynamics",
            "Beale-Kato-Majda",
            "Model Validity",
            "Continuum Mechanics",
            "Cavitation",
            "Neuro-Symbolic AI"
        ],
        "version": "5.6.1",
        "license": "cc-by-4.0",
        "access_right": "open",
        "related_identifiers": [
            {
                "identifier": "https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit",
                "relation": "isSupplementTo",
                "scheme": "url"
            },
            {
                "identifier": "https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/releases/tag/v5.6.1",
                "relation": "isIdenticalTo",
                "scheme": "url"
            },
            {
                "identifier": "https://github.com/openai/NavierStokesAndEuler",
                "relation": "references",
                "scheme": "url"
            }
        ]
    }
}


def get_token():
    for p in [os.environ.get("ZENODO_TOKEN"), os.environ.get("ZENODO_ACCESS_TOKEN")]:
        if p:
            return p
    for path in [os.path.expanduser("~/.config/zenodo/token"), os.path.expanduser("~/.zenodo_token")]:
        if os.path.exists(path):
            with open(path) as f:
                t = f.read().strip()
                if t:
                    return t
    return None


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def create_certified_zip(repo_root, output_zip):
    print(f"[*] Packaging certified Zenodo distribution zip: {output_zip}")
    manifest = {}
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path, arcname in FILES_TO_PACKAGE:
            filepath = os.path.join(repo_root, rel_path)
            if not os.path.exists(filepath):
                print(f"[-] Error: Missing asset {filepath}", file=sys.stderr)
                sys.exit(1)
            sha = compute_sha256(filepath)
            manifest[arcname] = sha
            zf.write(filepath, arcname=arcname)
            print(f"  + {arcname:<36} (SHA-256: {sha[:16]}...)")
        
        zf.writestr("metadata.json", json.dumps(METADATA, indent=2))
        zf.writestr("manifest_sha256.json", json.dumps(manifest, indent=2))

    print(f"[+] Generated archive: {output_zip} ({os.path.getsize(output_zip):,} bytes)")
    return manifest


def confirm_publish():
    """
    Prompt user for confirmation before publishing to Zenodo.
    This is a destructive action and cannot be easily undone.
    """
    print("\n" + "=" * 65)
    print(" WARNING: Destructive Action - Publishing to Zenodo")
    print("=" * 65)
    print("This will publish the deposit to Zenodo, making it publicly")
    print("accessible and permanently versioned. This action cannot be undone.")
    print("=" * 65 + "\n")

    response = input("Do you want to continue? (type 'yes' to confirm): ").strip().lower()
    return response == "yes"


def _get_json(url, headers, attempts=6, wait_s=20):
    """
    GET a Zenodo API URL and return parsed JSON, retrying 5xx responses.
    Zenodo intermittently answers with an HTML '504 Gateway Time-out' page;
    calling .json() on that raises a decode error mid-upload, which is how an
    earlier run of this script failed. Non-5xx errors are not retried.
    """
    import time
    last = None
    for i in range(attempts):
        r = requests.get(url, headers=headers, timeout=120)
        if r.status_code == 200:
            return r.json()
        last = r
        if r.status_code < 500:
            break
        print(f"  [!] {r.status_code} from Zenodo, retry {i + 1}/{attempts} in {wait_s}s")
        time.sleep(wait_s)
    print(f"[-] GET {url} failed: {last.status_code} {last.text[:200]}", file=sys.stderr)
    sys.exit(1)


def push_to_zenodo(token, repo_root, publish=False, draft_id=None):
    headers = {"Authorization": f"Bearer {token}"}

    # 0. An explicit draft id bypasses discovery. The listing endpoint does not
    #    reliably return an existing unsubmitted draft, and requesting a new
    #    version while one exists fails with "Please remove all files first".
    if draft_id:
        chk = _get_json(f"{ZENODO_BASE_URL}/deposit/depositions/{draft_id}", headers)
        if chk.get("submitted"):
            print(f"[-] Draft {draft_id} is already submitted; refusing to continue.", file=sys.stderr)
            sys.exit(1)
        print(f"[+] Using explicit unsubmitted draft: {draft_id}")

    # 1. Check existing draft or create new version from RECORD_ID
    deposits = []
    concept_id = None
    if not draft_id:
        print(f"[*] Checking Zenodo record {RECORD_ID}...")
        r = requests.get(f"{ZENODO_BASE_URL}/deposit/depositions", headers=headers)
        if r.status_code != 200:
            print(f"[-] Failed to fetch deposits: {r.status_code} {r.text}", file=sys.stderr)
            sys.exit(1)
        deposits = r.json()

    for d in deposits:
        if str(d.get("id")) == str(RECORD_ID):
            concept_id = str(d.get("conceptrecid"))
            break

    if concept_id:
        for d in deposits:
            if str(d.get("conceptrecid")) == concept_id and not d.get("submitted"):
                draft_id = str(d.get("id"))
                print(f"[+] Found active unsubmitted draft: {draft_id}")
                break

    if not draft_id:
        print(f"[*] Requesting newversion from record {RECORD_ID}...")
        nv_r = requests.post(f"{ZENODO_BASE_URL}/deposit/depositions/{RECORD_ID}/actions/newversion", headers=headers)
        if nv_r.status_code not in (200, 201):
            print(f"[-] Failed to create new version: {nv_r.status_code} {nv_r.text}", file=sys.stderr)
            sys.exit(1)
        nv_data = nv_r.json()
        draft_url = nv_data.get("links", {}).get("latest_draft", "")
        draft_id = draft_url.split("/")[-1] if draft_url else str(nv_data.get("id"))
        print(f"[+] Created newversion draft: {draft_id}")
    
    # 2. Get draft details & bucket
    draft_info = _get_json(f"{ZENODO_BASE_URL}/deposit/depositions/{draft_id}", headers)
    bucket_url = draft_info.get("links", {}).get("bucket")
    print(f"[*] Draft {draft_id} bucket: {bucket_url}")
    
    # 3. Update metadata
    print("[*] Updating draft metadata...")
    meta_r = requests.put(f"{ZENODO_BASE_URL}/deposit/depositions/{draft_id}",
                          headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                          json=METADATA)
    if meta_r.status_code != 200:
        print(f"[-] Failed to update metadata: {meta_r.status_code} {meta_r.text}", file=sys.stderr)
        sys.exit(1)
    print(f"[+] Metadata updated successfully. Title: {METADATA['metadata']['title']}")
    
    # 4. Clear any existing draft files to ensure exact replacement
    existing_files = draft_info.get("files", [])
    if existing_files:
        print(f"[*] Removing {len(existing_files)} stale files from draft...")
        for f in existing_files:
            fid = f.get("id")
            requests.delete(f"{ZENODO_BASE_URL}/deposit/depositions/{draft_id}/files/{fid}", headers=headers)
    
    # 5. Upload files to the draft bucket
    print("[*] Uploading certified files to draft bucket...")
    for rel_path, arcname in FILES_TO_PACKAGE:
        filepath = os.path.join(repo_root, rel_path)
        print(f"  -> Uploading {arcname} ({os.path.getsize(filepath):,} bytes)...")
        with open(filepath, "rb") as f:
            up_r = requests.put(f"{bucket_url}/{arcname}", data=f, headers=headers)
            if up_r.status_code not in (200, 201):
                print(f"  [-] Error uploading {arcname}: {up_r.status_code} {up_r.text}", file=sys.stderr)
                sys.exit(1)
    
    # Upload zip bundle as well
    zip_path = os.path.join(repo_root, "01_Verification_Paper", "zenodo_bundle_v5.zip")
    if os.path.exists(zip_path):
        print(f"  -> Uploading zenodo_bundle_v5.zip ({os.path.getsize(zip_path):,} bytes)...")
        with open(zip_path, "rb") as f:
            up_r = requests.put(f"{bucket_url}/zenodo_bundle_v5.zip", data=f, headers=headers)
            if up_r.status_code not in (200, 201):
                print(f"  [-] Error uploading zip bundle: {up_r.status_code} {up_r.text}", file=sys.stderr)
                sys.exit(1)
    
    print(f"[+] All files successfully uploaded to Zenodo draft {draft_id}.")
    
    # 6. Publish if requested
    if publish:
        print(f"[*] Publishing Zenodo deposit {draft_id}...")
        pub_r = requests.post(f"{ZENODO_BASE_URL}/deposit/depositions/{draft_id}/actions/publish", headers=headers)
        if pub_r.status_code not in (200, 201, 202):
            print(f"[-] Publication failed: {pub_r.status_code} {pub_r.text}", file=sys.stderr)
            print(f"[*] You can review and publish manually at: https://zenodo.org/deposit/{draft_id}")
            sys.exit(1)
        
        pub_data = pub_r.json()
        doi = pub_data.get("doi")
        record_url = pub_data.get("links", {}).get("record_html") or f"https://zenodo.org/record/{draft_id}"
        print("=" * 65)
        print("  🎉 SUCCESSFULLY PUBLISHED TO ZENODO!")
        print(f"  DOI:        https://doi.org/{doi}")
        print(f"  Record URL: {record_url}")
        print("=" * 65)
        return pub_data
    else:
        print(f"[*] Draft {draft_id} ready for manual review at: https://zenodo.org/deposit/{draft_id}")
        return draft_info


def main():
    parser = argparse.ArgumentParser(
        description="Zenodo Synchronizer & Certified Packager",
        epilog="SAFETY: By default, this script uploads to a draft without publishing. Use --publish to publish (requires confirmation)."
    )
    parser.add_argument("--token", default=get_token(), help="Zenodo Personal Access Token")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="DESTRUCTIVE: Publish deposit immediately after upload (requires confirmation prompt)"
    )
    parser.add_argument(
        "--draft-only",
        action="store_true",
        help="Deprecated: Use without --publish instead. Upload files and metadata but do not publish."
    )
    parser.add_argument(
        "--draft-id",
        default=None,
        help="Target this existing unsubmitted draft instead of discovering or creating one."
    )
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_zip = os.path.join(repo_root, "01_Verification_Paper", "zenodo_bundle_v5.zip")

    print("=" * 65)
    print(" ZENODO SYNCHRONIZER & CERTIFIED PACKAGER (VERSION 2)")
    print(" Organization: Socrate AI Lab (French Association Loi 1901)")
    print(f" Record ID:    10.5281/zenodo.{RECORD_ID}")
    print("=" * 65)

    create_certified_zip(repo_root, output_zip)

    if not args.token:
        print("[-] Error: No Zenodo token found. Set ZENODO_TOKEN or save to ~/.zenodo_token", file=sys.stderr)
        sys.exit(1)

    # Determine publish action: --publish flag takes precedence, fall back to --draft-only
    should_publish = args.publish and not args.draft_only

    # If publishing, ask for confirmation
    if should_publish and not confirm_publish():
        print("[*] Publication cancelled by user. Draft is ready for manual review.")
        sys.exit(0)

    push_to_zenodo(args.token, repo_root, publish=should_publish, draft_id=args.draft_id)


if __name__ == "__main__":
    main()
