#!/usr/bin/env python3
"""Build gate for The Signature Computer Chip Maker and Archive.
Fails loudly on: duplicate/missing IDs, count mismatch across every source,
chunk gaps, hash mismatch, stale index_hash, determinism drift, trademark
leakage, license field in JSON-LD, malformed deep links. Exit 0 = all pass."""
import gzip, hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-chip-maker/"
fails = []
passed = 0
total_checks = 0
def check(name, cond, detail=""):
    global passed, total_checks
    total_checks += 1
    if cond:
        passed += 1
    print(("PASS " if cond else "FAIL ") + name + ((" — " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(name)

def rows():
    out = []
    d = os.path.join(ROOT, "data", "chunks")
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json.gz"):
            for line in gzip.open(os.path.join(d, fn), "rt"):
                out.append(json.loads(line))
    out.sort(key=lambda r: r["id"])
    return out

rs = rows()
ids = [r["id"] for r in rs]
n = len(rs)

# 1. ID uniqueness + contiguity
check("unique IDs", len(set(ids)) == n, "%d dupes" % (n - len(set(ids))))
expect = ["JAH-CHIP-%06d" % i for i in range(1, n + 1)]
check("contiguous IDs 1..%d" % n, ids == expect,
      "first gap: %s" % next((e for e in expect if e not in set(ids)), "?"))

# 2. ID format
check("ID format JAH-CHIP-######", all(re.fullmatch(r"JAH-CHIP-\d{6}", i) for i in ids))

# 3. chunk continuity: 200/chunk, files c00001..cNNNNN
d = os.path.join(ROOT, "data", "chunks")
cfs = sorted(f for f in os.listdir(d) if f.endswith(".json.gz"))
exp_files = ["c%05d.json.gz" % i for i in range(1, len(cfs) + 1)]
check("chunk files contiguous", cfs == exp_files, "%d files" % len(cfs))
per = [sum(1 for _ in gzip.open(os.path.join(d, f), "rt")) for f in cfs]
check("chunks hold %d each (last may be partial)" % 200,
      all(c == 200 for c in per[:-1]) and per[-1] <= 200, str(per[-3:]))

# 4. count agreement everywhere
man = json.load(open(os.path.join(ROOT, "chip-archive-manifest.json")))
api = json.load(open(os.path.join(ROOT, "api.json")))
cat = json.load(open(os.path.join(ROOT, "data", "chips-catalog.json")))
idx_n = sum(1 for _ in gzip.open(os.path.join(ROOT, "data/index/chips.search.json.gz"), "rt"))
hsh_n = sum(1 for _ in gzip.open(os.path.join(ROOT, "data/index/chips.hashes.json.gz"), "rt"))
sm_n = 0
for fn in sorted(os.listdir(ROOT)):
    if re.fullmatch(r"sitemap-chips-b\d{3}\.xml", fn):
        sm_n += open(os.path.join(ROOT, fn)).read().count("<loc>")
check("manifest total == chunk rows", man["total_designs"] == n, "%s vs %d" % (man["total_designs"], n))
check("api total == chunk rows", api["total_designs"] == n)
check("catalog records == chunk rows", len(cat["records"]) == n, str(len(cat["records"])))
check("search index rows == chunk rows", idx_n == n, str(idx_n))
check("hash index rows == chunk rows", hsh_n == n, str(hsh_n))
check("sitemap URLs == chunk rows", sm_n == n, str(sm_n))
check("state next_index == n+1", json.load(open(os.path.join(ROOT, "data/state.json")))["next_index"] == n + 1)

# 5. family counts reconcile
fam_sum = sum(f["count"] for f in man["families"])
check("family counts sum to total", fam_sum == n, str(fam_sum))
check("16 families", man["family_count"] == 16 and len(man["families"]) == 16)
check("earliest/latest IDs", man["earliest_id"] == "JAH-CHIP-000001" and man["latest_id"] == ids[-1])

# 6. index_hash matches the actual file
h = hashlib.sha256()
with open(os.path.join(ROOT, "data/index/chips.search.json.gz"), "rb") as f:
    for b in iter(lambda: f.read(1 << 20), b""):
        h.update(b)
check("manifest index_hash matches file", man["index_hash_sha256"] == h.hexdigest())

# 7. sitemap deep-link form
bad = 0
for fn in sorted(os.listdir(ROOT)):
    if re.fullmatch(r"sitemap-chips-b\d{3}\.xml", fn):
        for m in re.finditer(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, fn)).read()):
            if not re.fullmatch(re.escape(BASE) + r"\?chip=JAH-CHIP-\d{6}", m.group(1)):
                bad += 1
check("sitemap deep-link form", bad == 0, "%d bad" % bad)

# 8. determinism: test vectors re-render to the same hashes
# (hashes index was rendered by build_hashes.js from canonicalRecord;
#  vectors pin the expected values, so any engine drift fails loudly)
tv = json.load(open(os.path.join(ROOT, "code/test_vectors.json")))
vec = {v["id"]: v["expected_hash_sha256"] for v in tv["vectors"]}
hmap = {}
for line in gzip.open(os.path.join(ROOT, "data/index/chips.hashes.json.gz"), "rt"):
    r = json.loads(line)
    hmap[r["id"]] = (r["hash"], r["engine"])
ok = all(hmap[i][0] == vec[i] and hmap[i][1] == tv["engine_version"] for i in vec)
check("test-vector hashes match (%d vectors)" % len(vec), ok)

# 9. trademark safety: no real manufacturer branding anywhere in data/engine
BLOCK = ["intel", "amd", "nvidia", "qualcomm", "apple inc", "samsung", "tsmc",
         "broadcom", "mediatek", "texas instruments", "microchip", "nxp", "infineon",
         "cortex", "snapdragon", "ryzen", "geforce", "radeon", "xeon"]
blob = " ".join(r["name"] for r in rs).lower() + open(os.path.join(ROOT, "engine.js")).read().lower()
hits = [b for b in BLOCK if re.search(r"\b" + re.escape(b) + r"\b", blob)]
check("no real manufacturer branding", not hits, str(hits))

# 10. JSON-LD carries no license field (his rule)
html = open(os.path.join(ROOT, "index.html")).read()
check("no license field in JSON-LD/page", '"license"' not in html.lower())

# 11. rendered record honesty fields present (sample via node)
sample = rs[0]
chk = subprocess.run(["node", "-e",
    "const E=require(%s).ChipEngine;const c=E.canonicalRecord(%s);"
    "const need=['record_schema','specs','pin_groups','diagram','creation_mode','value_kind',"
    "'design_status','sim_status','test_status','mfg_status','canonical_url','parent_chip_id'];"
    "const miss=need.filter(k=>!(k in c));"
    "const unitsOk=c.specs.every(s=>s.unit&&s.kind==='GENERATED_TARGET');"
    "console.log(JSON.stringify({miss:miss,unitsOk:unitsOk,"
    "statusOk:c.design_status==='CONCEPT'&&c.sim_status==='NOT_SIMULATED'&&c.test_status==='NOT_TESTED'&&c.mfg_status==='NOT_MANUFACTURED'}));"
    % (json.dumps(os.path.join(ROOT, "engine.js")), json.dumps(sample))],
    capture_output=True, text=True)
res = json.loads(chk.stdout)
check("canonical record honesty fields", not res["miss"] and res["unitsOk"] and res["statusOk"],
      str(res))

# 12. no undefined/placeholder text in any rendered string value (sample via node)
chk2 = subprocess.run(["node", "-e",
    "const E=require(%s).ChipEngine;const rec=E.canonicalRecord(%s);"
    "let bad=[];"
    "function walk(v,path){if(typeof v==='string'){if(/undefined|TODO|FIXME|lorem ipsum/i.test(v))bad.push(path);} "
    "else if(v&&typeof v==='object'){for(const k in v)walk(v[k],path+'.'+k);}}"
    "walk(rec,'rec');console.log(JSON.stringify({bad:bad}));"
    % (json.dumps(os.path.join(ROOT, "engine.js")), json.dumps(sample))],
    capture_output=True, text=True)
res2 = json.loads(chk2.stdout)
check("no placeholder text in record strings", not res2["bad"], str(res2["bad"][:3]))

# 14. sitemap XML well-formed + listed in index
import xml.dom.minidom
sm_files = ["sitemap.xml"] + [f for f in sorted(os.listdir(ROOT)) if re.fullmatch(r"sitemap(-core|-chips-b\d{3})\.xml", f)]
try:
    for f in sm_files:
        xml.dom.minidom.parse(os.path.join(ROOT, f))
    check("sitemap XML well-formed (%d files)" % len(sm_files), True)
except Exception as e:
    check("sitemap XML well-formed", False, str(e))
idx = open(os.path.join(ROOT, "sitemap.xml")).read()
check("sitemap index lists all parts",
      all(p in idx for p in ["sitemap-core.xml"] + ["sitemap-chips-b%03d.xml" % (i + 1) for i in range(len(cfs) * 200 // 1000)]))

# 15. api.json version + health
check("api.json health block", api.get("health", {}).get("status") == "OK"
      and api["health"].get("index_records") == n)

if fails:
    print("FAILED: %s" % ", ".join(fails))
    sys.exit(1)
print("ALL QA CHECKS PASSED (%d/%d, %d designs)" % (passed, total_checks, n))
