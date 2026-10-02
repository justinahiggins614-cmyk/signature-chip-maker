#!/usr/bin/env python3
"""AI canon coherence check — The Signature Computer Chip Maker and Archive.

Manon's order (2026-10-02): "There should be no ai any website incoherent" —
every AI profile a site presents must match the phone-book canon exactly.

Compares every AI identity the site presents against the canon
~/workspace/jah-ai-models/ai-catalog.json:
  1. ID scan: every JAH-AI-<id> claimed on the site must exist in the canon;
     a nearby presented name/description must match canon NAME/DESCRIPTION
     exactly (whitespace-normalized).
  2. Name scan: any canon AI NAME presented as an on-site AI identity must
     carry its matching canon ID (no impersonation without the ID).
  3. Helper hygiene: generic site helpers (kind:"helper" JAHtalk profiles)
     must NOT claim any canon JAH-AI ID.

Exit 0 = coherent. Exit 1 = DRIFT (loud report).
"""
import glob
import json
import os
import re
import sys

SITE_NAME = "The Signature Computer Chip Maker and Archive"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_PATH = os.environ.get(
    "JAH_AI_CANON", os.path.expanduser("~/workspace/jah-ai-models/ai-catalog.json"))

ID_RE = re.compile(r"JAH-AI-[A-Za-z0-9][A-Za-z0-9\-]*")


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def load_canon(path):
    with open(path, encoding="utf-8") as f:
        c = json.load(f)
    recs = c["records"] if isinstance(c, dict) and "records" in c else c
    by_id = {}
    for r in recs:
        i = norm(r.get("ID") or r.get("id"))
        if i:
            by_id[i] = {"NAME": norm(r.get("NAME") or r.get("name")),
                        "DESCRIPTION": norm(r.get("DESCRIPTION") or r.get("description"))}
    return by_id


def site_files():
    pats = ["index.html", "engine.js", "js/*.js", "code/*.js"]
    out = []
    for p in pats:
        out.extend(glob.glob(os.path.join(REPO, p)))
    return sorted({f for f in out if os.path.isfile(f)})


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def nearby_claim(text, pos, key, window=700):
    """Find a nearby presented name/description claim for an AI identity."""
    ctx = text[max(0, pos - window):pos + window]
    pats = {
        "name": [r'["\']name["\']\s*:\s*["\']([^"\']{1,160})["\']',
                 r'\bname\s*=\s*"([^"]{1,160})"',
                 r'\bNAME\s*[:=]\s*"([^"]{1,160})"'],
        "description": [r'["\']description["\']\s*:\s*["\']([^"\']{1,600})["\']',
                        r'\bDESCRIPTION\s*[:=]\s*"([^"]{1,600})"'],
    }[key]
    for pat in pats:
        m = re.search(pat, ctx)
        if m:
            return m.group(1)
    return None


def main():
    by_id = load_canon(CANON_PATH)
    canon_names = sorted({v["NAME"] for v in by_id.values() if len(v["NAME"]) > 4},
                         key=len, reverse=True)
    files = site_files()
    texts = {f: read_text(f) for f in files}

    issues = []
    helpers = []
    ids_checked = 0

    for f, t in texts.items():
        rel = os.path.relpath(f, REPO)
        # --- 1. ID scan ---
        for m in ID_RE.finditer(t):
            aid = m.group(0)
            ids_checked += 1
            if aid not in by_id:
                issues.append("UNKNOWN CANON ID: site file %s claims %s, "
                              "which is not in the canon %s"
                              % (rel, aid, CANON_PATH))
                continue
            canon = by_id[aid]
            sname = nearby_claim(t, m.start(), "name")
            if sname and norm(sname) != canon["NAME"]:
                issues.append("NAME DRIFT: %s presents name %r but canon NAME is %r (%s)"
                              % (aid, norm(sname), canon["NAME"], rel))
            sdesc = nearby_claim(t, m.start(), "description")
            if sdesc and norm(sdesc) != canon["DESCRIPTION"]:
                issues.append("DESCRIPTION DRIFT: %s description on site does not "
                              "match canon (%s)" % (aid, rel))
        # --- 3. helper hygiene ---
        for m in re.finditer(r'kind\s*:\s*["\']helper["\']', t):
            ctx = t[max(0, m.start() - 800):m.start() + 800]
            helpers.append(rel)
            bad = ID_RE.search(ctx)
            if bad:
                issues.append("HELPER CLAIMS CANON ID: generic helper near %s "
                              "carries %s — helpers must not claim canon IDs (%s)"
                              % (rel, bad.group(0), rel))
            if re.search(r'["\']id["\']\s*:\s*["\']JAH-AI', ctx):
                issues.append("HELPER CLAIMS CANON ID: generic helper profile has an "
                              "id field with a JAH-AI value (%s)" % rel)

    # --- 2. name scan (quoted on-site AI identity claims vs canon names) ---
    for f, t in texts.items():
        rel = os.path.relpath(f, REPO)
        for nm in canon_names:
            for m in re.finditer(
                    r'["\']name["\']\s*:\s*["\']' + re.escape(nm) + r'["\']',
                    t, re.IGNORECASE):
                ctx = t[max(0, m.start() - 800):m.start() + 800]
                # find which canon ID owns this name
                owner = next((i for i, v in by_id.items()
                              if v["NAME"].lower() == nm.lower()), None)
                if owner and owner not in ctx:
                    issues.append("NAME WITHOUT ID: site presents canon AI name %r "
                                  "as an identity with no matching canon ID nearby — "
                                  "possible incoherence (%s)" % (nm, rel))

    print("=" * 72)
    print("AI CANON COHERENCE CHECK — %s" % SITE_NAME)
    print("=" * 72)
    print("canon: %s (%d AI records)" % (CANON_PATH, len(by_id)))
    print("site files scanned: %d" % len(files))
    print("canon IDs claimed on site: %d" % ids_checked)
    print("generic helpers found (kind:\"helper\", no canon ID): %d"
          % len(set(helpers)))
    for h in sorted(set(helpers)):
        print("  helper surface: %s" % h)
    print("-" * 72)
    if issues:
        print("DRIFT DETECTED — %d issue(s):" % len(issues))
        for i, msg in enumerate(issues, 1):
            print("  [%d] %s" % (i, msg))
        print("RESULT: INCOHERENT — fix before shipping.")
        return 1
    print("RESULT: COHERENT — every presented AI identity matches the canon;")
    print("helpers claim no canon IDs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
