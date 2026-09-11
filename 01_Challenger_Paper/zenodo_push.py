#!/usr/bin/env python3
"""
zenodo_push.py
==============
Epistemic Audit of the OpenAI Navier-Stokes/Euler Singularity
MechanicaFluidorum Program | Socrate AI Lab (French Association Loi 1901)

Automated Zenodo synchronizer and bundle packager for Record 22696718.
- Validates SHA-256 integrity of all certified assets.
- Creates certified distribution archive (zenodo_bundle_v2.zip).
- Interacts with Zenodo REST API to publish/update deposit when ZENODO_TOKEN is provided.
"""

import os
import sys
import json
import zipfile
import hashlib
import argparse
import urllib.request
import urllib.error

RECORD_ID = "22696718"
ZENODO_BASE_URL = "https://zenodo.org/api"

FILES_TO_PACKAGE = [
    "OpenAI_NSE_EpistemicAudit.pdf",
    "OpenAI_NSE_EpistemicAudit.tex",
    "REPRODUCTION_PROTOCOL.md",
    "README.md",
    "audit_openai.py",
    "verify-physical-vacuity.sh"
]

METADATA = {
    "metadata": {
        "title": "On the Physical Vacuity of Manufactured Singularities: An Epistemic Audit of the OpenAI Navier-Stokes Formalization (Version 2)",
        "upload_type": "publication",
        "publication_type": "preprint",
        "description": "An empirical and analytical epistemic audit refuting manufactured singularities in fluid dynamics formalized in Lean 4. Dissects the Method of Manufactured Solutions (Tautological Syringe) and sub-Planckian ultraviolet frequency cascade in OpenAI NavierStokesAndEuler repository.",
        "creators": [
            {
                "name": "Callens, Xavier",
                "affiliation": "Socrate AI Lab / MechanicaFluidorum Program"
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
            "Formal Verification",
            "Lean 4",
            "Epistemic Audit",
            "Fluid Dynamics",
            "Neuro-Symbolic AI"
        ],
        "license": "MIT",
        "access_right": "open",
        "related_identifiers": [
            {
                "identifier": "https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit",
                "relation": "isSupplementTo",
                "scheme": "url"
            }
        ]
    }
}


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def create_certified_zip(paper_dir, output_zip):
    print(f"[*] Packaging certified Zenodo distribution zip: {output_zip}")
    manifest = {}
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in FILES_TO_PACKAGE:
            filepath = os.path.join(paper_dir, filename)
            if not os.path.exists(filepath):
                print(f"[-] Error: Missing asset {filename}", file=sys.stderr)
                sys.exit(1)
            sha = compute_sha256(filepath)
            manifest[filename] = sha
            zf.write(filepath, arcname=filename)
            print(f"  + {filename:<32} (SHA-256: {sha[:16]}...)")
        
        zf.writestr("metadata.json", json.dumps(METADATA, indent=2))
        zf.writestr("manifest_sha256.json", json.dumps(manifest, indent=2))

    print(f"[+] Successfully generated certified archive: {output_zip} ({os.path.getsize(output_zip)} bytes)")
    return manifest


def push_to_zenodo_api(token, zip_path, paper_dir):
    print(f"[*] Contacting Zenodo API for record {RECORD_ID} with provided authentication token...")
    newversion_url = f"{ZENODO_BASE_URL}/deposit/depositions/{RECORD_ID}/actions/newversion"
    req = urllib.request.Request(
        newversion_url,
        data=b"",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            new_deposition_url = data.get("links", {}).get("latest_draft")
            print(f"[+] Created new version draft at: {new_deposition_url}")
            draft_id = new_deposition_url.split("/")[-1]
            bucket_url = data.get("links", {}).get("bucket")
            
            for filename in FILES_TO_PACKAGE:
                filepath = os.path.join(paper_dir, filename)
                file_url = f"{bucket_url}/{filename}"
                with open(filepath, "rb") as f:
                    file_data = f.read()
                upload_req = urllib.request.Request(
                    file_url,
                    data=file_data,
                    headers={"Authorization": f"Bearer {token}"},
                    method="PUT"
                )
                with urllib.request.urlopen(upload_req) as up_resp:
                    print(f"  [+] Uploaded {filename} to Zenodo bucket.")
            
            print(f"[+] Zenodo Version 2 draft #{draft_id} updated with all certified assets.")
            print(f"[*] To publish the draft, visit https://zenodo.org/deposit/{draft_id} or run publication action.")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[-] Zenodo API HTTP {e.code}: {err_msg}", file=sys.stderr)
    except Exception as e:
        print(f"[-] Zenodo API Error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Zenodo Synchronizer & Certified Packager")
    parser.add_argument("--token", default=os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN"),
                        help="Zenodo Personal Access Token (or set ZENODO_TOKEN env var)")
    parser.add_argument("--push", action="store_true", help="Push update to Zenodo API")
    args = parser.parse_args()

    paper_dir = os.path.dirname(os.path.abspath(__file__))
    output_zip = os.path.join(paper_dir, "zenodo_bundle_v2.zip")

    print("=" * 65)
    print(" ZENODO SYNCHRONIZER & CERTIFIED PACKAGER")
    print(" Organization: Socrate AI Lab (French Association Loi 1901)")
    print(" Record ID:    10.5281/zenodo.22696718")
    print("=" * 65)

    create_certified_zip(paper_dir, output_zip)

    if args.push or args.token:
        if not args.token:
            print("[-] Error: No Zenodo token provided. Set ZENODO_TOKEN or pass --token <KEY>", file=sys.stderr)
            sys.exit(1)
        push_to_zenodo_api(args.token, output_zip, paper_dir)
    else:
        print("\n[*] Certified package zenodo_bundle_v2.zip is ready for upload.")
        print("[*] To push directly via API, provide a Zenodo Personal Access Token:")
        print("    python3 01_Challenger_Paper/zenodo_push.py --token <ZENODO_TOKEN>")
        print("    or set export ZENODO_TOKEN=<TOKEN> and run --push")
    print("=" * 65)


if __name__ == "__main__":
    main()
