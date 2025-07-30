# *Neisseria bergeri*

This is the GenomeQC page for *Neisseria bergeri*. For detailed methods on how these thresholds were calculated, please see [Methods](../../methods.md).
The suggested thresholds are: 

| metric                 | lower_bounds   | upper_bounds   |
|:-----------------------|:---------------|:---------------|
| N50                    | 97000.0        |                |
| no_of_contigs          |                | 100.0          |
| GC_Content             | 52.0           | 52.0           |
| Completeness           | 100.0          |                |
| Contamination          |                | 1.0            |
| Total_Coding_Sequences | 1800.0         | 2200.0         |
| Genome_Size            | 1900000.0      | 2300000.0      |

[Download metrics CSV](Neisseria_bergeri_metrics.csv){.md-button}


These thresholds are based on **0** genomes from RefSeq and **132** genomes from ATB / SRA.

These thresholds were applied to all the bacteria dataset, which resulted in removing **111** and retaining **21**.
The list of genomes retained (i.e. high quality) and the list of genomes rejected (filtered) can be downloaded below. These files are in `.xz` format. The rejected genomes file, also includes the reason why.

[Download high quality genomes list](Neisseria_bergeri_high_quality_genomes.csv.xz)


[Download rejected genomes list](Neisseria_bergeri_filtered_out_genomes.csv.xz)



## Summary Tables
These tables provide a summary of the distribution of each metric, including SDeviation, Mean, Median, and Percentiles.

[Download full summary tables](summary.csv)

[Download simple summary tables](selected_summary.csv)

## Illustrating the filtering process
These plots illustrate the data, pre and post filtering to demostrate what type of outliers have been removed. While this was applied to metric, we will demonstrate using total assembly length and N50.
N50 vs total length for all genomes in the dataset.

![ALL Total Length vs N50](Neisseria_bergeri_all_total_length_N50.png)

N50 vs total length for genomes in the dataset, coloured according to whether they are an anomaly or not.

![Sampled Total Length vs N50](Neisseria_bergeri_sample_total_length_N50.png)

N50 vs total length post filtering on the dataset.

![Filtered Total Length vs N50](Neisseria_bergeri_filt_total_length_N50.png)

### Additional Plots

These plots provide additional insights into the genome characteristics:

- [N50 vs number of contigs, all genomes](Neisseria_bergeri_all_N50_number.png)
- [N50 vs number of contigs, sampled genomes](Neisseria_bergeri_sample_N50_number.png)
- [N50 vs number of contigs, filtered genomes](Neisseria_bergeri_filt_N50_number.png)
- [GC Content vs Total Length, all genomes](Neisseria_bergeri_all_total_length_GC_Content.png)
- [GC Content vs Total Length, sampled genomes](Neisseria_bergeri_sample_total_length_GC_Content.png)
- [GC Content vs Total Length, filtered genomes](Neisseria_bergeri_filt_total_length_GC_Content.png)
- [Longest Contig vs Total Length, all genomes](Neisseria_bergeri_all_total_length_longest.png)
- [Longest Contig vs Total Length, sampled genomes](Neisseria_bergeri_sample_total_length_longest.png)
- [Longest Contig vs Total Length, filtered genomes](Neisseria_bergeri_filt_total_length_longest.png)
