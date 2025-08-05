# *Xanthomonas cissicola*

This is the QualiBact page for *Xanthomonas cissicola*. For detailed methods on how these thresholds were calculated, please see [Methods](../../methods.md).
The suggested thresholds are: 

| metric                 | lower_bounds   | upper_bounds   |
|:-----------------------|:---------------|:---------------|
| N50                    | 57000.0        |                |
| no_of_contigs          |                | 300.0          |
| GC_Content             | 65.0           | 65.0           |
| Completeness           | 100.0          |                |
| Contamination          |                | 1.0            |
| Total_Coding_Sequences | 4200.0         | 4800.0         |
| Genome_Size            | 5000000.0      | 5500000.0      |

[Download metrics CSV](Xanthomonas_cissicola_metrics.csv){.md-button}


These thresholds are based on **0** genomes from RefSeq and **560** genomes from ATB / SRA.

These thresholds were applied to all the bacteria dataset, which resulted in removing **41** and retaining **519**.
The list of genomes retained (i.e. high quality) and the list of genomes rejected (filtered) can be downloaded below. These files are in `.xz` format. The rejected genomes file, also includes the reason why.

[Download high quality genomes list](Xanthomonas_cissicola_high_quality_genomes.csv.xz)


[Download rejected genomes list](Xanthomonas_cissicola_filtered_out_genomes.csv.xz)



## Summary Tables
These tables provide a summary of the distribution of each metric, including SDeviation, Mean, Median, and Percentiles.

[Download full summary tables](summary.csv)

[Download simple summary tables](selected_summary.csv)

This plot shows the relationship between the number of coding sequences (CDS) and genome size. It helps to visualize how genome size correlates with the number of genes. This should be linear - as the genome size increases, the number of coding sequences should also increase. Any secondary trend lines or non-linear behaviour indicates bone fide seperate populations within the retained genomes, or some remaining contaminant. 

![CDS vs Genome Size](Xanthomonas cissicola_CDS_vs_Genome_Size.png)

## Illustrating the filtering process
These plots illustrate the data, pre and post filtering to demostrate what type of outliers have been removed. While this was applied to all metrics, we will demonstrate using total assembly length and N50.

N50 vs total length for all genomes in the dataset.

![ALL Total Length vs N50](Xanthomonas_cissicola_all_total_length_N50.png)

N50 vs total length for genomes in the dataset, coloured according to whether they are an anomaly or not.

![Sampled Total Length vs N50](Xanthomonas_cissicola_sample_total_length_N50.png)

N50 vs total length post filtering on the dataset.

![Filtered Total Length vs N50](Xanthomonas_cissicola_filt_total_length_N50.png)

### Additional Plots

These plots provide additional insights into the genome characteristics:

- [N50 vs number of contigs, all genomes](Xanthomonas_cissicola_all_N50_number.png)
- [N50 vs number of contigs, sampled genomes](Xanthomonas_cissicola_sample_N50_number.png)
- [N50 vs number of contigs, filtered genomes](Xanthomonas_cissicola_filt_N50_number.png)
- [GC Content vs Total Length, all genomes](Xanthomonas_cissicola_all_total_length_GC_Content.png)
- [GC Content vs Total Length, sampled genomes](Xanthomonas_cissicola_sample_total_length_GC_Content.png)
- [GC Content vs Total Length, filtered genomes](Xanthomonas_cissicola_filt_total_length_GC_Content.png)
- [Longest Contig vs Total Length, all genomes](Xanthomonas_cissicola_all_total_length_longest.png)
- [Longest Contig vs Total Length, sampled genomes](Xanthomonas_cissicola_sample_total_length_longest.png)
- [Longest Contig vs Total Length, filtered genomes](Xanthomonas_cissicola_filt_total_length_longest.png)
