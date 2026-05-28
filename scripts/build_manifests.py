#!/usr/bin/env python3
"""
Generate per-(species, scheme) manifest.json files and the new
/api/v2/ aggregate endpoints from website_summary.json + each
species' summary.csv + content/species-notes.yml.

This is WORKPLAN.md §3 Phase A — ship the new data shape without
yet migrating the frontend to consume it. The website still reads
website_summary.json for now; downstream tools (Kleborate, SpecCheck)
can start consuming /api/v2/ immediately, and a future PR migrates
the species page to read manifest.json instead.

Outputs:
  public/static/species/{Species}/{scheme}/manifest.json — one per pair
  public/api/v2/thresholds.csv  — flat CSV (Kleborate-friendly)
  public/api/v2/thresholds.json — same data, JSON shape
  public/api/v2/index.json      — registry of all (species, scheme) pairs

Run:
  python3 scripts/build_manifests.py
"""

from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC = REPO_ROOT / "public"
SPECIES_ROOT = PUBLIC / "static" / "species"
MANIFEST = PUBLIC / "website_summary.json"
API_DIR = PUBLIC / "api" / "v2"
SUMMARY_DIR = PUBLIC / "static" / "summary"
SPECIES_NOTES_PATH = REPO_ROOT / "content" / "species-notes.yml"

SCHEMA_VERSION = "1.0"

METRIC_ALIASES = {
    "Completeness": "Completeness_Specific",
    "number": "no_of_contigs",
}

# Buffer applied locally when {Species}_metrics.csv is still 2-bound
# (legacy pipeline shape) — mirrors scripts/regenerate_thresholds.py so
# WARN bounds in manifest.json stay populated until the engine re-runs
# emit the 4-bound shape natively.
WARN_BUFFER_PCT = 0.10
PCT_METRICS = {"GC_Content", "Completeness_Specific", "Contamination"}


def _warn_from_fail_lower(metric: str, fail: float | None) -> float | None:
    if fail is None:
        return None
    if metric in PCT_METRICS:
        return fail + 1.0
    return fail * (1.0 + WARN_BUFFER_PCT)


def _warn_from_fail_upper(metric: str, fail: float | None) -> float | None:
    if fail is None:
        return None
    if metric in PCT_METRICS:
        return fail - 1.0
    return fail * (1.0 - WARN_BUFFER_PCT)


def _num(s) -> float | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s) if math.isfinite(float(s)) else None
    s = str(s).strip()
    if s == "":
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def _normalise_gc(metric: str, v: float | None) -> float | None:
    """GC_Content can be a fraction (0–1) or percentage (0–100) in
    summary.csv — sometimes mixed within one row. Coerce to percentage
    on read so every consumer sees consistent units."""
    if v is None:
        return v
    if metric == "GC_Content" and abs(v) <= 1.5:
        return v * 100
    return v


def read_metrics_csv(scheme_dir: Path, species: str) -> dict[str, dict]:
    """Read {Species}_metrics.csv and return per-metric 4-bound + source.

    Detects two shapes:
    - **New engine output** (qualibact-v1.1+ as of 2026-05): header includes
      ``FINAL_lower``, ``FINAL_upper``, ``WARN_lower``, ``WARN_upper`` and
      optionally ``source``. WARN/FAIL both come from the file; source is
      ``computed`` / ``pinned`` from the engine.
    - **Legacy 2-bound** (anything pre-2026 imported via sync_public.py or
      the older import path): only ``lower_bounds`` / ``upper_bounds``.
      ``final_lower``/``final_upper`` come from this file; ``warn_lower``/
      ``warn_upper`` are filled in by the caller from summary.csv FINAL_*
      (or computed via the buffer rule). ``source`` defaults to ``computed``.

    Returns ``{metric: {final_lower, final_upper, warn_lower, warn_upper, source}}``
    with ``None`` for absent bounds. Empty dict if no metrics.csv exists.
    """
    p = scheme_dir / f"{species}_metrics.csv"
    if not p.exists():
        return {}
    try:
        with open(p, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            rows = list(reader)
    except OSError:
        return {}
    if not header:
        return {}

    def ix(col: str) -> int:
        return header.index(col) if col in header else -1

    i_metric = ix("metric")
    if i_metric < 0:
        return {}

    # Detect new engine output by FINAL_lower presence (case sensitive).
    i_final_l = ix("FINAL_lower")
    i_final_u = ix("FINAL_upper")
    i_warn_l = ix("WARN_lower")
    i_warn_u = ix("WARN_upper")
    i_source = ix("source")
    new_shape = i_final_l >= 0 or i_final_u >= 0

    # Legacy columns.
    i_legacy_l = ix("lower_bounds")
    i_legacy_u = ix("upper_bounds")

    out: dict[str, dict] = {}
    for r in rows:
        raw_metric = (r[i_metric] if i_metric < len(r) else "").strip()
        if not raw_metric:
            continue
        metric = METRIC_ALIASES.get(raw_metric, raw_metric)

        def cell(i: int) -> float | None:
            if i < 0 or i >= len(r):
                return None
            s = r[i].strip()
            if s == "":
                return None
            try:
                v = float(s)
            except ValueError:
                return None
            if not math.isfinite(v):
                return None
            return v

        def _src() -> str:
            if i_source < 0 or i_source >= len(r):
                return "computed"
            return r[i_source].strip().lower() or "computed"

        if new_shape:
            final_l = _normalise_gc(metric, cell(i_final_l))
            final_u = _normalise_gc(metric, cell(i_final_u))
            warn_l = _normalise_gc(metric, cell(i_warn_l))
            warn_u = _normalise_gc(metric, cell(i_warn_u))
            source = _src()
        else:
            final_l = _normalise_gc(metric, cell(i_legacy_l))
            final_u = _normalise_gc(metric, cell(i_legacy_u))
            warn_l = None  # filled in by caller from summary.csv
            warn_u = None
            source = "computed"

        out[metric] = {
            "final_lower": final_l,
            "final_upper": final_u,
            "warn_lower": warn_l,
            "warn_upper": warn_u,
            "source": source,
        }
    return out


def read_summary_csv(scheme_dir: Path) -> dict[str, dict[str, float | None]]:
    """For each metric in summary.csv return per-metric bounds + KS stats.
    GC normalised to percentage."""
    out: dict[str, dict[str, float | None]] = {}
    p = scheme_dir / "summary.csv"
    if not p.exists():
        return out
    text = p.read_text(encoding="utf-8").strip().split("\n")
    if len(text) < 2:
        return out
    header = [h.strip() for h in text[0].split(",")]

    def ix(col: str) -> int:
        return header.index(col) if col in header else -1

    i_metric = ix("metric")
    i_ml_l = ix("FINAL_LOWER")
    i_ml_u = ix("FINAL_UPPER")
    i_lb = ix("lower_bound")
    i_ub = ix("upper_bound")
    i_rs_lb = ix("refseq_lower_bound")
    i_rs_ub = ix("refseq_upper_bound")
    i_ks_p = ix("KS_p_value")
    i_ks_stat = ix("KS_statistic")
    if i_metric < 0:
        return out
    for raw_row in text[1:]:
        cells = raw_row.split(",")
        raw_metric = (cells[i_metric] if i_metric < len(cells) else "").strip()
        if not raw_metric:
            continue
        metric = METRIC_ALIASES.get(raw_metric, raw_metric)
        out[metric] = {
            "ml_lower": _normalise_gc(metric, _num(cells[i_ml_l]) if i_ml_l >= 0 and i_ml_l < len(cells) else None),
            "ml_upper": _normalise_gc(metric, _num(cells[i_ml_u]) if i_ml_u >= 0 and i_ml_u < len(cells) else None),
            "auto_lower": _normalise_gc(metric, _num(cells[i_lb]) if i_lb >= 0 and i_lb < len(cells) else None),
            "auto_upper": _normalise_gc(metric, _num(cells[i_ub]) if i_ub >= 0 and i_ub < len(cells) else None),
            "refseq_lower": _normalise_gc(metric, _num(cells[i_rs_lb]) if i_rs_lb >= 0 and i_rs_lb < len(cells) else None),
            "refseq_upper": _normalise_gc(metric, _num(cells[i_rs_ub]) if i_rs_ub >= 0 and i_rs_ub < len(cells) else None),
            "ks_p_value": _num(cells[i_ks_p]) if i_ks_p >= 0 and i_ks_p < len(cells) else None,
            "ks_statistic": _num(cells[i_ks_stat]) if i_ks_stat >= 0 and i_ks_stat < len(cells) else None,
        }
    return out


# Warning thresholds.
#
# low_genome: matches the engine's `min_genome_count` default (100).
#
# species_separation: tried an auto-compute based on the KS test against
# RefSeq, but ATB-vs-RefSeq divergence is the *norm* in this dataset
# (different sampling, different filtering, different scale), so even
# the moderate-effect threshold (KS_statistic >= 0.3) tripped ~93% of
# the catalogue. The correct signal would be a within-species
# multimodality test (Hartigan's dip, GMM with k>1) in qualibact-engine;
# that's tracked as an engine TODO. For now, species_separation is
# entirely manually-set — flag a species via content/species-notes.yml
# (the free-text note appears alongside the bool flag on the page).
LOW_GENOME_THRESHOLD = 100


def read_engine_flags(scheme_dir: Path) -> dict | None:
    """Load the engine's per-species flags.json. The engine emits a
    ``severity`` (info / warn / error) per (species, scheme) plus a
    ``quality_signals`` block flagging individual checks
    (frac_high_contamination, max_contamination_over_100,
    frac_oversized_genome, wide_gc_range, frac_incomplete,
    frac_short_genome, ...). The website must surface this — when the
    engine says the reference dataset is broken, users need to know
    before trusting the thresholds."""
    p = scheme_dir / "flags.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


_INTERPRETATION_STRIP = (
    " Use the WARN band as the practical threshold for the listed "
    "metrics — the FINAL band is dictated by outliers, not the bulk of "
    "the species's distribution."
)

# Engine wording -> friendlier wording. The engine references its own
# internal pipeline step ("IsolationForest") in the user-facing
# interpretation; rephrase to terms the species page audience will
# recognise without losing the meaning.
_INTERPRETATION_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "either in the species data that survived IsolationForest",
        "either in the submitted species data",
    ),
]


