#!/usr/bin/env python3
"""Build browse.html: the unified A-Z archive page for the Chip Maker.

By family (16 collapsible sections) + by design-name letter (26 collapsible
sections), a live search box, and lazy-loaded index data (chips.search.json.gz
is only fetched when a section opens — never the whole catalog at once).

STAMP RULE: called from gen.py main() AFTER rebuild_index(), using the fresh
row count as the single source of truth — the stamped count can never be
one-run-behind. Standalone re-runs (python3 code/build_browse.py) re-stamp
from the current search index.
"""
import gzip
import json
import os
import re
from collections import Counter
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "data", "index", "chips.search.json.gz")

FAMLABELS = {"CPU": "Signature CPU", "GPU": "Signature GPU",
             "NPU": "Signature NPU AI Accelerator", "SOC": "Signature SoC",
             "MCU": "Signature Microcontroller", "FPGA": "Signature FPGA",
             "MEMC": "Signature Memory Controller", "SENSOR": "Signature Sensor Chip",
             "PMIC": "Signature Power Management IC", "QCTRL": "Signature Quantum Control Chip",
             "PHOT": "Signature Photonic Chip", "NEURO": "Signature Neuromorphic Chip",
             "DSP": "Signature DSP", "MODEM": "Signature Baseband Modem",
             "SEC": "Signature Security Enclave", "CHIPLET": "Signature Chiplet"}
FAMS = list(FAMLABELS.keys())

STATUS_TOKENS = ("design_status=CONCEPT \u00b7 sim_status=NOT_SIMULATED \u00b7 "
                 "test_status=NOT_TESTED \u00b7 mfg_status=NOT_MANUFACTURED")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<script>try{var _jt=localStorage.getItem('jah-theme');if(_jt==='dark'){document.documentElement.setAttribute('data-theme','dark');}}catch(_je){}</script>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Browse the Full Chip Archive A–Z — The Signature Computer Chip Maker and Archive</title>
