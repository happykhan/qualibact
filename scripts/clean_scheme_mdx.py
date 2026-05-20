#!/usr/bin/env python3
"""
Strip procedurally-generated boilerplate from per-scheme MDX files.

Now that SchemeIntroBlock renders the counts intro and the methods-page
link directly on the species page (sourced from manifest.json), the old
qualibact-pack-generated paragraphs are redundant. This one-shot script
removes the known boilerplate patterns from
``content/{Species}/{scheme}.mdx`` files. If the remaining body is empty,
the file is deleted entirely — the species page falls back to the
procedural intro.

The species-level ``index.mdx`` is left alone — it holds the authored
species description.

Usage:
    python3 scripts/clean_scheme_mdx.py            # dry-run
    python3 scripts/clean_scheme_mdx.py --write
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT = REPO_ROOT / "content"

# Patterns whose entire line / paragraph is generated boilerplate.
# Order matters only for readability; each pattern is independently
# applied. Patterns are matched against trimmed paragraphs.
BOILERPLATE_PATTERNS = [
    re.compile(r"^#\s+QC Scheme\s+\S+\s*$", re.MULTILINE),
    re.compile(
        r"^This page presents the QualiBact .*? thresholds for \*[^*]+\*\.[^\n]*$",
        re.MULTILINE,
    ),
    re.compile(
        r"^For detailed methods on how these thresholds were calculated[^\n]*$",
        re.MULTILINE,
    ),
    re.compile(r"^The suggested thresholds are in the table below\.\s*$", re.MULTILINE),
    re.compile(
        r"^These thresholds are based on \*\*[\d,]+\*\* genomes from RefSeq[^\n]*$",
        re.MULTILINE,
    ),
    re.compile(
        r"^These thresholds were applied to all the bacteria dataset[^\n]*$",
        re.MULTILINE,
    ),
]

FRONTMATTER_RE = re.compile(r"\A(---\n[\s\S]*?\n---\n*)([\s\S]*)\Z")


def clean(text: str) -> tuple[str, bool, bool]:
    """Return (cleaned_text, changed, body_is_empty_after_clean)."""
    m = FRONTMATTER_RE.match(text)
    if m:
        frontmatter, body = m.group(1), m.group(2)
    else:
        frontmatter, body = "", text

    cleaned = body
    for pat in BOILERPLATE_PATTERNS:
        cleaned = pat.sub("", cleaned)
    # Collapse runs of blank lines.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    new_text = (frontmatter + cleaned + ("\n" if cleaned else "")) if cleaned else ""
    changed = new_text != text
    return new_text, changed, cleaned == ""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true", help="apply changes (default: dry-run)")
    args = p.parse_args()

    # Only species directories (Genus_species). Skip methods/, who-priority/,
    # etc. — those carry authored docs, not auto-generated per-scheme stubs.
    SKIP_DIRS = {"methods", "who-priority"}
    targets: list[Path] = []
    for sp_dir in sorted(CONTENT.iterdir()):
        if not sp_dir.is_dir() or sp_dir.name in SKIP_DIRS:
            continue
        if "_" not in sp_dir.name:
            continue  # need a Genus_species shape
        for f in sorted(sp_dir.iterdir()):
            if f.name == "index.mdx" or not f.name.endswith(".mdx"):
                continue
            targets.append(f)

    n_changed = 0
    n_deleted = 0
    for f in targets:
        text = f.read_text(encoding="utf-8")
        new_text, changed, empty = clean(text)
        if not changed:
            continue
        if empty:
            n_deleted += 1
            print(f"  DELETE {f.relative_to(REPO_ROOT)}")
            if args.write:
                f.unlink()
        else:
            n_changed += 1
            print(f"  CLEAN  {f.relative_to(REPO_ROOT)}")
            if args.write:
                f.write_text(new_text, encoding="utf-8")

    mode = "wrote" if args.write else "would"
    print(f"\n{mode}: clean {n_changed} files, delete {n_deleted} files (of {len(targets)} scanned)")
    if not args.write:
        print("Re-run with --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
