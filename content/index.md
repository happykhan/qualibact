# QualiBact — Community-agreed bacterial genome assembly quality thresholds

## What is QualiBact?
QualiBact is a repository of community-agreed thresholds for assessing the quality of bacterial genome assemblies. We evaluate genomes using a set of standard metrics to help public-health laboratories and researchers identify high-quality assemblies for downstream analyses. The thresholds described here are implemented in [SpecCheck](https://github.com/cgps-group/speccheck/). Source code for this website is available at [QualiBact](https://github.com/cgps-group/qualibact).

We have developed an automated and consistent process for defining thresholds, `qualibact-engine`. This is the default method applied for many species. For a full description see the methods page for [`qualibact-v1.0`](/methods/qualibact-v1.0). The source code for the engine is available at [QualiBact-engine](https://github.com/cgps-group/qualibact-engine).

The repository also includes manually curated thresholds for certain species where the automated approach was insufficient.

QualiBact operates on assembled genomes. For complementary checks at the read level (species identification, contamination, coverage), we recommend [bactscout](https://github.com/cgps-group/bactscout) as a companion tool.

## What QualiBact is NOT

- A universal definition of genome quality  
- A replacement for manual curation in special cases  
- Tailored to long-read assemblies (though GC and genome size thresholds still apply)  
- A strict pass/fail system — thresholds are intended as *guidance*, not biological absolutes

## Quick Start: How to Use QualiBact

1. **Find your species** on the [species list](/species).  
2. **Review the thresholds** and summary metrics for your organism.  
3. **Apply thresholds** using [SpecCheck](https://github.com/cgps-group/speccheck/) or in your own analysis pipeline.  
4. **Request new species or improvements** via the [Requests page](/organism-requests).

## Who is QualiBact for?

- Public-health laboratories performing routine bacterial genomics  
- Researchers analysing genomic diversity, AMR, or phylogeny  
- Bioinformatics pipeline developers  
- Benchmarking and validation studies  
- Anyone who needs a consistent, species-aware QC framework

## Citation
If you use QualiBact, please cite the following:
> Alikhan, NF. Species specific quality control of bacterial de novo genome assemblies using QualiBact. Available at: [https://github.com/cgps-group/qualibact](https://github.com/cgps-group/qualibact) (Accessed: [insert date]).

There maybe additional citations for specific methods used, which will be mentioned on the relevant QC scheme pages.