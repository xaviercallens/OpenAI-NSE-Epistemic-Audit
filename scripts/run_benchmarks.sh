#!/usr/bin/env bash
# Reproducibility benchmark: re-runs the checks behind the paper's verified claims and compares the
# regenerated numbers with the committed reference results (scripts/compare_benchmarks.py).
#
#   scripts/run_benchmarks.sh            # quick tier  (~10-20 min on 8 cores)
#   scripts/run_benchmarks.sh --full     # adds the 32^3 axial gate-vs-drain run
#
# Nothing under experiments/results/ is overwritten: experiment scripts are copied into a scratch
# run directory ($BENCH_OUT, default benchmark_runs/<UTC timestamp>) and write their JSON there.
# Requirements: python3 (numpy, scipy, pytest), cargo (offline; rusty-SUNDIALS checked out at
# ../../rusty-SUNDIALS relative to the repo for gate G3), and OpenAI's NavierStokesAndEuler project
# with Mathlib oleans at $OPENAI_LEAN (default ../NavierStokesAndEuler) for the Lean stage.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TIER="quick"; [[ "${1:-}" == "--full" ]] && TIER="full"
RUN="${BENCH_OUT:-$REPO/benchmark_runs/$(date -u +%Y%m%dT%H%M%SZ)}"
OPENAI_LEAN="${OPENAI_LEAN:-$REPO/../NavierStokesAndEuler}"
EXP="$REPO/05_Community_Research_Directions/experiments"
RUST="$REPO/05_Community_Research_Directions/kinetic_lock_rs"
LEAN_SRC="$REPO/03_Lean4_Topological_Censorship/src"
LEAN_FILES=(CoreScaling LerayAlphaFilter LatticeBGKEntropy AlphaEnergyIdentity NonlinearBGKEntropy KineticSpectralCap OpenAIAdmissibility BlowupRegimeMap LerayAlphaLinearization QuantumVortexLink)

mkdir -p "$RUN/experiments/results" "$RUN/logs"
cp "$EXP"/*.py "$RUN/experiments/"
echo "tier=$TIER run_dir=$RUN"
echo "{\"tier\": \"$TIER\", \"started_utc\": \"$(date -u +%FT%TZ)\", \"git\": \"$(git -C "$REPO" rev-parse --short HEAD)\"}" > "$RUN/run_info.json"

stage() {  # stage <name> <command...>: run, time, record exit code
  local name="$1"; shift
  echo "== $name"
  local t0=$(date +%s)
  ( "$@" ) > "$RUN/logs/$name.log" 2>&1
  local rc=$?
  echo "{\"stage\": \"$name\", \"rc\": $rc, \"wall_s\": $(( $(date +%s) - t0 ))}" >> "$RUN/stages.jsonl"
  echo "   rc=$rc  $(( $(date +%s) - t0 )) s"
}

stage pytest            bash -c "cd '$REPO' && python3 -m pytest -q"
stage lock_k_spectrum   bash -c "cd '$RUN/experiments' && python3 lock_k_kinetic_spectrum.py"
stage forced_core_32    bash -c "cd '$RUN/experiments' && python3 forced_core.py --n 32 --nu 0.01 --l0 1.0 --points 4 --l-min-cells 2.5 --sqrt-a-lo 0.5 --sqrt-a-hi 0.8 --tag v3"
stage cargo_test        bash -c "cd '$RUST' && cargo test --offline --release --features sundials"
stage rust_gates        bash -c "cd '$RUST' && RAYON_NUM_THREADS=\${RAYON_NUM_THREADS:-4} cargo run --offline --release --features sundials --bin gates -- --dt-over-tau 0.05 --out '$RUN/experiments/results/kinetic_lock_gates.json' --spectrum '$EXP/results/lock_k_kinetic_spectrum.json'"
if [[ "$TIER" == "full" ]]; then
  stage compressible_core_study bash -c "cd '$RUN/experiments' && python3 compressible_core_study.py"
  stage forced_core_axial_32 bash -c "cd '$RUN/experiments' && python3 forced_core_axial.py --n 32"
fi

# Lean: every verified file compiles in OpenAI's project environment (needed by OpenAIAdmissibility;
# the others import Mathlib only). Output is parsed by the comparison step.
stage lean_prereq bash -c "cd '$OPENAI_LEAN' && lake build NavierStokes.PeriodicUniqueness"
for f in "${LEAN_FILES[@]}"; do
  stage "lean_$f" bash -c "cd '$OPENAI_LEAN' && lake env lean '$LEAN_SRC/$f.lean'"
done

python3 "$REPO/scripts/compare_benchmarks.py" "$RUN" | tee "$RUN/summary.txt"
exit "${PIPESTATUS[0]}"
