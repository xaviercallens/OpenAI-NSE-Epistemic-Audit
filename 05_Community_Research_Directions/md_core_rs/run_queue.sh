#!/bin/sh
# Sequential job queue: each line "<name> <md_run args...>". Output runs/<name>.json, logs/<name>.log.
# Jobs whose JSON already exists are skipped.
jobs="$1"
while read -r name args; do
  case "$name" in ''|'#'*) continue;; esac
  [ -f "runs/$name.json" ] && continue
  RAYON_NUM_THREADS=${RAYON_NUM_THREADS:-4} ./target/release/md_run $args --out "runs/$name.json" > "logs/$name.log" 2>&1
done < "$jobs"
