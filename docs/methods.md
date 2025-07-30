# Methods

## Datasets

Criteria cutoffs were determined using a combination of standard statistical methods and machine learning techniques to identify outliers and establish robust QC thresholds. Two datasets were used for this purpose:

1. **Allthebacteria dataset:** The 2024-08 release comprised 2.4 million uniformly reprocessed genome assemblies, including taxonomic estimates aligned to the GTDB phylogeny. Pre-calculated "assembly stats" (N50, longest contig, total assembly length, GC content, number of contigs, and longest contig size) and CheckM results (contamination and completeness) were used. Taxonomic classification was based on Allthebacteria’s sylph (v0.5.1) results with the GTDB r214 database. Only species with more than 1,000 genome records (as defined by sylph) were included. For more information, see the [Allthebacteria documentation](https://allthebacteria.readthedocs.io/en/latest/).

2. **NCBI RefSeq complete genomes:** Complete genomes from RefSeq were used to compare metrics such as genome size, number of coding sequences, and GC content. Metadata was downloaded using the NCBI Datasets command-line tool, filtered for completeness, cached as JSON, and parsed for analysis.

## Outlier Detection and Filtering

To identify and remove potential outliers prior to downstream analyses, an unsupervised machine learning approach using the Isolation Forest algorithm was implemented. This method is well-suited for high-dimensional biological data and does not require labeled training examples.

The outlier filter was applied to features representing key genome quality and assembly metrics: total_length, GC_Content, N50, number (contigs), longest (contig length), Completeness_Specific, and Contamination. The scikit-learn (v1.6.1) `IsolationForest` implementation was used with a fixed random seed (random_state=42) for reproducibility. Each sample received an anomaly score, and was classified as either inlier (anomaly = 1) or outlier (anomaly = -1). Outlier-filtered datasets were retained in parallel with unfiltered data for comparative analyses. Source code for this process is available at [GenomeQC](https://github.com/happykhan/genomeqc).

## Statistical Analysis and Threshold Selection

Summary statistics (mean, standard deviation, quartiles, interquartile range) were calculated for genome quality metrics. Normality was assessed using the D’Agostino–Pearson test. For metrics without RefSeq values (e.g., N50, number of contigs), lower and upper bounds were set by applying Isolation Forest filtering, then selecting the 0.5th and 99.5th percentiles of the filtered data. For genome size and GC content, distributions were compared to RefSeq using the Kolmogorov–Smirnov test and Wasserstein distance. Final bounds were set as the most extreme values between RefSeq-derived limits and the 0.5th–99.5th percentile range of SRA genomes after filtering. Histograms were generated to visualize comparative distributions.
