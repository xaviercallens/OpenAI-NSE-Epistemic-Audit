#!/usr/bin/env python3
"""
zenodo_retriever.py
===================
Epistemic Audit of the OpenAI Navier-Stokes/Euler Singularity
MechanicaFluidorum Program | SocrateAI Research Initiative

Title: Zenodo Certified Archive Verifier (DOI: 10.5281/zenodo.22696718)
Description: 
    Validates that the local files in the 01_Challenger_Paper directory
    exactly match the cryptographic MD5 checksums of the certified
    Zenodo open-science deposit.
"""

import os
import sys
import hashlib
import argparse

# Hardcoded cryptographic manifest from Zenodo Deposit 22696718
# UPDATED POST-PEER REVIEW
ZENODO_MANIFEST = {
    "verify-physical-vacuity.sh": "e9fc106f14c36f1860bc470c36c0d57a",
    "OpenAI_NSE_EpistemicAudit.tex": "30950306b8d2300b54d5bad9960729a5",
    "REPRODUCTION_PROTOCOL.md": "fe3d098425ed093147a1b0c0f82be8c6",
    "OpenAI_NSE_EpistemicAudit.pdf": "92670f2e03e40558043032f43f3904e7",
    "audit_openai.py": "49236846dda9838e208f9658e7e25e17"
}

def calculate_md5(filepath):
    """Calculates the MD5 checksum of a file."""
    if not os.path.exists(filepath):
        return None
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_archive():
    print("=================================================================")
    print(" CRYPTOGRAPHIC AUDIT: ZENODO CERTIFIED ARCHIVE (10.5281/zenodo.22696718)")
    print("=================================================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    all_match = True
    
    for filename, expected_md5 in ZENODO_MANIFEST.items():
        filepath = os.path.join(script_dir, filename)
        actual_md5 = calculate_md5(filepath)
        
        if actual_md5 is None:
            print(f"[MISSING] {filename:<32} -> Expected {expected_md5}")
            all_match = False
        elif actual_md5 == expected_md5:
            print(f"[MATCH]   {filename:<32} -> MD5 {actual_md5} (OK)")
        else:
            print(f"[FAIL]    {filename:<32} -> Expected {expected_md5}, got {actual_md5}")
            all_match = False

    print("=================================================================")
    if all_match:
        print("[STATUS]  ALL CERTIFIED ASSETS COMPLIANT WITH ZENODO DEPOSIT")
        sys.exit(0)
    else:
        print("[STATUS]  CRYPTOGRAPHIC MISMATCH DETECTED. FILES MAY BE ALTERED.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zenodo Archive Verifier")
    parser.add_argument("--verify", action="store_true", help="Verify local files against Zenodo MD5 manifest")
    parser.add_argument("--download", action="store_true", help="Simulate Zenodo download (dry run)")
    args = parser.parse_args()

    if args.download:
        print("[ZENODO] Simulating download from API...")
        print("[ZENODO] All assets are already present locally. Run --verify to check integrity.")
    
    if args.verify or not (args.download):
        verify_archive()
