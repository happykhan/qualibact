#!/usr/bin/env python3
"""
Import per-species output from qualibact-engine into public/static/species/.

This handles the *new* engine output layout (qualibact-v1.1+):
- Flat per-species directories at the engine output root (no scheme nesting)
- Top-level `filtered_metrics.csv` already holds the published thresholds
- Top-level `species_counts.csv` for genome counts
- Per-species `{Species name}.json` (RefSeq reports), assembly_stats.parquet,
  summary.csv, selected_summary.csv, refseq plot PNGs and a `filtered_plots/` subdir
- Some files use a space in the species name (`Campylobacter jejuni.json`); we
  rename to underscores on copy

For each requested species we drop everything into
public/static/species/{Species}/{scheme}/ and update website_summary.json so
the species page renders. Set as preferred QC scheme.

Usage:
    python3 scripts/import_engine_output.py \\
        --engine-dir /path/to/qualibact_output_feedback \\
        --scheme qualibact-v1.1 \\
        [--skip Neisseria_commensals ...]
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = REPO_ROOT / "public" / "static" / "species"
CONTENT_DIR = REPO_ROOT / "content"
MANIFEST = REPO_ROOT / "public" / "website_summary.json"

# Engine output may use these legacy metric names; normalise on import.
METRIC_ALIASES = {
    "number": "no_of_contigs",
    "Completeness": "Completeness_Specific",
}

SKIP_FILE_EXTS = {".sh", ".out", ".err"}

# Files dropped from the public/ tree as of the 2026-05 cleanup. The
# engine still emits selected_summary.csv but nothing reads it — the
# species page consumes summary.csv directly, and the aggregate
# pipeline reads {Species}_metrics.csv. See WORKPLAN §0 for the data
# scatter that drove this.
SKIP_FILE_NAMES = {"selected_summary.csv"}


def normalise_basename(name: str, species: str) -> str:
    """Engine sometimes uses 'Genus species' (with space) in filenames; rewrite
    to the underscore form so the static-export path layout is consistent."""
    space = species.replace("_", " ")
    return name.replace(space, species)


def _rename_columns(target: Path) -> None:
    """Engine output still emits MY_LOWER / MY_UPPER as column headers.
    QualiBact internal data uses FINAL_LOWER / FINAL_UPPER (renamed
    2026-05-13 for clarity — they're the published-threshold edges, not
    "Nabil's MY_* model"). Translate column headers on import."""
    if target.suffix.lower() != ".csv":
        return
    try:
        text = target.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    if "MY_LOWER" not in text and "MY_UPPER" not in text:
        return
    new = text.replace("MY_LOWER", "FINAL_LOWER").replace("MY_UPPER", "FINAL_UPPER")
    target.write_text(new, encoding="utf-8")


def copy_species_files(src_dir: Path, dst_dir: Path, species: str) -> None:
    """Mirror engine output for one species into the public scheme dir.

    Tarball entries that are symlinks pointing at the engine cluster
    (e.g. /well/aanensen/... for assembly_stats / refseq_genomes
    archives) are silently skipped when broken — they're heavy inputs
    not needed for the published website. Real files copy as before.
    """
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    def _safe_copy(src: Path, tgt: Path) -> bool:
        if src.is_symlink() and not src.resolve(strict=False).exists():
            return False
        try:
            shutil.copy2(src, tgt)
        except FileNotFoundError:
            return False
        return True

    for entry in src_dir.iterdir():
        if entry.name == "filtered_plots":
            tgt_sub = dst_dir / "filtered_plots"
            tgt_sub.mkdir(exist_ok=True)
            for f in entry.iterdir():
                if not f.is_file():
                    continue
                tgt = tgt_sub / normalise_basename(f.name, species)
                if _safe_copy(f, tgt):
                    _rename_columns(tgt)
            continue
        if entry.is_dir():
            continue
        if entry.suffix in SKIP_FILE_EXTS:
            continue
        if entry.name in SKIP_FILE_NAMES:
            continue
        tgt = dst_dir / normalise_basename(entry.name, species)
        if _safe_copy(entry, tgt):
            _rename_columns(tgt)


def extract_thresholds(engine_dir: Path, species: str) -> list[dict[str, str]]:
    """Pull the species' rows out of filtered_metrics.csv (top-level)."""
    csv_path = engine_dir / "filtered_metrics.csv"
    if not csv_path.exists():
        return []
    space = species.replace("_", " ")
    rows: list[dict[str, str]] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("species") or "").strip() != space:
                continue
            metric = (row.get("metric") or "").strip()
            metric = METRIC_ALIASES.get(metric, metric)
            rows.append(
                {
                    "metric": metric,
                    "lower": (row.get("lower_bounds") or "").strip(),
                    "upper": (row.get("upper_bounds") or "").strip(),
                }
            )
    return rows


def write_metrics_csv(thresholds: list[dict[str, str]], species: str, dst_dir: Path) -> None:
    """Write {Species}_metrics.csv mirroring the canonical published-thresholds shape."""
    out = dst_dir / f"{species}_metrics.csv"
    space = species.replace("_", " ")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["species", "metric", "lower_bounds", "upper_bounds"])
        for r in thresholds:
            w.writerow([space, r["metric"], r["lower"], r["upper"]])


def extract_genome_count(engine_dir: Path, species: str) -> int:
    """Look up species count from species_counts.csv (top-level)."""
    csv_path = engine_dir / "species_counts.csv"
    if not csv_path.exists():
        return 0
    space = species.replace("_", " ")
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("species") or "").strip() == space:
                try:
                    return int(row.get("count") or 0)
                except ValueError:
                    return 0
    return 0


