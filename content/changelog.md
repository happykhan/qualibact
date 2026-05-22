# Changelog

What's changed in QualiBact, by release date.

## 21 May 2026 — `qualibact-v1.1` launch + engine rev2

### 1. New scheme: `qualibact-v1.1` (expert-review overlay)

15 species now publish a v1.1 row alongside v1.0. v1.0 is the raw engine output; v1.1 is the expert-review layer with manually-pinned values and curated re-runs requested by the Nov 2025 community survey:

- **Adjusted thresholds** where experts pointed at specific values — e.g. *Campylobacter jejuni* assembly-size upper raised from 2.0 Mb to 2.1 Mb; *Neisseria meningitidis* tightened from 2.4 Mb to 2.3 Mb.
- **Curated re-runs** for species where the v1.0 reference set was noisy — e.g. *Achromobacter xylosoxidans* now incorporates 441 additional genomes beyond AllTheBacteria-2024-08.
- **Full hand-pinned audit trail** rendered at the bottom of the [v1.1 methods page](/methods/qualibact-v1.1/) — every override lists the metric, value, and rationale.

A species without a v1.1 row falls back to v1.0 automatically.

### 2. PASS / WARN / FAIL three-tier verdict system

The old single-FAIL boundary was too coarse. Each species page now shows a 4-bound view:

| Band | Lower percentile | Upper percentile |
|------|------------------|------------------|
| FAIL outside | 0.5 | 99.5 |
| WARN | 2.5 | 97.5 |

The WARN band lives between the FAIL and PASS lines — useful for flagging "unusual but not failing" assemblies. The bands are percentile-based on the post-Isolation-Forest species pool, not a ±buffer.

### 3. `/api/v2/` threshold API on R2

Programmatic consumers (SpecCheck, Kleborate, custom pipelines) can now fetch the 4-bound thresholds directly:

- [`/api/v2/thresholds.csv`](https://static.qualibact.org/api/v2/thresholds.csv) — flat CSV, one row per (species, scheme, metric)
- [`/api/v2/thresholds.json`](https://static.qualibact.org/api/v2/thresholds.json) — nested JSON
- [`/api/v2/thresholds.xlsx`](https://static.qualibact.org/api/v2/thresholds.xlsx) — Excel
- [`/api/v2/index.json`](https://static.qualibact.org/api/v2/index.json) — registry of species + schemes + preferred scheme
- [`/api/v2/threshold-rationale.yml`](https://static.qualibact.org/api/v2/threshold-rationale.yml) — every hand-pinned override + reason

Served from Cloudflare R2 at `static.qualibact.org` — fast, public, no auth.

### 4. Other surfaced bits on the species page

- **Engine quality-flag banner** at the top of each species page when the engine itself flagged the reference dataset as having issues (low genome count, high contamination fraction, oversized references, wide GC range, etc.). Helps you judge whether to trust the published thresholds for that species.
- **PASS / WARN / FAIL genome lists** — three download buttons giving you the full AllTheBacteria-2024-08 set classified against the published thresholds, with per-metric reasons for any WARN or FAIL row.
- **Per-assembly inputs** — the engine input table (sample, N50, contig count, completeness, contamination, etc.) is now downloadable alongside the RefSeq calibration table.
- **Inline summary statistics** — distribution stats (mean, median, IQR, percentiles) for each metric are now collapsible inline on the species page rather than buried in a separate CSV.

### 5. MCP server

A read-only [Model Context Protocol](https://modelcontextprotocol.io) endpoint at **`mcp.qualibact.org/mcp`**. Add it to your Claude Desktop / Claude Code / Cursor MCP config and the LLM can call QualiBact tools directly:

- `list_species(genus?)`
- `list_schemes()`
- `get_thresholds(species, scheme?, metric?)`
- `list_pinned_thresholds(species?)`
- `get_pinned_threshold(species, scheme, metric)`

### Engine-side fixes (rev2)

The underlying `qualibact-engine` shipped a `v1.0-rev2` pipeline-bug fix alongside this release. The biggest behavioural change: **Contamination upper bounds** were materially loosened for most species — the old engine clipped them too aggressively. Genome_Size, GC_Content, Total_Coding_Sequences, and Completeness bounds are essentially unchanged (<10 % drift for >99 % of species).

If you'd been using QualiBact's Contamination upper bound in a pipeline, expect different numbers — re-pull from `/api/v2/thresholds.csv`.

---

_Older releases were ad-hoc and undated. This changelog starts here._
