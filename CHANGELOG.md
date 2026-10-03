# Changelog — The Signature Computer Chip Maker and Archive

## 2026-10-03 — Chip Record Standard v1.0
- Authoritative `chip-archive-manifest.json`: total designs, generated designs,
  1,000,000 target, 16 family counts, earliest/latest JAH-CHIP ID,
  archive/generator/schema/index versions, index SHA-256, timestamp.
- Chip Record Standard: every design renders a machine-readable canonical
  record (`JAH-CHIP-RECORD/1.0`) with explicit SI units on every numeric spec,
  GENERATED_TARGET labeling, pin-group map (labeled NOT a fabrication pinout),
  versioned block diagram, and separate design/simulation/manufacturing/test
  statuses (CONCEPT / NOT_SIMULATED / NOT_MANUFACTURED / NOT_TESTED).
- Per-design SHA-256 content hashes in `data/index/chips.hashes.json.gz` +
  deterministic test vectors (`code/test_vectors.json`).
- JSON Schemas: `schema/` (chip, chip-family, pin-group, simulation-record,
  manifest, search-result).
- Homepage counter now loads the manifest (bounded: live → cached
  LAST VERIFIED → stamped → error with retry; 12s timeout).
- Chip Finder: exact `JAH-CHIP-######` fast path; empty state reads
  "No matching archived chip design".
- Chip view: per-record canonical URL, Verify Design (local hash
  recomputation vs published index), Report design problem (locally kept),
  downloads carry record version + statuses + units + engineering disclaimer.
- `llms.txt`, `ai-manifest.json`, `methodology.html` published.
- Archive QA gate `code/qa_chip_archive.py` (23 checks: ID uniqueness/
  contiguity, count agreement across manifest/chunks/index/catalog/sitemap/api,
  hash integrity, trademark scan, JSON-LD license check).
