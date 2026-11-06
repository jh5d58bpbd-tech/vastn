#!/bin/bash
# レンダラーをビルドする。OpenMP（並列計算）が使えなければ自動で1スレッド版にする。
cd "$(dirname "$0")"
try() { echo "build: $*"; "$@" -o pt pt.cpp 2>/dev/null && return 0; return 1; }
try g++ -O3 -fopenmp -march=native && exit 0
for v in 15 14 13 12; do command -v g++-$v >/dev/null && try g++-$v -O3 -fopenmp && exit 0; done   # macOS: brew install gcc
if command -v brew >/dev/null && [ -d "$(brew --prefix libomp 2>/dev/null)" ]; then              # macOS: brew install libomp
  L=$(brew --prefix libomp); try clang++ -O3 -Xpreprocessor -fopenmp -I$L/include -L$L/lib -lomp && exit 0
fi
try c++ -O3 && { echo "注意: OpenMP なしでビルドしました（1スレッドなので遅い）"; exit 0; }
echo "ビルド失敗: C++ コンパイラを入れてください（macOS: xcode-select --install）"; exit 1
