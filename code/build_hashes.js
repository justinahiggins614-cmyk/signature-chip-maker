#!/usr/bin/env node
/* Build per-design content hashes: sha256 over the canonical record JSON
   (sorted keys) for every seeded design. Deterministic: same seed + same
   engine version => same record => same hash. Writes
   data/index/chips.hashes.json.gz and code/test_vectors.json. */
"use strict";
const fs = require("fs"), path = require("path"), zlib = require("zlib"), crypto = require("crypto");
const ROOT = path.dirname(__dirname);
const E = require(path.join(ROOT, "engine.js")).ChipEngine;

function sortKeys(v) {
  if (Array.isArray(v)) return v.map(sortKeys);
  if (v && typeof v === "object") {
    const o = {};
    Object.keys(v).sort().forEach(k => { o[k] = sortKeys(v[k]); });
    return o;
  }
  return v;
}
function recordHash(rec) {
  const canon = JSON.stringify(sortKeys(rec));
  return crypto.createHash("sha256").update(canon, "utf8").digest("hex");
}

const chunkDir = path.join(ROOT, "data", "chunks");
const files = fs.readdirSync(chunkDir).filter(f => f.endsWith(".json.gz")).sort();
const out = [];
let n = 0;
for (const fn of files) {
  const lines = zlib.gunzipSync(fs.readFileSync(path.join(chunkDir, fn))).toString("utf8").trim().split("\n");
  for (const ln of lines) {
    const row = JSON.parse(ln);
    const rec = E.canonicalRecord(row);
    out.push(JSON.stringify({ id: rec.id, seed: rec.seed, engine: rec.engineVer, hash: recordHash(rec) }));
    n++;
  }
}
fs.writeFileSync(path.join(ROOT, "data", "index", "chips.hashes.json.gz"), zlib.gzipSync(out.join("\n") + "\n"));

// test vectors: first 3, a middle, and the last design
const picks = [out[0], out[1], out[2], out[Math.floor(out.length / 2)], out[out.length - 1]];
const tv = {
  engine_version: E.version,
  record_schema: E.recordSchema,
  generated_utc: new Date().toISOString().slice(0, 10),
  vectors: picks.map(p => JSON.parse(p)).map(v => ({
    id: v.id, seed: v.seed, engine_version: v.engine,
    expected_hash_sha256: v.hash,
    note: "same seed + same engine version must reproduce this exact hash"
  }))
};
fs.writeFileSync(path.join(ROOT, "code", "test_vectors.json"), JSON.stringify(tv, null, 1) + "\n");
console.log("hashed " + n + " designs, " + picks.length + " test vectors");