<meta name="description" content="Browse every original Signature chip design A–Z: %%COUNT%% designs across 16 families, each with full specs, status tokens and a deep-linked record page.">
<link rel="canonical" href="https://justinahiggins614-cmyk.github.io/signature-chip-maker/browse.html">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"The Signature Computer Chip Maker and Archive — A–Z Browse","url":"https://justinahiggins614-cmyk.github.io/signature-chip-maker/browse.html"}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"ItemList","name":"Signature Chip Design Archive","numberOfItems":%%COUNTRAW%%,"itemListOrder":"http://schema.org/ItemListOrderAscending"}</script>
<style>
:root{--navy:#0a1628;--navy2:#0d2036;--panel:#12294a;--copper:#d08a3e;--gold:#e8b34b;--cyan:#4fd8e8;--ink:#cfe8ff;--dim:#7fa8c9}
*{box-sizing:border-box}
body{background:var(--navy);color:var(--ink);font-family:ui-monospace,Menlo,Consolas,monospace;margin:0;line-height:1.5}
a{color:var(--cyan)}
header.brand{background:linear-gradient(180deg,#0d2036,#0a1628);border-bottom:3px solid var(--copper);padding:18px 14px;text-align:center}
header.brand h1{margin:0;color:var(--gold);font-size:clamp(20px,4.5vw,34px);letter-spacing:1px}
header.brand p{margin:6px 0;color:var(--dim)}
.countchip{display:inline-block;background:var(--panel);border:2px solid var(--copper);border-radius:20px;padding:6px 18px;margin-top:8px;color:var(--gold);font-weight:bold}
.staticcount{color:var(--dim);font-size:13px;text-align:center;margin:8px}
#finderbar{background:var(--panel);border:2px solid var(--cyan);border-radius:12px;margin:14px auto;max-width:860px;padding:12px}
#finderbar .frow{display:flex;gap:8px}
#finderbar input{flex:1;background:#0a1628;border:1px solid var(--cyan);color:var(--ink);border-radius:8px;padding:10px;font-size:15px;font-family:inherit;min-width:0}
#finderbar button{background:var(--cyan);color:#0a1628;border:0;border-radius:8px;padding:10px 16px;font-weight:bold;cursor:pointer;font-family:inherit}
#finderres{margin-top:10px}
main{max-width:1080px;margin:0 auto;padding:10px 12px 60px}
.fcard{background:#0a1628;border:1px solid var(--copper);border-radius:8px;padding:8px 10px;margin:6px 0}
.fcard b{color:var(--gold)}
.fcard a.takeme{float:right;color:var(--cyan);font-weight:bold}
.fcard .meta{color:var(--dim);font-size:12px}
.fcard .stat{color:var(--dim);font-size:11.5px;margin-top:3px}
details.bsec{background:var(--navy2);border:1px solid #2a4a73;border-radius:10px;margin:10px 0;overflow:hidden}
details.bsec>summary{cursor:pointer;padding:12px 14px;font-weight:bold;color:var(--gold);font-size:15px;list-style:none}
details.bsec>summary::-webkit-details-marker{display:none}
details.bsec>summary:before{content:"\25B6 ";color:var(--copper);font-size:12px}
details.bsec[open]>summary:before{content:"\25BC "}
details.bsec>summary:hover{background:#122a4e}
details.bsec>summary .cnt{color:var(--dim);font-weight:normal;font-size:12.5px;margin-left:8px}
details.bsec .body{padding:4px 12px 12px;border-top:1px solid #1d3a5f}
.azrow{text-align:center;margin:10px 4px}
.azrow a{color:var(--cyan);margin:2px 3px;text-decoration:none;background:none;border:1px solid #1d3a5f;border-radius:6px;padding:3px 8px;cursor:pointer;font-family:inherit;font-size:13px;display:inline-block}
.azrow a:hover{border-color:var(--copper)}
.loadline{color:var(--dim);padding:14px;text-align:center}
h2.sec{color:var(--gold);border-bottom:2px solid var(--copper);padding-bottom:6px;margin:26px 0 8px;font-size:clamp(17px,3.5vw,22px)}
.jtabbar{display:flex;gap:8px;overflow-x:auto;padding:10px 12px;-webkit-overflow-scrolling:touch;scrollbar-width:thin;border-bottom:1px solid rgba(128,128,128,.25)}
.jtabbar a.jtab{flex:0 0 auto;text-decoration:none;border:1px solid rgba(160,160,160,.45);border-radius:999px;padding:9px 16px;font-size:.92em;color:inherit;background:rgba(127,127,127,.08);white-space:nowrap;font-family:inherit}
.jtabbar a.jtab.on{background:#f5c518;border-color:#f5c518;color:#191919;font-weight:700}
footer{border-top:2px solid var(--copper);padding:16px;text-align:center;color:var(--dim);font-size:12.5px}
</style>
</head>
<body>
<header class="brand">
<h1>The Signature Computer Chip Maker and Archive</h1>
<p>The full design archive — every chip, A to Z</p>
<div class="countchip">&#9881; <span id="browsecount">%%COUNT%%</span> original Signature chip designs</div>
</header>
<nav class="jtabbar" aria-label="Site sections">
<a class="jtab" href="index.html">🏠 Front Door</a>
<a class="jtab" href="chips.html">📚 1 Million Archive</a>
<a class="jtab on" href="browse.html">Browse</a><a class="jtab" href="methodology.html">Methodology</a>
</nav>
<main>
<p class="staticcount">%%COUNT%% original Signature chip designs archived as of %%TODAY%% — IDs JAH-CHIP-000001&hellip;JAH-CHIP-%%LASTID%%, 16 families. Full records render deterministically in-browser from design seeds. Statuses: design CONCEPT (design only), simulation NOT_SIMULATED, test NOT_TESTED, manufacturing NOT_MANUFACTURED. <a href="index.html" style="color:var(--cyan)">&#8592; Back to the live archive</a></p>
<div id="finderbar" role="search">
<div class="frow"><input id="q" type="search" placeholder="Search %%COUNT%% chip designs — name or JAH-CHIP-###### &hellip;" aria-label="Search chip designs"><button id="qgo" type="button">Search</button></div>
<div id="finderres" aria-live="polite"></div>
</div>
<h2 class="sec">Browse by chip family</h2>
<div class="azrow" aria-label="Family quick links">%%FAMQUICK%%</div>
%%FAMSECTIONS%%
<h2 class="sec">Browse by design name, A&ndash;Z</h2>
<p style="color:var(--dim);font-size:13px">Letters index the design name after &ldquo;Signature &rdquo; (e.g. VoltCore under <b>V</b>). Each letter loads only when opened.</p>
<div class="azrow" aria-label="A to Z quick links">%%AZQUICK%%</div>
%%AZSECTIONS%%
</main>
<footer>
THE JAH NETWORK &middot; The Signature Computer Chip Maker and Archive &middot; all designs are original Signature-line works — no real manufacturer branding or part numbers.<br>
<a href="index.html">Live archive</a> &middot; <a href="chips.html">Static design index</a> &middot; <a href="methodology.html">Data &amp; methodology</a> &middot; <a href="sitemap.xml">sitemap.xml</a>
</footer>
<script>
"use strict";
var FAMLABELS = %%FAMLABELS_JSON%%;
var STATUS_TOKENS = "%%STATUS_TOKENS%%";
var IDXURL = "data/index/chips.search.json.gz";
var rows = null, rowsPromise = null;
function esc(t){return String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function fmt(n){return String(n).replace(/\B(?=(\d{3})+(?!\d))/g,",");}
function letterOf(name){var n=String(name).replace(/^Signature\s+/i,"");var c=n.charAt(0).toUpperCase();return (c>="A"&&c<="Z")?c:"#";}
function loadRows(){
  if(rowsPromise) return rowsPromise;
  rowsPromise = fetch(IDXURL).then(function(r){
    if(!r.ok) throw new Error("index fetch "+r.status);
    return r.arrayBuffer();
  }).then(function(buf){
    var ds = new DecompressionStream("gzip");
    var stream = new Blob([buf]).stream().pipeThrough(ds);
    return new Response(stream).text();
  }).then(function(txt){
    rows = [];
    var lines = txt.split("\n");
    for(var i=0;i<lines.length;i++){var l=lines[i].trim();if(l) rows.push(JSON.parse(l));}
    var chip = document.getElementById("browsecount");
    if(chip) chip.textContent = fmt(rows.length);
    return rows;
  }).catch(function(e){
    rowsPromise = null;
    throw e;
  });
  return rowsPromise;
}
function card(r){
  var id=r[0], name=r[1], fam=r[2], era=r[3];
  var lab = FAMLABELS[fam] || fam;
  return '<div class="fcard"><a class="takeme" href="index.html?chip='+id+'">Open full record &#8594;</a>'+
    '<b>'+esc(name)+'</b><br><span class="meta">'+id+' &middot; '+esc(lab)+' &middot; '+esc(era)+'</span>'+
    '<div class="stat">'+esc(STATUS_TOKENS)+'</div></div>';
}
function renderInto(body, list, cap){
  cap = cap || 0;
  var shown = cap && list.length > cap ? list.slice(0,cap) : list;
  body.innerHTML = shown.map(card).join("") +
    (cap && list.length > cap ? '<p class="loadline">Showing '+fmt(shown.length)+' of '+fmt(list.length)+' — refine with search.</p>' : "") +
    (list.length === 0 ? '<p class="loadline">No designs here yet.</p>' : "");
}
function wireSection(det, kind, key){
  var body = det.querySelector(".body");
  var done = false;
  det.addEventListener("toggle", function(){
    if(!det.open || done) return;
    done = true;
    body.innerHTML = '<p class="loadline">Loading designs&hellip;</p>';
    loadRows().then(function(rs){
      var list;
      if(kind === "fam") list = rs.filter(function(r){return r[2]===key;});
      else list = rs.filter(function(r){return letterOf(r[1])===key;});
      renderInto(body, list, 0);
    }).catch(function(){
      done = false;
      body.innerHTML = '<p class="loadline">Could not load the index. Check your connection and reopen.</p>';
    });
  });
}
function init(){
  var dets = document.querySelectorAll("details.bsec");
  for(var i=0;i<dets.length;i++){
    wireSection(dets[i], dets[i].getAttribute("data-kind"), dets[i].getAttribute("data-key"));
  }
  var q = document.getElementById("q"), res = document.getElementById("finderres");
  var t = null;
  function doSearch(){
    var s = q.value.trim().toLowerCase();
    if(s.length < 2){ res.innerHTML = ""; return; }
    res.innerHTML = '<p class="loadline">Searching&hellip;</p>';
    loadRows().then(function(rs){
      var hits = [];
      for(var i=0;i<rs.length && hits.length<300;i++){
        var r = rs[i];
        if(r[1].toLowerCase().indexOf(s) > -1 || r[0].toLowerCase().indexOf(s) > -1) hits.push(r);
      }
      res.innerHTML = '<div style="color:var(--cyan);margin:6px 0">&#9889; '+fmt(hits.length)+
        (hits.length===300?' (first 300)':'')+' match'+(hits.length===1?"":"es")+' for &ldquo;'+esc(q.value.trim())+'&rdquo;:</div>'+
        hits.map(card).join("");
    }).catch(function(){
      res.innerHTML = '<p class="loadline">Search needs the archive index — check your connection.</p>';
    });
  }
  q.addEventListener("input", function(){ clearTimeout(t); t = setTimeout(doSearch, 300); });
  document.getElementById("qgo").addEventListener("click", doSearch);
}
if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
</script>
</body>
</html>
"""


def load_rows():
    rows = []
    with gzip.open(IDX, "rt") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_browse(total=None):
    rows = load_rows()
    n = len(rows) if total is None else total
    nfmt = format(n, ",d")
    today = date.today().isoformat()
    last_id = "JAH-CHIP-%06d" % n
    fam_counts = Counter(r[2] for r in rows)

    fam_quick = " ".join(
        '<a href="#fam-%s">%s</a>' % (k, FAMLABELS[k]) for k in FAMS)
    az_quick = " ".join(
        '<a href="#az-%s">%s</a>' % (c, c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    fam_sections = []
    for k in FAMS:
        c = fam_counts.get(k, 0)
        fam_sections.append(
            '<details class="bsec" id="fam-%s" data-kind="fam" data-key="%s">'
            '<summary>%s<span class="cnt">%s designs</span></summary>'
            '<div class="body"><p class="loadline">Open to load this family\u2019s designs.</p></div>'
            '</details>' % (k, k, FAMLABELS[k], format(c, ",d")))
    fam_sections = "\n".join(fam_sections)

    # Per-letter design counts for the A-Z summaries: same bucketing as the
    # client-side letterOf() (strip a leading "Signature " from the name).
    az_counts = Counter()
    for r in rows:
        nm = re.sub(r"^Signature\s+", "", str(r[1]), flags=re.I)
        ch = nm[0].upper() if nm else "#"
        az_counts[ch if "A" <= ch <= "Z" else "#"] += 1

    az_sections = []
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        az_sections.append(
            '<details class="bsec" id="az-%s" data-kind="az" data-key="%s">'
            '<summary>Letter %s<span class="cnt">%s designs</span></summary>'
            '<div class="body"><p class="loadline">Open to load designs under %s.</p></div>'
            '</details>' % (c, c, c, format(az_counts.get(c, 0), ",d"), c))
    az_sections = "\n".join(az_sections)

    html = (TEMPLATE
            .replace("%%COUNT%%", nfmt)
            .replace("%%COUNTRAW%%", str(n))
            .replace("%%TODAY%%", today)
            .replace("%%LASTID%%", last_id)
            .replace("%%FAMQUICK%%", fam_quick)
            .replace("%%AZQUICK%%", az_quick)
            .replace("%%FAMSECTIONS%%", fam_sections)
            .replace("%%AZSECTIONS%%", az_sections)
            .replace("%%FAMLABELS_JSON%%", json.dumps(FAMLABELS))
            .replace("%%STATUS_TOKENS%%", STATUS_TOKENS))
    out = os.path.join(ROOT, "browse.html")
    open(out, "w").write(html)
    return out


if __name__ == "__main__":
    print("browse.html built:", build_browse())
