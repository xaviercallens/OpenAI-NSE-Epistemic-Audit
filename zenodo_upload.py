#!/usr/bin/env python3
"""
Zenodo Upload Script for Thermodynamic Censorship Paper

Uploads the complete research package to Zenodo via the REST API.
Requires ZENODO_TOKEN environment variable or ~/.zenodo_token file.

Usage:
  export ZENODO_TOKEN=your_token_here
  python3 zenodo_upload.py

To get a token: https://zenodo.org/account/settings/applications/tokens/new/
Grant scopes: deposit:actions, deposit:write
"""

import json
import os
import sys
import requests

# ============================================================
# Configuration
# ============================================================
ZENODO_API = "https://zenodo.org/api"
# ZENODO_API = "https://sandbox.zenodo.org/api"  # Use sandbox for testing

METADATA = {
    "metadata": {
        "title": "Thermodynamic Censorship of Navier-Stokes Singularities: "
                 "Why Mathematical Blow-ups Are Physically Unrealizable",
        "upload_type": "publication",
        "publication_type": "preprint",
        "description": (
            "<p>An independent epistemic audit of OpenAI's Lean 4 formalized proof "
            "of finite-time blow-up for the forced 3D incompressible Navier-Stokes "
            "equations (Clay Millennium Prize, Alternatives C &amp; D).</p>"
            "<p>We verify the proof is formally flawless (0 sorry, 0 axioms, correct "
            "C∞ force type) but demonstrate the construction is physically unrealizable: "
            "enstrophy diverges (τ<sup>-0.515</sup>), Jacobian condition number reaches "
            "10<sup>28</sup>, and the Mach number exceeds 0.3 at τ ≈ 10<sup>-14</sup> s.</p>"
            "<p>We propose the Thermodynamic Censorship Principle: physically admissible "
            "solutions must satisfy uniform bounded enstrophy.</p>"
            "<p>Includes: complete LaTeX paper, 6 computational audit scripts (Python/SymPy), "
            "Lean 4 formalization (ThermodynamicCensorship.lean), and structured dataset.</p>"
        ),
        "creators": [
            {
                "name": "Callens, Xavier",
                "affiliation": "Socrate AI Lab, MechanicaFluidorum Program",
                "orcid": ""
            }
        ],
        "keywords": [
            "Navier-Stokes equations",
            "Millennium Prize Problem",
            "Lean 4",
            "formal verification",
            "thermodynamic censorship",
            "fluid dynamics",
            "OpenAI",
            "epistemic audit",
            "enstrophy",
            "blow-up",
            "singularity"
        ],
        "subjects": [
            {"term": "Mathematical physics", "identifier": "https://id.loc.gov/authorities/subjects/sh85082139"},
            {"term": "Fluid dynamics", "identifier": "https://id.loc.gov/authorities/subjects/sh85049376"}
        ],
        "license": "cc-by-4.0",
        "related_identifiers": [
            {
                "identifier": "https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit",
                "relation": "isSupplementTo",
                "scheme": "url"
            },
            {
                "identifier": "https://github.com/openai/NavierStokesAndEuler",
                "relation": "references",
                "scheme": "url"
            },
            {
                "identifier": "https://huggingface.co/datasets/callensxavier/OpenAI-NSE-Thermodynamic-Censorship",
                "relation": "isSupplementTo",
                "scheme": "url"
            }
        ],
        "version": "1.0.0"
    }
}

ZIP_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "OpenAI-NSE-Thermodynamic-Censorship-v1.0.zip"
)


def get_token():
    """Get Zenodo token from environment or file."""
    token = os.environ.get("ZENODO_TOKEN")
    if token:
        return token
    
    token_file = os.path.expanduser("~/.zenodo_token")
    if os.path.exists(token_file):
        with open(token_file) as f:
            return f.read().strip()
    
    return None


def main():
    token = get_token()
    if not token:
        print("=" * 60)
        print("ZENODO UPLOAD INSTRUCTIONS")
        print("=" * 60)
        print()
        print("No Zenodo token found. To upload:")
        print()
        print("1. Go to: https://zenodo.org/account/settings/applications/tokens/new/")
        print("2. Create a token with scopes: deposit:actions, deposit:write")
        print("3. Run one of:")
        print("   export ZENODO_TOKEN=your_token_here")
        print("   echo 'your_token_here' > ~/.zenodo_token")
        print("4. Re-run this script: python3 zenodo_upload.py")
        print()
        print(f"Archive ready for upload: {ZIP_FILE}")
        print(f"Archive size: {os.path.getsize(ZIP_FILE) / 1024:.1f} KB")
        print()
        print("Or upload manually at: https://zenodo.org/deposit/new")
        print("using the metadata below:")
        print()
        print(json.dumps(METADATA, indent=2))
        return 1
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Create empty deposition
    print("Creating Zenodo deposition...")
    r = requests.post(f"{ZENODO_API}/deposit/depositions",
                     json=METADATA, headers=headers)
    if r.status_code != 201:
        print(f"Error creating deposition: {r.status_code}")
        print(r.json())
        return 1
    
    dep = r.json()
    dep_id = dep["id"]
    bucket_url = dep["links"]["bucket"]
    doi = dep["metadata"].get("prereserve_doi", {}).get("doi", "pending")
    
    print(f"  Deposition ID: {dep_id}")
    print(f"  Pre-reserved DOI: {doi}")
    
    # Step 2: Upload ZIP file
    print(f"Uploading {ZIP_FILE}...")
    with open(ZIP_FILE, "rb") as f:
        r = requests.put(
            f"{bucket_url}/OpenAI-NSE-Thermodynamic-Censorship-v1.0.zip",
            data=f, headers=headers
        )
    
    if r.status_code not in (200, 201):
        print(f"Error uploading: {r.status_code}")
        print(r.json())
        return 1
    
    print(f"  Upload successful: {r.json()['size']} bytes")
    
    # Step 3: Publish
    print("Publishing...")
    r = requests.post(f"{ZENODO_API}/deposit/depositions/{dep_id}/actions/publish",
                     headers=headers)
    
    if r.status_code != 202:
        print(f"Error publishing: {r.status_code}")
        print(r.json())
        print("\nDeposition created but not published. Visit:")
        print(f"  https://zenodo.org/deposit/{dep_id}")
        return 1
    
    pub = r.json()
    print()
    print("=" * 60)
    print("✅ PUBLISHED TO ZENODO")
    print("=" * 60)
    print(f"  DOI: {pub['doi']}")
    print(f"  URL: {pub['links']['html']}")
    print(f"  Record: {pub['links']['record_html']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
