#!/usr/bin/env python3
"""
Extract & Audit Script for OpenAI Navier-Stokes & Euler Lean 4 Formalization
MechanicaFluidorum Program / SocrateAI Lab (September 2026)

This script:
1. Clones/fetches https://github.com/openai/NavierStokesAndEuler.git.
2. Extracts the exact Git commit SHA and all necessary Lean 4 proof source files.
3. Computes SHA-256 cryptographic checksums for every Lean 4 file.
4. Executes the AST Crawling & Epistemic Audit verification protocol.
5. Emits an immutable, machine-verifiable audit certificate `openai_lean_audit_certificate.json`.
"""

import os
import sys
import subprocess
import hashlib
import json
import re
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

REPO_URL = "https://github.com/openai/NavierStokesAndEuler.git"
TARGET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "openai_repo")
CERTIFICATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "openai_lean_audit_certificate.json")

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def clone_or_update_repo():
    """Returns (sha, degraded). `degraded=True` means this run did NOT audit
    the real OpenAI repository -- either the clone failed and we fell back to
    a 1-line stub, or we could not determine a real git SHA. Callers MUST
    propagate `degraded` into the certificate rather than silently presenting
    stub-file results as if they audited the real repo."""
    print(f"[*] Checking repository target at {TARGET_DIR}...")
    degraded = False
    if not os.path.exists(TARGET_DIR):
        print(f"[*] Cloning {REPO_URL} into {TARGET_DIR}...")
        code, out, err = run_cmd(f"git clone {REPO_URL} \"{TARGET_DIR}\"")
        if code != 0:
            print(f"[!] Git clone failed: {err}")
            print("[!!!] DEGRADED RUN: could not fetch the real OpenAI repository.")
            print("[!!!] Falling back to a 1-line placeholder file. Any audit results")
            print("[!!!] from this run describe the placeholder, NOT OpenAI's actual")
            print("[!!!] Lean formalization, and must not be reported as if they do.")
            degraded = True
            os.makedirs(TARGET_DIR, exist_ok=True)
            with open(os.path.join(TARGET_DIR, "ProblemStatement.lean"), "w", encoding="utf-8") as f:
                f.write("-- FALLBACK STUB: real OpenAI repo could not be cloned; this is not the real proof.\n")
    else:
        print(f"[*] Repository already exists at {TARGET_DIR}.")

    code, sha, _ = run_cmd("git rev-parse HEAD", cwd=TARGET_DIR)
    if code != 0 or not sha:
        print("[!!!] DEGRADED RUN: could not determine a real git commit SHA for the target directory.")
        sha = "UNKNOWN_SHA_DEGRADED_RUN"
        degraded = True
    print(f"[{'!' if degraded else '✓'}] Target Repository Git SHA: {sha}{'  (DEGRADED)' if degraded else ''}")
    return sha, degraded

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_and_catalog_lean_files():
    lean_catalog = {}
    total_lines = 0
    total_bytes = 0
    
    for root, _, files in os.walk(TARGET_DIR):
        if ".git" in root or ".lake" in root or "lake-packages" in root:
            continue
        for file in files:
            if file.endswith(".lean"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, TARGET_DIR).replace("\\", "/")
                
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines()
                
                file_hash = sha256_file(full_path)
                file_bytes = os.path.getsize(full_path)
                
                lean_catalog[rel_path] = {
                    "sha256": file_hash,
                    "line_count": len(lines),
                    "size_bytes": file_bytes,
                    "is_core_path": "ComparatorChallenges" not in rel_path
                }
                
                total_lines += len(lines)
                total_bytes += file_bytes
                
    print(f"[✓] Cataloged {len(lean_catalog)} Lean 4 files ({total_lines} lines, {total_bytes} bytes).")
    return lean_catalog

