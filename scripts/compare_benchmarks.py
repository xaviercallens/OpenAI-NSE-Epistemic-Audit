#!/usr/bin/env python3
"""Compare a benchmark run (scripts/run_benchmarks.sh) against the committed reference results.

Each check pairs a number quoted in the paper / CHANGELOG with its regenerated value. Deterministic
quantities must match to a tight relative tolerance; wall-clock times are reported, never checked.
Writes <run>/benchmark_summary.json and prints a table; exits non-zero if any check fails.

Usage: python3 scripts/compare_benchmarks.py <run_dir>
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REF = REPO / "05_Community_Research_Directions" / "experiments" / "results"
STD_AXIOMS = "[propext, Classical.choice, Quot.sound]"
LEAN_DECLS = {"CoreScaling": 10, "LerayAlphaFilter": 7, "LatticeBGKEntropy": 7, "AlphaEnergyIdentity": 5,
              "NonlinearBGKEntropy": 7, "KineticSpectralCap": 6, "OpenAIAdmissibility": 15,
              "BlowupRegimeMap": 13, "LerayAlphaLinearization": 4,
              "QuantumVortexLink": 11}


def load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def main(run: Path) -> int:
    rows: list[dict] = []

    def check(group, name, ref, got, ok, note=""):
        rows.append({"group": group, "check": name, "reference": ref, "reproduced": got, "pass": bool(ok), "note": note})

    def close(a, b, rel):
        return a is not None and b is not None and math.isclose(a, b, rel_tol=rel, abs_tol=rel * 1e-12)

    stages = {}
    if (run / "stages.jsonl").exists():
        for line in (run / "stages.jsonl").read_text().splitlines():
            s = json.loads(line)
            stages[s["stage"]] = s

    def log(name):
        p = run / "logs" / f"{name}.log"
        return p.read_text(errors="replace") if p.exists() else ""

    # --- test suites -------------------------------------------------------------------------------
    m = re.search(r"(\d+) passed", log("pytest"))
    f = re.search(r"(\d+) failed", log("pytest"))
    check("tests", "pytest suite", "all pass", f"{m.group(1) if m else 0} passed, {f.group(1) if f else 0} failed",
          stages.get("pytest", {}).get("rc") == 0 and m is not None)
    passed = sum(int(x) for x in re.findall(r"test result: ok\. (\d+) passed", log("cargo_test")))
    check("tests", "cargo test (kinetic_lock_rs)", "all pass", f"{passed} passed",
          stages.get("cargo_test", {}).get("rc") == 0 and passed > 0)

    # --- linear BGK spectrum (link 4, linear) ------------------------------------------------------
    ref, got = load(REF / "lock_k_kinetic_spectrum.json"), load(run / "experiments/results/lock_k_kinetic_spectrum.json")
    if got:
        qc = got["c_critical_q"]["M1_bisection"]
        check("link4-linear", "termination k*lambda (bisection) vs sqrt(pi/2)", math.sqrt(math.pi / 2), qc,
              abs(qc - math.sqrt(math.pi / 2)) < 1e-9)
        c = got["a_small_k"]["burnett_coefficient_c"]
        check("link4-linear", "Burnett coefficient", 1.0, c, abs(c - 1) < 1e-4)
        check("link4-linear", "damping <= collision rate everywhere", True,
              got["b_max_damping"]["bounded_by_collision_rate_everywhere"], got["b_max_damping"]["bounded_by_collision_rate_everywhere"])
        r = got["d_barrier_vs_kinetic"]["1.0"]["barrier_over_kinetic"]
        check("link4-linear", "barrier/kinetic damping at k*lambda=1", ref["d_barrier_vs_kinetic"]["1.0"]["barrier_over_kinetic"], r,
              close(r, ref["d_barrier_vs_kinetic"]["1.0"]["barrier_over_kinetic"], 1e-6))
        d = got["M1_M2_max_rel_diff_q_le_0.5"]
        check("link4-linear", "two independent methods agree (q<=0.5)", "<1e-10", d, d < 1e-10)
    else:
        check("link4-linear", "lock_k_kinetic_spectrum.json produced", "yes", "missing", False)

    # --- forced core 32^3 (Direction 1) ------------------------------------------------------------
    ref, got = load(REF / "forced_core_32_v3.json"), load(run / "experiments/results/forced_core_32_v3.json")
    if got:
        e = got["control"]["max_rel_l2_error"]
        check("direction1", "32^3 control: whole-field L2 error vs target", ref["control"]["max_rel_l2_error"], e,
              e < 1e-6 and close(e, ref["control"]["max_rel_l2_error"], 0.05))
        for key, label in (("prefactor_C", "B/F prefactor C (pooled)"), ("slope", "B/F pooled slope"),
                           ("C_spread_rel", "per-run C spread")):
            a, b = ref["mechanism_bf_law"][key], got["mechanism_bf_law"][key]
            check("direction1", label, a, b, close(a, b, 1e-3))
        check("direction1", "B/F collapses onto alpha'/(nu tau)", True, got["mechanism_bf_law"]["collapses"],
              got["mechanism_bf_law"]["collapses"])
    else:
        check("direction1", "forced_core_32_v3.json produced", "yes", "missing", False)

    ref, got = load(REF / "forced_core_axial_32.json"), load(run / "experiments/results/forced_core_axial_32.json")
    if got is not None and ref is not None:
        a, b = ref["control"]["max_rel_l2_error"], got["control"]["max_rel_l2_error"]
        check("direction1", "32^3 axial control L2 error", a, b, b < 1e-5 and close(a, b, 0.05))
        for rr, rg in zip(ref["runs"], got["runs"]):
            lab = f"axial lag at end: {rr['model']} alpha={rr['alpha']}"
            check("direction1", lab, rr["lag_at_end"], rg["lag_at_end"], close(rr["lag_at_end"], rg["lag_at_end"], 1e-3))

    # --- re-derived from committed data (long runs are not re-simulated) ---------------------------
    d96 = load(REF / "forced_core_96_v3.json")
    if d96:
        import numpy as np
        a = np.array([r["alpha_prime"] for r in d96["runs"]])
        sel = slice(0, 4)  # clean band sqrt(alpha') <= 0.435
        crossings = sum(bool(r["arrested_before_end"]) for r in d96["runs"])
        check("direction1-96", "96^3: B/F>=1 crossings (paper: 0 of 6)", 0, crossings, crossings == 0)
        for key, paper in (("ell_meas", 0.42), ("u_max", -0.43)):
            v = np.array([d96["series"][repr(x)][key][-1] for x in a])
            p = float(np.polyfit(np.log(a[sel]), np.log(v[sel]), 1)[0])
            check("direction1-96", f"96^3 window-end exponent {key} (clean band)", paper, round(p, 3), abs(p - paper) < 0.006)
        ctl = d96["series"]["None"]
        tau, ell = np.array(ctl["tau"]), np.array(ctl["ell_meas"])
        k = len(tau) // 5
        s = float(np.polyfit(np.log(tau[-k:]), np.log(ell[-k:]), 1)[0])
        check("direction1-96", "96^3 control collapse rate d ln l/d ln tau", 0.5, round(s, 4), abs(s - 0.5) < 0.005)
    kin = load(REF / "kinetic_lock_collapse.json")
    if kin:
        # paper quotes the core size at the first 10% lag (ell_kin_over_lambda_at_lag_crossing), dx 0.67 -> 0.17 lambda
        for re_core, (lo, hi) in ((1.0, (0.98, 0.52)), (0.25, (0.96, 0.35))):
            lad = [L for L in kin["resolution_ladders"] if L["lambda"] == 0.065 and L["re_core"] == re_core][0]
            arr = lad["ell_kin_over_lambda_at_lag_crossing"]
            check("link4-nonlinear", f"lambda=0.065 Re={re_core}: arrest moves with grid (paper {lo} -> {hi} lambda)",
                  f"{lo} -> {hi}", f"{arr[0]:.2f} -> {arr[1]:.2f} -> {arr[-1]:.2f}",
                  abs(arr[0] - lo) < 0.006 and abs(arr[-1] - hi) < 0.006)
        worst = max(r["nse_control"]["max_abs_lag_up_to_kinetic_arrest"] for r in kin["runs_main"])
        check("link4-nonlinear", "NSE control |lag| through kinetic event (paper <= 4e-4)", 4e-4, worst, worst <= 4e-4)
        ahead = min(L["most_ahead_lag"][0] for L in kin["resolution_ladders"])
        check("link4-nonlinear", "kinetic core ahead of NSE (paper: up to 12%)", -0.12, round(ahead, 4), -0.13 < ahead < -0.11)

    # --- Rust kinetic gates (link 4, nonlinear solver validation) ----------------------------------
    ref, got = load(REF / "kinetic_lock_gates.json"), load(run / "experiments/results/kinetic_lock_gates.json")
    if got:
        for g in ("G1", "G2", "G4", "G5"):
            check("link4-nonlinear", f"gate {g}", "pass", "pass" if got[g].get("pass") else "FAIL", got[g].get("pass"))
        g3 = got["G3_cvode"]
        check("link4-nonlinear", "gate G3 (rusty-SUNDIALS CVODE cross-check)", "pass",
              "pass" if g3.get("pass") else f"FAIL/{g3.get('note', '')}", g3.get("pass"))
        a, b = ref["M1_reference_check"]["max_rel_diff"], got["M1_reference_check"]["max_rel_diff"]
        check("link4-nonlinear", "lattice vs exact BGK reference points", a, b, b < 1e-10)
        check("link4-nonlinear", "all gates pass", True, got["all_gates_pass"], got["all_gates_pass"])
    else:
        check("link4-nonlinear", "kinetic_lock_gates.json produced", "yes", "missing", False)

    # --- compressible / thermal forced core ---------------------------------------------------------
    got = load(run / "experiments/results/compressible_core_study.json")
    refc = load(REF / "compressible_core_study.json")
    if got and refc:
        for case, label in (("control_lowMach", "low-Mach control max lag"), ("B_iso_muConst_mass", "Re=1 real-gas mu, isothermal: max lag"),
                            ("D_full_muT_mass", "Re=1 air, full thermodynamics: max lag")):
            a, b = refc[case]["max_lag"], got[case]["max_lag"]
            check("compressible", label, a, b, close(a, b, 1e-3) or (abs(a) < 1e-3 and abs(b) < 1e-3))
        check("compressible", "grid convergence (n=400 vs 800), air", "<1%", abs(got["D_n800"]["max_lag"] / got["D_full_muT_mass"]["max_lag"] - 1),
              abs(got["D_n800"]["max_lag"] / got["D_full_muT_mass"]["max_lag"] - 1) < 0.01)
    sw = load(REF / "compressible_core_re_sweep.json")
    if sw:
        m16, m64 = (sw[f"air_full_mass_re{r}"]["series"]["mach_local"][-1] for r in ("16", "64"))
        deep = sw["air_full_mass_re16_n700_lend0.125"]["series"]["mach_local"][-1]
        check("compressible", "air Mach lock at target Ma=4, Re=16 / 64 (paper 0.70)", 0.70, f"{m16:.3f} / {m64:.3f}", abs(m16 - 0.70) < 0.01 and abs(m64 - 0.70) < 0.01)
        check("compressible", "air Mach lock persists at target Ma=8 (paper 0.70)", 0.70, round(deep, 3), abs(deep - 0.70) < 0.01)
        conv = sw["air_full_mass_re16_n1000_lend0.25"]["series"]["mach_local"][-1]
        check("compressible", "Mach lock grid convergence n=500 vs 1000", "<0.5%", abs(conv / m16 - 1), abs(conv / m16 - 1) < 5e-3)
        iso = sw["iso_muRho_mass_re16"]["series"]["mach_local"][-1]
        check("compressible", "nu-const isothermal control does not lock (paper 1.91)", 1.91, round(iso, 2), abs(iso - 1.91) < 0.02)

    # --- Lean ---------------------------------------------------------------------------------------
    for name, n in LEAN_DECLS.items():
        out = log(f"lean_{name}")
        flat = re.sub(r"\s+", " ", out)
        axioms = re.findall(r"depends on axioms: (\[[^\]]*\])", flat)
        errors = len(re.findall(r"\berror\b", out))
        sorry = "sorryAx" in out
        nonstd = [a for a in axioms if a != STD_AXIOMS]
        ok = stages.get(f"lean_{name}", {}).get("rc") == 0 and errors == 0 and not sorry and len(axioms) == n and not nonstd
        check("lean", f"{name}.lean", f"{n} decls, std axioms", f"{len(axioms)} decls, {errors} errors, sorry={sorry}, non-std={len(nonstd)}", ok)

    # --- report -------------------------------------------------------------------------------------
    summary = {"run_dir": str(run), "stages": stages, "checks": rows,
               "passed": sum(r["pass"] for r in rows), "total": len(rows)}
    (run / "benchmark_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    w = max(len(r["check"]) for r in rows)
    for r in rows:
        print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['group']:16s} {r['check']:{w}s}  ref={r['reference']}  got={r['reproduced']}")
    print("\nstage wall times (s): " + ", ".join(f"{k}={v['wall_s']}" for k, v in stages.items()))
    print(f"\n{summary['passed']}/{summary['total']} checks pass")
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]).resolve()))
