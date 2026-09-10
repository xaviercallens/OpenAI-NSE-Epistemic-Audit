#!/usr/bin/env python3
"""
zenodo_retriever.py
===================
Epistemic Audit of the OpenAI Navier-Stokes/Euler Singularity
MechanicaFluidorum Program | SocrateAI Research Initiative

Automated retrieval and cryptographic verification tool for the certified
Zenodo open-science archive:
    Record ID: 22696718
    DOI:       10.5281/zenodo.22696718
    URL:       https://zenodo.org/records/22696718
"""

import os
import sys
import hashlib
import argparse
import urllib.request
import json

ZENODO_RECORD_ID = "22696718"
ZENODO_DOI = "10.5281/zenodo.22696718"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

def compute_md5(filepath: str) -> str:
    """Calculate the MD5 hexadecimal digest of a local file."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def fetch_zenodo_metadata() -> dict:
    """Fetch record metadata directly from the Zenodo REST API."""
    req = urllib.request.Request(
        ZENODO_API_URL,
        headers={"User-Agent": "ZenodoRetriever-MechanicaFluidorum/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"Zenodo API responded with HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))

def verify_files(target_dir: str, metadata: dict) -> bool:
    """Verify local files against the remote Zenodo MD5 checksums."""
    files = metadata.get("files", [])
    print(f"\n=================================================================")
    print(f" CRYPTOGRAPHIC AUDIT: ZENODO CERTIFIED ARCHIVE ({ZENODO_DOI})")
    print(f"=================================================================")
    all_ok = True
    for item in files:
        fname = item.get("key")
        expected_md5 = item.get("checksum", "").replace("md5:", "")
        expected_size = item.get("size", 0)
        
        # Look in target_dir or parent directories
        candidate_paths = [
            os.path.join(target_dir, fname),
            os.path.join(os.path.dirname(target_dir), fname),
            os.path.join(os.path.dirname(target_dir), "01_Challenger_Paper", fname)
        ]
        local_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                local_path = p
                break
        
        if not local_path:
            print(f"[MISSING] {fname:<32} (Size: {expected_size} B, MD5: {expected_md5})")
            all_ok = False
            continue
            
        actual_md5 = compute_md5(local_path)
        actual_size = os.path.getsize(local_path)
        
        if actual_md5 == expected_md5:
            print(f"[MATCH]   {fname:<32} -> MD5 {actual_md5} (OK)")
        else:
            print(f"[CORRUPT] {fname:<32} -> Expected {expected_md5}, got {actual_md5}")
            all_ok = False

    print(f"=================================================================")
    if all_ok:
        print("[STATUS]  ALL CERTIFIED ASSETS COMPLIANT WITH ZENODO DEPOSIT")
    else:
        print("[WARNING] SOME ASSETS ARE MISSING OR CHECKSUM MISMATCHED")
    print(f"=================================================================\n")
    return all_ok

def download_missing(target_dir: str, metadata: dict):
    """Download certified assets from Zenodo repository."""
    os.makedirs(target_dir, exist_ok=True)
    files = metadata.get("files", [])
    print(f"Downloading {len(files)} certified assets to {target_dir}...")
    for item in files:
        fname = item.get("key")
        download_url = item.get("links", {}).get("self")
        dest_path = os.path.join(target_dir, fname)
        print(f"-> Fetching {fname} from {download_url}...")
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "ZenodoRetriever-MechanicaFluidorum/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as out_file:
            out_file.write(resp.read())
        print(f"   Saved {fname} ({os.path.getsize(dest_path)} bytes)")

def print_record_info(metadata: dict):
    """Print high-level metadata of the certified deposit."""
    meta = metadata.get("metadata", {})
    print(f"\nZenodo Certified Record Summary:")
    print(f"  Title:       {meta.get('title')}")
    print(f"  DOI:         {metadata.get('doi', ZENODO_DOI)}")
    print(f"  Date:        {meta.get('publication_date')}")
    print(f"  Creators:    {', '.join([c.get('name', '') for c in meta.get('creators', [])])}")
    print(f"  License:     {meta.get('license', {}).get('id', 'Open Access')}")
    print(f"  Files Count: {len(metadata.get('files', []))}")
    for f in metadata.get("files", []):
        print(f"    - {f.get('key'):<30} {f.get('size'):>8} B  [{f.get('checksum')}]")
    print()

def main():
    parser = argparse.ArgumentParser(description="Zenodo Archive Retriever and Validator")
    parser.add_argument("--verify", action="store_true", help="Verify local file hashes against Zenodo record")
    parser.add_argument("--download", action="store_true", help="Download all certified assets into the target directory")
    parser.add_argument("--info", action="store_true", help="Display metadata for the certified Zenodo record")
    parser.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)), help="Working directory for verification/download")
    args = parser.parse_args()

    try:
        metadata = fetch_zenodo_metadata()
    except Exception as e:
        print(f"Error querying Zenodo API: {e}", file=sys.stderr)
        sys.exit(1)

    if args.info or (not args.verify and not args.download):
        print_record_info(metadata)

    if args.download:
        download_missing(args.dir, metadata)

    if args.verify or args.download:
        success = verify_files(args.dir, metadata)
        if not success:
            sys.exit(2)

if __name__ == "__main__":
    main()
