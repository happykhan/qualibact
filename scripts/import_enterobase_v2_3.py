#!/usr/bin/env python3
"""
One-shot importer for EnteroBase's `QA_evaluation_V2_3.ini` -> a QualiBact
`enterobase-v2.3` scheme.

EnteroBase only QCs species in its **named** genus blocks (Salmonella,
Escherichia, Yersinia, Klebsiella, etc.) plus species explicitly listed
under an `allow species` directive (e.g. Shigella accepted under
Escherichia; Enterobacter aerogenes accepted under Klebsiella). This
importer writes a per-species metrics CSV ONLY for those species —
never the catch-all `[species/default]` block, never the `Virus` block.
A QualiBact species in a genus EnteroBase doesn't cover (e.g.
*Achromobacter xylosoxidans*) gets NO `enterobase-v2.3` row, and
therefore no /enterobase-v2.3/ species page.

For each covered species we also write a sidecar JSON listing the
upstream criteria QualiBact doesn't model (read quality, % low-Q sites,
Kraken species-call agreement, `allow species` aliasing).

Usage:
    python3 scripts/import_enterobase_v2_3.py [--ini path/to/QA_evaluation_V2_3.ini]
"""

from __future__ import annotations

import argparse
import configparser
import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INI = REPO_ROOT / "QA_evaluation_V2_3.ini"
INDEX_JSON = REPO_ROOT / "public" / "api" / "v2" / "index.json"
SPECIES_ROOT = REPO_ROOT / "public" / "static" / "species"

SCHEME = "enterobase-v2.3"

# Mapped metrics: EnteroBase INI key (lowercased by configparser) ->
# (QualiBact metric, which side).
MAP = {
    "min total bases": ("Genome_Size", "FINAL_lower"),
    "max total bases": ("Genome_Size", "FINAL_upper"),
    "min n50": ("N50", "FINAL_lower"),
    "max contig number": ("no_of_contigs", "FINAL_upper"),
}

# EnteroBase metrics QualiBact does NOT model. Captured as a sidecar so
# the species page can footnote them.
OUT_OF_SCOPE_KEYS = [
    "min accepted quality",
    "max percent of low quality sites",
    "proportion of correct species",
    "allow species",
]

# Blocks that should never be applied as a species threshold source:
#   - default: EnteroBase's catch-all; we don't infer it onto unrelated
#              species (e.g. Achromobacter), which mis-claims that
#              EnteroBase QCs them when it doesn't.
#   - Virus:   non-bacterial; doesn't intersect QualiBact's catalogue
#              anyway, but skipped explicitly to be safe.
SKIP_BLOCKS = {"default", "Virus"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ini", type=Path, default=DEFAULT_INI)
    args = ap.parse_args()
    if not args.ini.exists():
        alt = Path.home() / "Downloads" / "QA_evaluation_V2_3.ini"
        if alt.exists():
            args.ini = alt
        else:
            print(f"ERROR: {args.ini} not found")
            return 2

    # Top-level keys without a section header confuse configparser; skip.
    raw = args.ini.read_text(encoding="utf-8")
    first_section = raw.find("[")
    if first_section > 0:
        raw = raw[first_section:]
    cp = configparser.ConfigParser()
    cp.read_string(raw)

    # Collect blocks. Each block has its full cutoff dict + the parsed
    # allow-species list (which we'll treat as additional species the
    # block accepts beyond its own genus).
    blocks: dict[str, dict] = {}
    for section in cp.sections():
        if not section.startswith("species/"):
            continue
        name = section.split("/", 1)[1]
        if name in SKIP_BLOCKS:
            continue
        items = dict(cp.items(section))
        allow_raw = items.get("allow species", "").strip()
        allow_list: list[str] = []
        if allow_raw and allow_raw.upper() != "ALL":
            allow_list = [s.strip() for s in allow_raw.split(",") if s.strip()]
        blocks[name] = {"items": items, "allow_species": allow_list}

    # Build the mapping: which block applies to which QualiBact species.
    #   - If the species' genus matches a block name, that block applies.
    #   - Additionally, if the species name (with underscore -> space)
    #     matches an `allow species` entry verbatim, that block applies.
    if not INDEX_JSON.exists():
        print(f"ERROR: {INDEX_JSON} not found — run build_manifests.py first")
        return 2

    idx = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    species_list = idx.get("species", [])

    coverage: dict[str, tuple[str, dict]] = {}  # species -> (block_name, block)
    for entry in species_list:
        species: str = entry["species"]
        genus = species.split("_", 1)[0]
        pretty = species.replace("_", " ")

        # Primary: genus name matches a block name.
        if genus in blocks:
            coverage[species] = (genus, blocks[genus])
            continue

        # Secondary: cross-genus alias via `allow species`. A block lists
        # a specific species name like "Enterobacter aerogenes" — we map
        # that species back to this block.
        for bname, bdata in blocks.items():
            for allowed in bdata["allow_species"]:
                # Cross-genus alias (single-word genus): e.g. "Shigella"
                # under Escherichia. Match by the species's genus.
                if " " not in allowed and allowed == genus:
                    coverage[species] = (bname, bdata)
                    break
                # Exact "Genus species" alias: e.g. "Enterobacter aerogenes"
                # under Klebsiella.
                if allowed == pretty:
                    coverage[species] = (bname, bdata)
                    break
            else:
                continue
            break

    written = 0
    for species, (block_name, block) in coverage.items():
        cutoffs = block["items"]
        scheme_dir = SPECIES_ROOT / species / SCHEME
        scheme_dir.mkdir(parents=True, exist_ok=True)

        per_metric: dict[str, dict[str, str]] = {}
        for ini_key, (metric, side) in MAP.items():
            val = cutoffs.get(ini_key, "")
            per_metric.setdefault(metric, {"final_lower": "", "final_upper": ""})
            if side == "FINAL_lower":
                per_metric[metric]["final_lower"] = str(int(float(val))) if val else ""
            else:
                per_metric[metric]["final_upper"] = str(int(float(val))) if val else ""

        out_csv = scheme_dir / f"{species}_metrics.csv"
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["metric", "FINAL_lower", "FINAL_upper", "WARN_lower", "WARN_upper", "source"])
            for metric, vals in per_metric.items():
                w.writerow([metric, vals["final_lower"], vals["final_upper"], "", "", "external"])

        sidecar = {
            "scheme": SCHEME,
            "species": species,
            "matched_block": block_name,
            "out_of_scope_for_qualibact": {
                k: cutoffs.get(k)
                for k in OUT_OF_SCOPE_KEYS
                if cutoffs.get(k) is not None
            },
            "source": (
                "EnteroBase QA_evaluation_V2_3 — single-FAIL cutoffs, no WARN band. "
                f"Mapped from EnteroBase's [species/{block_name}] block. "
                "Read-level and species-ID metrics retained here for transparency."
            ),
        }
        (scheme_dir / "enterobase-notes.json").write_text(
            json.dumps(sidecar, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written += 1

    print(f"Wrote {written} (species, {SCHEME}) directories.")
    print("Genera with blocks:", sorted(blocks))
    print(f"QualiBact species covered: {written} of {len(species_list)}")
    print("Now run: python3 scripts/build_manifests.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
