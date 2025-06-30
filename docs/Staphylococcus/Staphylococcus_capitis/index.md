# *Staphylococcus capitis*

This is the GenomeQC page for *Staphylococcus capitis*. For detailed methods on how these thresholds were calculated, please see [Methods](/methods).
The suggested thresholds are: 

| metric                 | lower_bounds   | upper_bounds   |
|:-----------------------|:---------------|:---------------|
| N50                    | 39000.0        |                |
| no_of_contigs          |                | 150.0          |
| GC_Content             | 32.0           | 34.0           |
| Completeness           | 98.0           |                |
| Contamination          |                | 1.0            |
| Total_Coding_Sequences | 2200.0         | 2700.0         |
| Genome_Size            | 2300000.0      | 2800000.0      |

[Download metrics CSV](/Staphylococcus/Staphylococcus_capitis/Staphylococcus_capitis_metrics.csv){.md-button}


These thresholds are based on **0** genomes from RefSeq and **1612** genomes from ATB / SRA.

These thresholds were applied to all the bacteria dataset, which resulted in removing **67** and retaining **1545**.
The list of genomes retained (i.e. high quality) and the list of genomes rejected (filtered) can be downloaded below. 


## Summary Tables
These tables provide a summary of the distribution of each metric, including SDeviation, Mean, Median, and Percentiles.

[Download full summary tables](/Staphylococcus/Staphylococcus_capitis/summary.csv)

[Download simple summary tables](/Staphylococcus/Staphylococcus_capitis/selected_summary.csv)

## Plots and Visualizations

This plot is a histogram comparing genome sizes between the SRA and RefSeq datasets. Each bar represents the density of genomes within a specific size range for both datasets. By comparing the shapes and positions of the bars, you can identify differences in genome size distributions, such as shifts, peaks, or outliers. This visualization helps reveal whether one dataset tends to have larger or smaller genomes, or if there are notable differences in variability or coverage between SRA and RefSeq.

![Genome Size Distribution](Genome_Size_refseq_histogram_kde.png)

This plot is a QQ (quantile-quantile) plot, which compares the distribution of the SRA data with RefSeq. Points falling along the diagonal line indicate that the data follows the expected distribution. Deviations from the line suggest departures from normality, such as skewness or outliers. This helps assess whether the dataset is consistently distributed or if there are systematic differences.

![Genome Size QQ Plot](Genome_Size_refseq_qqplot.png)

This plot shows the relationship between the number of coding sequences (CDS) and genome size. It helps to visualize how genome size correlates with the number of genes. This should be linear - as the genome size increases, the number of coding sequences should also increase. Any secondary trend lines or non-linear behaviour indicates bone fide seperate populations within the retained genomes, or some remaining contaminant. 

![CDS vs Genome Size](Staphylococcus_capitis_CDS_vs_Genome_Size.png

### Additional Plots

These plots provide additional insights into the genome characteristics:

- [GC Content Histogram](Staphylococcus_capitis_GC_Content_refseq_histogram_kde.png)
- [GC Content QQ Plot](Staphylococcus_capitis_GC_Content_refseq_qqplot.png)
- [Total Coding Sequences Histogram](Staphylococcus_capitis_Total_Coding_Sequences_refseq_histogram_kde.png)
- [Total Coding Sequences QQ Plot](Staphylococcus_capitis_Total_Coding_Sequences_refseq_qqplot.png)
- [Genome Size Histogram](Staphylococcus_capitis_Genome_Size_refseq_histogram_kde.png)
- [Genome Size QQ Plot](Staphylococcus_capitis_Genome_Size_refseq_qqplot.png)
## Illustrating the filtering process
These plots illustrate the data, pre and post filtering to demostrate what type of outliers have been removed. While this was applied to metric, we will demonstrate using total assembly length and N50.
N50 vs total length for all genomes in the dataset.

![ALL Total Length vs N50](Staphylococcus_capitis_all_total_length_N50.png)

N50 vs total length for genomes in the dataset, coloured according to whether they are an anomaly or not.

![Sampled Total Length vs N50](Staphylococcus_capitis_sample_total_length_N50.png)

N50 vs total length post filtering on the dataset.

![Filtered Total Length vs N50](Staphylococcus_capitis_filt_total_length_N50.png)

### Additional Plots

These plots provide additional insights into the genome characteristics:

- [N50 vs number of contigs, all genomes](Staphylococcus_capitis_all_N50_number.png)
- [N50 vs number of contigs, sampled genomes](Staphylococcus_capitis_sample_N50_number.png)
- [N50 vs number of contigs, filtered genomes](Staphylococcus_capitis_filt_N50_number.png)
- [GC Content vs Total Length, all genomes](Staphylococcus_capitis_all_total_length_GC_Content.png)
- [GC Content vs Total Length, sampled genomes](Staphylococcus_capitis_sample_total_length_GC_Content.png)
- [GC Content vs Total Length, filtered genomes](Staphylococcus_capitis_filt_total_length_GC_Content.png)
- [Longest Contig vs Total Length, all genomes](Staphylococcus_capitis_all_total_length_longest.png)
- [Longest Contig vs Total Length, sampled genomes](Staphylococcus_capitis_sample_total_length_longest.png)
- [Longest Contig vs Total Length, filtered genomes](Staphylococcus_capitis_filt_total_length_longest.png)
