#!/usr/bin/env python3
"""
zenodo_retriever.py
===================
Physical Verification of the OpenAI Navier-Stokes/Euler Singularity
MechanicaFluidorum Program | SocrateAI Research Initiative

Title: Zenodo Certified Archive Verifier (DOI: 10.5281/zenodo.22696718)
Description: 
    Validates that the local files in the 01_Challenger_Paper directory
    exactly match the cryptographic SHA-256 checksums of the certified
    Zenodo open-science deposit.
"""

import os
import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.error

ZENODO_RECORD_ID = "22696718"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

# Certified SHA-256 Manifest for Zenodo Deposit 10.5281/zenodo.22696718
ZENODO_SHA256_MANIFEST = {
    "OpenAI_NSE_Verification.pdf": "21068c6bfcee224225356a13dcf3947a9c0876ed94edd4e204b6b89804ee374e",
    "OpenAI_NSE_Verification.tex": "2f1870efb0f5ff4badd5465e769a053f958914850b59f472b59b2bbdca47e8d6",
    "REPRODUCTION_PROTOCOL.md": "becf58bd3903e58e238078eabb137548b9fbc4dc7230eed5c6f1de0181e5d600",
    "README.md": "ab26a6de1884b3b5d99a86bed78de10b5cc7646402d5ff692b45565599683187",
    "audit_openai.py": "87f69e6786d5ea86228bef8d9bca112cd92a0acbb65ab35a2341d3a26a0820b6",
    "verify-physical-vacuity.sh": "cf1cedc4e0836ae216deecfab43a4bd6a44bd0c089095958d5c53c87b6e94f16"
}


def calculate_sha256(filepath):
    """Calculates the cryptographically secure SHA-256 checksum of a file."""
    if not os.path.exists(filepath):
        return None
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError as e:
        print(f"[-] Error reading {filepath}: {e}", file=sys.stderr)
        return None


def fetch_zenodo_metadata():
    """Fetches record metadata from the Zenodo REST API."""
    print(f"[*] Querying Zenodo REST API for record {ZENODO_RECORD_ID}...")
    req = urllib.request.Request(
        ZENODO_API_URL, 
        headers={"User-Agent": "MechanicaFluidorum-Audit/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"[-] Warning: Unable to query Zenodo API ({e}). Falling back to certified local manifest.", file=sys.stderr)
        return None


def verify_archive():
    """Performs SHA-256 cryptographic verification of all certified paper assets."""
    print("=================================================================")
    print(f" CRYPTOGRAPHIC AUDIT: ZENODO CERTIFIED ARCHIVE ({ZENODO_RECORD_ID})")
    print(" Algorithm: SHA-256 (NIST Secure Hash Standard)")
    print("=================================================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    all_match = True
    
    for filename, expected_hash in ZENODO_SHA256_MANIFEST.items():
        filepath = os.path.join(script_dir, filename)
        actual_hash = calculate_sha256(filepath)
        
        if actual_hash is None:
            print(f"[MISSING] {filename:<30} -> Expected {expected_hash[:16]}...")
            all_match = False
        elif actual_hash.lower() == expected_hash.lower():
            print(f"[MATCH]   {filename:<30} -> SHA-256: {actual_hash[:16]}... (OK)")
        else:
            print(f"[FAIL]    {filename:<30} -> Expected {expected_hash[:16]}..., got {actual_hash[:16]}...")
            all_match = False

    print("=================================================================")
    if all_match:
        print("[STATUS]  ALL CERTIFIED ASSETS COMPLIANT WITH ZENODO DEPOSIT")
        return 0
    else:
        print("[STATUS]  CRYPTOGRAPHIC MISMATCH DETECTED. FILES MAY BE ALTERED.")
        return 1


def download_missing_assets():
    """Downloads missing assets from Zenodo if network connection is available."""
    metadata = fetch_zenodo_metadata()
    if not metadata or "files" not in metadata:
        print("[*] Remote API unavailable or deposit files offline. Using local files.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    for f in metadata["files"]:
        filename = f.get("key", f.get("filename", ""))
        download_url = f.get("links", {}).get("self", "")
        dest_path = os.path.join(script_dir, filename)
        if not os.path.exists(dest_path) and download_url:
            print(f"[*] Downloading {filename} from Zenodo...")
            try:
                urllib.request.urlretrieve(download_url, dest_path)
                print(f"[+] Downloaded {filename} successfully.")
            except Exception as e:
                print(f"[-] Failed downloading {filename}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Zenodo Certified Archive Cryptographic Verifier")
    parser.add_argument("--verify", action="store_true", help="Verify local files against certified SHA-256 manifest")
    parser.add_argument("--download", action="store_true", help="Fetch remote metadata or missing assets from Zenodo API")
    args = parser.parse_args()

    if args.download:
        download_missing_assets()
    
    # Default behavior is verification
    exit_code = verify_archive()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
