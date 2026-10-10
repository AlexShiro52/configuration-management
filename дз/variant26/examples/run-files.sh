#!/bin/sh
cd "$(dirname "$0")/.." || exit 1
python3 examples/make_vfs.py || exit 1
python3 src/main.py --vfs examples/files.zip --script examples/files.txt
