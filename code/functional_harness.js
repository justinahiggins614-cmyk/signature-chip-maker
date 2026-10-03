/* Functional exercise harness for signature-chip-maker (site 18 wave).
   Drives REAL shipped engine.js + REAL data. Run: node code_harness.js */
"use strict";
const fs = require("fs"), path = require("path"), zlib = require("zlib"), crypto = require("crypto");
const ROOT = "/home/hatch/workspace/signature-chip-maker";
const E = require(path.join(ROOT, "engine.js")).ChipEngine;
let pass = 0, fail = 0;
function t(name, ok, extra) {
  if (ok) { pass++; console.log("PASS " + name); }
  else { fail++; console.log("FAIL " + name + (extra ? " :: " + extra : "")); }
}
// sorted-keys canonicalization — mirrors code/build_hashes.js exactly
function canonJSON(c){function sk(v){if(Array.isArray(v))return v.map(sk);if(v&&typeof v==="object"){const o={};Object.keys(v).sort().forEach(k=>{o[k]=sk(v[k]);});return o;}return v;}return JSON.stringify(sk(c));}
const sha256 = s => crypto.createHash("sha256").update(s, "utf8").digest("hex");

// ---- load all chunk rows (real data) ----
const chunkDir = path.join(ROOT, "data", "chunks");
const files = fs.readdirSync(chunkDir).filter(f => f.endsWith(".json.gz")).sort();
const rows = [];
for (const fn of files) {
  const lines = zlib.gunzipSync(fs.readFileSync(path.join(chunkDir, fn))).toString("utf8").trim().split("\n");
  for (const ln of lines) rows.push(JSON.parse(ln));
}
t("T1: 15,600 rows across 78 chunk files", rows.length === 15600, "got " + rows.length);
t("T1b: IDs contiguous JAH-CHIP-000001..015600", rows.every((r, i) => r.id === "JAH-CHIP-" + String(i + 1).padStart(6, "0")));

// ---- index parity ----
const idx = zlib.gunzipSync(fs.readFileSync(path.join(ROOT, "data/index/chips.search.json.gz"))).toString("utf8").trim().split("\n").map(l => JSON.parse(l));
t("T2: search index covers all 15,600 IDs", idx.length === 15600 && idx.every((r, i) => r[0] === "JAH-CHIP-" + String(i + 1).padStart(6, "0")));
t("T2b: index family matches chunk family for sample", idx.slice(0, 50).every((r, i) => r[2] === rows[i].fam));

// ---- loadRow chunk-mapping formula (from page) vs real files ----
function chunkFor(id) { const n = parseInt(id.split("-")[2], 10); return "c" + String(Math.floor((n - 1) / 200) + 1).padStart(5, "0") + ".json.gz"; }
const sampleIds = ["JAH-CHIP-000001", "JAH-CHIP-000200", "JAH-CHIP-000201", "JAH-CHIP-007800", "JAH-CHIP-015600"];
let loadOk = true;
for (const id of sampleIds) {
  const fn = chunkFor(id);
  const lines = zlib.gunzipSync(fs.readFileSync(path.join(chunkDir, fn))).toString("utf8").trim().split("\n");
  if (!lines.some(l => JSON.parse(l).id === id)) loadOk = false;
}
t("T3: loadRow chunk formula finds IDs (incl. boundaries 200/201/15600)", loadOk);

// ---- featured design (spotlight: first Modern-era row) ----
const feat = idx.find(r => r[3] === "Modern");
t("T4: spotlight featured design resolves to a real Modern row", !!feat && !!rows.find(r => r.id === feat[0]), JSON.stringify(feat && feat[0]));

// ---- determinism: canonicalRecord twice -> byte-identical ----
const r1 = rows[0], rMid = rows[7799], rLast = rows[rows.length - 1];
const cA = E.canonicalRecord(r1), cB = E.canonicalRecord(r1);
t("T5: deterministic regeneration — re-run is byte-identical", canonJSON(cA) === canonJSON(cB));
const cMid = E.canonicalRecord(rMid);
t("T5b: determinism holds for middle + last record", canonJSON(cMid) === canonJSON(E.canonicalRecord(rMid)));

// ---- test vectors vs engine (Verify Design backend) ----
const tv = JSON.parse(fs.readFileSync(path.join(ROOT, "code/test_vectors.json"), "utf8"));
let tvOk = true, tvMsg = "";
for (const v of tv.vectors) {
  const n = parseInt(v.id.split("-")[2], 10);
  const row = rows[n - 1];
  if (!row || row.seed !== v.seed) { tvOk = false; tvMsg = "seed mismatch " + v.id; break; }
  const hex = sha256(canonJSON(E.canonicalRecord(row)));
  if (hex !== v.expected_hash_sha256) { tvOk = false; tvMsg = "hash mismatch " + v.id; break; }
}
t("T6: test vectors — engine reproduces all " + tv.vectors.length + " published hashes", tvOk, tvMsg);

// ---- published hashes index parity (what Verify Design button compares against) ----
const hashes = zlib.gunzipSync(fs.readFileSync(path.join(ROOT, "data/index/chips.hashes.json.gz"))).toString("utf8").trim().split("\n").map(l => JSON.parse(l));
t("T7: hashes index has 15,600 entries", hashes.length === 15600, "got " + hashes.length);
let hOk = true;
for (const id of sampleIds) {
  const pub = hashes.find(h => h.id === id);
  const n = parseInt(id.split("-")[2], 10);
  if (!pub || pub.hash !== sha256(canonJSON(E.canonicalRecord(rows[n - 1])))) { hOk = false; break; }
}
t("T8: Verify-Design flow — recomputed hash matches published hash (sample incl. first/last)", hOk);

