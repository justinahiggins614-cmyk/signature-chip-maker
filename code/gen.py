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
    core_urls = [base, base + "?browse=all", base + "browse.html", base + "chips.html", base + "methodology.html"]
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

# --- TAB-WAVE (2026-10-04): tab bar + Ask-the-AI, baked into every regenerated chips.html ---
TABBAR_CHIP = r"""<!-- JAH TAB BAR — Manon's 2026-10-04 order (calculator screenshot as spec).
     Paste right after </header> (or after the hero/title block) on index.html AND on the archive page.
     On index.html: "Front Door" carries class "on". On the archive page: "1 Million Archive" carries "on".
     Replace <a class="jtab" href="browse.html">Browse</a><a class="jtab" href="methodology.html">Methodology</a> with <a class="jtab" href="...">Label</a> items (may be empty). -->
<style>
.jtabbar{display:flex;gap:8px;overflow-x:auto;padding:10px 12px;-webkit-overflow-scrolling:touch;scrollbar-width:thin;border-bottom:1px solid rgba(128,128,128,.25)}
.jtabbar a.jtab{flex:0 0 auto;text-decoration:none;border:1px solid rgba(160,160,160,.45);border-radius:999px;padding:9px 16px;font-size:.92em;color:inherit;background:rgba(127,127,127,.08);white-space:nowrap;font-family:inherit}
.jtabbar a.jtab.on{background:#f5c518;border-color:#f5c518;color:#191919;font-weight:700}
</style>
<nav class="jtabbar" aria-label="Site sections">
<a class="jtab" href="index.html">🏠 Front Door</a>
<a class="jtab on" href="chips.html">📚 1 Million Archive</a>
<a class="jtab" href="browse.html">Browse</a><a class="jtab" href="methodology.html">Methodology</a>
</nav>
"""
ASKAI_CHIP = r"""<!-- ASK THE AI — Manon's 2026-10-04 order. Paste on the archive page, directly under the
     search/filter area (or at the top of the archive section if there is no search box).
     It FINDS records by scanning the page's own archive list, and ANSWERS with his real
     Signature Llama (same loader as the phone book). Never fake: if the Llama can't load,
     the found records are still shown honestly. Replace The Signature Computer Chip Maker and Archive and the chip-design archive. -->
<div class="jah-askai" id="jah-askai">
<style>
.jah-askai{border:1px solid rgba(160,160,160,.4);border-radius:12px;padding:14px;margin:14px 0;background:rgba(127,127,127,.06)}
.jah-askai h2{margin:0 0 4px;font-size:1.15em}
.jah-askai .jah-askai-sub{margin:0 0 10px;font-size:.9em;opacity:.85}
.jah-askai .jah-askai-row{display:flex;gap:8px}
.jah-askai input#jah-askai-q{flex:1;min-width:0;padding:10px 12px;border-radius:8px;border:1px solid rgba(160,160,160,.5);font-size:1em;background:#fff;color:#111}
.jah-askai button#jah-askai-go{padding:10px 18px;border-radius:8px;border:1px solid #f5c518;background:#f5c518;color:#191919;font-weight:700;font-size:1em;cursor:pointer}
.jah-askai #jah-askai-out{margin-top:10px;font-size:.95em}
.jah-askai #jah-askai-out ul{margin:6px 0;padding-left:20px}
.jah-askai .jah-askai-ans{border-left:3px solid #f5c518;padding-left:10px;margin-top:8px}
.jah-askai .jah-askai-thinking{opacity:.7;font-style:italic}
</style>
<h2>🤖 Ask the AI</h2>
<p class="jah-askai-sub">Ask about anything in this archive — the AI searches the records and answers.</p>
<div class="jah-askai-row">
<input id="jah-askai-q" type="text" autocomplete="off" placeholder="Ask about this archive…" aria-label="Ask about this archive">
<button id="jah-askai-go" type="button">Ask</button>
</div>
<div id="jah-askai-out" aria-live="polite"></div>
<script>
(function(){
var SITE="The Signature Computer Chip Maker and Archive", DESC="the chip-design archive";
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
/* Real Signature Llama loader — same pattern as the phone book. */
var LLAMA_BASE="https://justinahiggins614-cmyk.github.io/signature-backend/sigllama/";
var LLAMA_VOCAB="vocab2.json", LLAMA_BIN="sigllama-v2.bin";
var net={loading:null,ready:false};
function llamaEnsure(){
  if(net.ready) return Promise.resolve(true);
  if(net.loading) return net.loading;
  net.loading=new Promise(function(resolve){
    function fin(ok){net.ready=!!ok;resolve(net.ready);}
    function boot(){try{
      if(typeof SigLlama==="undefined"){fin(false);return;}
      SigLlama.load(LLAMA_BASE,LLAMA_VOCAB,LLAMA_BIN).then(function(){fin(true);},function(){fin(false);});
    }catch(e){fin(false);}}
    if(typeof SigLlama!=="undefined"){boot();return;}
    var s=document.createElement("script");s.src=LLAMA_BASE+"sigllama.js";s.async=true;
    s.onload=boot;s.onerror=function(){fin(false);};document.head.appendChild(s);
  });
  return net.loading;
}
/* FIND: keyword scan over the page's own archive list links. */
function findRecords(q){
  var words=String(q).toLowerCase().split(/[^a-z0-9]+/).filter(function(w){return w.length>2;});
  if(!words.length) return [];
  var scope=document.getElementById("jah-askai-scope")||document.querySelector("main")||document.body;
  var links=scope.getElementsByTagName("a"),out=[],seen={};
  for(var i=0;i<links.length;i++){
    var a=links[i];
    if(a.closest("nav")||a.closest("header")||a.closest("footer")||a.closest(".jah-askai")) continue;
    var t=(a.textContent||"").replace(/\s+/g," ").trim();
    if(t.length<3||t.length>160) continue;
    var tl=t.toLowerCase(),score=0;
    for(var j=0;j<words.length;j++) if(tl.indexOf(words[j])>=0) score++;
    if(score>0&&!seen[a.href]){seen[a.href]=1;out.push({t:t,h:a.href,s:score});}
    if(out.length>=60) break;
  }
  out.sort(function(x,y){return y.s-x.s;});
  return out.slice(0,5);
}
function ask(){
  var q=document.getElementById("jah-askai-q").value.trim();
  var out=document.getElementById("jah-askai-out");
  if(!q){out.innerHTML="<p>Please type a question first.</p>";return;}
  var found=findRecords(q),html="";
  if(found.length){
    html+="<p><b>📎 I found "+found.length+" record"+(found.length>1?"s":"")+" matching your words:</b></p><ul>"+
      found.map(function(f){return '<li><a href="'+esc(f.h)+'">'+esc(f.t)+"</a></li>";}).join("")+"</ul>";
  }else{
    html+="<p>No record titles matched those words — asking the AI anyway.</p>";
  }
  html+='<p class="jah-askai-thinking">🤖 thinking…</p>';
  out.innerHTML=html;
  var think=out.querySelector(".jah-askai-thinking");
  llamaEnsure().then(function(ok){
    if(!ok||typeof SigLlama==="undefined"||!SigLlama.loaded||!SigLlama.loaded()){
      think.textContent="The AI voice could not load right now — the records above are what matched your words.";return;}
    var ctx="You are the "+SITE+" archive helper. "+DESC+".\n"+
      (found.length?("Records matching the question: "+found.map(function(f){return f.t;}).join(" | ")+"\n"):"")+
      "User: "+q.slice(0,300)+"\nHelper (one to three sentences, plain words):";
    var done=false;
    function show(t){
      if(done) return; done=true;
      t=String(t||"").trim().replace(/^Helper\s*:\s*/i,"");
      if(t.length<8||/User\s*:/.test(t)) t="I searched the archive for you — the matching records are listed above.";
      think.outerHTML='<p class="jah-askai-ans">🤖 '+esc(t)+"</p>";
    }
    try{
      SigLlama.generate(ctx,{maxTokens:90,temperature:0.5,topK:40}).then(show,function(){show("");});
      setTimeout(function(){show("");},25000);
    }catch(e){show("");}
  });
}
document.getElementById("jah-askai-go").addEventListener("click",ask);
document.getElementById("jah-askai-q").addEventListener("keydown",function(e){if(e.key==="Enter")ask();});
})();
</script>
</div>
"""
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
    idx_h += TABBAR_CHIP
    for k in FAMS:
        cnt = sum(1 for r in rows if r["fam"] == k)
        idx_h += "<div class='fam'><a href='chips-fam-%s.html'>%s</a> — %s designs</div>" % (k, FAMLABELS[k], format(cnt, ",d"))
    idx_h += ASKAI_CHIP
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
                + TABBAR_CHIP
                + "<table><tr><th>ID</th><th>Name</th><th>Type</th><th>Era</th><th>Summary</th><th>Record status</th></tr>"
                + "".join(trs) + "</table></body></html>")
        open(os.path.join(ROOT, "chips-fam-%s.html" % k), "w").write(page)
    # re-stamp counts in index.html so bots + first paint see the true number.
    # The manifest is the source of truth; keep the stamped static sentence and the
    # livecount chip's initial content in sync every drip run.
    ip = os.path.join(ROOT, "index.html")
    h = open(ip).read()
    import re
    today = date.today().isoformat()
    new_line = ("%s original Signature chip designs archived as of %s — IDs JAH-CHIP-000001…JAH-CHIP-%s, "
                "16 families. Full records render deterministically in-browser from design seeds. "
                "Statuses: design CONCEPT (design only), simulation NOT_SIMULATED, test NOT_TESTED, "
                "manufacturing NOT_MANUFACTURED. Machine-readable: chip-archive-manifest.json · api.json · "
                "schema/ · llms.txt · ai-manifest.json. "
                "<a href=\"methodology.html\" style=\"color:var(--cyan)\">Data &amp; methodology</a>"
                % (format(n, ",d"), today, str(n).zfill(6)))
    h2 = re.sub(r">[0-9,]+ original Signature chip designs archived.*?</p>",
                ">" + new_line + "</p>", h, flags=re.S)
    h3 = re.sub(r'(<span id="livecount">)[^<]*(</span>)',
                lambda m: m.group(1) + format(n, ",d") + m.group(2), h2)
    if h3 != h:
        open(ip, "w").write(h3)
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
           "static_catalog": "chips.html (per-family: chips-fam-<KEY>.html), browse.html (unified A-Z archive)",
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
    # Unified A-Z browse page — AFTER the index rebuild, stamped with the same
    # fresh total, so the count is never one drip behind.
    import build_browse
    build_browse.build_browse(total)
    st["next_index"] = start + n
    save_state(st)
    print("seeded +%d designs, total %d, sitemap %d urls" % (n, total, urls))

if __name__ == "__main__":
    main()
