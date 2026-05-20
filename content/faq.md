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

## Where can I report issues or bugs?
Open an issue on the [QualiBact GitHub repository](https://github.com/cgps-group/qualibact) with as much context as possible (species, scheme, error logs). You can also email the maintainers if the problem involves sensitive data.

## Are there related tools / cross-references for genome size?
NCBI's [GenBank genome-size-check](https://www.ncbi.nlm.nih.gov/genbank/genome-size-check/) publishes daily-updated expected genome-size ranges per species (taxid → min / max / expected) at <https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/species_genome_size.txt.gz>. It covers ~6,000 taxa and is a good independent sanity check. QualiBact's `Genome_Size` thresholds are typically tighter than NCBI's `min`–`max` range (we reject partial/incomplete assemblies that NCBI's range accommodates); for the species the two share, 95% of QualiBact bounds are within ±50% of NCBI's, and zero have *both* sides drift >50%.

For read-level QC (sequencing depth, contamination identity, heterozygosity) see [bactscout](https://github.com/cgps-group/bactscout) as the recommended companion tool — QualiBact operates on the assembled genome.

## Funding
QualiBact is supported by the National Institute for Health Research (NIHR) under grant number **NIHR133307**. The views expressed are those of the maintainers and contributors, and do not necessarily reflect those of the NIHR or the UK Department of Health and Social Care.
