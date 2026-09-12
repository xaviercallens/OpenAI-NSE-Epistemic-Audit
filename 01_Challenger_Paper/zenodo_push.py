#!/usr/bin/env python3
"""
zenodo_push.py
==============
Epistemic Audit of the OpenAI Navier-Stokes/Euler Singularity
MechanicaFluidorum Program | Socrate AI Lab (French Association Loi 1901)

Automated Zenodo synchronizer and bundle packager for Record 22696718 (Version 2).
- Validates SHA-256 integrity of all certified assets.
- Packages distribution archive (zenodo_bundle_v2.zip).
- Synchronizes with Zenodo REST API and publishes the updated deposit.
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
    ("01_Challenger_Paper/OpenAI_NSE_EpistemicAudit.pdf", "OpenAI_NSE_EpistemicAudit.pdf"),
    ("01_Challenger_Paper/OpenAI_NSE_EpistemicAudit.tex", "OpenAI_NSE_EpistemicAudit.tex"),
    ("01_Challenger_Paper/REPRODUCTION_PROTOCOL.md", "REPRODUCTION_PROTOCOL.md"),
    ("01_Challenger_Paper/README.md", "README.md"),
    ("01_Challenger_Paper/audit_openai.py", "audit_openai.py"),
    ("01_Challenger_Paper/verify-physical-vacuity.sh", "verify-physical-vacuity.sh"),
    ("03_Lean4_Topological_Censorship/src/ThermodynamicCensorship.lean", "ThermodynamicCensorship.lean"),
    ("dataset/audit_results.json", "audit_results.json"),
    ("scripts/academic_outreach_campaign.json", "academic_outreach_campaign.json"),
    ("scripts/directive2_thermodynamic_paradox.py", "directive2_thermodynamic_paradox.py"),
    ("scripts/directive3_jacobian_instability.py", "directive3_jacobian_instability.py"),
    ("scripts/directive4_gevrey_regularity.py", "directive4_gevrey_regularity.py"),
    ("scripts/directive5_mach_divergence.py", "directive5_mach_divergence.py"),
    ("scripts/directive6_thermal_instability.py", "directive6_thermal_instability.py"),
]

METADATA = {
    "metadata": {
        "title": "On the Physical Vacuity of Manufactured Singularities: A Comprehensive Epistemic Audit of the OpenAI Navier-Stokes Formalization (Version 2)",
        "upload_type": "publication",
        "publication_type": "preprint",
        "description": (
            "<p>In September 2026, an OpenAI multi-agent system formalized finite-time blow-up proofs "
            "for the forced 3D Navier-Stokes equations (Millennium Prize Alternatives C and D) and the "
            "unforced Euler equations within Lean 4. While this represents a landmark achievement in "
            "automated theorem proving and syntactic mathematics, a rigorous epistemic audit reveals "
            "that these singularities are driven by pathological mathematics rather than natural fluid dynamics.</p>"
            "<p>We confirm the Lean 4 proof contains no axiomatic hallucinations and legally satisfies "
            "the Clay Mathematics Institute criteria via Gevrey-2 class cutoffs. However, this mathematical "
            "ingenuity exposes five profound epistemic disconnects:</p>"
            "<ol>"
            "<li><strong>Structural Instability:</strong> requiring 10<sup>28</sup>-digit precision to "
            "maintain Reynolds stress cancellation against 300K thermal fluctuations;</li>"
            "<li><strong>Thermodynamic Paradox:</strong> local enstrophy diverges as &tau;<sup>-0.515</sup>, "
            "generating infinite viscous dissipation and violating incompressibility;</li>"
            "<li><strong>Mach Number Self-Invalidation:</strong> local Mach number exceeds 0.3 at "
            "&tau; &approx; 6.7 &times; 10<sup>-14</sup> seconds before blow-up;</li>"
            "<li><strong>Teleological Reversal:</strong> Newtonian causality is inverted, with the external "
            "force reverse-engineered from the desired singularity;</li>"
            "<li><strong>Ultraviolet Bomb:</strong> in unforced Euler, active kinetic energy is injected at "
            "infinite spatial frequencies, violating the continuum hypothesis at t = 0.</li>"
            "</ol>"
            "<p>We formalize the <em>Thermodynamic Censorship Principle</em>: physically admissible "
            "solutions must satisfy uniform bounded enstrophy. Under this axiom, Gevrey-2 vortex collapse "
            "blow-ups are provably censored. We conclude that autonomous, naturally occurring 3D fluids "
            "do not blow up in finite time.</p>"
            "<p>This certified distribution includes the full publication manuscript (PDF and LaTeX), "
            "the Lean 4 formalization (ThermodynamicCensorship.lean), 6 Python verification scripts, "
            "pre-computed output logs, and the complete academic outreach campaign.</p>"
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
            "Epistemic Audit",
            "Fluid Dynamics",
            "Thermodynamic Censorship",
            "Gevrey Regularity",
            "Structural Instability",
            "Neuro-Symbolic AI"
        ],
        "version": "2.0.0",
        "license": "cc-by-4.0",
        "access_right": "open",
        "related_identifiers": [
            {
                "identifier": "https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit",
                "relation": "isSupplementTo",
                "scheme": "url"
            },
            {
                "identifier": "https://huggingface.co/datasets/callensxavier/OpenAI-NSE-Thermodynamic-Censorship",
                "relation": "isSupplementTo",
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


def push_to_zenodo(token, repo_root, publish=True):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Check existing draft or create new version from RECORD_ID
    print(f"[*] Checking Zenodo record {RECORD_ID}...")
    r = requests.get(f"{ZENODO_BASE_URL}/deposit/depositions", headers=headers)
    if r.status_code != 200:
        print(f"[-] Failed to fetch deposits: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    
    deposits = r.json()
    concept_id = None
    draft_id = None

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
    draft_r = requests.get(f"{ZENODO_BASE_URL}/deposit/depositions/{draft_id}", headers=headers)
    draft_info = draft_r.json()
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
    zip_path = os.path.join(repo_root, "01_Challenger_Paper", "zenodo_bundle_v2.zip")
    if os.path.exists(zip_path):
        print(f"  -> Uploading zenodo_bundle_v2.zip ({os.path.getsize(zip_path):,} bytes)...")
        with open(zip_path, "rb") as f:
            up_r = requests.put(f"{bucket_url}/zenodo_bundle_v2.zip", data=f, headers=headers)
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
    parser = argparse.ArgumentParser(description="Zenodo Synchronizer & Certified Packager")
    parser.add_argument("--token", default=get_token(), help="Zenodo Personal Access Token")
    parser.add_argument("--publish", action="store_true", default=True, help="Publish deposit immediately (default: True)")
    parser.add_argument("--draft-only", action="store_true", help="Upload files and metadata but do not call publish action")
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_zip = os.path.join(repo_root, "01_Challenger_Paper", "zenodo_bundle_v2.zip")

    print("=" * 65)
    print(" ZENODO SYNCHRONIZER & CERTIFIED PACKAGER (VERSION 2)")
    print(" Organization: Socrate AI Lab (French Association Loi 1901)")
    print(f" Record ID:    10.5281/zenodo.{RECORD_ID}")
    print("=" * 65)

    create_certified_zip(repo_root, output_zip)

    if not args.token:
        print("[-] Error: No Zenodo token found. Set ZENODO_TOKEN or save to ~/.zenodo_token", file=sys.stderr)
        sys.exit(1)

    should_publish = not args.draft_only
    push_to_zenodo(args.token, repo_root, publish=should_publish)


if __name__ == "__main__":
    main()