def audit_lean_codebase(lean_catalog):
    print("[*] Executing Epistemic Audit AST Crawling & Verification Protocol...")

    sorry_core_count = 0
    sorry_total_count = 0
    custom_axiom_count = 0
    opaque_count = 0
    contdiff_infty_found = False
    energy_bound_found = False

    # Anchored to actual Lean 4 declaration syntax (optional modifiers, then the
    # keyword, then a name) so we don't match the word appearing in prose or in
    # a doc comment that explicitly says e.g. "not an axiom". Lean 4 has no
    # `constant` keyword (that was Lean 3) so it is intentionally NOT matched
    # here -- matching it against English prose ("a physical constant") is
    # exactly the false-positive pattern this rewrite removes.
    axiom_decl_re = re.compile(r'^(private\s+|protected\s+|scoped\s+|noncomputable\s+)*axiom\s+\w')
    opaque_decl_re = re.compile(r'^(private\s+|protected\s+|scoped\s+|noncomputable\s+)*opaque\s+\w')

    for rel_path, meta in lean_catalog.items():
        full_path = os.path.join(TARGET_DIR, rel_path.replace("/", os.sep))
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.splitlines()

        is_core = meta["is_core_path"]
        in_block_comment = False

        for line in lines:
            # Track (non-nested) /- ... -/ block comments so prose inside them
            # (e.g. "0 custom axioms", "no sorry used here") is never scanned
            # as code. This is a simple single-level tracker: it does not
            # handle nested block comments, which Lean permits but which are
            # rare in practice; a line that both opens and closes a block
            # comment is treated as fully commented.
            raw = line
            if in_block_comment:
                if "-/" in raw:
                    raw = raw.split("-/", 1)[1]
                    in_block_comment = False
                else:
                    continue
            if "/-" in raw:
                before, _, after = raw.partition("/-")
                if "-/" in after:
                    raw = before + after.split("-/", 1)[1]
                else:
                    raw = before
                    in_block_comment = True

            # Strip line comments
            clean_line = raw.split("--")[0].strip()
            if not clean_line:
                continue

            if re.search(r'\bsorry\b', clean_line) or re.search(r'\badmit\b', clean_line):
                sorry_total_count += 1
                if is_core:
                    sorry_core_count += 1

            if axiom_decl_re.search(clean_line):
                custom_axiom_count += 1

            if opaque_decl_re.search(clean_line):
                opaque_count += 1

            if "ContDiff ℝ ⊤" in clean_line or "ContDiff ℝ ∞" in clean_line:
                contdiff_infty_found = True

            if "kineticEnergy" in clean_line or "finite_energy" in clean_line or "∫ x, ‖v x t‖ ^ 2" in clean_line:
                energy_bound_found = True

    verification_results = {
        "check_1_sorry_admit_core": {
            "expected": 0,
            "found": sorry_core_count,
            "status": "PASSED" if sorry_core_count == 0 else "FAILED"
        },
        "check_2_custom_axioms": {
            "expected": 0,
            "found": custom_axiom_count,
            "status": "PASSED" if custom_axiom_count == 0 else "FAILED"
        },
        "check_3_opaque_declarations": {
            "expected": 0,
            "found": opaque_count,
            "status": "PASSED" if opaque_count == 0 else "FAILED"
        },
        "check_4_force_smoothness": {
            "expected": "ContDiff ℝ ⊤ (C^∞)",
            "found": "ContDiff ℝ ⊤ found in scanned source" if contdiff_infty_found else "NOT FOUND in scanned source",
            "status": "PASSED" if contdiff_infty_found else "NOT_FOUND"
        },
        "check_5_energy_bound_uniform": {
            "expected": "A kinetic-energy / finite-energy identifier appears in the scanned source",
            "found": "found" if energy_bound_found else "NOT FOUND in scanned source",
            "status": "PASSED" if energy_bound_found else "NOT_FOUND"
        },
        # ----------------------------------------------------------------
        # checks 6-9 are NOT derived by scanning this run's cloned repository
        # -- they are static reference figures carried over from this
        # project's own physical-verification analysis
        # (01_Verification_Paper/OpenAI_NSE_Verification.tex). They will
        # print identically regardless of which repository/commit was
        # cloned above. They are kept here for convenient cross-reference,
        # NOT as live audit results, and must not be presented as if this
        # script derived them from the Lean source it just scanned.
        # ----------------------------------------------------------------
        "check_6_gevrey_index_STATIC_REFERENCE": {
            "source": "static_reference_not_derived_from_this_scan",
            "theoretical_asymptotic_s": 1.5,
            "empirical_preasymptotic_slope": 2.22,
            "function_class": "Gevrey-1.5 (C^infty, not real-analytic)",
        },
        "check_7_thermodynamic_scaling_STATIC_REFERENCE": {
            "source": "static_reference_not_derived_from_this_scan",
            "local_energy_density_scaling": "tau^(-1.010)",
            "enstrophy_scaling": "tau^(-0.515)",
            "note": "Global L2 energy remains bounded; these are LOCAL/intensive quantities. See OpenAI_NSE_Verification.tex Table 1 for the corrected framing.",
        },
        "check_8_mach_invalidation_timeline_STATIC_REFERENCE": {
            "source": "static_reference_not_derived_from_this_scan",
            "ma_0_3_breach_physical_seconds": 6.69e-12,
            "picoseconds_before_singularity": 6.69,
            "note": "Corrected value (physical time t = T*tau, T = l0^2/nu = 100s for water); see OpenAI_NSE_Verification.tex Table tab:mach. An earlier draft mislabeled the dimensionless tau value directly as seconds (100x too small).",
        },
        "check_9_matrix_conditioning_STATIC_REFERENCE": {
            "source": "static_reference_not_derived_from_this_scan",
            "raw_unscaled_kappa_A_at_XR_1000": 1.78e28,
            "nondimensional_kappa_B": 4.11e5,
            "note": "The raw figure is a non-dimensionalization artifact, not physical fine-tuning; see OpenAI_NSE_Verification.tex Section 3.",
        }
    }

    return verification_results

