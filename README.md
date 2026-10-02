# The Signature Computer Chip Maker and Archive

Manon's 20th website. Deterministic chip-design generator + archive marching to 1,000,000 designs.

- Live: https://justinahiggins614-cmyk.github.io/signature-chip-maker/
- IDs: `JAH-CHIP-######` · Signature parts: `SIG-CHIP-####` (all Signature-original, no real manufacturer branding/part numbers)
- Engine: `engine.js` (deterministic; same family+seed = same design forever) + `code/gen.py` (seeder/drip, compact rows only)
- Data: `data/chunks/cNNNNN.json.gz` (200/chunk), `data/index/chips.search.json.gz`, `data/state.json`
- Deep links: `?chip=JAH-CHIP-000001`
- Drip: `code/drip.py` (+1,000 designs/run), cron `jah-chip-drip` every 2h, silent, 800MB guard
- Features: SVG circuit-board image per design (theme-matched, 8 labeled sections with descriptions), tiered TTS read-aloud, per-design Q&A AI (data-grounded), copy/download .txt/.json, chip finder bar, A–Z + family browse, X/1M counter
