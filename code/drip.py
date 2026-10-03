#!/usr/bin/env python3
"""2h drip for the Chip Maker: +1000 designs/run toward 1M. Silent unless failure/milestone."""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r

# 800MB repo guard
total = 0
for dp, dn, fn in os.walk("data"):
    for f in fn:
        total += os.path.getsize(os.path.join(dp, f))
if total > 800*1024*1024:
    print("GUARD: data dir over 800MB, drip paused")
    sys.exit(2)

r = sh("python3 code/gen.py 1000")
print(r.stdout.strip() or r.stderr.strip())
if r.returncode != 0:
    sys.exit(1)

# JS syntax check on engine.js
r = sh("node --check engine.js && echo JSOK")
if "JSOK" not in r.stdout:
    print("engine.js syntax FAIL"); sys.exit(1)

# per-design content hashes (deterministic) — must rebuild after new designs
r = sh("node code/build_hashes.js")
print(r.stdout.strip() or r.stderr.strip())
if r.returncode != 0:
    print("hash build FAIL"); sys.exit(1)

import json
n = sum(1 for _ in open(os.devnull))  # placeholder
# count from search index
import gzip
cnt = sum(1 for _ in gzip.open("data/index/chips.search.json.gz", "rt"))
sh('git add -A && git -c user.name="JAH System" -c user.email="jah@chipmaker.local" commit -qm "Chip drip: +1000 (%d designs)" && git push -q origin main' % cnt)
print("drip done, %d designs live-seeded" % cnt)
