#!/bin/bash
# 美容室パース 4面を書き出す。使い方: ./run_salon.sh [W] [H] [SPP]
cd "$(dirname "$0")"
W=${1:-1440}; H=${2:-900}; SPP=${3:-160}
mkdir -p out
[ -x pt ] || ./build.sh || exit 1
for v in north east west south; do
  python3 scene5.py $v $W $H $SPP out/$v.txt >/dev/null
  ./pt out/$v.txt out/${v}_f > /dev/null 2> out/${v}_log.txt
  python3 post2.py out/${v}_f $W $H out/salon_${v}.jpg
  echo "$v done $(date +%T)"
done
