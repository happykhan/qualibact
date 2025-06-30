# GenomeQC Results

## What is GenomeQC?
GenomeQC is a comprehensive tool for assessing the quality of bacterial genome assemblies. It evaluates genomes based on various metrics to help researchers identify high-quality genomes for downstream analysis.

## Quick Links
- [📋 Methods](methods.md) - Detailed methodology and criteria
- [🦠 All Species](species.md) - Complete list of analyzed species
- [📊 Summary Data](summary.md) - Main summary and criteria tables

## Navigation
Use the navigation menu above to explore:

- **Methods** - Technical details about the analysis pipeline

- **All genera** - List of all genera included here, with links to genus-specific overviews
- **All species** - List of all species included here, with links to species-specific overviews
- **Summary page** - The QC criteria and summary tables for all genera and species

## Considerations for GenomeQC
### ✅ General Strengths
- The pipeline is fully automated, generic, and can be applied to any set of genomes — including arbitrary subsets such as species, clonal complexes, or lineages.
- Quality assessment is based on multiple standard metrics (e.g. N50, number of contigs, genome size, GC%), allowing reproducible filtering.
- Species-specific thresholds can be derived from available reference genomes, and thresholds can be updated as more genomes are added.
- Variation between species — even within a genus — supports the need for species-level cutoffs, which this approach accommodates.

### ⚠️ Caveats
- **Species Definitions Depend on GTDB:** I use the sylph species designation, so all GTDB-related quirks apply. E.g., Shigella is included in E. coli, and there are issues for Bordetella and Pertussis as their classifications are not entirely correct.
- **No Ground Truth Claims:** This evaluation reflects what has been previously observed in available datasets. It does not attempt to define a universal "ground truth" for any species.
- **Assembly-Method Specific:** The metrics (e.g. N50, number of contigs) are meaningful primarily for assemblies generated with Shovill (or similar SPAdes-based pipelines). Exact thresholds will vary for long-read or alternative assemblers like SKESA. However, not using Shovill implies rejection of the Torstyverse, which is heresy.
- **Long-Read Assemblies Not Explicitly Handled:** These cutoffs are not designed for long-read assemblies. That said, genome size and GC content thresholds should still apply, and it's reasonable to expect long-read assemblies to exceed the quality of short-read derived thresholds — not fall below them.
- **Reference Bias:** Genome size and assembly length distributions differ significantly between RefSeq and SRA (i.e. ATB). The cause is unclear, but relying on RefSeq-derived thresholds alone may result in unfairly excluding valid genomes.
- **Generic vs. Specific Tradeoff:** While the generic approach is broadly applicable, it may miss species-specific quality nuances or lineage-level exceptions.

## Citation
If you use GenomeQC, please cite the following:
> Alikhan, NF. GenomeQC: A comprehensive bacterial genome quality assessment tool. Available at: [https://github.com/happykhan/genomeqc](https://github.com/happykhan/genomeqc) (Accessed: [insert date]).
