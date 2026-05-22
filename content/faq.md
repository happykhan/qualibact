# Frequently Asked Questions

## What is QualiBact?
QualiBact is a community-driven framework for species-specific quality control of bacterial genome assemblies. We curate thresholds, visualizations, and reference datasets to help labs adopt consistent QC standards.

## Who maintains the thresholds?
Thresholds are derived from the QualiBact pipeline (typically the `qualibact-v1.0` scheme) and reviewed by the CGPS team plus community contributors. Each release lists the scheme version used for every species.

## How often is QualiBact updated?
We update the dataset whenever we finish a new curation cycle—usually every few months, or sooner when large data contributions arrive. Check the Summary page or release notes for the most recent timestamp.

## How do I request a new species?
See the [Organism Requests](/organism-requests) page for the current queue and submission instructions. If your species is missing, email `nabil.alikhan@cgps.group` with relevant details so we can prioritize it.

## Can I contribute my own thresholds or data?
Yes! The [Contributing](/contributing) page outlines two workflows: submitting raw assembly metrics so we can run QualiBact, or sharing your own validated thresholds for inclusion. Contributors receive credit in releases and publications.

## What formats do you support for downloads?
All tabular results are provided as CSV (often compressed as `.csv.xz`). Plots are PNG files. The Next.js app also includes manifests in JSON—such as `refseq_metrics.json`—to help downstream tooling discover assets.

For programmatic access without scraping the site, the `/api/v2/` endpoints expose flat threshold tables:

- [`/api/v2/thresholds.csv`](https://static.qualibact.org/api/v2/thresholds.csv) — one row per (species, scheme, metric)
- [`/api/v2/thresholds.json`](https://static.qualibact.org/api/v2/thresholds.json) — nested JSON
- [`/api/v2/index.json`](https://static.qualibact.org/api/v2/index.json) — registry of species + schemes + preferred scheme

## Can I query QualiBact from Claude / Cursor / other LLM clients?

Yes. QualiBact runs an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server at **`https://mcp.qualibact.org/mcp`**. Any MCP-aware client can call it directly instead of web-searching for thresholds.

To wire it into Claude Desktop, Claude Code, Cursor, etc., add one entry to your MCP config file (location varies by client — see your client's docs):

```jsonc
{
  "mcpServers": {
    "qualibact": {
      "transport": {
        "type": "http",
        "url": "https://mcp.qualibact.org/mcp"
      }
    }
  }
}
```

Reload the client and five tools become available:

| Tool | What it returns |
|------|------------------|
| `list_species(genus?)` | All species + preferred scheme + every scheme that has data |
| `list_schemes()` | Every QC scheme + species count |
| `get_thresholds(species, scheme?, metric?)` | The 4-bound (FAIL_lower / WARN_lower / WARN_upper / FAIL_upper) rows |
| `list_pinned_thresholds(species?)` | All hand-pinned expert overrides with rationale |
| `get_pinned_threshold(species, scheme, metric)` | Rationale for one specific pin |

Once it's wired in, asking *"What's the QualiBact N50 floor for E. coli?"* gets you the authoritative answer (`FAIL_lower = 20000`, `WARN_lower = 23000`) instead of an educated guess.

The MCP is read-only, public (no auth), and read-through-caches the same `/api/v2/` blobs above.

## Where can I report issues or bugs?
Open an issue on the [QualiBact GitHub repository](https://github.com/cgps-group/qualibact) with as much context as possible (species, scheme, error logs). You can also email the maintainers if the problem involves sensitive data.

## Are there related tools / cross-references for genome size?
NCBI's [GenBank genome-size-check](https://www.ncbi.nlm.nih.gov/genbank/genome-size-check/) publishes daily-updated expected genome-size ranges per species (taxid → min / max / expected) at <https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/species_genome_size.txt.gz>. It covers ~6,000 taxa and is a good independent sanity check. QualiBact's `Genome_Size` thresholds are typically tighter than NCBI's `min`–`max` range (we reject partial/incomplete assemblies that NCBI's range accommodates); for the species the two share, 95% of QualiBact bounds are within ±50% of NCBI's, and zero have *both* sides drift >50%.

For read-level QC (sequencing depth, contamination identity, heterozygosity) see [bactscout](https://github.com/cgps-group/bactscout) as the recommended companion tool — QualiBact operates on the assembled genome.

## Funding
QualiBact is supported by the National Institute for Health Research (NIHR) under grant number **NIHR133307**. The views expressed are those of the maintainers and contributors, and do not necessarily reflect those of the NIHR or the UK Department of Health and Social Care.