def _clean_interpretation(text: str | None) -> str | None:
    if not text:
        return text
    t = text.replace(_INTERPRETATION_STRIP, "")
    for src, dst in _INTERPRETATION_REPLACEMENTS:
        t = t.replace(src, dst)
    t = t.rstrip()
    return t or None


def summarise_engine_flags(flags: dict | None) -> dict:
    """Project the engine's full flags.json into the trimmed shape we
    carry in manifest.warnings.engine. Keeps only fields the species
    page renders.

    The engine's `final_bound_dragged` interpretation ends with a
    prescriptive recommendation ("Use the WARN band as the practical
    threshold ...") that the website prefers to leave to the methods
    page rather than repeat on every species banner — stripped here so
    it never reaches the rendered UI or the per-species reports.
    """
    if not flags:
        return {}
    severity = (flags.get("severity") or "").strip().lower() or None
    fired: list[dict] = []
    for signal_name, signal in (flags.get("quality_signals") or {}).items():
        if not isinstance(signal, dict):
            continue
        flag = signal.get("flag")
        if not flag:  # null = signal didn't fire
            continue
        fired.append({
            "signal": signal_name,
            "flag": flag,
            "fraction": signal.get("fraction"),
            "count": signal.get("count"),
            "n": signal.get("n"),
            "interpretation": _clean_interpretation(signal.get("interpretation")),
        })
    return {
        "severity": severity,
        "low_count_flag": flags.get("low_count_flag"),
        "fired_signals": fired,
    }


def compute_warnings(scheme_data: dict, summary_bounds: dict) -> tuple[bool, bool]:
    """Compute (low_genome, species_separation) from data, not from the
    legacy flags carried over in website_summary.json. REFSEQ-QC-v1 schemes
    use the refseq_genome_count field; everything else uses genome_count."""
    scheme = (scheme_data.get("scheme") or "").upper()
    # External / third-party schemes (e.g. enterobase-v2.3) don't ship a
    # derivation cohort, so the low-genome warning would always fire and
    # is misleading there — they're not derived from genomes at all.
    if scheme.startswith("ENTEROBASE"):
        return False, False
    if scheme.startswith("REFSEQ"):
        count = scheme_data.get("refseq_genome_count") or scheme_data.get("genome_count") or 0
    else:
        count = scheme_data.get("genome_count") or 0
    low_genome = count < LOW_GENOME_THRESHOLD

    # species_separation is manually-set (see comment near
    # LOW_GENOME_THRESHOLD above for why auto-computation was scrapped).
    # Always False here; the actual signal comes from
    # content/species-notes.yml entries which surface the same amber
    # banner via a free-text caveat.
    species_separation = False
    return low_genome, species_separation


def load_species_notes() -> dict[tuple[str, str | None], list[str]]:
    if not SPECIES_NOTES_PATH.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    data = yaml.safe_load(SPECIES_NOTES_PATH.read_text()) or {}
    out: dict[tuple[str, str | None], list[str]] = {}
    for entry in data.get("notes") or []:
        sp = (entry.get("species") or "").strip()
        sc = entry.get("scheme")
        if sp and entry.get("note"):
            out.setdefault((sp, sc.strip() if sc else None), []).append(entry["note"])
    return out


def notes_for(species: str, scheme: str, notes: dict) -> list[str]:
    return notes.get((species, None), []) + notes.get((species, scheme), [])


