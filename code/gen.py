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
    core_urls = [base, base + "?browse=all", base + "chips.html", base + "methodology.html"]
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
    idx_h += "<p class='sitekicker'><b>SITE 18 OF 27</b> &middot; THE JAH NETWORK</p>"
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
                + "<p class='sitekicker'><b>SITE 18 OF 27</b> &middot; THE JAH NETWORK</p>"
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


def build_manifest(n, base="https://justinahiggins614-cmyk.github.io/signature-chip-maker/"):
    """Authoritative chip-archive manifest: ONE source every counter reads.
    chip-archive-manifest.json at repo root."""
    import hashlib
    from datetime import datetime, timezone
    rows = all_rows()
    fam_counts = {k: 0 for k in FAMS}
    for r in rows:
        fam_counts[r["fam"]] = fam_counts.get(r["fam"], 0) + 1
    idx_path = os.path.join(IDX, "chips.search.json.gz")
    idx_hash = ""
    if os.path.exists(idx_path):
        h = hashlib.sha256()
        with open(idx_path, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        idx_hash = h.hexdigest()
    chunk_files = sorted(f for f in os.listdir(CHUNKS) if f.endswith(".json.gz"))
    ids = [r["id"] for r in rows]
    man = {
        "manifest_id": "JAH-CHIP-MANIFEST",
        "site": "The Signature Computer Chip Maker and Archive",
        "site_url": base,
        "site_number": 20,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_designs": n,
        "generated_designs": n,
        "archived_designs": n,
        "goal": GOAL,
        "remaining_to_goal": GOAL - n,
        "progress": "%d / %d DESIGNS" % (n, GOAL),
        "families": [{"key": k, "label": FAMLABELS[k], "count": fam_counts[k]} for k in FAMS],
        "family_count": len(FAMS),
        "id_scheme": "JAH-CHIP-######",
        "earliest_id": min(ids) if ids else None,
        "latest_id": max(ids) if ids else None,
        "archive_version": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generator_version": "chipgen-1.0",
        "engine_version": "1.0",
        "schema_version": "JAH-CHIP-RECORD/1.0",
        "index_version": "chip-index-1.0",
        "index_hash_sha256": idx_hash,
        "hashes_index": "data/index/chips.hashes.json.gz",
        "chunks": {"pattern": "data/chunks/cNNNNN.json.gz", "per_chunk": CHUNK_N,
                   "count": len(chunk_files)},
        "deep_link": "?chip=JAH-CHIP-000001",
        "record_status": "SIGNATURE ORIGINAL",
        "creation_mode": "SIGNATURE-GENERATED",
        "value_kind": "GENERATED_TARGET",
        "value_kind_note": "Every numeric specification is a deterministically generated design target from the design seed. None are measured, simulated, manufactured, or tested values.",
        "completeness_status_vocabulary": ["CONCEPT", "PLANNED", "SPECIFIED", "LOGIC-DESIGNED",
            "SCHEMATIC", "SIMULATED", "LAYOUT-DESIGNED", "PROTOTYPE", "MANUFACTURED", "TESTED"],
        "design_status": {
            "current": "CONCEPT",
            "definition": "'Fully planned, drawn and specified' means: the architecture is planned (spec table), the board is drawn (generated block-diagram image), and every field of the Chip Record Standard is specified. It does NOT mean fabricated, simulated, or tested.",
            "sim_status": "NOT_SIMULATED",
            "test_status": "NOT_TESTED",
            "mfg_status": "NOT_MANUFACTURED",
        },
        "creation_modes": ["SIGNATURE-GENERATED", "USER-CREATED", "SOURCE-DERIVED", "IMPORTED", "REMIXED"],
        "catalog_feed": "data/chips-catalog.json",
        "search_index": "data/index/chips.search.json.gz",
        "static_catalog": "chips.html (per-family: chips-fam-<KEY>.html)",
        "sitemap_index": "sitemap.xml -> sitemap-core.xml + sitemap-chips-bNNN.xml",
        "note": "All designs are original Signature-line works. No real manufacturer branding, part numbers, or datasheet text.",
    }
    out = os.path.join(ROOT, "chip-archive-manifest.json")
    json.dump(man, open(out, "w"), indent=1)
    return out

def build_api(n):
    man = {}
    mp = os.path.join(ROOT, "chip-archive-manifest.json")
    if os.path.exists(mp):
        man = json.load(open(mp))
    api = {"site": "The Signature Computer Chip Maker and Archive",
           "site_url": "https://justinahiggins614-cmyk.github.io/signature-chip-maker/",
           "site_number": 20,
           "manifest": "chip-archive-manifest.json",
           "designs_seeded": n, "total_designs": man.get("total_designs", n),
           "goal": GOAL, "remaining_to_goal": man.get("remaining_to_goal"),
           "latest_id": man.get("latest_id"), "earliest_id": man.get("earliest_id"),
           "families": man.get("families"), "family_count": man.get("family_count"),
           "archive_version": man.get("archive_version"),
           "generator_version": man.get("generator_version"),
           "engine_version": man.get("engine_version"),
           "schema_version": man.get("schema_version"),
           "index_version": man.get("index_version"),
           "index_hash_sha256": man.get("index_hash_sha256"),
           "updated": man.get("updated"),
           "id_scheme": "JAH-CHIP-######", "part_scheme": "SIG-CHIP-#### (Signature-original)",
           "deep_link": "?chip=JAH-CHIP-000001",
           "search_index": "data/index/chips.search.json.gz",
           "catalog_feed": "data/chips-catalog.json",
           "static_catalog": "chips.html (per-family: chips-fam-<KEY>.html)",
           "sitemap_index": "sitemap.xml -> sitemap-core.xml + sitemap-chips-bNNN.xml",
           "chunks": "data/chunks/cNNNNN.json.gz (%d/chunk)" % CHUNK_N,
           "health": {"status": "OK", "last_build": man.get("updated"),
                      "index_records": n, "index_hash_sha256": man.get("index_hash_sha256")},
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
    build_manifest(total)
    build_api(total)
    build_catalog(total)
    build_static_catalog(total)
    st["next_index"] = start + n
    save_state(st)
    print("seeded +%d designs, total %d, sitemap %d urls" % (n, total, urls))

if __name__ == "__main__":
    main()
