#!/usr/bin/env python3
"""
Emit a human-readable markdown drift report comparing the baseline
threshold fixture against the current per-species manifest values.

Used after an engine-output import to capture *what changed* in a form
that can be linked from release notes and outreach emails. Pair with
``scripts/check_thresholds.py snapshot`` to update the baseline.

Usage:
    python3 scripts/threshold_drift_report.py --label 2026-05-19-kleb
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECIES_ROOT = REPO_ROOT / "public" / "static" / "species"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "published-thresholds.json"
DRIFT_DIR = REPO_ROOT / "tests" / "fixtures"


def _norm(v):
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


def _current() -> dict:
    out: dict = {}
    if not SPECIES_ROOT.exists():
        return out
    for sp_dir in sorted(SPECIES_ROOT.iterdir()):
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
                if lo is None and up is None:
                    continue
                out.setdefault(species, {}).setdefault(scheme, {})[metric] = {
                    "lower": lo, "upper": up,
                }
    return out


def _fmt_bound(v):
    if v is None:
        return "—"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _delta_pct(old, new):
    if old is None or new is None or old == 0:
        return ""
    return f"{(new - old) / abs(old) * 100:+.1f}%"


def report(label: str | None = None) -> int:
    if not FIXTURE_PATH.exists():
        print(f"ERROR: fixture missing at {FIXTURE_PATH}", file=sys.stderr)
        return 2
    baseline = json.loads(FIXTURE_PATH.read_text())
    current = _current()

    # Bucket diffs by (species, scheme)
    diffs: dict[tuple[str, str], list[tuple[str, dict | None, dict | None]]] = {}
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
                    diffs.setdefault((species, scheme), []).append((metric, b, c))

    if not diffs:
        print("No threshold drift detected.")
        return 0

    lines: list[str] = []
    label = label or date.today().isoformat()
    lines.append(f"# Threshold drift report — {label}")
    lines.append("")
    n_rows = sum(len(v) for v in diffs.values())
    lines.append(
        f"Comparison of `tests/fixtures/published-thresholds.json` (baseline) "
        f"against the current per-species manifests. **{n_rows} metric rows "
        f"drifted across {len(diffs)} (species, scheme) pair(s).**"
    )
    lines.append("")
    for (species, scheme), rows in sorted(diffs.items()):
        lines.append(f"## {species.replace('_', ' ')} — {scheme}")
        lines.append("")
        lines.append("| Metric | Baseline lower – upper | Current lower – upper | Δ% lower | Δ% upper |")
        lines.append("|---|---|---|---|---|")
        for metric, b, c in rows:
            b_lo = (b or {}).get("lower")
            b_up = (b or {}).get("upper")
            c_lo = (c or {}).get("lower")
            c_up = (c or {}).get("upper")
            lines.append(
                f"| `{metric}` | {_fmt_bound(b_lo)} – {_fmt_bound(b_up)} | "
                f"{_fmt_bound(c_lo)} – {_fmt_bound(c_up)} | "
                f"{_delta_pct(b_lo, c_lo)} | {_delta_pct(b_up, c_up)} |"
            )
        lines.append("")

    out_path = DRIFT_DIR / f"threshold-drift-{label}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path.relative_to(REPO_ROOT)} ({n_rows} drift rows, {len(diffs)} pairs)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--label", help="Slug for the output filename (default: today's ISO date)")
    args = p.parse_args()
    return report(args.label)


if __name__ == "__main__":
    sys.exit(main())
