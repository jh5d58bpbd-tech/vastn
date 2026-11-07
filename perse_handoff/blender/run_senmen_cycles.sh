#!/bin/bash
# 洗面脱衣所 クロス×床 4案（render/senmen.py）を Cycles で書き出す。使い方: ./run_senmen_cycles.sh [W] [H] [SPP] [案番号...]
cd "$(dirname "$0")"
W=${1:-1440}; H=${2:-900}; SPP=${3:-96}
shift 3 2>/dev/null
VARS=${@:-1 2 3 4}
mkdir -p out/senmen
for v in $VARS; do
  VARIANT=$v SCENE=senmen python3 kyuke_cycles.py main $W $H $SPP out/senmen/an$v > out/senmen/an${v}_log.txt 2>&1 || { echo "$v failed (see out/senmen/an${v}_log.txt)"; continue; }
  CONTRAST=${CONTRAST:-0.14} SAT=${SAT:-1.0} python3 post_cycles.py out/senmen/an$v.npy out/senmen/senmen_an$v.jpg ${EXPO:-0.68}
  echo "$v done $(date +%T)"
done
