#!/usr/bin/env python3
"""
Generate a per-species markdown report of every (species, scheme) that
either:
  - has a non-null severity in flags.json (info | warn | error), OR
  - has any threshold metric drifting >50% from the OLD engine output.

Each species section lists the engine's severity, fired signals (with
fraction/count/interpretation), and a per-metric table of which bounds
moved relative to the OLD MY_LOWER / MY_UPPER values in
all_metrics_selected_summary.csv.

Output: tests/fixtures/engine-problem-species-{YYYY-MM-DD}.md

Usage:
    python3 scripts/engine_problem_report.py \\
        --old /Users/nfareed/Downloads/all_metrics_selected_summary\\ (1).csv \\
        --label 2026-05-20
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECIES_ROOT = REPO_ROOT / "public" / "static" / "species"
OUT_DIR = REPO_ROOT / "tests" / "fixtures"

ALIASES = {"number": "no_of_contigs", "Completeness": "Completeness_Specific"}
PCT_METRICS = {"GC_Content", "Completeness_Specific", "Contamination"}

SIGNAL_LABEL = {
    "frac_incomplete": "Incomplete genomes",
    "frac_short_genome": "Genomes shorter than 70% of median",
    "frac_oversized_genome": "Genomes larger than 2x median",
    "frac_high_contamination": "Genomes with Contamination > 5%",
    "max_contamination_over_100": "Contamination > 100% (CheckM2 ceiling breach)",
    "wide_gc_range": "GC range wider than 5 percentage points",
    "final_bound_dragged": "FINAL band dragged beyond WARN band by outliers",
    "low_count_flag": "Low reference-genome count",
}


def _num(s):
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _norm_gc(metric, v):
    if v is None:
        return None
    if metric == "GC_Content" and abs(v) <= 1.5:
        return v * 100
    return v


def _load_old(path: Path) -> dict:
    """Return {(species_underscored, metric): (my_lower, my_upper)}."""
    out: dict = {}
    if not path.exists():
        return out
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            sp = row["species"].strip().replace(" ", "_")
            m = ALIASES.get(row["metric"].strip(), row["metric"].strip())
            out[(sp, m)] = (
                _norm_gc(m, _num(row.get("MY_LOWER"))),
                _norm_gc(m, _num(row.get("MY_UPPER"))),
            )
    return out


def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return f"{v:.4g}"


def _rel_change(old, new):
    if old is None or new is None or old == 0:
        return None
    return (new - old) / abs(old)


def _signal_str(s: dict) -> str:
    label = SIGNAL_LABEL.get(s["signal"], s["signal"])
    flag = s.get("flag") or "—"
    frac = s.get("fraction")
    n = s.get("n")
    cnt = s.get("count")
    parts = [f"**{label}** ({flag})"]
    if frac is not None and n is not None:
        pct = frac * 100
        if cnt is not None:
            parts.append(f"{pct:.1f}% ({cnt}/{n})")
        else:
            parts.append(f"{pct:.1f}%")
    interp = s.get("interpretation")
    if interp:
        parts.append(f"*{interp}*")
    return " — ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", required=True, type=Path,
                    help="Path to the OLD all_metrics_selected_summary CSV")
    ap.add_argument("--label", default=date.today().isoformat(),
                    help="Slug for the output filename")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="Min |rel change| for a metric to be flagged as drifted (default 0.5 = 50%)")
    args = ap.parse_args()

    old = _load_old(args.old)
    if not old:
        print(f"ERROR: no rows loaded from {args.old}", file=sys.stderr)
        return 2

    # For each (species, scheme) on disk: collect engine flags + per-metric diffs
    species_sections: list[dict] = []
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
                m = json.loads(mp.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            species = m.get("species") or sp_dir.name
            scheme = m.get("scheme") or sc_dir.name
            engine = (m.get("warnings") or {}).get("engine") or {}
            severity = engine.get("severity")
            fired = engine.get("fired_signals") or []

            # Per-metric diffs (only metrics in old AND in this manifest)
            drifts: list[dict] = []
            for t in m.get("thresholds") or []:
                metric = (t.get("metric") or "").strip()
                if not metric:
                    continue
                metric = ALIASES.get(metric, metric)
                key = (species, metric)
                if key not in old:
                    continue
                old_lo, old_up = old[key]
                new_final_lo = t.get("final_lower")
                new_final_up = t.get("final_upper")
                new_warn_lo = t.get("warn_lower")
                new_warn_up = t.get("warn_upper")
                rl = _rel_change(old_lo, new_final_lo)
                ru = _rel_change(old_up, new_final_up)
                worst = 0.0
                for rc in (rl, ru):
                    if rc is not None and abs(rc) > worst:
                        worst = abs(rc)
                if worst >= args.threshold:
                    drifts.append({
                        "metric": metric,
                        "old_lower": old_lo,
                        "old_upper": old_up,
                        "new_final_lower": new_final_lo,
                        "new_final_upper": new_final_up,
                        "new_warn_lower": new_warn_lo,
                        "new_warn_upper": new_warn_up,
                        "rel_lower": rl,
                        "rel_upper": ru,
                        "worst": worst,
                    })

            # Include species if either: severity in (warn, error) OR any drift
            if severity in ("warn", "error") or drifts:
                species_sections.append({
                    "species": species,
                    "scheme": scheme,
                    "severity": severity,
                    "fired": fired,
                    "drifts": drifts,
                    "genome_count": (m.get("counts") or {}).get("genome_count", 0),
                    "refseq_count": (m.get("counts") or {}).get("refseq_count", 0),
                })

    # Sort: error first, then warn, then info/None; within each, by species name
    severity_rank = {"error": 0, "warn": 1, "info": 2, None: 3}
    species_sections.sort(key=lambda s: (severity_rank.get(s["severity"], 9), s["species"], s["scheme"]))

    # Render
    out_path = OUT_DIR / f"engine-problem-species-{args.label}.md"
    by_sev = {"error": 0, "warn": 0, "info": 0, None: 0}
    total_drifts = 0
    for s in species_sections:
        by_sev[s["severity"]] = by_sev.get(s["severity"], 0) + 1
        total_drifts += len(s["drifts"])

    lines: list[str] = []
    lines.append(f"# Engine problem species — {args.label}\n")
    lines.append(
        f"Generated {date.today().isoformat()} from `tests/fixtures` + "
        f"per-species `flags.json` + diff against the OLD engine output "
        f"({args.old.name}).\n"
    )
    lines.append(
        f"**{len(species_sections)}** (species, scheme) pairs flagged "
        f"(severity error: {by_sev.get('error', 0)}, warn: {by_sev.get('warn', 0)}, "
        f"info-or-none with drift: {by_sev.get('info', 0) + by_sev.get(None, 0)}). "
        f"**{total_drifts}** total metric drifts >{int(args.threshold*100)}% "
        f"relative to the OLD `MY_LOWER` / `MY_UPPER`.\n"
    )
    lines.append("Table-of-contents per severity tier:\n")
    for sev in ("error", "warn", "info", None):
        sev_label = sev or "no severity"
        targets = [s for s in species_sections if s["severity"] == sev]
        if not targets:
            continue
        lines.append(f"- **{sev_label}**: " + ", ".join(
            f"[{s['species'].replace('_', ' ')} ({s['scheme']})](#{s['species'].lower().replace('_', '-')}-{s['scheme'].lower().replace('.', '')})"
            for s in targets[:50]
        ) + (f" … and {len(targets) - 50} more" if len(targets) > 50 else "") + "\n")
    lines.append("")

    for s in species_sections:
        anchor = f"{s['species'].lower().replace('_', '-')}-{s['scheme'].lower().replace('.', '')}"
        sev = s["severity"] or "no severity"
        sev_badge = {"error": "🔴", "warn": "🟡", "info": "🔵"}.get(s["severity"], "⚪")
        lines.append(f"## <a id=\"{anchor}\"></a>{sev_badge} *{s['species'].replace('_', ' ')}* — `{s['scheme']}` (severity: **{sev}**)")
        lines.append("")
        lines.append(f"Reference dataset: **{s['genome_count']}** genomes ({s['refseq_count']} from RefSeq).")
        lines.append("")
        if s["fired"]:
            lines.append("**Engine quality signals fired:**")
            lines.append("")
            for sig in s["fired"]:
                lines.append(f"- {_signal_str(sig)}")
            lines.append("")
        else:
            lines.append("_No engine quality signals fired._")
            lines.append("")
        if s["drifts"]:
            lines.append("**Metric drifts (OLD `MY_*` → NEW `FINAL_*` / `WARN_*`):**")
            lines.append("")
            lines.append("| Metric | OLD MY_lower | OLD MY_upper | NEW FINAL_lower | NEW FINAL_upper | NEW WARN_lower | NEW WARN_upper | Δ lower | Δ upper |")
            lines.append("|---|---|---|---|---|---|---|---|---|")
            s["drifts"].sort(key=lambda d: d["worst"], reverse=True)
            for d in s["drifts"]:
                def pct(v):
                    return f"{v*100:+.0f}%" if v is not None else ""
                lines.append(
                    f"| `{d['metric']}` "
                    f"| {_fmt(d['old_lower'])} | {_fmt(d['old_upper'])} "
                    f"| {_fmt(d['new_final_lower'])} | {_fmt(d['new_final_upper'])} "
                    f"| {_fmt(d['new_warn_lower'])} | {_fmt(d['new_warn_upper'])} "
                    f"| {pct(d['rel_lower'])} | {pct(d['rel_upper'])} |"
                )
            lines.append("")
        else:
            lines.append("_No threshold metric drifted by more than the threshold._")
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")
    print(f"  {len(species_sections)} (species, scheme) pairs")
    print(f"  severity: error={by_sev.get('error', 0)} warn={by_sev.get('warn', 0)} info={by_sev.get('info', 0)} none={by_sev.get(None, 0)}")
    print(f"  total metric drifts > {int(args.threshold*100)}%: {total_drifts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
