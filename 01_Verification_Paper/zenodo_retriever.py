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

# Certified SHA-256 Manifest for Zenodo Deposit 10.5281/zenodo.22696718.
# NOTE: this is a frozen snapshot of a specific historical deposit, not a live
# fetch from the Zenodo API (see fetch_zenodo_metadata()/verify_against_live_api()
# below for that path, which needs network access this environment doesn't
# always have). A mismatch against this manifest during active development is
# EXPECTED and does not by itself mean anything was "altered" maliciously --
# see verify_archive()'s messaging, which used to imply tampering.
# "audit_openai.py" was renamed to "verify_openai.py" after this manifest was
# recorded; the key below reflects the current filename so the comparison is
# at least checking the file that actually exists.
ZENODO_SHA256_MANIFEST = {
    "OpenAI_NSE_Verification.pdf": "21068c6bfcee224225356a13dcf3947a9c0876ed94edd4e204b6b89804ee374e",
    "OpenAI_NSE_Verification.tex": "2f1870efb0f5ff4badd5465e769a053f958914850b59f472b59b2bbdca47e8d6",
    "REPRODUCTION_PROTOCOL.md": "becf58bd3903e58e238078eabb137548b9fbc4dc7230eed5c6f1de0181e5d600",
    "README.md": "ab26a6de1884b3b5d99a86bed78de10b5cc7646402d5ff692b45565599683187",
    "verify_openai.py": "87f69e6786d5ea86228bef8d9bca112cd92a0acbb65ab35a2341d3a26a0820b6",
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
    """Compares local files against the frozen manifest snapshot above (NOT a
    live Zenodo API fetch -- see verify_against_live_api() for that)."""
    print("=================================================================")
    print(f" LOCAL vs. FROZEN-SNAPSHOT MANIFEST: ZENODO DEPOSIT {ZENODO_RECORD_ID}")
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
            print(f"[DIFFERS] {filename:<30} -> snapshot {expected_hash[:16]}..., local {actual_hash[:16]}...")
            all_match = False

    print("=================================================================")
    if all_match:
        print("[STATUS]  Local files match the recorded Zenodo deposit snapshot exactly.")
        return 0
    else:
        print("[STATUS]  Local files differ from the frozen Zenodo deposit snapshot above.")
        print("          This is EXPECTED during normal editing and is not, by itself,")
        print("          evidence of tampering -- it just means these local files have")
        print("          changed since that specific deposit was made. To check against")
        print("          the CURRENT live deposit instead of this frozen snapshot, run")
        print("          with --live (requires network access to zenodo.org).")
        return 1


def calculate_md5(filepath):
    """Zenodo's API reports checksums as MD5 (field format 'md5:<hex>'), not
    SHA-256, so a genuine live comparison needs this rather than
    calculate_sha256()."""
    if not os.path.exists(filepath):
        return None
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError as e:
        print(f"[-] Error reading {filepath}: {e}", file=sys.stderr)
        return None


def verify_against_live_api():
    """Fetches the CURRENT file list/checksums for this deposit directly from
    the Zenodo API and compares local files against that, instead of the
    frozen snapshot manifest in verify_archive(). This is the accurate check;
    it just needs network access, which is not always available."""
    print("=================================================================")
    print(f" LIVE CRYPTOGRAPHIC AUDIT: ZENODO DEPOSIT {ZENODO_RECORD_ID} (current API state)")
    print("=================================================================")
    metadata = fetch_zenodo_metadata()
    if not metadata or "files" not in metadata:
        print("[-] Could not reach the live Zenodo API (no network, or the record/API changed).")
        print("[-] Falling back to the frozen snapshot manifest instead (verify_archive()).")
        return verify_archive()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    all_match = True
    for f in metadata["files"]:
        filename = f.get("key", f.get("filename", ""))
        checksum_field = f.get("checksum", "")
        expected_md5 = checksum_field.split(":", 1)[1] if ":" in checksum_field else checksum_field
        filepath = os.path.join(script_dir, filename)
        actual_md5 = calculate_md5(filepath)
        if actual_md5 is None:
            print(f"[MISSING] {filename:<30} -> not present locally")
            all_match = False
        elif expected_md5 and actual_md5.lower() == expected_md5.lower():
            print(f"[MATCH]   {filename:<30} -> MD5: {actual_md5[:16]}... (OK)")
        else:
            print(f"[DIFFERS] {filename:<30} -> deposit {expected_md5[:16]}..., local {actual_md5[:16]}...")
            all_match = False

    print("=================================================================")
    if all_match:
        print("[STATUS]  Local files match the CURRENT live Zenodo deposit exactly.")
        return 0
    else:
        print("[STATUS]  Local files differ from the current live Zenodo deposit.")
        print("          As above: expected during editing between deposits, not")
        print("          itself evidence of tampering.")
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
    parser.add_argument("--verify", action="store_true", help="Verify local files against the frozen snapshot manifest (default behavior)")
    parser.add_argument("--live", action="store_true", help="Verify against the CURRENT live Zenodo API instead of the frozen snapshot (needs network)")
    parser.add_argument("--download", action="store_true", help="Fetch remote metadata or missing assets from Zenodo API")
    args = parser.parse_args()

    if args.download:
        download_missing_assets()

    exit_code = verify_against_live_api() if args.live else verify_archive()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