def build_manifest(
    species: str,
    scheme: str,
    scheme_data: dict,
    summary_bounds: dict,
    notes: list[str],
    generated_at: str,
    metrics_csv_bounds: dict | None = None,
) -> dict:
    """Compose a single per-(species, scheme) manifest.

    Threshold rows carry two parallel pairs of bounds for the transition
    period from old (2-bound `{Species}_metrics.csv` + buffer-computed
    WARN) to new (4-bound `{Species}_metrics.csv` from the engine):

    - `lower` / `upper` are the published FAIL boundary (legacy column
      names; equal to `final_lower` / `final_upper`).
    - `final_lower` / `final_upper` mirror `lower` / `upper` with the
      canonical engine naming.
    - `warn_lower` / `warn_upper` are the WARN tier. Sourced from the
      engine's WARN_lower/WARN_upper when the metrics.csv is the new
      4-bound shape; otherwise from summary.csv FINAL_LOWER/UPPER; as
      a last resort, computed via the ±10% / ±1pp buffer.
    - `source` is `pinned` when the engine flagged the value as a
      manual override, else `computed`.

    `ml_*` / `auto_*` / `refseq_*` legacy columns are still populated
    for backwards compatibility with consumers that read them; they
    will be dropped in a follow-up commit once the column rename has
    propagated through the frontend.
    """
    canonical_metrics = [
        "Genome_Size", "GC_Content", "Total_Coding_Sequences",
        "Completeness_Specific", "Contamination", "N50",
        "no_of_contigs", "longest",
    ]
    # Prefer the per-species metrics CSV (canonical source) for FAIL +
    # WARN + source. Fall back to whatever scheme_data carried in.
    mc = metrics_csv_bounds or {}
    published = {}
    if mc:
        for m, row in mc.items():
            published[m] = {
                "lower": row.get("final_lower"),
                "upper": row.get("final_upper"),
            }
    else:
        for t in scheme_data.get("thresholds", []) or []:
            m = METRIC_ALIASES.get(t.get("metric", ""), t.get("metric", ""))
            published[m] = {
                "lower": _num(t.get("lower")),
                "upper": _num(t.get("upper")),
            }

    threshold_rows = []
    for metric in canonical_metrics:
        pub = published.get(metric, {"lower": None, "upper": None})
        eng = summary_bounds.get(metric, {})
        mc_row = mc.get(metric, {})

        # WARN tier resolution: engine column > summary.csv FINAL_* >
        # locally-computed buffer.
        warn_l = mc_row.get("warn_lower")
        warn_u = mc_row.get("warn_upper")
        source = mc_row.get("source", "computed")
        # Third-party / external schemes (e.g. enterobase-v2.3) are
        # single-FAIL — leave WARN blank verbatim, don't synthesise from
        # the engine summary or a buffer.
        if source != "external":
            if warn_l is None:
                warn_l = eng.get("ml_lower")
            if warn_u is None:
                warn_u = eng.get("ml_upper")
            if warn_l is None and pub["lower"] is not None:
                warn_l = _warn_from_fail_lower(metric, pub["lower"])
            if warn_u is None and pub["upper"] is not None:
                warn_u = _warn_from_fail_upper(metric, pub["upper"])

        threshold_rows.append({
            "metric": metric,
            "lower": pub["lower"],
            "upper": pub["upper"],
            # New canonical fields:
            "final_lower": pub["lower"],
            "final_upper": pub["upper"],
            "warn_lower": warn_l,
            "warn_upper": warn_u,
            "source": source,
            # Legacy fields (kept for the transition window):
            "ml_lower": eng.get("ml_lower"),
            "ml_upper": eng.get("ml_upper"),
            "auto_lower": eng.get("auto_lower"),
            "auto_upper": eng.get("auto_upper"),
            "refseq_lower": eng.get("refseq_lower"),
            "refseq_upper": eng.get("refseq_upper"),
        })

    # Plot inventory directly from manifest (sync already populates this)
    plots = scheme_data.get("plots") or {}

    low_genome, species_separation = compute_warnings({**scheme_data, "scheme": scheme}, summary_bounds)
    engine_flags = summarise_engine_flags(scheme_data.get("engine_flags"))
    return {
        "schema_version": SCHEMA_VERSION,
        "species": species,
        "scheme": scheme,
        "generated_at": generated_at,
        "counts": {
            "genome_count": scheme_data.get("genome_count", 0),
            "refseq_count": scheme_data.get("refseq_genome_count", 0),
            "final_count": scheme_data.get("final_count", scheme_data.get("genome_count", 0)),
            "filtered_out_count": scheme_data.get("filtered_out_count", 0),
            **(scheme_data.get("tier_counts") or {}),
        },
        "warnings": {
            "low_genome": low_genome,
            "species_separation": species_separation,
            "notes": notes,
            "engine": engine_flags,
        },
        "thresholds": threshold_rows,
        "plots": plots,
        "filtered_plot_files": scheme_data.get("filtered_plot_files", []),
        "has_cds_plot": bool(scheme_data.get("has_cds_plot", False)),
        "sidecars": {
            "summary_csv": _sidecar(scheme_data, "summaries.summary", species, scheme, "summary.csv"),
            "metrics_csv": scheme_data.get("metrics", {}).get("species_metrics"),
            "refseq_archive": scheme_data.get("metrics", {}).get("refseq_genomes") or _build_refseq_path(species, scheme, scheme_data),
            "assembly_stats_archive": _build_assembly_stats_path(species, scheme, scheme_data),
            "atb_pass_archive": scheme_data.get("metrics", {}).get("atb_pass"),
            "atb_warn_archive": scheme_data.get("metrics", {}).get("atb_warn"),
            "atb_fail_archive": scheme_data.get("metrics", {}).get("atb_fail"),
            "species_json": _build_species_json_path(species, scheme, scheme_data),
        },
        "mdx_path": f"content/{species}/{scheme}.mdx",
    }


def _sidecar(scheme_data: dict, dotted: str, species: str, scheme: str, fname: str) -> str | None:
    keys = dotted.split(".")
    cur = scheme_data
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    if not cur:
        return None
    return f"{species}/{scheme}/{fname}"


def _build_refseq_path(species: str, scheme: str, scheme_data: dict) -> str | None:
    fn = scheme_data.get("refseq_archive_filename")
    if fn:
        return f"{species}/{scheme}/{fn}"
    return None


def _build_species_json_path(species: str, scheme: str, scheme_data: dict) -> str | None:
    fn = scheme_data.get("species_json_filename")
    if fn:
        return f"{species}/{scheme}/{fn}"
    return None


def _build_assembly_stats_path(species: str, scheme: str, scheme_data: dict) -> str | None:
    fn = scheme_data.get("assembly_stats_filename")
    if fn:
        return f"{species}/{scheme}/{fn}"
    return None


def write_per_species_manifests(manifests: list[dict]) -> int:
    n = 0
    for m in manifests:
        sp = m["species"]
        sc = m["scheme"]
        out = SPECIES_ROOT / sp / sc / "manifest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(m, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        n += 1
    return n


def write_aggregates_from_pairs(
    manifests: list[dict],
    pairs: dict[str, list[str]],
    preferred: dict[str, str | None],
    generated_at: str,
) -> tuple[int, int]:
    """Thin wrapper that injects pairs+preferred into write_aggregates().
    Avoids a website_summary.json round-trip — the registry is built
    fresh from the filesystem walk by main()."""
    return write_aggregates(manifests, generated_at, pairs=pairs, preferred=preferred)


