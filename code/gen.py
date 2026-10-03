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

def all_rows():
    """Every seeded design row, in ID order."""
    files = sorted(f for f in os.listdir(CHUNKS) if f.endswith(".json.gz"))
    rows = []
    for fn in files:
        for line in gzip.open(os.path.join(CHUNKS, fn), "rt"):
            rows.append(json.loads(line))
    rows.sort(key=lambda r: r["id"])
    return rows

def build_sitemap(base="https://justinahiggins614-cmyk.github.io/signature-chip-maker/"):
    """Modular sitemap: sitemap.xml is an INDEX over sitemap-core.xml +
    per-batch sitemap-chips-bNNN.xml files (1000 designs each)."""
    rows = all_rows()
    batch = 1000
    parts = []
    core_urls = [base, base + "?browse=all", base + "chips.html"]
    core = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in core_urls:
        core.append("<url><loc>%s</loc><changefreq>weekly</changefreq></url>" % u)
    core.append("</urlset>")
    open(os.path.join(ROOT, "sitemap-core.xml"), "w").write("\n".join(core))
    parts.append("sitemap-core.xml")
    for i in range(0, len(rows), batch):
        n = i // batch + 1
        name = "sitemap-chips-b%03d.xml" % n
        x = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for r in rows[i:i + batch]:
            x.append("<url><loc>%s?chip=%s</loc><changefreq>weekly</changefreq></url>" % (base, r["id"]))
        x.append("</urlset>")
        open(os.path.join(ROOT, name), "w").write("\n".join(x))
        parts.append(name)
    idx = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in parts:
        idx.append("<sitemap><loc>%s%s</loc></sitemap>" % (base, p))
    idx.append("</sitemapindex>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(idx))
    return len(rows) + len(core_urls)

FAMLABELS = {"CPU": "Signature CPU", "GPU": "Signature GPU", "NPU": "Signature NPU AI Accelerator",
             "SOC": "Signature SoC", "MCU": "Signature Microcontroller", "FPGA": "Signature FPGA",
             "MEMC": "Signature Memory Controller", "SENSOR": "Signature Sensor Chip",
             "PMIC": "Signature Power Management IC", "QCTRL": "Signature Quantum Control Chip",
             "PHOT": "Signature Photonic Chip", "NEURO": "Signature Neuromorphic Chip",
             "DSP": "Signature DSP", "MODEM": "Signature Baseband Modem",
             "SEC": "Signature Security Enclave", "CHIPLET": "Signature Chiplet Interconnect"}

def build_catalog(n, base="https://justinahiggins614-cmyk.github.io/signature-chip-maker/"):
    """Standardized machine-readable catalog feed: data/chips-catalog.json."""
    from datetime import datetime, timezone
    rows = all_rows()
    feed = {
        "site": "The Signature Computer Chip Maker and Archive",
        "site_url": base,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "designs": n,
        "goal": GOAL,
        "id_scheme": "JAH-CHIP-######",
        "families": [{"key": k, "label": FAMLABELS[k]} for k in FAMS],
        "records": [{"id": r["id"], "name": r["name"], "fam": r["fam"],
                     "type": FAMLABELS[r["fam"]], "era": r["era"],
                     "url": base + "?chip=" + r["id"]} for r in rows],
    }
    p = os.path.join(DATA, "chips-catalog.json")
    json.dump(feed, open(p, "w"), separators=(",", ":"))
    return p

def build_static_catalog(n, base="https://justinahiggins614-cmyk.github.io/signature-chip-maker/"):
    """Pre-rendered static HTML tables for non-JS crawlers: chips.html index +
    one chips-fam-<KEY>.html table page per family (id, name, type, era, summary)."""
    import html
    from datetime import date
    rows = all_rows()
    css = ("<style>body{background:#0a1628;color:#cfe8ff;font-family:ui-monospace,Menlo,Consolas,monospace;"
           "margin:0;padding:18px}a{color:#4fd8e8}h1{color:#e8b34b}table{border-collapse:collapse;"
           "width:100%%;font-size:13px}td,th{border-bottom:1px solid #1d3a5f;padding:6px 8px;text-align:left}"
           "th{color:#e8b34b}.fam{margin:6px 0}"
           ".sitekicker{font-size:11px;letter-spacing:.28em;color:#7fa8c9}"
           ".recbadge{display:inline-block;border:2px solid #e8b34b;background:#3a2a12;color:#e8b34b;"
           "border-radius:10px;padding:2px 10px;font-size:11px;font-weight:bold;letter-spacing:.06em}</style>")
    head = ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>")
    # index page
    idx_h = head + "<title>Chip design index — The Signature Computer Chip Maker and Archive</title></head><body>" + css
    idx_h += "<p class='sitekicker'><b>SITE 20 OF 25</b> &middot; THE JAH NETWORK</p>"
    idx_h += "<h1>Chip design index</h1><p>%s original Signature chip designs, by family. " % format(n, ",d")
    idx_h += "Every design below carries record status <span class='recbadge'>SIGNATURE ORIGINAL</span>. "
    idx_h += "<a href='%s'>Back to the live archive</a></p>" % base
    for k in FAMS:
        cnt = sum(1 for r in rows if r["fam"] == k)
        idx_h += "<div class='fam'><a href='chips-fam-%s.html'>%s</a> — %s designs</div>" % (k, FAMLABELS[k], format(cnt, ",d"))
    idx_h += "</body></html>"
    open(os.path.join(ROOT, "chips.html"), "w").write(idx_h)
    # per-family tables
    for k in FAMS:
        fam_rows = [r for r in rows if r["fam"] == k]
        trs = []
        for r in fam_rows:
            summary = "%s era %s" % (r["era"], FAMLABELS[k].replace("Signature ", ""))
            trs.append("<tr><td><a href='%s?chip=%s'>%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><span class='recbadge'>SIGNATURE ORIGINAL</span></td></tr>"
                       % (base, r["id"], r["id"], html.escape(r["name"]),
                          html.escape(FAMLABELS[k]), r["era"], html.escape(summary)))
        page = (head + "<title>%s designs — The Signature Computer Chip Maker and Archive</title></head><body>" % FAMLABELS[k] + css
                + "<p class='sitekicker'><b>SITE 20 OF 25</b> &middot; THE JAH NETWORK</p>"
                + "<h1>%s</h1><p>%s designs. <a href='chips.html'>All families</a> · <a href='%s'>Live archive</a></p>"
                % (FAMLABELS[k], format(len(fam_rows), ",d"), base)
                + "<table><tr><th>ID</th><th>Name</th><th>Type</th><th>Era</th><th>Summary</th><th>Record status</th></tr>"
                + "".join(trs) + "</table></body></html>")
        open(os.path.join(ROOT, "chips-fam-%s.html" % k), "w").write(page)
    # re-stamp the static count line in index.html so bots see a fresh number
    ip = os.path.join(ROOT, "index.html")
    h = open(ip).read()
    import re
    new_line = "%s original Signature chip designs archived as of %s — the live counter above keeps growing." % (format(n, ",d"), date.today().isoformat())
    h2 = re.sub(r">[0-9,]+ original Signature chip designs archived as of [0-9-]+ — the live counter above keeps growing\.<",
                ">" + new_line + "<", h)
    if h2 != h:
        open(ip, "w").write(h2)
    return len(fam_rows) if rows else 0

def build_api(n):
    api = {"site": "The Signature Computer Chip Maker and Archive",
           "site_url": "https://justinahiggins614-cmyk.github.io/signature-chip-maker/",
           "designs_seeded": n, "goal": GOAL,
           "id_scheme": "JAH-CHIP-######", "part_scheme": "SIG-CHIP-#### (Signature-original)",
           "deep_link": "?chip=JAH-CHIP-000001",
           "search_index": "data/index/chips.search.json.gz",
           "catalog_feed": "data/chips-catalog.json",
           "static_catalog": "chips.html (per-family: chips-fam-<KEY>.html)",
           "sitemap_index": "sitemap.xml -> sitemap-core.xml + sitemap-chips-bNNN.xml",
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
    urls = build_sitemap()
    build_api(total)
    build_catalog(total)
    build_static_catalog(total)
    st["next_index"] = start + n
    save_state(st)
    print("seeded +%d designs, total %d, sitemap %d urls" % (n, total, urls))

if __name__ == "__main__":
    main()
