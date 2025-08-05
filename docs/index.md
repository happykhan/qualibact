# QualiBact Results

## What is QualiBact?
QualiBact is a set of thresholds assessing the quality of bacterial genome assemblies. We have evaluated genomes based on various metrics to help researchers identify high-quality genomes for downstream analysis. These thresholds described here are implemented in [SpecCheck](https://github.com/happykhan/speccheck/). Source code for this process is available at [QualiBact](https://github.com/happykhan/qualibact).

## Quick Links
- [📋 Methods](methods.md) - Detailed methodology and criteria
- [🦠 All Species](species.md) - Complete list of analyzed species
- [📊 Summary Data](summary.md) - Main summary and criteria tables

## Navigation
Use the navigation menu above to explore:

- **Methods** - Technical details about the analysis pipeline

- **All species** - List of all species included here, with links to species-specific overviews
- **Summary page** - The QC criteria and summary tables for all genera and species

## Considerations for QualiBact
### ✅ General Strengths
- The pipeline is fully automated, generic, and can be applied to any set of genomes — including arbitrary subsets such as species, clonal complexes, or lineages.
- Quality assessment is based on multiple standard metrics (e.g. N50, number of contigs, genome size, GC%), allowing reproducible filtering.
- Species-specific thresholds can be derived from available reference genomes, and thresholds can be updated as more genomes are added.
- Variation between species — even within a genus — supports the need for species-level cutoffs, which this approach accommodates.

- Variation between SRA and Refseq: We have observed that Genome size and assembly length distributions differ significantly between RefSeq and SRA (i.e. ATB). The cause is unclear, but relying on RefSeq-derived thresholds alone may result in unfairly excluding valid genomes. This approach combines both datasets to ensure a more inclusive and representative set of thresholds.

### ⚠️ Caveats
- **Species Definitions Depend on GTDB:** This tools uses Sylph for species designation, so all GTDB-related quirks apply. E.g., Shigella spp. is included in E. coli, and there are issues separating Burkholderia mallei from Burkholderia pseudomallei and Bordetella pertussis/Bordetella parapertussis from Bordetella bronchiseptica.
- **No Ground Truth Claims:** This evaluation reflects what has been previously observed in available datasets. It does not attempt to define a universal "ground truth" for any species.
- **Assembly-Method Specific:** The metrics (e.g. N50, number of contigs) are meaningful primarily for assemblies generated with Shovill (or similar SPAdes-based pipelines). Exact thresholds will vary for long-read or alternative assemblers like SKESA. However, not using Shovill implies rejection of the Torstyverse, which is heresy.
- **Long-Read Assemblies Not Explicitly Handled:** These cutoffs are not designed for long-read assemblies. That said, genome size and GC content thresholds should still apply, and it's reasonable to expect long-read assemblies to exceed the quality of short-read derived thresholds — not fall below them.
- **Generic vs. Specific Tradeoff:** While the generic approach is broadly applicable, it may miss species-specific quality nuances or lineage-level exceptions.

## Citation
If you use QualiBact, please cite the following:
> Alikhan, NF. Species specific quality control of bacterial de novo genome assemblies using QualiBact. Available at: [https://github.com/happykhan/qualibact](https://github.com/happykhan/qualibact) (Accessed: [insert date]).
