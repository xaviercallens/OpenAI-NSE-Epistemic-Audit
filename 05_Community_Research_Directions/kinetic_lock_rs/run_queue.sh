#!/bin/sh
# Sequential job queue for the kinetic-lock runs. Each line of the job file:
#   <name> <collapse_run args...>
# Output: runs/<name>.json, logs/<name>.log. Jobs whose JSON already exists are skipped.
jobs="$1"
while read -r name args; do
  case "$name" in ''|'#'*) continue;; esac
  [ -f "runs/$name.json" ] && continue
  RAYON_NUM_THREADS=4 ./target/release/collapse_run $args --out "runs/$name.json" > "logs/$name.log" 2>&1
done < "$jobs"
