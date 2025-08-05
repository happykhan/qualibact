# *Paenibacillus larvae*

This is the QualiBact page for *Paenibacillus larvae*. For detailed methods on how these thresholds were calculated, please see [Methods](../../methods.md).
The suggested thresholds are: 

| metric                 | lower_bounds   | upper_bounds   |
|:-----------------------|:---------------|:---------------|
| N50                    | 21000.0        |                |
| no_of_contigs          |                | 800.0          |
| GC_Content             | 43.0           | 46.0           |
| Completeness           | 85.0           |                |
| Contamination          |                | 4.0            |
| Total_Coding_Sequences | 3800.0         | 5300.0         |
| Genome_Size            | 3600000.0      | 4800000.0      |

[Download metrics CSV](Paenibacillus_larvae_metrics.csv){.md-button}


These thresholds are based on **12** genomes from RefSeq and **1164** genomes from ATB / SRA.

These thresholds were applied to all the bacteria dataset, which resulted in removing **98** and retaining **1066**.
The list of genomes retained (i.e. high quality) and the list of genomes rejected (filtered) can be downloaded below. These files are in `.xz` format. The rejected genomes file, also includes the reason why.

[Download high quality genomes list](Paenibacillus_larvae_high_quality_genomes.csv.xz)


[Download rejected genomes list](Paenibacillus_larvae_filtered_out_genomes.csv.xz)



## Summary Tables
These tables provide a summary of the distribution of each metric, including SDeviation, Mean, Median, and Percentiles.

[Download full summary tables](summary.csv)

[Download simple summary tables](selected_summary.csv)

## Plots and Visualizations

This plot is a histogram comparing genome sizes between the SRA and RefSeq datasets. Each bar represents the density of genomes within a specific size range for both datasets. By comparing the shapes and positions of the bars, you can identify differences in genome size distributions, such as shifts, peaks, or outliers. This visualization helps reveal whether one dataset tends to have larger or smaller genomes, or if there are notable differences in variability or coverage between SRA and RefSeq.

![Genome Size Distribution](Genome_Size_refseq_histogram_kde.png)

This plot is a QQ (quantile-quantile) plot, which compares the distribution of the SRA data with RefSeq. Points falling along the diagonal line indicate that the data follows the expected distribution. Deviations from the line suggest departures from normality, such as skewness or outliers. This helps assess whether the dataset is consistently distributed or if there are systematic differences.

![Genome Size QQ Plot](Genome_Size_refseq_qqplot.png)

This plot shows the relationship between the number of coding sequences (CDS) and genome size. It helps to visualize how genome size correlates with the number of genes. This should be linear - as the genome size increases, the number of coding sequences should also increase. Any secondary trend lines or non-linear behaviour indicates bone fide seperate populations within the retained genomes, or some remaining contaminant. 

![CDS vs Genome Size](Paenibacillus larvae_CDS_vs_Genome_Size.png)

### Additional Plots

These plots provide additional insights into the genome characteristics:

- [GC Content Histogram](GC_Content_refseq_histogram_kde.png)
- [GC Content QQ Plot](GC_Content_refseq_qqplot.png)
- [Total Coding Sequences Histogram](Total_Coding_Sequences_refseq_histogram_kde.png)
- [Total Coding Sequences QQ Plot](Total_Coding_Sequences_refseq_qqplot.png)
- [Genome Size Histogram](Genome_Size_refseq_histogram_kde.png)
- [Genome Size QQ Plot](Genome_Size_refseq_qqplot.png)
## Illustrating the filtering process
These plots illustrate the data, pre and post filtering to demostrate what type of outliers have been removed. While this was applied to all metrics, we will demonstrate using total assembly length and N50.

N50 vs total length for all genomes in the dataset.

![ALL Total Length vs N50](Paenibacillus_larvae_all_total_length_N50.png)

N50 vs total length for genomes in the dataset, coloured according to whether they are an anomaly or not.

![Sampled Total Length vs N50](Paenibacillus_larvae_sample_total_length_N50.png)

N50 vs total length post filtering on the dataset.

![Filtered Total Length vs N50](Paenibacillus_larvae_filt_total_length_N50.png)

### Additional Plots

These plots provide additional insights into the genome characteristics:

- [N50 vs number of contigs, all genomes](Paenibacillus_larvae_all_N50_number.png)
- [N50 vs number of contigs, sampled genomes](Paenibacillus_larvae_sample_N50_number.png)
- [N50 vs number of contigs, filtered genomes](Paenibacillus_larvae_filt_N50_number.png)
- [GC Content vs Total Length, all genomes](Paenibacillus_larvae_all_total_length_GC_Content.png)
- [GC Content vs Total Length, sampled genomes](Paenibacillus_larvae_sample_total_length_GC_Content.png)
- [GC Content vs Total Length, filtered genomes](Paenibacillus_larvae_filt_total_length_GC_Content.png)
- [Longest Contig vs Total Length, all genomes](Paenibacillus_larvae_all_total_length_longest.png)
- [Longest Contig vs Total Length, sampled genomes](Paenibacillus_larvae_sample_total_length_longest.png)
- [Longest Contig vs Total Length, filtered genomes](Paenibacillus_larvae_filt_total_length_longest.png)
