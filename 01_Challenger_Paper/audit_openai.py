#!/usr/bin/env python3
import os
import re
import subprocess

REPO_URL = "https://github.com/openai/NavierStokesAndEuler.git"
REPO_DIR = "NavierStokesAndEuler"

def clone_repo():
    if not os.path.exists(REPO_DIR):
        print("[*] Cloning OpenAI repository...")
        subprocess.run(["git", "clone", REPO_URL])
    else:
        print("[*] Repository already present.")

def extract_evidence(filepath, pattern, description):
    print(f"\n[ SEARCH ] {description}")
    full_path = os.path.join(REPO_DIR, filepath)
    if not os.path.exists(full_path):
        print(f"  -> ❌ File not found: {filepath}")
        return

    with open(full_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    found = False
    for i, line in enumerate(lines):
        if re.search(pattern, line):
            print(f"  ✅ Line {i+1} : {line.strip()}")
            found = True
            
    if not found:
        print(f"  -> ⚠️ Pattern not found.")

print("==========================================================")
print(" EPISTEMIC AUDIT : EXTRACTING OPENAI LEAN 4 ARTIFACTS")
print("==========================================================\n")

clone_repo()

# 1. Proof of Initial Rest (Energy solely from forcing)
extract_evidence(
    "NavierStokes/ProblemStatement.lean", 
    r"zero_initial_velocity", 
    "Navier-Stokes: Proof that the fluid starts from absolute rest (u_0 = 0)"
)

# 2. Proof of Tautological Forcing (Manufactured Solution)
extract_evidence(
    "NavierStokes/CandidateFromLimits.lean", 
    r"def tracedResidual|pastResidual", 
    "Navier-Stokes: External force is defined as the mathematical residual of the equation"
)

# 3. Proof of Continuum Violation (Euler)
extract_evidence(
    "Euler/PacketSourceScaleSequence.lean", 
    r"def frequency.*J.*X.*n", 
    "Euler: Vortex spatial scale depends on a frequency sequence that diverges"
)
extract_evidence(
    "Euler/PacketInitialSmoothLimit.lean", 
    r"∑ n ∈ range N", 
    "Euler: Initial condition is an infinite superposition pushed into the ultraviolet"
)
print("\n==========================================================")
print(" Utilize these exact Lean 4 lines in the paper to source the critique.")
print("==========================================================")