def generate_audit_certificate(git_sha, degraded, lean_catalog, verification_results):
    # Derive the headline verdict from the actual computed sub-checks instead
    # of asserting it as a fixed string, so it cannot silently disagree with
    # the checks printed right above it.
    structural_checks = ["check_1_sorry_admit_core", "check_2_custom_axioms", "check_3_opaque_declarations"]
    failed = [k for k in structural_checks if verification_results[k]["status"] != "PASSED"]
    if degraded:
        syntactic_soundness = "DEGRADED_RUN_DID_NOT_SCAN_REAL_REPOSITORY"
    elif failed:
        syntactic_soundness = "STRUCTURAL_CHECKS_FAILED: " + ", ".join(failed)
    else:
        syntactic_soundness = "ALL_STRUCTURAL_CHECKS_PASSED_0_SORRY_0_AXIOM_0_OPAQUE"

    cert_payload = {
        "certificate_title": "OpenAI Navier-Stokes Lean Source Structural-Check Certificate",
        "repository_url": REPO_URL,
        "git_commit_sha": git_sha,
        "degraded_run": degraded,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "formalization_verdict": {
            "syntactic_soundness": syntactic_soundness,
            "note": (
                "This certificate covers ONLY the structural checks in check_1-5 above, "
                "which are actually derived from scanning the cloned repository's Lean "
                "source. check_6-9 are static reference figures from this project's own "
                "physical-verification paper (see each check's 'source' field) and are "
                "NOT derived from this scan. Any physical-realizability or "
                "'censorship' verdict is a separate, explicitly-labeled hypothesis "
                "discussed in OpenAI_NSE_Verification.tex Sec. 10.4 -- not something "
                "this script establishes -- and is intentionally not asserted here."
            ),
        },
        "verification_protocol": verification_results,
        "extracted_sources_summary": {
            "total_files": len(lean_catalog),
            "files": lean_catalog
        }
    }
    
    # Calculate self-referential payload SHA-256
    payload_str = json.dumps(cert_payload, sort_keys=True, indent=2)
    cert_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
    cert_payload["certificate_signature_sha256"] = cert_hash
    
    with open(CERTIFICATE_PATH, "w", encoding="utf-8") as f:
        json.dump(cert_payload, f, indent=2)
        
    print(f"\n[✓] Audit Certificate successfully generated at:\n    {CERTIFICATE_PATH}")
    print(f"[✓] Certificate SHA-256 Signature: {cert_hash}")
    return cert_payload

def main():
    print("=========================================================================")
    print(" OpenAI Navier-Stokes Formalization Extraction & Structural-Check Audit")
    print("=========================================================================")
    sha, degraded = clone_or_update_repo()
    catalog = extract_and_catalog_lean_files()
    verdict = audit_lean_codebase(catalog)
    cert = generate_audit_certificate(sha, degraded, catalog, verdict)
    print("\n--- AUDIT SUMMARY ---")
    print(f"Git SHA         : {cert['git_commit_sha']}{'  (DEGRADED RUN)' if cert['degraded_run'] else ''}")
    print(f"Syntactic Proof : {cert['formalization_verdict']['syntactic_soundness']}")
    print("(See formalization_verdict.note in the JSON certificate for scope of this verdict.)")
    print("=========================================================================")

if __name__ == "__main__":
    main()
