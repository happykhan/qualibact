#!/usr/bin/env python3
"""
Snapshot and verify published threshold values across species/schemes.

The values rendered on each species page (sourced from
public/static/species/{Species}/{scheme}/manifest.json) are consumed
by downstream tools and must not drift unintentionally across
refactors.

Commands
--------
snapshot
    Walk per-species manifest.json files, extract every
    species x scheme x metric -> {lower, upper}, write
    tests/fixtures/published-thresholds.json. Run after every
    intentional engine import; pair with scripts/threshold_drift_report.py
    for a markdown changelog.

verify
    Re-extract and assert every value equals the fixture. Non-zero
    exit on drift. Wired into npm run build (prebuild) as warn-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECIES_ROOT = REPO_ROOT / "public" / "static" / "species"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "published-thresholds.json"


def _norm(v):
    """Normalize a threshold value: '' / None -> None, numerics -> float."""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return None
        try:
            return float(s)
        except ValueError:
            return s
    if isinstance(v, (int, float)):
        return float(v)
    return v


def extract(species_root: Path = SPECIES_ROOT) -> dict:
    """Walk public/static/species/*/[scheme]/manifest.json and extract every
    (species, scheme, metric) -> {lower, upper}. Replaces the old behaviour
    of reading from website_summary.json, which no longer carries the
    per-scheme thresholds blob (slimmed to a thin registry)."""
    out: dict[str, dict[str, dict[str, dict[str, float | None]]]] = {}
    if not species_root.exists():
        return out
    for sp_dir in sorted(species_root.iterdir()):
        if not sp_dir.is_dir():
            continue
        for sc_dir in sorted(sp_dir.iterdir()):
            if not sc_dir.is_dir():
                continue
            mp = sc_dir / "manifest.json"
            if not mp.exists():
                continue
            try:
                data = json.loads(mp.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            species = data.get("species") or sp_dir.name
            scheme = data.get("scheme") or sc_dir.name
            for row in data.get("thresholds") or []:
                metric = (row.get("metric") or "").strip()
                if not metric:
                    continue
                lo = _norm(row.get("lower"))
                up = _norm(row.get("upper"))
                # Skip rows with no bound on either side — they're metrics
                # the manifest schema enumerates exhaustively (e.g. 'longest')
                # but for which this (species, scheme) has no published
                # threshold. They don't belong in the regression baseline.
                if lo is None and up is None:
                    continue
                out.setdefault(species, {}).setdefault(scheme, {})[metric] = {
                    "lower": lo,
                    "upper": up,
                }
    return out


def snapshot() -> int:
    extracted = extract()
    species_count = len(extracted)
    pair_count = sum(len(s) for s in extracted.values())
    metric_count = sum(len(m) for s in extracted.values() for m in s.values())
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(json.dumps(extracted, indent=2, sort_keys=True) + "\n")
    print(
        f"Wrote {FIXTURE_PATH.relative_to(REPO_ROOT)}: "
        f"{species_count} species, {pair_count} (species,scheme) pairs, "
        f"{metric_count} metric rows"
    )
    return 0


def verify() -> int:
    if not FIXTURE_PATH.exists():
        print(
            f"ERROR: fixture missing at {FIXTURE_PATH}. "
            "Run `python scripts/check_thresholds.py snapshot` first.",
            file=sys.stderr,
        )
        return 2
    baseline = json.loads(FIXTURE_PATH.read_text())
    current = extract()
    diffs: list[str] = []
    species_set = set(baseline) | set(current)
    for species in sorted(species_set):
        base_sp = baseline.get(species, {})
        cur_sp = current.get(species, {})
        scheme_set = set(base_sp) | set(cur_sp)
        for scheme in sorted(scheme_set):
            base_sch = base_sp.get(scheme, {})
            cur_sch = cur_sp.get(scheme, {})
            metric_set = set(base_sch) | set(cur_sch)
            for metric in sorted(metric_set):
                b = base_sch.get(metric)
                c = cur_sch.get(metric)
                if b != c:
                    diffs.append(
                        f"  {species}/{scheme}/{metric}: baseline={b}  current={c}"
                    )
    if diffs:
        print(
            f"FAIL: {len(diffs)} threshold drift(s) from baseline:",
            file=sys.stderr,
        )
        for line in diffs[:50]:
            print(line, file=sys.stderr)
        if len(diffs) > 50:
            print(f"  ... and {len(diffs) - 50} more", file=sys.stderr)
        print(
            "\nIf intentional, regenerate the fixture: "
            "python scripts/check_thresholds.py snapshot",
            file=sys.stderr,
        )
        return 1
    print(
        f"OK: {sum(len(m) for s in current.values() for m in s.values())} "
        "metric rows match baseline"
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["snapshot", "verify"])
    args = p.parse_args()
    if args.command == "snapshot":
        return snapshot()
    return verify()


if __name__ == "__main__":
    sys.exit(main())
