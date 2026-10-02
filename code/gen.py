#!/usr/bin/env python3
"""Seed + drip generator for the Signature Chip Maker and Archive.
Appends compact rows {id,fam,era,seed,name}; the full design renders
deterministically client-side in engine.js. Name formula mirrors engine.js chipName()."""
import json, os, gzip, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CHUNKS = os.path.join(DATA, "chunks")
IDX = os.path.join(DATA, "index")
STATE = os.path.join(DATA, "state.json")
CHUNK_N = 200
GOAL = 1_000_000

FAMS = ["CPU","GPU","NPU","SOC","MCU","FPGA","MEMC","SENSOR","PMIC","QCTRL","PHOT","NEURO","DSP","MODEM","SEC","CHIPLET"]
ERAS = ["Historic","Modern","Projected"]
ERA_W = [0.25, 0.55, 0.20]

PRE=["Volt","Helix","Nova","Flux","Tera","Pulse","Zenith","Axiom","Cobalt","Drift","Ember","Ferro","Ion","Lumen","Onyx","Kryo","Grav","Jolt","Nexus","Prism","Quanta","Ridge","Slate","Torque","Umbra","Vex","Weld","Xen","Yield","Zephyr"]
MID=["Core","Forge","Mesh","Grid","Weave","Stack","Array","Engine","Matrix","Node","Circuit","Signal","Vector","Spark","Alloy"]
SUF=["X1","X4","M7","S9","P2","Q5","R3","T8","V6","Z2","A1","B5","C3","D9","E4"]

def chip_name(idx):
    g = idx // 6750
    return "Signature %s%s %s%s" % (PRE[idx%30], MID[(idx//30)%15], SUF[(idx//450)%15], (" G%d"%g) if g else "")

def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"next_index": 1}

def save_state(s):
    json.dump(s, open(STATE, "w"))

def gen_rows(n, start):
    rng = random.Random(20261002)
    rows = []
    for i in range(start, start+n):
        fam = FAMS[(i-1) % len(FAMS)]
        era = rng.choices(ERAS, weights=ERA_W)[0]
        rows.append({"id": "JAH-CHIP-%06d" % i, "fam": fam, "era": era,
                     "seed": rng.randrange(1, 2**31), "name": chip_name(i-1)})
    return rows

def write_chunks(rows):
    os.makedirs(CHUNKS, exist_ok=True)
    # group rows by chunk number derived from id
    by_chunk = {}
    for r in rows:
        idx = int(r["id"].split("-")[-1])
        c = (idx-1)//CHUNK_N + 1
        by_chunk.setdefault(c, []).append(r)
    for c, rs in by_chunk.items():
        p = os.path.join(CHUNKS, "c%05d.json.gz" % c)
        existing = []
        if os.path.exists(p):
            existing = [json.loads(l) for l in gzip.open(p, "rt")]
        seen = {x["id"] for x in existing}
        existing += [x for x in rs if x["id"] not in seen]
        existing.sort(key=lambda x: x["id"])
        with gzip.open(p, "wt") as f:
            for x in existing:
                f.write(json.dumps(x, separators=(",", ":")) + "\n")

def rebuild_index(total_hint=None):
    os.makedirs(IDX, exist_ok=True)
    # compact search rows [id,name,fam,era] across all chunks
    files = sorted(f for f in os.listdir(CHUNKS) if f.endswith(".json.gz"))
    n = 0
    with gzip.open(os.path.join(IDX, "chips.search.json.gz"), "wt") as out:
        for fn in files:
            for line in gzip.open(os.path.join(CHUNKS, fn), "rt"):
                r = json.loads(line)
                out.write(json.dumps([r["id"], r["name"], r["fam"], r["era"]], separators=(",", ":")) + "\n")
                n += 1
    return n

def build_sitemap(n, base="https://justinahiggins614-cmyk.github.io/signature-chip-maker/"):
    urls = [base, base+"?browse=all"]
    files = sorted(f for f in os.listdir(CHUNKS) if f.endswith(".json.gz"))
    for fn in files:
        for line in gzip.open(os.path.join(CHUNKS, fn), "rt"):
            r = json.loads(line)
            urls.append(base+"?chip="+r["id"])
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append("<url><loc>%s</loc><changefreq>weekly</changefreq></url>" % u)
    xml.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(xml))
    return len(urls)

def build_api(n):
    api = {"site": "The Signature Computer Chip Maker and Archive",
           "site_url": "https://justinahiggins614-cmyk.github.io/signature-chip-maker/",
           "designs_seeded": n, "goal": GOAL,
           "id_scheme": "JAH-CHIP-######", "part_scheme": "SIG-CHIP-#### (Signature-original)",
           "deep_link": "?chip=JAH-CHIP-000001",
           "search_index": "data/index/chips.search.json.gz",
           "chunks": "data/chunks/cNNNNN.json.gz (%d/chunk)" % CHUNK_N,
           "note": "All designs are original Signature-line works. No real manufacturer branding, part numbers, or datasheet text."}
    json.dump(api, open(os.path.join(ROOT, "api.json"), "w"), indent=1)

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1600
    st = load_state()
    start = st["next_index"]
    rows = gen_rows(n, start)
    write_chunks(rows)
    total = rebuild_index()
    urls = build_sitemap(total)
    build_api(total)
    st["next_index"] = start + n
    save_state(st)
    print("seeded +%d designs, total %d, sitemap %d urls" % (n, total, urls))

if __name__ == "__main__":
    main()
