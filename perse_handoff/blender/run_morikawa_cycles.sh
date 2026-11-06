#!/bin/bash
# 森川ビル パースを Blender Cycles で書き出す。使い方: ./run_morikawa_cycles.sh [W] [H] [SPP] [view...]
# 画角: ldk_1-4, datsui_1-4, genkan_1-4, toilet_1-4（render/morikawa.py の VIEWS）
cd "$(dirname "$0")"
W=${1:-1440}; H=${2:-900}; SPP=${3:-128}
shift 3 2>/dev/null
VIEWS=${@:-ldk_1 ldk_2 ldk_3 ldk_4 datsui_1 datsui_2 datsui_3 datsui_4 genkan_1 genkan_2 genkan_3 genkan_4 toilet_1 toilet_2 toilet_3 toilet_4}
mkdir -p out/morikawa
for v in $VIEWS; do
  SCENE=morikawa python3 kyuke_cycles.py $v $W $H $SPP out/morikawa/$v > out/morikawa/${v}_log.txt 2>&1 || { echo "$v failed (see out/morikawa/${v}_log.txt)"; continue; }
  CONTRAST=${CONTRAST:-0.18} SAT=${SAT:-1.06} python3 post_cycles.py out/morikawa/$v.npy out/morikawa/morikawa_$v.jpg ${EXPO:-0.60}
  echo "$v done $(date +%T)"
done