def list_plot_files(dst_dir: Path, species: str) -> dict:
    """Build the manifest `plots` dict from filenames present after copy."""
    plots: dict = {}
    metrics = [
        "GC_Content",
        "Completeness_Specific",
        "Contamination",
        "Genome_Size",
        "Total_Coding_Sequences",
        "N50",
    ]
    species_path_prefix = f"{species}/{dst_dir.name}"
    for m in metrics:
        hist = dst_dir / f"{m}_refseq_histogram_kde.png"
        qq = dst_dir / f"{m}_refseq_qqplot.png"
        if hist.exists() or qq.exists():
            plots[m] = {}
            if hist.exists():
                plots[m]["histogram_kde"] = f"{species_path_prefix}/{hist.name}"
            if qq.exists():
                plots[m]["qqplot"] = f"{species_path_prefix}/{qq.name}"
    cds = dst_dir / f"{species}_CDS_vs_Genome_Size.png"
    if cds.exists():
        plots["CDS_vs_Genome_Size"] = f"{species_path_prefix}/{cds.name}"
    return plots


def list_filtered_plot_files(dst_dir: Path) -> list[str]:
    sub = dst_dir / "filtered_plots"
    if not sub.exists():
        return []
    return sorted(f.name for f in sub.iterdir() if f.is_file() and f.suffix.lower() == ".png")


def find_assembly_stats(dst_dir: Path, species: str) -> str | None:
    for ext in ("parquet", "csv.gz", "csv.xz"):
        p = dst_dir / f"{species}_assembly_stats.{ext}"
        if p.exists():
            return p.name
    return None


def import_species(engine_dir: Path, scheme: str, species: str, manifest: dict) -> None:
    """Copy engine output into public/static/species/{species}/{scheme}/ and
    update the website_summary.json registry. Per-scheme data (thresholds,
    plots, counts, sidecars) is no longer written here — build_manifests.py
    derives all of that from filesystem on next prebuild and rewrites
    website_summary.json as the slim registry."""
    src = engine_dir / species
    if not src.exists():
        raise FileNotFoundError(f"engine source missing for {species}: {src}")

    dst = PUBLIC_DIR / species / scheme
    copy_species_files(src, dst, species)

    # If the engine emits a top-level filtered_metrics.csv aggregate, we
    # treat it as authoritative and overwrite the per-species
    # {Species}_metrics.csv with the rounded 2-bound values. When the
    # tarball ships only per-species 4-bound metrics CSVs (the modern
    # engine output), copy_species_files() has already placed them in
    # dst and we leave them alone.
    thresholds = extract_thresholds(engine_dir, species)
    if thresholds:
        write_metrics_csv(thresholds, species, dst)

    # Registry-only update. The bloated scheme_block lived here when
    # build_manifests.py read website_summary.json on input; A6 made
    # build_manifests.py derive everything from filesystem, so writing
    # a scheme_block is wasted work (it gets overwritten on prebuild).
    species_entry = manifest.setdefault("species", {}).setdefault(
        species,
        {"qc_schemes": [], "preferred_qc_scheme": None},
    )
    species_entry.setdefault("qc_schemes", [])
    if scheme not in species_entry["qc_schemes"]:
        species_entry["qc_schemes"].insert(0, scheme)
    species_entry["preferred_qc_scheme"] = scheme


def ensure_mdx_stub(species: str, scheme: str) -> None:
    """No-op as of 2026-05.

    The species page now renders the procedural intro (counts +
    methods-page link) directly from manifest.json via the
    SchemeIntroBlock component, so a boilerplate MDX stub adds no
    information. Per-scheme MDX is reserved for *authored* content
    only — threshold rationale paragraphs, contributor attributions,
    etc. — and is created by hand when an expert provides text worth
    publishing. See scripts/clean_scheme_mdx.py for the one-shot that
    removed the legacy stubs.
    """
    return


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engine-dir", type=Path, required=True)
    p.add_argument("--scheme", default="qualibact-v1.1")
    p.add_argument("--skip", action="append", default=[])
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.engine_dir.exists():
        print(f"ERROR: engine dir not found: {args.engine_dir}", file=sys.stderr)
        return 2

    skip = set(args.skip)
    # Skip dotfiles, engine housekeeping dirs (anything starting with
    # "_" — _array logs, _ecoli_baseline etc.), the cross-species
    # all_summary aggregate, and any species the caller explicitly asks
    # to omit via --skip.
    species_dirs = sorted(
        d for d in args.engine_dir.iterdir()
        if d.is_dir()
        and d.name not in skip
        and not d.name.startswith(".")
        and not d.name.startswith("_")
        and d.name != "all_summary"
    )
    print(f"Importing scheme={args.scheme} for {len(species_dirs)} species "
          f"(skipping: {sorted(skip)})")
    for d in species_dirs:
        print(f"  - {d.name}")

    if args.dry_run:
        return 0

    manifest = json.loads(MANIFEST.read_text())
    for d in species_dirs:
        try:
            import_species(args.engine_dir, args.scheme, d.name, manifest)
            ensure_mdx_stub(d.name, args.scheme)
            print(f"  imported {d.name}")
        except Exception as e:
            print(f"  FAILED {d.name}: {e}", file=sys.stderr)
            return 1

    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    print(f"\nUpdated {MANIFEST.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