// ---- honesty statuses on every record view ----
function statusesOk(c) {
  return c.design_status === "CONCEPT" && c.sim_status === "NOT_SIMULATED" &&
    c.test_status === "NOT_TESTED" && c.mfg_status === "NOT_MANUFACTURED" &&
    c.completeness_status === "CONCEPT" && c.value_kind === "GENERATED_TARGET" &&
    Array.isArray(c.specs) && c.specs.length > 0 && c.specs.every(s => s.kind === "GENERATED_TARGET" && s.unit) &&
    typeof c.designStatus === "string" && /CONCEPTUAL DESIGN/i.test(c.designStatus);
}
t("T9: honesty statuses present on detail records (first/mid/last)", statusesOk(cA) && statusesOk(cMid) && statusesOk(E.canonicalRecord(rLast)));
// download text: extract chipText from the page and run it
const pageSrc = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
function extractFn(src, name) {
  const start = src.indexOf("function " + name + "(");
  if (start < 0) return null;
  let i = src.indexOf("{", start), depth = 0;
  for (; i < src.length; i++) { if (src[i] === "{") depth++; else if (src[i] === "}") { depth--; if (!depth) break; } }
  return src.slice(start, i + 1);
}
const chipTextSrc = extractFn(pageSrc, "chipText");
t("T10a: chipText download builder found in page", !!chipTextSrc);
let dlOk = false, dlMsg = "";
if (chipTextSrc) {
  try {
    const chipText = eval("(" + chipTextSrc.replace("function chipText(c)", "function(c)") + ")");
    const txt = chipText(cA);
    dlOk = /NOT_SIMULATED/.test(txt) && /NOT_TESTED/.test(txt) && /NOT_MANUFACTURED/.test(txt) &&
      /CONCEPT/.test(txt) && /GENERATED_TARGET|GENERATED design target/.test(txt) && txt.includes(cA.id);
  } catch (e) { dlMsg = e.message; }
}
t("T10b: .txt/.json downloads carry all four statuses + GENERATED_TARGET", dlOk, dlMsg);

// ---- board SVG ----
const svg = E.boardSVG(cA);
t("T11: boardSVG returns a complete labeled SVG", svg.startsWith("<svg") && svg.includes(cA.id) && svg.includes(cA.sigpart) && (svg.match(/<rect/g) || []).length > 20);

// ---- families: 16, search rows, finder scoring (page logic replicated) ----
t("T12: 16 families defined", E.FAMS.length === 16, "got " + E.FAMS.length);
const famCounts = {};
for (const r of rows) famCounts[r.fam] = (famCounts[r.fam] || 0) + 1;
t("T12b: all 16 families present in data (975 each)", E.FAMS.every(f => famCounts[f] === 975), JSON.stringify(famCounts));
const byId = {}; idx.forEach(r => byId[r[0]] = r);
function finderSearch(q) { // replica of Finder.search scoring core
  const stop = new Set("the,a,an,for,with,and,that,this,from,into,need,needing,want,make,chip,design".split(","));
  const kw = q.toLowerCase().replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(w => w.length >= 3 && !stop.has(w));
  if (!kw.length) return [];
  return idx.map(r => {
    const hay = (r[1] + " " + E.FAMDEF[r[2]].label + " " + E.FAMDEF[r[2]].desc + " " + r[3]).toLowerCase();
    let s = 0; kw.forEach(k => { if (r[0].toLowerCase().includes(k)) s += 6; else if (r[1].toLowerCase().includes(k)) s += 4; else if (hay.includes(k)) s += 2; });
    return [r, s];
  }).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1] || (a[0][0] < b[0][0] ? -1 : 1)).slice(0, 5);
}
const queries = ["low power sensor wearable", "fast graphics", "quantum", "security enclave", "microcontroller"];
let fq = true;
for (const q of queries) { const res = finderSearch(q); if (!res.length || !res.every(x => byId[x[0][0]])) { fq = false; console.log("   query failed: " + q); } }
t("T13: Chip Finder returns real archived results for 5 queries", fq);
// exact ID fast path (page regex: /^JAH-CHIP-(\d{1,6})$/i)
function normId(q) { const m = q.match(/^JAH-CHIP-(\d{1,6})$/i); if (!m) return null; return "JAH-CHIP-" + m[1].padStart(6, "0"); }
t("T14: exact ID fast path — variants normalize", normId("JAH-CHIP-000123") === "JAH-CHIP-000123" && normId("jah-chip-123") === "JAH-CHIP-000123" && normId("JAH-CHIP-1") === "JAH-CHIP-000001");
t("T15: exact ID — in-archive resolves, out-of-range 999999 reports missing", byId[normId("JAH-CHIP-015600")] && !byId[normId("JAH-CHIP-015601")] && !byId[normId("JAH-CHIP-999999")]);

// ---- manifest parity ----
const man = JSON.parse(fs.readFileSync(path.join(ROOT, "chip-archive-manifest.json"), "utf8"));
t("T16: manifest total_designs == 15,600 == true count", man.total_designs === 15600 && man.generated_designs === 15600 && man.archived_designs === 15600);
t("T16b: manifest family counts sum to 15,600", man.families.reduce((a, f) => a + f.count, 0) === 15600);
t("T16c: manifest latest_id == JAH-CHIP-015600", man.latest_id === "JAH-CHIP-015600");

// ---- QA: name generator boundary ----
t("T17: chipName(0)/chipName(15599) return Signature names", /^Signature /.test(E.chipName(0)) && /^Signature /.test(E.chipName(15599)));

console.log("\n==== " + pass + " PASS / " + fail + " FAIL ====");
process.exit(fail ? 1 : 0);
