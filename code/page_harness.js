/* End-to-end page harness: runs the REAL inline index.html script + tour script
   in Node with DOM stubs, against REAL local data via a fetch shim.
   Usage: node page_harness.js [--fail-index] [--fail-chunks] */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = "/home/hatch/workspace/signature-chip-maker";
const failIndex = process.argv.includes("--fail-index");
const failChunks = process.argv.includes("--fail-chunks");
let pass = 0, fail = 0;
function t(name, ok, extra) {
  if (ok) { pass++; console.log("PASS " + name); }
  else { fail++; console.log("FAIL " + name + (extra ? " :: " + extra : "")); }
}
// ---------- DOM stubs ----------
function mkEl(id) {
  return {
    id, innerHTML: "", textContent: "", value: "", title: "", href: "", rel: "", type: "", disabled: false,
    dataset: {}, style: {},
    classList: { toggle() {}, add() {}, remove() {}, contains() { return false; } },
    closest() { return null; }, appendChild() {}, removeChild() {},
    insertAdjacentHTML(p, h) { this.innerHTML += h; },
    querySelector() { return null; }, querySelectorAll() { return []; },
    addEventListener() {}, removeAttribute() {}, setAttribute() {}, getAttribute() { return null; },
    focus() {}, click() {}, scrollIntoView() {},
    getBoundingClientRect() { return { left: 10, top: 10, width: 100, height: 50, right: 110, bottom: 60 }; }
  };
}
const els = {};
const listeners = {};
const store = {};
global.window = global;
global.addEventListener = (ty, fn) => { (listeners[ty] = listeners[ty] || []).push(fn); };
global.document = {
  getElementById(id) { return els[id] || (els[id] = mkEl(id)); },
  querySelector() { return null; }, querySelectorAll() { return []; },
  createElement(tag) { return mkEl(tag); },
  head: mkEl("head"), body: mkEl("body"), title: "",
  addEventListener(ty, fn) { (listeners[ty] = listeners[ty] || []).push(fn); }
};
global.localStorage = {
  getItem(k) { return k in store ? store[k] : null; },
  setItem(k, v) { store[k] = String(v); }, removeItem(k) { delete store[k]; }
};
global.location = { search: "", origin: "https://x.test", pathname: "/", href: "https://x.test/" };
try { Object.defineProperty(global, "navigator", { value: {}, configurable: true }); } catch (e) {}
global.Audio = class { constructor() { this.onended = null; } set src(v) {} play() { return Promise.resolve(); } pause() {} };
global.fetch = async (url) => {
  if (failIndex && url === "data/index/chips.search.json.gz") throw new Error("simulated index fetch failure");
  if (failChunks && String(url).startsWith("data/chunks/")) throw new Error("simulated chunk fetch failure");
  const buf = fs.readFileSync(path.join(ROOT, url));
  return {
    ok: true, status: 200,
    json: async () => JSON.parse(buf.toString("utf8")),
    arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength)
  };
};
// globalThis.crypto is already webcrypto in Node 24 — nothing to do.
// engine (sets window.ChipEngine since window=global)
require(path.join(ROOT, "engine.js"));
// ---------- load inline scripts ----------
const pageSrc = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const blocks = [...pageSrc.matchAll(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const mainSrc = blocks.find(b => b.includes("var DB="));
const tourSrc = blocks.find(b => b.includes("jah-tour-seen-chips"));
t("harness: main + tour scripts located", !!mainSrc && !!tourSrc);
eval(mainSrc + "\n;globalThis.__P={UI,Finder,TTS,DB,QA,openChip,chipBack,loadManifest,loadIndex,loadRow};");
eval(tourSrc); // assigns window.Tour / window.Guide
const P = globalThis.__P;
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  // boot
  for (const fn of (listeners["DOMContentLoaded"] || [])) await fn();
  await sleep(2500); // let async boot settle (incl. tour auto-start timer)
  t("boot: livecount shows live manifest count 15,600", els["livecount"].textContent === "15,600", JSON.stringify(els["livecount"].textContent));
  if (!failIndex && !failChunks) {
    t("spotlight: featured design renders (real design)", /FEATURED DESIGN/.test(els["spotlight"].innerHTML) && /JAH-CHIP-/.test(els["spotlight"].innerHTML), els["spotlight"].innerHTML.slice(0, 80));
    t("spotlight: honesty pill present", /CONCEPTUAL DESIGN/.test(els["spotlight"].innerHTML));
    t("grid: 48 cards rendered with status pills", (els["grid"].innerHTML.match(/class="card"/g) || []).length === 48 && /NOT_SIMULATED/.test(els["grid"].innerHTML) && /NOT_MANUFACTURED/.test(els["grid"].innerHTML));
    t("grid: loadstat counts", /Showing 48 of 15,600/.test(els["loadstat"].textContent), els["loadstat"].textContent);
    // Load More
    P.UI.more();
    t("Load More: 96 cards after second page", (els["grid"].innerHTML.match(/class="card"/g) || []).length === 96);
    // Family filter x16
    const fams = ["CPU","GPU","NPU","SOC","MCU","FPGA","MEMC","SENSOR","PMIC","QCTRL","PHOT","NEURO","DSP","MODEM","SEC","CHIPLET"];
    let famOk = true;
    for (const f of fams) { P.UI.setFam(f); if (P.UI.rows().length !== 975) { famOk = false; console.log("   family " + f + " -> " + P.UI.rows().length); } }
    t("family search: all 16 families filter to 975 rows", famOk);
    P.UI.setFam("");
    // A-Z filter
    P.UI.setLetter("V");
    t("A-Z: V filter returns rows starting SIGNATURE V", P.UI.rows().length > 0 && P.UI.rows().every(r => r[1].toUpperCase().indexOf("SIGNATURE V") === 0), String(P.UI.rows().length));
    P.UI.setLetter("");
    // Chip Finder keyword
    document.getElementById("finderq").value = "low power sensor chip for a wearable";
    P.Finder.ask();
    t("Finder: keyword search returns live matches", /live match/.test(els["finderres"].innerHTML) && /JAH-CHIP-/.test(els["finderres"].innerHTML));
    // exact ID fast path
    document.getElementById("finderq").value = "JAH-CHIP-000123"; P.Finder.ask();
    t("Finder: exact ID navigates", location.search === "?chip=JAH-CHIP-000123", location.search);
    location.search = "";
    document.getElementById("finderq").value = "jah-chip-42"; P.Finder.ask();
    t("Finder: case-insensitive + zero-pad ID", location.search === "?chip=JAH-CHIP-000042", location.search);
    location.search = "";
    document.getElementById("finderq").value = "JAH-CHIP-999999"; P.Finder.ask();
    t("Finder: out-of-range ID reports missing", /No archived design/.test(els["finderres"].innerHTML));
    // random design
    location.search = ""; P.UI.random();
    t("random: resolves to a real in-range design", /^\?chip=JAH-CHIP-(\d{6})$/.test(location.search) && parseInt(location.search.slice(15), 10) <= 15600, location.search);
    location.search = "";
    // design detail view
    await P.openChip("JAH-CHIP-000001");
    const cv = els["chipview"].innerHTML;
    t("detail: full record loads", /JAH-CHIP-000001/.test(cv) && /spec table|Process node/i.test(cv));
    t("detail: statuses present", /CONCEPT/.test(cv) && /NOT_SIMULATED/.test(cv) && /NOT_TESTED/.test(cv) && /NOT_MANUFACTURED/.test(cv));
    t("detail: toolbar buttons present", /Read aloud/.test(cv) && /Verify design/.test(cv) && /Download .json/.test(cv));
    t("detail: board SVG present", /<svg/.test(cv));
    // Verify Design button
    P.UI.verify();
    await sleep(1500);
    t("Verify: recomputed hash MATCHES published", /MATCH — byte-identical/.test(els["recinfo"].innerHTML), els["recinfo"].innerHTML.replace(/<[^>]+>/g, "").slice(0, 90));
    // Read-aloud controls
    P.TTS.readChip();
    t("TTS: readChip shows floating bar", els["ttsbar"].style.display === "block");
    P.TTS.pause(); P.TTS.resume();
    t("TTS: pause/resume callable without error", true);
    P.TTS.stop();
    t("TTS: stop hides the bar", els["ttsbar"].style.display === "none");
  } else if (failIndex) {
    t("error state: grid shows retry when index fails", /could not load/.test(els["grid"].innerHTML) && /Retry/.test(els["grid"].innerHTML));
    t("error state: livecount falls back to stamped count", /15,600/.test(els["livecount"].textContent), els["livecount"].textContent);
  } else if (failChunks) {
    await P.UI.spotlight();
    t("error state: spotlight shows retry when chunks fail", /Retry/.test(els["spotlight"].innerHTML));
  }
  // ---------- tour + guide ----------
  // seed the guide panel's static HTML (the stub DOM never parsed the page markup)
  (function(){const gi=pageSrc.indexOf('<div id="guidepanel"');const gj=pageSrc.indexOf("To take this tour again",gi);const gk=pageSrc.indexOf("</div>",gj);if(gi>0&&gk>0)document.getElementById("guidepanel").innerHTML=pageSrc.slice(gi,gk);})();
  t("tour: global exposed", typeof Tour !== "undefined" && typeof Guide !== "undefined");
  Tour.start();
  t("tour: step 1 of 8", document.getElementById("tourstep").textContent === "Step 1 of 8");
  Tour.next();
  t("tour: next -> step 2", document.getElementById("tourstep").textContent === "Step 2 of 8");
  Tour.back();
  t("tour: back -> step 1", document.getElementById("tourstep").textContent === "Step 1 of 8");
  Tour.next(); Tour.next(); Tour.next(); Tour.next(); Tour.next(); Tour.next(); Tour.next();
  t("tour: reaches final step", document.getElementById("tourstep").textContent === "Step 8 of 8" && /Done/.test(document.getElementById("tournext").textContent));
  Tour.skip();
  t("tour: skip dismisses + marks seen", document.getElementById("tourcard").style.display === "none" && store["jah-tour-seen-chips"] === "1");
  Guide.open();
  t("guide: panel opens with full feature docs", document.getElementById("guidepanel").style.display === "block" && /Verify design/.test(document.getElementById("guidepanel").innerHTML) && /Read aloud/.test(document.getElementById("guidepanel").innerHTML));
  Guide.close();
  t("guide: panel closes", document.getElementById("guidepanel").style.display === "none");
  console.log("\n==== " + pass + " PASS / " + fail + " FAIL ====");
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error("HARNESS ERROR:", e); process.exit(2); });
