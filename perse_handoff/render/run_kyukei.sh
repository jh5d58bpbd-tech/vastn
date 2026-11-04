#!/bin/bash
# 休憩室パース 3面を書き出す。使い方: ./run_kyukei.sh [W] [H] [SPP]
cd "$(dirname "$0")"
W=${1:-1440}; H=${2:-900}; SPP=${3:-128}
mkdir -p out
[ -x pt ] || ./build.sh || exit 1
for v in south north kitchen; do
  python3 kyuke.py $v $W $H $SPP out/$v.txt >/dev/null
  ./pt out/$v.txt out/${v}_f > /dev/null 2> out/${v}_log.txt
  e=$(python3 post2.py out/${v}_f $W $H /dev/null 2>/dev/null | awk '{print $2}')
  python3 post2.py out/${v}_f $W $H out/kyukei_${v}.jpg $(python3 -c "print($e*0.85)")
  echo "$v done $(date +%T)"
done
