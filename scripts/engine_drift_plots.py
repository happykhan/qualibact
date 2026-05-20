#!/usr/bin/env python3
"""
Produce visualisations of the OLD-vs-NEW engine threshold divergence.

Outputs (PNG) to tests/fixtures/engine-drift-plots/:
  01-drift-counts.png             Per-metric, per-bound stacked count of
                                  species in change-magnitude buckets.
  02-scatter-grid.png             8x2 grid of scatter plots: OLD vs NEW
                                  per (metric, lower/upper) with y=x line.
  03-foldchange-violins.png       Per-metric violin/box of log2(new/old).
  04-species-heatmap.png          Species x (metric,bound) heatmap of
                                  signed log2 fold-change.

Usage:
    python3 scripts/engine_drift_plots.py \\
        --old "/Users/.../all_metrics_selected_summary (1).csv"
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECIES_ROOT = REPO_ROOT / "public" / "static" / "species"
OUT_DIR = REPO_ROOT / "tests" / "fixtures" / "engine-drift-plots"
ALIASES = {"number": "no_of_contigs", "Completeness": "Completeness_Specific"}

METRIC_ORDER = [
    "Genome_Size", "GC_Content", "Total_Coding_Sequences",
    "Completeness_Specific", "Contamination", "N50",
    "no_of_contigs", "longest",
]


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


def load_old(path: Path) -> dict:
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            sp = row["species"].strip().replace(" ", "_")
            m = ALIASES.get(row["metric"].strip(), row["metric"].strip())
            out[(sp, m)] = (_norm_gc(m, _num(row.get("MY_LOWER"))),
                            _norm_gc(m, _num(row.get("MY_UPPER"))))
    return out


def load_new() -> dict:
    out = {}
    for sp_dir in sorted(SPECIES_ROOT.iterdir()):
        if not sp_dir.is_dir():
            continue
        for sc_dir in sorted(sp_dir.iterdir()):
            if not sc_dir.is_dir():
                continue
            mp = sc_dir / "manifest.json"
            if not mp.exists():
                continue
            m = json.loads(mp.read_text())
            sp = m["species"]
            for t in m["thresholds"]:
                metric = t["metric"]
                out[(sp, metric)] = (t.get("final_lower"), t.get("final_upper"))
    return out


def plot_drift_counts(old, new, fp: Path):
    """Stacked bar: per (metric, bound), counts in eq / <10% / 10-50% / 50-200% / >=200%."""
    bins = ["unchanged", "<10%", "10-50%", "50-200%", ">=200%"]
    colors = ["#bdbdbd", "#9ecae1", "#fdae6b", "#fd8d3c", "#a50f15"]
    labels = []
    data = {b: [] for b in bins}
    for metric in METRIC_ORDER:
        for side, idx in (("lower", 0), ("upper", 1)):
            labels.append(f"{metric}\n{side}")
            counts = {b: 0 for b in bins}
            for k in set(old) & set(new):
                if k[1] != metric:
                    continue
                o = old[k][idx]
                n = new[k][idx]
                if o is None or n is None or o == 0:
                    continue
                r = abs((n - o) / o)
                if r < 1e-3:
                    counts["unchanged"] += 1
                elif r < 0.1:
                    counts["<10%"] += 1
                elif r < 0.5:
                    counts["10-50%"] += 1
                elif r < 2.0:
                    counts["50-200%"] += 1
                else:
                    counts[">=200%"] += 1
            for b in bins:
                data[b].append(counts[b])
    fig, ax = plt.subplots(figsize=(15, 6))
    x = np.arange(len(labels))
    bottom = np.zeros(len(labels))
    for b, c in zip(bins, colors):
        ax.bar(x, data[b], bottom=bottom, color=c, label=b, edgecolor="white", linewidth=0.4)
        bottom += np.array(data[b])
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=0)
    ax.set_ylabel("Species count")
    ax.set_title("Drift magnitude buckets per (metric, bound) — OLD MY_* vs NEW FINAL_*")
    ax.legend(loc="upper left", framealpha=0.95, fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(fp, dpi=120)
    plt.close(fig)


def plot_scatter_grid(old, new, fp: Path):
    """8x2 grid: per metric, lower bound | upper bound scatter, OLD x NEW with y=x line.
    Log scale where appropriate (size/count metrics)."""
    fig, axes = plt.subplots(8, 2, figsize=(11, 22))
    for row, metric in enumerate(METRIC_ORDER):
        for col, (side, idx) in enumerate((("lower", 0), ("upper", 1))):
            ax = axes[row][col]
            xs = []; ys = []
            for k in set(old) & set(new):
                if k[1] != metric:
                    continue
                o = old[k][idx]
                n = new[k][idx]
                if o is None or n is None or o <= 0 or n <= 0:
                    continue
                xs.append(o); ys.append(n)
            if not xs:
                ax.text(0.5, 0.5, "no data", transform=ax.transAxes, ha="center", va="center")
                ax.set_title(f"{metric} — {side}", fontsize=10)
                continue
            xs_a = np.array(xs); ys_a = np.array(ys)
            # color by fold-change magnitude
            ratios = np.log2(ys_a / xs_a)
            ax.scatter(xs_a, ys_a, c=ratios, cmap="RdBu_r",
                       vmin=-4, vmax=4, s=20, edgecolor="black", linewidth=0.3, alpha=0.85)
            lo = min(xs_a.min(), ys_a.min())
            hi = max(xs_a.max(), ys_a.max())
            ax.plot([lo, hi], [lo, hi], "--", color="black", linewidth=0.7, alpha=0.5)
            if metric not in {"GC_Content", "Completeness_Specific", "Contamination"}:
                ax.set_xscale("log"); ax.set_yscale("log")
            ax.set_xlabel(f"OLD MY_{side}", fontsize=8)
            ax.set_ylabel(f"NEW FINAL_{side}", fontsize=8)
            ax.set_title(f"{metric} — {side}  (n={len(xs)})", fontsize=10)
            ax.grid(alpha=0.3)
    fig.suptitle("OLD MY_* vs NEW FINAL_* per (metric, bound) — points off y=x are drift\nColour = log2(new/old): red=loosened, blue=tightened", fontsize=12)
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    plt.savefig(fp, dpi=120)
    plt.close(fig)


def plot_foldchange_violins(old, new, fp: Path):
    """Per-metric distribution of log2(new/old) for each bound."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 7), sharey=True)
    for col, (side, idx) in enumerate((("lower", 0), ("upper", 1))):
        ax = axes[col]
        all_data = []
        labels = []
        for metric in METRIC_ORDER:
            ratios = []
            for k in set(old) & set(new):
                if k[1] != metric:
                    continue
                o = old[k][idx]; n = new[k][idx]
                if o is None or n is None or o <= 0 or n <= 0:
                    continue
                ratios.append(math.log2(n / o))
            if not ratios:
                ratios = [0.0]
            all_data.append(ratios)
            labels.append(f"{metric}\nn={len([r for r in ratios if r != 0])}")
        parts = ax.violinplot(all_data, showmedians=True, widths=0.8)
        for body in parts["bodies"]:
            body.set_facecolor("#9ecae1"); body.set_alpha(0.8)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels, fontsize=8, rotation=20, ha="right")
        ax.set_ylabel("log2(new / old)")
        ax.axhline(0, color="black", linewidth=0.5)
        ax.axhline(1, color="red", linewidth=0.4, linestyle="--", alpha=0.5, label="2x loosening")
        ax.axhline(-1, color="blue", linewidth=0.4, linestyle="--", alpha=0.5, label="2x tightening")
        ax.set_title(f"{side} bound fold-change distribution", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        if col == 0:
            ax.legend(loc="upper left", fontsize=8)
    fig.suptitle("Per-metric distribution of log2(NEW / OLD) — same dataset, methodology drift", fontsize=12)
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    plt.savefig(fp, dpi=120)
    plt.close(fig)


def plot_species_heatmap(old, new, fp: Path):
    """Heatmap: rows = species with any |log2(new/old)| >= 1 on any
    (metric, bound), columns = (metric, bound). Cell = signed
    log2(new/old). Only species with at least one big drift."""
    species_order = sorted({sp for (sp, _) in (set(old) & set(new))})
    cols = []
    for metric in METRIC_ORDER:
        for side, idx in (("lo", 0), ("up", 1)):
            cols.append((metric, side, idx))
    matrix = []
    row_labels = []
    for sp in species_order:
        row = []
        any_big = False
        for (metric, side, idx) in cols:
            k = (sp, metric)
            if k in old and k in new:
                o = old[k][idx]; n = new[k][idx]
                if o is None or n is None or o <= 0 or n <= 0:
                    row.append(np.nan)
                    continue
                v = math.log2(n / o)
                row.append(v)
                if abs(v) >= 1:
                    any_big = True
            else:
                row.append(np.nan)
        if any_big:
            matrix.append(row)
            row_labels.append(sp.replace("_", " "))
    if not matrix:
        return
    m = np.array(matrix)
    fig, ax = plt.subplots(figsize=(14, max(12, len(row_labels) * 0.18)))
    im = ax.imshow(m, aspect="auto", cmap="RdBu_r", vmin=-5, vmax=5)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([f"{c[0]} {c[1]}" for c in cols], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=6)
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("log2(NEW / OLD) — red: loosened, blue: tightened, white: unchanged")
    ax.set_title(f"Species x (metric, bound) — only species with |log2(new/old)| >= 1 somewhere ({len(row_labels)} of {len(species_order)})")
    plt.tight_layout()
    plt.savefig(fp, dpi=110)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", required=True, type=Path)
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    old = load_old(args.old)
    new = load_new()
    print(f"OLD: {len(old)}  NEW: {len(new)}  common: {len(set(old) & set(new))}")
    plot_drift_counts(old, new, OUT_DIR / "01-drift-counts.png")
    plot_scatter_grid(old, new, OUT_DIR / "02-scatter-grid.png")
    plot_foldchange_violins(old, new, OUT_DIR / "03-foldchange-violins.png")
    plot_species_heatmap(old, new, OUT_DIR / "04-species-heatmap.png")
    for p in sorted(OUT_DIR.glob("*.png")):
        print(f"  {p.relative_to(REPO_ROOT)}  ({p.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
