# QualiBact

Community-curated, species-specific quality control thresholds for bacterial de novo genome assemblies.

**Website:** https://qualibact.org

This repository is the Next.js website. It renders thresholds and per-species statistics produced upstream by [qualibact-engine](https://github.com/happykhan/qualibact-engine) (which compares AllTheBacteria assemblies against NCBI RefSeq genomes, applies Isolation-Forest outlier filtering, and emits the FINAL/WARN bounds plus distribution stats).

Downstream, the published thresholds are consumed by [SpecCheck](https://github.com/happykhan/speccheck) — a CLI that flags assemblies that fall outside their species' QualiBact band.

## What lives where

- `https://qualibact.org/` — the live site (Cloudflare Pages, custom domain).
- `https://qualibact.org/api/v2/` — public threshold API: `thresholds.csv` / `.json` / `.xlsx`, `index.json`, `threshold-rationale.yml`.
- `https://qualibact.org/{Genus}/{Species}/{scheme}/` — per-species page (thresholds, summary stats, PASS/WARN/FAIL ATB genome lists, refseq calibration set, distribution plots).
- `https://qualibact.org/methods/qualibact-v1.0/` — engine pipeline + percentile-band methodology.
- `https://qualibact.org/methods/qualibact-v1.1/` — expert-feedback overrides layered on top of v1.0.

## QC schemes currently published

- **`qualibact-v1.0`** — raw engine output (no manual overrides). 307 species.
- **`qualibact-v1.1`** — expert-review layer on top of v1.0: pinned thresholds requested by domain experts, plus a small number of curated re-runs on different reference sets. 15 species (only species with an actual change ship a v1.1 row; everything else falls back to v1.0 automatically).
- **`REFSEQ-QC-v1`** — RefSeq-only baseline. 10 species.

## Tech stack

- Next.js 16 (App Router, static export) + React 19 + TypeScript.
- Tailwind CSS 3 with `next-themes` (light default).
- MDX content in `content/`.
- Python ingest pipeline (`scripts/build_manifests.py`).
- Cloudflare Pages hosting; Cloudflare R2 for bulk static assets (PNGs, ATB tier CSVs, refseq archives, per-assembly stats).

## Local development

```bash
npm install
npm run dev              # http://localhost:3000
npm run build            # static export to ./out/
npm run lint             # ESLint
npm run build-manifests  # rebuild per-(species, scheme) manifest.json + /api/v2/ aggregates
```

A full local build needs engine output staged under `public/static/species/{Species}/{scheme}/`. The committed tree ships only the build-time-required slice (`manifest.json` + `summary.csv` per pair, plus `/api/v2/` and `/static/summary/` aggregates); bulk plots / CSVs live on R2.

## Contributing

PRs welcome. Major contributions to source code, manuscript development, metric validation, or providing additional data for calibrating quality thresholds qualify for authorship on publications.

- Threshold revision requests for a specific species → file via the **Requests** page on the website or open an issue.
- New experts willing to review a species' thresholds — see the **Contributors** page; the survey + sign-off process is described there.

## Citation

A QualiBact publication is in preparation. In the meantime, please link to https://qualibact.org and cite the relevant scheme version (e.g. `qualibact-v1.0` or `qualibact-v1.1`) when referencing a specific bound.
