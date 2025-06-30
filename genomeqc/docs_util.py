from rich.console import Console
from pathlib import Path


def create_methods_page(docs_dir):
    """Create a methods page explaining the GenomeQC pipeline"""
    # Force the docs_dir to be a Path object
    docs_dir = Path(docs_dir)
    methods_path = docs_dir / "methods.md"
    
    lines = [
        "# Methods\n",
        "## Datasets\n",
        "Criteria cutoffs were determined using a combination of standard statistical methods and machine learning techniques to identify outliers and establish robust QC thresholds. Two datasets were used for this purpose:\n",
        "1. **Allthebacteria dataset:** The 2024-08 release comprised 2.4 million uniformly reprocessed genome assemblies, including taxonomic estimates aligned to the GTDB phylogeny. Pre-calculated \"assembly stats\" (N50, longest contig, total assembly length, GC content, number of contigs, and longest contig size) and CheckM results (contamination and completeness) were used. Taxonomic classification was based on Allthebacteria’s sylph (v0.5.1) results with the GTDB r214 database. Only species with more than 1,000 genome records (as defined by sylph) were included. For more information, see the [Allthebacteria documentation](https://allthebacteria.readthedocs.io/en/latest/).\n",
        "2. **NCBI RefSeq complete genomes:** Complete genomes from RefSeq were used to compare metrics such as genome size, number of coding sequences, and GC content. Metadata was downloaded using the NCBI Datasets command-line tool, filtered for completeness, cached as JSON, and parsed for analysis.\n",
        "## Outlier Detection and Filtering\n",
        "To identify and remove potential outliers prior to downstream analyses, an unsupervised machine learning approach using the Isolation Forest algorithm was implemented. This method is well-suited for high-dimensional biological data and does not require labeled training examples.\n",
        "The outlier filter was applied to features representing key genome quality and assembly metrics: total_length, GC_Content, N50, number (contigs), longest (contig length), Completeness_Specific, and Contamination. The scikit-learn (v1.6.1) `IsolationForest` implementation was used with a fixed random seed (random_state=42) for reproducibility. Each sample received an anomaly score, and was classified as either inlier (anomaly = 1) or outlier (anomaly = -1). Outlier-filtered datasets were retained in parallel with unfiltered data for comparative analyses. Source code for this process is available at [GenomeQC](https://github.com/happykhan/genomeqc).\n",
        "## Statistical Analysis and Threshold Selection\n",
        "Summary statistics (mean, standard deviation, quartiles, interquartile range) were calculated for genome quality metrics. Normality was assessed using the D’Agostino–Pearson test. For metrics without RefSeq values (e.g., N50, number of contigs), lower and upper bounds were set by applying Isolation Forest filtering, then selecting the 0.5th and 99.5th percentiles of the filtered data. For genome size and GC content, distributions were compared to RefSeq using the Kolmogorov–Smirnov test and Wasserstein distance. Final bounds were set as the most extreme values between RefSeq-derived limits and the 0.5th–99.5th percentile range of SRA genomes after filtering. Histograms were generated to visualize comparative distributions.\n"
    ]
    
    methods_path.write_text("\n".join(lines))
    console = Console()

def create_index_page(docs_dir: Path):
    """Create an index page linking to all genera"""
    # Force the docs_dir to be a Path object
    docs_dir = Path(docs_dir)
    index_path = docs_dir / "index.md"
    
    lines = [
        "# GenomeQC Results\n",
        "## What is GenomeQC?",
        "GenomeQC is a comprehensive tool for assessing the quality of bacterial genome assemblies. It evaluates genomes based on various metrics to help researchers identify high-quality genomes for downstream analysis.\n",

        "## Quick Links",
        "- [📋 Methods](methods.md) - Detailed methodology and criteria",
        "- [🦠 All Species](species.md) - Complete list of analyzed species",
        "- [📊 Summary Data](summary.md) - Main summary and criteria tables\n",

        "## Navigation",
        "Use the navigation menu above to explore:\n",
        "- **Methods** - Technical details about the analysis pipeline\n",
        "- **All genera** - List of all genera included here, with links to genus-specific overviews",
        "- **All species** - List of all species included here, with links to species-specific overviews",
        "- **Summary page** - The QC criteria and summary tables for all genera and species\n",        

        "## Considerations for GenomeQC",
        "### ✅ General Strengths",
        "- The pipeline is fully automated, generic, and can be applied to any set of genomes — including arbitrary subsets such as species, clonal complexes, or lineages.",
        "- Quality assessment is based on multiple standard metrics (e.g. N50, number of contigs, genome size, GC%), allowing reproducible filtering.",
        "- Species-specific thresholds can be derived from available reference genomes, and thresholds can be updated as more genomes are added.",
        "- Variation between species — even within a genus — supports the need for species-level cutoffs, which this approach accommodates.\n",
        "### ⚠️ Caveats",
        "- **Species Definitions Depend on GTDB:** I use the sylph species designation, so all GTDB-related quirks apply. E.g., Shigella is included in E. coli, and there are issues for Bordetella and Pertussis as their classifications are not entirely correct.",
        "- **No Ground Truth Claims:** This evaluation reflects what has been previously observed in available datasets. It does not attempt to define a universal \"ground truth\" for any species.",
        "- **Assembly-Method Specific:** The metrics (e.g. N50, number of contigs) are meaningful primarily for assemblies generated with Shovill (or similar SPAdes-based pipelines). Exact thresholds will vary for long-read or alternative assemblers like SKESA. However, not using Shovill implies rejection of the Torstyverse, which is heresy.",
        "- **Long-Read Assemblies Not Explicitly Handled:** These cutoffs are not designed for long-read assemblies. That said, genome size and GC content thresholds should still apply, and it's reasonable to expect long-read assemblies to exceed the quality of short-read derived thresholds — not fall below them.",
        "- **Reference Bias:** Genome size and assembly length distributions differ significantly between RefSeq and SRA (i.e. ATB). The cause is unclear, but relying on RefSeq-derived thresholds alone may result in unfairly excluding valid genomes.",
        "- **Generic vs. Specific Tradeoff:** While the generic approach is broadly applicable, it may miss species-specific quality nuances or lineage-level exceptions.\n",
        "## Citation",
        "If you use GenomeQC, please cite the following:",
        "> Alikhan, NF. GenomeQC: A comprehensive bacterial genome quality assessment tool. Available at: [https://github.com/happykhan/genomeqc](https://github.com/happykhan/genomeqc) (Accessed: [insert date]).\n"
    ]
    
    index_path.write_text("\n".join(lines))

def write_mkdocs_yml():
    mkdocs_yml = f"""site_name: GenomeQC Results
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - content.code.copy
    - content.tabs.link
    - navigation.top
  palette:
    - scheme: default
      primary: blue
      accent: blue
markdown_extensions:
  - admonition
  - codehilite
  - toc:
      permalink: true
  - attr_list
  - md_in_html
  - tables

nav:
  - Home: index.md
  - Methods: methods.md
  - All Species: species.md
  - Summary: summary.md
"""

    Path("mkdocs.yml").write_text(mkdocs_yml)    