#!/bin/bash
# 休憩室パース 3面を Blender Cycles で書き出す。使い方: ./run_kyukei_cycles.sh [W] [H] [SPP] [view...]
# 必要: pip3 install bpy numpy opencv-python
# デザイン案: VARIANT=cafe ./run_kyukei_cycles.sh ...（render/variants.py。レイアウトは変えず仕上げ・色・光色だけ変える）
cd "$(dirname "$0")"
W=${1:-1440}; H=${2:-900}; SPP=${3:-256}
shift 3 2>/dev/null
VIEWS=${@:-south north kitchen}
mkdir -p out
for v in $VIEWS; do
  python3 kyuke_cycles.py $v $W $H $SPP out/$v${VARIANT:+_$VARIANT} > out/${v}${VARIANT:+_$VARIANT}_log.txt 2>&1 || { echo "$v failed (see out/${v}_log.txt)"; continue; }
  python3 post_cycles.py out/$v${VARIANT:+_$VARIANT}.npy out/kyukei_${v}_cycles${VARIANT:+_$VARIANT}.jpg 0.85
  echo "$v done $(date +%T)"
done