def write_aggregates(
    manifests: list[dict],
    generated_at: str,
    *,
    pairs: dict[str, list[str]] | None = None,
    preferred: dict[str, str | None] | None = None,
) -> tuple[int, int]:
    """Emit /api/v2/{thresholds.csv, thresholds.json, thresholds.xlsx, index.json}.
    Returns (csv_rows, species_count). When pairs/preferred are omitted the
    function falls back to deriving them from the manifest list — keeps
    the test-call signature stable.

    External (third-party) schemes are filtered OUT of the canonical
    /api/v2/ files and routed to /api/v2/external/{scheme}.json so the
    main API stays QualiBact-published-only. The cross-scheme compare
    view fetches the external file separately.
    """
    API_DIR.mkdir(parents=True, exist_ok=True)
    EXTERNAL_SCHEMES = {"enterobase-v2.3"}
    qb_manifests = [m for m in manifests if m["scheme"] not in EXTERNAL_SCHEMES]
    ext_manifests = [m for m in manifests if m["scheme"] in EXTERNAL_SCHEMES]

    # thresholds.csv — flat, four-bound aggregate. The new canonical
    # columns are FINAL_lower/FINAL_upper (FAIL boundary) +
    # WARN_lower/WARN_upper (WARN tier) + source (computed | pinned).
    # The legacy lower/upper/ml_*/auto_*/refseq_* columns are still
    # written for the transition window — consumers will be migrated
    # then the legacy columns dropped.
    def _write_csv_and_json(target_dir: Path, ms: list[dict]) -> int:
        target_dir.mkdir(parents=True, exist_ok=True)
        csv_p = target_dir / "thresholds.csv"
        rows = 0
        with open(csv_p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "species", "scheme", "metric",
                "FINAL_lower", "FINAL_upper",
                "WARN_lower", "WARN_upper",
                "source",
                "engine_severity",
                # Legacy aliases kept for the transition window:
                "lower", "upper",
                "ml_lower", "ml_upper",
                "auto_lower", "auto_upper",
                "refseq_lower", "refseq_upper",
            ])
            for m in ms:
                species_label = m["species"].replace("_", " ")
                severity = ((m.get("warnings") or {}).get("engine") or {}).get("severity") or ""
                # External schemes: only emit rows that the upstream
                # actually defines (i.e. have a non-null FINAL bound).
                # No "computed" placeholders for metrics the scheme
                # doesn't constrain.
                is_external = m["scheme"] in EXTERNAL_SCHEMES
                for t in m["thresholds"]:
                    if is_external and t.get("final_lower") is None and t.get("final_upper") is None:
                        continue
                    w.writerow([
                        species_label, m["scheme"], t["metric"],
                        _fmt(t["final_lower"]), _fmt(t["final_upper"]),
                        _fmt(t["warn_lower"]), _fmt(t["warn_upper"]),
                        t.get("source") or "computed",
                        severity,
                        _fmt(t["lower"]), _fmt(t["upper"]),
                        _fmt(t["ml_lower"]), _fmt(t["ml_upper"]),
                        _fmt(t["auto_lower"]), _fmt(t["auto_upper"]),
                        _fmt(t["refseq_lower"]), _fmt(t["refseq_upper"]),
                    ])
                    rows += 1

        # thresholds.json — same data, nested
        bs: dict[str, dict] = {}
        for m in ms:
            is_external = m["scheme"] in EXTERNAL_SCHEMES
            kept = [
                t for t in m["thresholds"]
                if not (is_external and t.get("final_lower") is None and t.get("final_upper") is None)
            ]
            bs.setdefault(m["species"], {"schemes": {}})
            bs[m["species"]]["schemes"][m["scheme"]] = {
                "thresholds": kept,
                "counts": m["counts"],
                "warnings": m["warnings"],
            }
        (target_dir / "thresholds.json").write_text(
            json.dumps({
                "schema_version": SCHEMA_VERSION,
                "generated_at": generated_at,
                "species": bs,
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        return rows

    csv_rows = _write_csv_and_json(API_DIR, qb_manifests)
    ext_rows = _write_csv_and_json(API_DIR / "external", ext_manifests) if ext_manifests else 0

    # index.json — registry. Built from the pairs/preferred maps the
    # caller supplied (filesystem-derived) so this function doesn't
    # depend on website_summary.json existing yet — it's written
    # *after* this returns.
    if pairs is None:
        pairs = {}
        for m in manifests:
            pairs.setdefault(m["species"], []).append(m["scheme"])
        for sp in list(pairs):
            # de-dupe / sort to keep output deterministic
            pairs[sp] = sorted(set(pairs[sp]))
    if preferred is None:
        preferred = {sp: infer_preferred(schemes) for sp, schemes in pairs.items()}

    def _write_index(target_dir: Path, pairs_subset: dict[str, list[str]], header_prefix: str) -> int:
        target_dir.mkdir(parents=True, exist_ok=True)
        entries = []
        for sp in sorted(pairs_subset):
            schemes = pairs_subset[sp]
            if not schemes:
                continue
            entries.append({
                "species": sp,
                "name": sp.replace("_", " "),
                "preferred_scheme": preferred.get(sp) if header_prefix == "" else None,
                "schemes": [
                    {"scheme": s, "manifest_url": f"/static/species/{sp}/{s}/manifest.json"}
                    for s in schemes
                ],
            })
        (target_dir / "index.json").write_text(
            json.dumps({
                "schema_version": SCHEMA_VERSION,
                "generated_at": generated_at,
                "species_count": len(entries),
                "endpoints": {
                    "thresholds_csv": f"/api/v2/{header_prefix}thresholds.csv",
                    "thresholds_json": f"/api/v2/{header_prefix}thresholds.json",
                    "per_species_manifest": "/static/species/{species}/{scheme}/manifest.json",
                },
                "species": entries,
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        return len(entries)

    qb_pairs = {sp: [s for s in scs if s not in EXTERNAL_SCHEMES] for sp, scs in pairs.items()}
    qb_pairs = {sp: scs for sp, scs in qb_pairs.items() if scs}
    species_count = _write_index(API_DIR, qb_pairs, "")

    if ext_manifests:
        ext_pairs = {sp: [s for s in scs if s in EXTERNAL_SCHEMES] for sp, scs in pairs.items()}
        ext_pairs = {sp: scs for sp, scs in ext_pairs.items() if scs}
        _write_index(API_DIR / "external", ext_pairs, "external/")

    return csv_rows, species_count


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _csv_to_xlsx(csv_path: Path, xlsx_path: Path, sheet_name: str) -> int:
    """Convert a CSV file to a sibling .xlsx, coercing cells that parse as
    numbers to numeric so Excel sorts/filters them naturally. Returns the
    row count written, or -1 if openpyxl is unavailable / source missing."""
    if not csv_path.exists():
        return -1
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        if xlsx_path.exists():
            xlsx_path.unlink()
        print(f"Skipped {xlsx_path.name} (install openpyxl to enable)")
        return -1
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    rows_written = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            wb.save(xlsx_path)
            return 0
        ws.append(header)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for r in reader:
            out: list = []
            for cell in r:
                if cell == "":
                    out.append(None)
                    continue
                try:
                    n = float(cell)
                except ValueError:
                    out.append(cell)
                    continue
                # Preserve int-ness so cells show "5300000" not "5300000.0".
                out.append(int(n) if n.is_integer() else n)
            ws.append(out)
            rows_written += 1
    ws.freeze_panes = "A2"
    wb.save(xlsx_path)
    return rows_written


def write_genus_csvs(manifests: list[dict]) -> tuple[int, int]:
    """Emit per-genus metrics + counts CSVs at
    public/static/genus/{Genus}/{Genus}_{metrics,counts}.csv.

    Returns (genera_written, metric_rows_written). Each genus folds in
    every (species, scheme) under that genus — the genus-page download
    is the rollup, not just the preferred scheme. Caller still picks
    preferred for any single-row-per-species view.
    """
    by_genus: dict[str, list[dict]] = {}
    for m in manifests:
        genus = (m.get("species") or "").split("_", 1)[0]
        if not genus:
            continue
        by_genus.setdefault(genus, []).append(m)

    metric_rows_total = 0
    genus_root = PUBLIC / "static" / "genus"
    for genus, ms in sorted(by_genus.items()):
        gdir = genus_root / genus
        gdir.mkdir(parents=True, exist_ok=True)

        # {Genus}_metrics.csv — 4-bound per (species, scheme, metric).
        mpath = gdir / f"{genus}_metrics.csv"
        with open(mpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "species", "scheme", "metric",
                "FINAL_lower", "FINAL_upper",
                "WARN_lower", "WARN_upper",
                "source",
            ])
            for m in sorted(ms, key=lambda x: (x["species"], x["scheme"])):
                species_label = m["species"].replace("_", " ")
                for t in m["thresholds"]:
                    w.writerow([
                        species_label, m["scheme"], t["metric"],
                        _fmt(t["final_lower"]), _fmt(t["final_upper"]),
                        _fmt(t["warn_lower"]), _fmt(t["warn_upper"]),
                        t.get("source") or "computed",
                    ])
                    metric_rows_total += 1

        # {Genus}_counts.csv — one row per species at its preferred scheme.
        seen: dict[str, dict] = {}
        for m in ms:
            sp = m["species"]
            # Prefer the preferred scheme if multiple schemes exist;
            # otherwise the first manifest is fine.
            if sp not in seen:
                seen[sp] = m
        cpath = gdir / f"{genus}_counts.csv"
        with open(cpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "species", "scheme",
                "genome_count", "refseq_count",
                "final_count", "filtered_out_count",
            ])
            for sp in sorted(seen):
                m = seen[sp]
                c = m.get("counts") or {}
                w.writerow([
                    sp.replace("_", " "), m["scheme"],
                    c.get("genome_count", 0),
                    c.get("refseq_count", 0),
                    c.get("final_count", 0),
                    c.get("filtered_out_count", 0),
                ])

    return len(by_genus), metric_rows_total


_TIER_RANK = {"Critical": 0, "High": 1, "Medium": 2}


def _resolve_who_priority(species_in_registry: set[str]) -> dict[int, dict[str, str]]:
    """Read content/who-priority/data.yml and return, per year, a map of
    {Species_underscore: tier} where tier is the strongest priority the
    species appears under. genusGroup entries expand to every species in
    those genera that we have in the registry; proxySpecies entries map
    the proxy species as well (so the page's link target is downloadable).
    """
    path = REPO_ROOT / "content" / "who-priority" / "data.yml"
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        sys.stderr.write("WARNING: PyYAML not installed; priority CSVs skipped.\n")
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    out: dict[int, dict[str, str]] = {}
    for lst in data.get("lists") or []:
        year = lst.get("year")
        if not isinstance(year, int):
            continue
        per_year: dict[str, str] = {}

        def upgrade(species: str, tier: str) -> None:
            if species not in species_in_registry:
                return
            cur = per_year.get(species)
            if cur is None or _TIER_RANK.get(tier, 99) < _TIER_RANK.get(cur, 99):
                per_year[species] = tier

        for tier in lst.get("tiers") or []:
            tname = tier.get("name")
            for entry in tier.get("entries") or []:
                sp = entry.get("species")
                proxy = entry.get("proxySpecies")
                genus_group = entry.get("genusGroup") or []
                if sp:
                    upgrade(sp, tname)
                if proxy:
                    upgrade(proxy, tname)
                for g in genus_group:
                    prefix = f"{g}_"
                    for k in species_in_registry:
                        if k.startswith(prefix):
                            upgrade(k, tname)
        out[year] = per_year
    return out


def write_priority_pathogens_csvs(manifests: list[dict]) -> dict[int, int]:
    """Emit one CSV per WHO year at
    public/static/priority-pathogens/who-{year}.csv, filtered to the
    species named (directly, via proxySpecies, or expanded from genusGroup)
    on that year's list. Returns {year: rows_written}.

    Schema matches the genus rollups but adds a leading ``tier`` column so
    consumers can split the download by Critical / High / Medium without
    cross-referencing the WHO list.
    """
    registry = {m["species"] for m in manifests}
    per_year = _resolve_who_priority(registry)
    if not per_year:
        return {}

    out_dir = PUBLIC / "static" / "priority-pathogens"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows_by_year: dict[int, int] = {}
    # group manifests by species for fast lookup; one species may have
    # multiple schemes — we include every scheme so the download mirrors
    # the per-genus aggregate shape.
    by_species: dict[str, list[dict]] = {}
    for m in manifests:
        by_species.setdefault(m["species"], []).append(m)

    for year, tier_map in per_year.items():
        path = out_dir / f"who-{year}.csv"
        rows = 0
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "who_year", "tier",
                "species", "scheme", "metric",
                "FINAL_lower", "FINAL_upper",
                "WARN_lower", "WARN_upper",
                "source",
            ])
            for sp in sorted(tier_map):
                tier = tier_map[sp]
                ms = sorted(by_species.get(sp, []), key=lambda x: x["scheme"])
                for m in ms:
                    species_label = sp.replace("_", " ")
                    for t in m["thresholds"]:
                        w.writerow([
                            year, tier,
                            species_label, m["scheme"], t["metric"],
                            _fmt(t["final_lower"]), _fmt(t["final_upper"]),
                            _fmt(t["warn_lower"]), _fmt(t["warn_upper"]),
                            t.get("source") or "computed",
                        ])
                        rows += 1
        rows_by_year[year] = rows
    return rows_by_year


VALID_SCHEMES = ("qualibact-v1.0", "qualibact-v1.1", "REFSEQ-QC-v1", "enterobase-v2.3")
# `enterobase-v2.3` is deliberately NOT in PREFERRED_PRIORITY — it's a
# third-party comparison scheme and should never be the default landing
# scheme for a species. It still appears in the scheme switcher.
PREFERRED_PRIORITY = ("qualibact-v1.1", "qualibact-v1.0", "REFSEQ-QC-v1")
BANNED_SCHEMES = {"ESGEM-AMR-v1", "Klebnet-v1"}


def discover_pairs() -> dict[str, list[str]]:
    """Walk public/static/species/ to find every (species, scheme) pair on
    disk. Returns {species: [schemes]}. The filesystem IS the source of
    truth — replaces the old behaviour of reading scheme membership from
    website_summary.json (which was being kept in sync by hand).
    """
    out: dict[str, list[str]] = {}
    if not SPECIES_ROOT.exists():
        return out
    for sp_dir in sorted(SPECIES_ROOT.iterdir()):
        if not sp_dir.is_dir() or sp_dir.name.startswith("."):
            continue
        schemes: list[str] = []
        for sc_dir in sorted(sp_dir.iterdir()):
            if not sc_dir.is_dir():
                continue
            name = sc_dir.name
            if name in BANNED_SCHEMES:
                continue
            if name not in VALID_SCHEMES:
                # Allow unknown schemes through but skip dotfiles / scratch
                if name.startswith("."):
                    continue
            schemes.append(name)
        if schemes:
            out[sp_dir.name] = schemes
    return out


def infer_preferred(schemes: list[str]) -> str | None:
    if not schemes:
        return None
    for candidate in PREFERRED_PRIORITY:
        if candidate in schemes:
            return candidate
    return schemes[0]


def _count_gz_rows(p: Path) -> int | None:
    """Row count (excluding header) of a gzipped CSV. None if file absent."""
    if not p.exists():
        return None
    import gzip
    try:
        with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
            return max(0, sum(1 for _ in f) - 1)
    except OSError:
        return None


def enrich_refseq_csv(scheme_dir: Path, species: str) -> bool:
    """Augment the per-species RefSeq genomes CSV with the rich metadata
    that lives in `{Species}.json` (annotation pipeline, assembly method,
    sequencing tech, ANI to type strain, BioSample attributes — strain,
    collection date, geographic origin, isolation source, host, etc.).

    Writes back to `{species}_refseq_genomes.csv.xz` so the existing
    download URL keeps working. Returns True if enrichment happened.
    """
    import gzip
    import lzma

    src_json = scheme_dir / f"{species}.json"
    if not src_json.exists():
        return False
    # Find existing csv (xz or gz) or fall through to writing fresh xz.
    src_csv = None
    src_kind = None
    for ext in ("csv.xz", "csv.gz"):
        cand = scheme_dir / f"{species}_refseq_genomes.{ext}"
        if cand.exists():
            src_csv = cand
            src_kind = ext
            break
    out_path = scheme_dir / f"{species}_refseq_genomes.csv.xz"

    try:
        report = json.loads(src_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    # Index existing CSV rows by accession so we can preserve the
    # per-genome QC metric values that came from the assembly_stats
    # tables (these are the values qualibact-engine actually used).
    existing_by_accession: dict[str, dict] = {}
    if src_csv is not None:
        opener = lzma.open if src_kind == "csv.xz" else gzip.open
        try:
            with opener(src_csv, "rt", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    acc = (row.get("accession") or "").strip()
                    if acc:
                        existing_by_accession[acc] = row
        except OSError:
            return False

    def _biosample_attr(report_, name: str) -> str:
        attrs = (report_.get("assembly_info", {}) or {}).get("biosample", {}).get("attributes") or []
        for a in attrs:
            if (a.get("name") or "").strip().lower() == name.lower():
                v = a.get("value")
                if v is not None:
                    return str(v).strip()
        return ""

    def _get(d: dict, *path, default=""):
        cur: object = d
        for p in path:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return default
            if cur is None:
                return default
        return cur if cur not in (None, "") else default

    # Output schema: existing 15 columns first (so any existing consumer
    # still finds them), followed by the enrichment columns.
    BASE_COLS = [
        "accession", "organism_name", "assembly_level",
        "N50", "number", "longest",
        "GC_Content", "Completeness_Specific", "Contamination",
        "Total_Coding_Sequences", "Genome_Size",
        "submitter", "release_date", "bioproject", "biosample",
    ]
    EXTRA_COLS = [
        "tax_id",
        "strain",
        "collection_date",
        "geo_loc_name",
        "isolation_source",
        "host",
        "sample_type",
        "lat_lon",
        "assembly_name",
        "assembly_method",
        "sequencing_tech",
        "annotation_method",
        "annotation_pipeline",
        "annotation_release_date",
        "annotation_software_version",
        "checkm_marker_set",
        "checkm_marker_set_rank",
        "checkm_version",
        "checkm_completeness_percentile",
        "genome_coverage",
        "contig_l50",
        "scaffold_n50",
        "number_of_scaffolds",
        "ani_best_match_organism",
        "ani_best_match_value",
        "ani_match_status",
        "source_database",
        "bioproject_title",
        "paired_assembly",
        "current_accession",
    ]
    all_cols = BASE_COLS + EXTRA_COLS

    rows_written = 0
    with lzma.open(out_path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_cols, extrasaction="ignore")
        writer.writeheader()
        for r in report.get("reports") or []:
            acc = (r.get("accession") or "").strip()
            if not acc:
                continue
            existing = existing_by_accession.get(acc, {})
            ai = r.get("assembly_info") or {}
            ann = r.get("annotation_info") or {}
            cm = r.get("checkm_info") or {}
            org = r.get("organism") or {}
            stats = r.get("assembly_stats") or {}
            ani_match = (r.get("average_nucleotide_identity") or {}).get("best_ani_match") or {}
            bioproject_title = ""
            lineage = ai.get("bioproject_lineage") or []
            if lineage:
                bps = (lineage[0] or {}).get("bioprojects") or []
                if bps:
                    bioproject_title = bps[0].get("title", "") or ""

            row = {**{k: existing.get(k, "") for k in BASE_COLS}}
            # Backfill the BASE columns from JSON when missing in legacy CSV.
            if not row["accession"]:
                row["accession"] = acc
            if not row["organism_name"]:
                row["organism_name"] = org.get("organism_name") or ""
            if not row["assembly_level"]:
                row["assembly_level"] = ai.get("assembly_level") or ""
            if not row["submitter"]:
                row["submitter"] = ai.get("submitter") or ""
            if not row["release_date"]:
                row["release_date"] = ai.get("release_date") or ""
            if not row["bioproject"]:
                row["bioproject"] = ai.get("bioproject_accession") or ""
            if not row["biosample"]:
                row["biosample"] = (ai.get("biosample") or {}).get("accession") or ""

            row.update({
                "tax_id": str(org.get("tax_id") or ""),
                "strain": _biosample_attr(r, "strain") or _get(org, "infraspecific_names", "strain"),
                "collection_date": _biosample_attr(r, "collection_date"),
                "geo_loc_name": _biosample_attr(r, "geo_loc_name"),
                "isolation_source": _biosample_attr(r, "isolation_source"),
                "host": _biosample_attr(r, "host"),
                "sample_type": _biosample_attr(r, "sample_type"),
                "lat_lon": _biosample_attr(r, "lat_lon"),
                "assembly_name": ai.get("assembly_name", ""),
                "assembly_method": ai.get("assembly_method", ""),
                "sequencing_tech": ai.get("sequencing_tech", ""),
                "annotation_method": ann.get("method", ""),
                "annotation_pipeline": ann.get("pipeline", ""),
                "annotation_release_date": ann.get("release_date", ""),
                "annotation_software_version": str(ann.get("software_version", "") or ""),
                "checkm_marker_set": cm.get("checkm_marker_set", ""),
                "checkm_marker_set_rank": cm.get("checkm_marker_set_rank", ""),
                "checkm_version": cm.get("checkm_version", ""),
                "checkm_completeness_percentile": str(cm.get("completeness_percentile", "") or ""),
                "genome_coverage": str(stats.get("genome_coverage", "") or ""),
                "contig_l50": str(stats.get("contig_l50", "") or ""),
                "scaffold_n50": str(stats.get("scaffold_n50", "") or ""),
                "number_of_scaffolds": str(stats.get("number_of_scaffolds", "") or ""),
                "ani_best_match_organism": ani_match.get("organism_name", ""),
                "ani_best_match_value": str(ani_match.get("ani", "") or ""),
                "ani_match_status": (r.get("average_nucleotide_identity") or {}).get("match_status", ""),
                "source_database": r.get("source_database", ""),
                "bioproject_title": bioproject_title,
                "paired_assembly": (r.get("paired_accession") or ""),
                "current_accession": r.get("current_accession", ""),
            })
            writer.writerow(row)
            rows_written += 1

    return rows_written > 0


def _read_atb_tier_counts(scheme_dir: Path, species: str) -> dict:
    """Return {pass_count, warn_count, fail_count} from the engine's
    atb_pass/warn/fail.csv.gz files, when present. These tally how many
    All-The-Bacteria assemblies fall into each tier under the published
    thresholds — surfaced on the species page intro."""
    out: dict = {}
    for tier in ("pass", "warn", "fail"):
        n = _count_gz_rows(scheme_dir / f"{species}_atb_{tier}.csv.gz")
        if n is not None:
            out[f"{tier}_count"] = n
    return out


def _read_counts_from_summary(scheme_dir: Path) -> tuple[int, int]:
    """First row of summary.csv carries the per-metric `count` and
    `refseq_count`; all rows should agree but we take the max to be safe.
    Returns (genome_count, refseq_count); zeros if summary.csv absent.
    """
    p = scheme_dir / "summary.csv"
    if not p.exists():
        return 0, 0
    g_max, r_max = 0, 0
    try:
        with open(p, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    g_max = max(g_max, int(float(row.get("count") or 0)))
                except (TypeError, ValueError):
                    pass
                try:
                    r_max = max(r_max, int(float(row.get("refseq_count") or 0)))
                except (TypeError, ValueError):
                    pass
    except OSError:
        return 0, 0
    return g_max, r_max


_METRICS_FOR_PLOTS = (
    "GC_Content", "Completeness_Specific", "Contamination",
    "Genome_Size", "Total_Coding_Sequences", "N50",
)


def _discover_plot_inventory(species: str, scheme: str, scheme_dir: Path) -> dict:
    """Build the manifest `plots` dict by inspecting filenames present in
    the scheme directory. Replaces the prefix-matching brittleness called
    out in WORKPLAN §0."""
    plots: dict = {}
    rel_prefix = f"{species}/{scheme}"
    for m in _METRICS_FOR_PLOTS:
        hist = scheme_dir / f"{m}_refseq_histogram_kde.png"
        qq = scheme_dir / f"{m}_refseq_qqplot.png"
        if hist.exists() or qq.exists():
            entry: dict = {}
            if hist.exists():
                entry["histogram_kde"] = f"{rel_prefix}/{hist.name}"
            if qq.exists():
                entry["qqplot"] = f"{rel_prefix}/{qq.name}"
            plots[m] = entry
    cds = scheme_dir / f"{species}_CDS_vs_Genome_Size.png"
    if cds.exists():
        plots["CDS_vs_Genome_Size"] = f"{rel_prefix}/{cds.name}"
    return plots


def _discover_filtered_plots(scheme_dir: Path) -> list[str]:
    sub = scheme_dir / "filtered_plots"
    if not sub.exists():
        return []
    return sorted(f.name for f in sub.iterdir() if f.is_file() and f.suffix.lower() == ".png")


def _find_sidecar(scheme_dir: Path, species: str, scheme: str, *candidates: str) -> str | None:
    """Return the first candidate filename that exists in scheme_dir,
    formatted as the {species}/{scheme}/{filename} path the frontend uses."""
    for name in candidates:
        if (scheme_dir / name).exists():
            return f"{species}/{scheme}/{name}"
    return None


def _derive_scheme_data_impl(species: str, scheme: str) -> dict:
    """Assemble the scheme_data dict from filesystem state. Equivalent
    shape to the per-scheme block website_summary.json used to carry,
    but each field is derived fresh from the on-disk per-species files
    so there's no stale-summary drift."""
    scheme_dir = SPECIES_ROOT / species / scheme
    genome_count, refseq_count = _read_counts_from_summary(scheme_dir)

    refseq_archive = None
    for ext in ("csv.xz", "csv.gz"):
        cand = scheme_dir / f"{species}_refseq_genomes.{ext}"
        if cand.exists():
            refseq_archive = cand.name
            break

    assembly_stats = None
    for ext in ("parquet", "csv.gz", "csv.xz"):
        cand = scheme_dir / f"{species}_assembly_stats.{ext}"
        if cand.exists():
            assembly_stats = cand.name
            break

    high_quality = _find_sidecar(
        scheme_dir, species, scheme,
        f"{species}_high_quality_genomes.csv.xz",
        f"{species}_high_quality_genomes.csv.gz",
    )
    filtered_out = _find_sidecar(
        scheme_dir, species, scheme,
        f"{species}_filtered_out_genomes.csv.xz",
        f"{species}_filtered_out_genomes.csv.gz",
    )
    atb_pass = _find_sidecar(scheme_dir, species, scheme, f"{species}_atb_pass.csv.gz")
    atb_warn = _find_sidecar(scheme_dir, species, scheme, f"{species}_atb_warn.csv.gz")
    atb_fail = _find_sidecar(scheme_dir, species, scheme, f"{species}_atb_fail.csv.gz")
    metrics_csv = (
        f"{species}/{scheme}/{species}_metrics.csv"
        if (scheme_dir / f"{species}_metrics.csv").exists()
        else None
    )
    species_json_name = (
        f"{species}.json" if (scheme_dir / f"{species}.json").exists() else None
    )

    return {
        "scheme": scheme,
        "species": species,
        "genome_count": genome_count,
        "refseq_genome_count": refseq_count,
        "plots": _discover_plot_inventory(species, scheme, scheme_dir),
        "filtered_plot_files": _discover_filtered_plots(scheme_dir),
        "has_cds_plot": (scheme_dir / f"{species}_CDS_vs_Genome_Size.png").exists(),
        "species_json_filename": species_json_name,
        "refseq_archive_filename": refseq_archive,
        "assembly_stats_filename": assembly_stats,
        "metrics": {
            "species_metrics": metrics_csv,
            "high_quality_genomes": high_quality,
            "filtered_out_genomes": filtered_out,
            "atb_pass": atb_pass,
            "atb_warn": atb_warn,
            "atb_fail": atb_fail,
        },
        "summaries": {
            # Truthy = the underlying file exists. _sidecar() in
            # build_manifest() consumes this dotted key.
            "summary": (scheme_dir / "summary.csv").exists(),
        },
        "engine_flags": read_engine_flags(scheme_dir),
        "tier_counts": _read_atb_tier_counts(scheme_dir, species),
        # thresholds is populated by build_manifest() from
        # read_metrics_csv(); no longer carried in this dict.
    }


def derive_scheme_data(species: str, scheme: str) -> dict:
    return _derive_scheme_data_impl(species, scheme)


def discover_genus_plots() -> dict[str, dict]:
    """Walk public/static/genus/ for `metric_range_*.png` files (or a
    `plots/` subdirectory). Returns {Genus: {plots: [...] | subdir_plots: [...]}}.
    """
    out: dict[str, dict] = {}
    root = PUBLIC / "static" / "genus"
    if not root.exists():
        return out
    for gdir in sorted(root.iterdir()):
        if not gdir.is_dir():
            continue
        plots_subdir = gdir / "plots"
        if plots_subdir.exists() and plots_subdir.is_dir():
            files = sorted(
                f.name for f in plots_subdir.iterdir()
                if f.is_file() and f.suffix.lower() == ".png"
            )
            if files:
                out[gdir.name] = {"subdir_plots": files}
                continue
        files = sorted(
            f.name for f in gdir.iterdir()
            if f.is_file() and f.suffix.lower() == ".png"
        )
        if files:
            out[gdir.name] = {"plots": files}
    return out


def write_slim_website_summary(
    pairs: dict[str, list[str]],
    preferred: dict[str, str | None],
    genera: dict[str, dict],
    last_updated: str,
) -> None:
    """Slim website_summary.json — registry only. Per-scheme data lives in
    per-species manifest.json now."""
    species_block = {
        sp: {
            "qc_schemes": pairs[sp],
            "preferred_qc_scheme": preferred.get(sp),
        }
        for sp in sorted(pairs)
    }
    MANIFEST.write_text(
        json.dumps({
            "schema_version": SCHEMA_VERSION,
            "last_updated": last_updated,
            "species": species_block,
            "genera": genera,
        }, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def write_summary_csvs(manifests: list[dict]) -> tuple[int, int]:
    """Regenerate public/static/summary/species_counts.csv and the
    cross-species summary_statistics.csv from per-species manifests.

    species_counts is intentionally richer than the old shape: now
    carries genome / RefSeq / non-RefSeq counts, engine severity flag,
    and PASS/WARN/FAIL tier counts. The legacy `filtered_out_count`
    column is dropped (engine doesn't reliably emit it).

    summary_statistics.csv is the cross-species roll-up of per-species
    summary.csv content. Rebuilt here so it isn't stale from a long-
    retired sync_public.py run.
    """
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    # 1) species_counts.csv
    counts_path = SUMMARY_DIR / "species_counts.csv"
    preferred_by_sp: dict[str, dict] = {}
    for m in manifests:
        sp = m["species"]
        if sp not in preferred_by_sp:
            preferred_by_sp[sp] = m  # first occurrence; manifests are
                                     # built in sorted scheme order so v1.1
                                     # comes before v1.0 alphabetically and
                                     # that's wrong. Override below.
        # Take the manifest matching the preferred scheme if/when we find it.
        # The caller's loop visits both schemes; whichever has the higher
        # preference under PREFERRED_PRIORITY wins.
    # Re-pick the preferred manifest per species using PREFERRED_PRIORITY.
    scheme_rank = {sc: i for i, sc in enumerate(PREFERRED_PRIORITY)}
    chosen: dict[str, dict] = {}
    for m in manifests:
        sp = m["species"]
        cur = chosen.get(sp)
        if cur is None or scheme_rank.get(m["scheme"], 99) < scheme_rank.get(cur["scheme"], 99):
            chosen[sp] = m

    with open(counts_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # `non_refseq_count` is what the engine's summary.csv calls `count`
        # (the non-RefSeq subset). `refseq_count` is RefSeq. The total
        # dataset used to fit the reference distribution is their sum.
        w.writerow([
            "species", "scheme", "engine_severity",
            "total_genome_count", "non_refseq_count", "refseq_count",
            "pass_count", "warn_count", "fail_count",
        ])
        for sp in sorted(chosen):
            m = chosen[sp]
            c = m.get("counts") or {}
            eng = (m.get("warnings") or {}).get("engine") or {}
            non_refseq = c.get("genome_count") or 0
            refseq = c.get("refseq_count") or 0
            total = non_refseq + refseq
            w.writerow([
                sp.replace("_", " "),
                m["scheme"],
                eng.get("severity") or "",
                total, non_refseq, refseq,
                c.get("pass_count", "") if c.get("pass_count") is not None else "",
                c.get("warn_count", "") if c.get("warn_count") is not None else "",
                c.get("fail_count", "") if c.get("fail_count") is not None else "",
            ])

    # 2) summary_statistics.csv — copy each per-species summary.csv into
    # one flat file, prepending species + scheme to every row.
    stats_path = SUMMARY_DIR / "summary_statistics.csv"
    stats_rows = 0
    header_written = False
    with open(stats_path, "w", newline="", encoding="utf-8") as fout:
        for m in manifests:
            sp = m["species"]
            sc = m["scheme"]
            scheme_dir = SPECIES_ROOT / sp / sc
            summary = scheme_dir / "summary.csv"
            if not summary.exists():
                continue
            try:
                with open(summary, newline="", encoding="utf-8") as fin:
                    rows = list(csv.reader(fin))
            except OSError:
                continue
            if not rows:
                continue
            header, *body = rows
            if not header_written:
                fout.write(",".join(["species", "scheme", *header]) + "\n")
                header_written = True
            sp_label = sp.replace("_", " ")
            for row in body:
                if not row or not (row[0] or "").strip():
                    continue
                # Quote any cells containing commas — minimal-safety CSV
                def _esc(v: str) -> str:
                    if "," in v or '"' in v or "\n" in v:
                        return '"' + v.replace('"', '""') + '"'
                    return v
                fout.write(",".join(_esc(c) for c in [sp_label, sc, *row]) + "\n")
                stats_rows += 1

    return len(chosen), stats_rows


def write_redirects() -> None:
    """Cloudflare Pages _redirects: legacy paths -> /api/v2/. Static
    files (.csv, .json) get a 301; the legacy /static/api/v1/species/
    pattern with a path placeholder routes to the per-species manifest
    at the preferred scheme (best-effort)."""
    text = (
        "# Legacy aggregate endpoints — see /api/v2/\n"
        "/static/summary/filtered_metrics.csv   /api/v2/thresholds.csv   301\n"
        "/static/api/v1/thresholds.json         /api/v2/thresholds.json  301\n"
        "/static/api/v1/index.json              /api/v2/index.json       301\n"
    )
    (PUBLIC / "_redirects").write_text(text, encoding="utf-8")


def main() -> int:
    notes = load_species_notes()
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Discover (species, scheme) pairs from the filesystem rather than
    # the website_summary.json blob. The on-disk per-species files are
    # the source of truth; website_summary.json is now a derived
    # registry that this script writes at the end.
    pairs = discover_pairs()
    preferred = {sp: infer_preferred(schemes) for sp, schemes in pairs.items()}

    manifests: list[dict] = []
    n_low_genome = 0
    n_species_sep = 0
    n_enriched = 0
    skipped_empty: list[str] = []
    for sp in sorted(list(pairs)):
        kept_schemes: list[str] = []
        for scheme in pairs[sp]:
            scheme_dir = SPECIES_ROOT / sp / scheme
            if enrich_refseq_csv(scheme_dir, sp):
                n_enriched += 1
            scheme_data = derive_scheme_data(sp, scheme)
            summary_bounds = read_summary_csv(scheme_dir)
            metrics_bounds = read_metrics_csv(scheme_dir, sp)
            ns = notes_for(sp, scheme, notes)
            m = build_manifest(
                sp, scheme, scheme_data, summary_bounds, ns,
                generated_at, metrics_csv_bounds=metrics_bounds,
            )
            # Skip (species, scheme) pairs the engine couldn't fit — no
            # genomes, no published thresholds. Their directories stay
            # on disk (for the {Species}.json metadata) but they don't
            # appear in the registry, sitemap, /api/v2/index.json, or
            # any genus rollup, so the public-facing route 404s cleanly.
            has_genomes = (m.get("counts") or {}).get("genome_count", 0) > 0
            has_thresholds = any(
                t.get("final_lower") is not None or t.get("final_upper") is not None
                for t in (m.get("thresholds") or [])
            )
            if not has_genomes and not has_thresholds:
                skipped_empty.append(f"{sp}/{scheme}")
                continue
            kept_schemes.append(scheme)
            manifests.append(m)
            if m["warnings"]["low_genome"]:
                n_low_genome += 1
            if m["warnings"]["species_separation"]:
                n_species_sep += 1
        # Update the registry to drop the skipped schemes; drop the
        # species entirely if all its schemes were empty.
        if kept_schemes:
            pairs[sp] = kept_schemes
        else:
            del pairs[sp]
            preferred.pop(sp, None)
    # Recompute preferred for species where we dropped the previously-preferred scheme.
    for sp, schemes in pairs.items():
        if sp not in preferred or preferred[sp] not in schemes:
            preferred[sp] = infer_preferred(schemes)
    if skipped_empty:
        print(f"Skipped {len(skipped_empty)} empty (species, scheme) pair(s) from registry:")
        for x in skipped_empty[:5]:
            print(f"  - {x}")
        if len(skipped_empty) > 5:
            print(f"  ... and {len(skipped_empty) - 5} more")

    n_man = write_per_species_manifests(manifests)
    csv_rows, sp_count = write_aggregates_from_pairs(
        manifests, pairs, preferred, generated_at,
    )
    n_genus, genus_metric_rows = write_genus_csvs(manifests)
    priority_rows = write_priority_pathogens_csvs(manifests)
    counts_rows, stats_rows = write_summary_csvs(manifests)
    write_redirects()

    genera = discover_genus_plots()
    write_slim_website_summary(pairs, preferred, genera, generated_at)
    print(f"Recomputed warnings: low_genome={n_low_genome}, species_separation={n_species_sep}")
    print(f"Enriched {n_enriched} RefSeq CSVs with BioSample / assembly / ANI metadata")

    print(f"Wrote {n_man} per-(species, scheme) manifest.json files")
    print(f"Wrote /api/v2/thresholds.csv: {csv_rows} rows")
    print(f"Wrote /api/v2/thresholds.json: {sp_count} species")
    print(f"Wrote /api/v2/index.json: {sp_count} species")
    print(f"Wrote per-genus CSVs: {n_genus} genera, {genus_metric_rows} metric rows")
    for year, rows in sorted(priority_rows.items()):
        print(f"Wrote priority-pathogens CSV: who-{year}.csv ({rows} rows)")
    print(f"Wrote static/summary/species_counts.csv: {counts_rows} species")
    print(f"Wrote static/summary/summary_statistics.csv: {stats_rows} metric rows")
    print("Wrote public/_redirects (legacy aggregate URLs -> /api/v2/)")

    # Threshold-rationale YAML: serve from /api/v2/ so the methods page (and
    # any reviewer) can fetch the audit trail on-site rather than linking to
    # GitHub. The file is documentation; pipeline overrides live in the
    # engine via {Species}_metrics.csv `source: pinned`.
    rationale_src = REPO_ROOT / "content" / "threshold-rationale.yml"
    if rationale_src.exists():
        rationale_dst = API_DIR / "threshold-rationale.yml"
        rationale_dst.write_text(rationale_src.read_text(encoding="utf-8"), encoding="utf-8")
        print("Wrote /api/v2/threshold-rationale.yml")

    # Excel mirrors of every downloadable CSV. Soft dependency on openpyxl —
    # _csv_to_xlsx returns -1 and prints a Skipped line if the source is
    # missing or the library isn't installed.
    for csv_path, xlsx_path, sheet in (
        (API_DIR / "thresholds.csv",                API_DIR / "thresholds.xlsx",          "thresholds"),
        (API_DIR / "external" / "thresholds.csv",   API_DIR / "external" / "thresholds.xlsx", "external_thresholds"),
        (SUMMARY_DIR / "summary_statistics.csv",    SUMMARY_DIR / "summary_statistics.xlsx", "summary_statistics"),
        (SUMMARY_DIR / "species_counts.csv",        SUMMARY_DIR / "species_counts.xlsx",  "species_counts"),
    ):
        n = _csv_to_xlsx(csv_path, xlsx_path, sheet)
        if n >= 0:
            print(f"Wrote {xlsx_path.relative_to(PUBLIC).as_posix()}: {n} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
