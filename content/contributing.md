# Contributing to QualiBact

We welcome contributions to QualiBact! Major contributions to source code, manuscript development, metric validation and adoption, and providing additional data for calibrating quality thresholds will be granted authorship on publications. [Pull requests are welcome through GitHub](https://github.com/cgps-group/qualibact).

## We Need More Data!

There are many bacterial species for which we have limited data to establish robust quality control (QC) thresholds. If there is a species you work with that is not mentioned in our current dataset, please make a request. See our current list of requests, and for details on how to suggest a species, see the [Requests page](/organism-requests).

The Qualibact standard of QC thresholds included here (usually qualibact-v1.0) is based on [AllTheBacteria](https://github.com/AllTheBacteria/AllTheBacteria) data, which used Shovill as the genome assembly software. We are aware that not all species of interest are covered, despite the dataset containing 2.4M genomes. We are also aware that the choice of assembler will affect certain metrics (such as N50 and number of contigs), and that many species have limited public data, which impacts our ability to set robust thresholds.

We are actively seeking contributions of additional data. There are two avenues for contribution:

- [Direct contribution](#route-1---direct-data-contribution) of genome assembly statistics, nucleotide composition data, and metadata for species of interest (see below for details). We will run the qualibact pipeline on these data and include them in future releases. This is the preferred route for most users, and provides consistent automated processing of data.
- [Presenting thresholds you have established](#route-2---present-your-own-thresholds) for species of interest based on your own data and analyses. We will include these thresholds in future releases, with appropriate attribution.


## Route 1 - Direct Data Contribution

In this route, you will provide us with values for common assembly metrics, metadata describing assembly methods, nucleotide composition data, and checkm2 results (optional) for genome assemblies of species you are interested in. We will run the qualibact pipeline on these data and include them in future releases. Specifically, we require:

- **Genome assembly statistics**
- **Nucleotide composition data** for genome assemblies
- **Metadata** describing assembly methods and parameters
- **OPTIONAL: CheckM2 quality assessment results** 

We do not need the assembly sequences themselves. The data you provide should be for genomes you consider to be of sufficient quality for tasks such as genotyping (e.g., cgMLST, nkST), antimicrobial resistance gene detection, and SNP-based phylogeny.

**As part of your submission, please also include the list of contributors, so we can appropriately attribute them. Please also include a description of the dataset you are submitting: number of genomes, how they were selected, and where they were sourced.**

### Data Requirements

Please provide the following files for each dataset:

1. **Nucleotide counts** (TSV format, compressed as .xz or .gz). 
2. **Metadata description** TSV file with assembly/sequencing details.
3. **Genome assembly stats** TSV file with genome assembly stats, like N50. 
4. **CheckM2 results** (TSV format, compressed as .xz or .gz) - This is optional. 

**File Naming Convention**

- **Nucleotide counts**: `nucleotide_counts_[dataset_name].tsv.xz`
- **Metadata**: `metadata_[dataset_name].tsv.xz`
- **Assembly stats**: `assembly_stats_[dataset_name].tsv.xz`
- **CheckM2 results**: `checkm2_results_[dataset_name].tsv.xz`

You can email links to these files to: **nabil.alikhan@cgps.group**

### Metadata Requirements
Please include the following information in your metadata file:
- Assembly software/pipeline and version
- Assembly parameters used
- Sequencing platform and instrument
- Species name
- Data source and accession numbers (if applicable)

That would be a csv file like:
```
filename            platform    instrument     species               accession       software    version    custom_parameters    Notes
SAMN40089455.fa     Illumina    NextSeq550     Salmonella enterica   SAMN40089455    SKESA       1.1        None                 SKESA, default parameters
SAMN40089456.fa     Illumina    NextSeq550     Escherichia coli      SAMN40089456    SPAdes      2.3        --isolate            SPAdes
my_reads_pri.fa     ONT         MinIon         Escherichia coli      NA              Flye        1.3        None                 None
```

The values in the `filename` field should match what you have provided in the other files.

### Genome assembly statistics 

We must have the following metrics:

| **Metric**     | **Description**                                                       |
| -------------- | --------------------------------------------------------------------- |
| `total_length` | Total number of base pairs across all contigs/scaffolds               |
| `number`       | Total number of contigs/scaffolds                                     |
| `N50`          | Contig length such that 50% of the assembly is in contigs ≥ this size |

**DO NOT APPLY A MINIMUM CONTIG SIZE FILTER.**

For the sake of consistency, please use `assembly-stats` as described by [AllTheBacteria](https://github.com/AllTheBacteria/AllTheBacteria/tree/main/reproducibility/All-samples/assembly-stats).
Assembly-stats is available on [conda](https://anaconda.org/bioconda/assembly-stats) and [biocontainers](https://biocontainers.pro/tools/assembly-stats), you can also [download the source from GitHub](https://github.com/sanger-pathogens/assembly-stats) and compile it yourself. 
It is very easy to use. The following command will run on all files in the folder matching the wildcard:

```
assembly-stats -t /workdir/assembly/*.fa.gz
```

The file should look something like this:

```
filename        total_length    number  mean_length     longest shortest        N_count Gaps    N50     N50n    N70     N70n    N90     N90n
SAMD00127152.fa.gz     5180815 165     31398.88        486012  206     0       0       143489  12      83834   22      25975   43
SAMD00127152.fa.gz     5180815 165     31398.88        486012  206     0       0       143489  12      83834   22      25975   43
SAMD00127153.fa.gz     5278830 113     46715.31        633980  211     100     1       245414  6       143082  12      43792   24
SAMD00127154.fa.gz     5263743 218     24145.61        390782  208     100     1       147090  12      94642   22      26394   41
SAMD00127155.fa.gz     5261650 147     35793.54        533596  209     100     1       178971  10      119101  16      33179   32
SAMD00127156.fa.gz     5262861 207     25424.45        588167  208     100     1       147090  11      96125   20      30157   39
```

We will also accept output from other tools, such as [Quast](https://github.com/ablab/quast), as long as the required metrics are present and clearly labelled.

### Nucleotide Composition Analysis

Other tools do provide GC content, but for some analyses we require more detailed nucleotide composition data. We need a table containing counts for each nucleotide in genome assemblies:

### Required Output Format
```
Filename	A	T	G	C	N	Other
SAMN40089455.fa	1234567	1200000	1345000	1320000	1000	50
SAMN40089456.fa	1000000	980000	1010000	990000	500	10
```

The Filename should match what you have provided in the other files.

### Example script
Here is an example script that you can adapt:

```bash
#!/bin/bash
# Usage: ./count_bases.sh path/to/file.fa

FASTA="$1"
FILENAME=$(basename "$FASTA")

# Write header if needed
echo -e "Filename\tA\tT\tG\tC\tN\tOther"

# Count nucleotides
grep -v "^>" "$FASTA" | tr -d '\n' | awk -v file="$FILENAME" '
BEGIN {
    A=0; T=0; G=0; C=0; N=0; other=0;
}
{
    for (i = 1; i <= length($0); i++) {
        b = toupper(substr($0, i, 1));
        if (b == "A") A++;
        else if (b == "T") T++;
        else if (b == "G") G++;
        else if (b == "C") C++;
        else if (b == "N") N++;
        else other++;
    }
}
END {
    printf "%s\t%d\t%d\t%d\t%d\t%d\t%d\n", file, A, T, G, C, N, other;
}'
```

### Running CheckM2 - Optional

I am aware that CheckM2 can be a tall order with thousands of genomes, and hence for submission this is optional. 

To ensure consistency with existing analyses, please follow the same protocol used by [AllTheBacteria](https://github.com/AllTheBacteria/AllTheBacteria/tree/main/reproducibility/All-samples/checkm2):

### Requirements
- **CheckM2 version 1.0.1**
- **CheckM2 database**: uniref100.KO.1.dmnd

We recommend using the same Singularity container used by AllTheBacteria:

**Container download:**

- **Source**: https://osf.io/7vpy3

```bash
wget -O checkm2.1.0.1--pyh7cba7a3_0.img https://osf.io/download/7vpy3/
```

**CheckM2 database download:**

- **Source**: https://osf.io/x5vtj

```bash
wget -O uniref100.KO.1.dmnd https://osf.io/download/x5vtj/
```

### Example CheckM2 Command
```bash
# Define variables
WORKDIR="/path/to/working_directory"
IMG="$WORKDIR/checkm2.1.0.1--pyh7cba7a3_0.img"
DB="$WORKDIR/path/to/uniref100.KO.1.dmnd"
OUTDIR="$WORKDIR/output"
FASTA="$WORKDIR/path/to/assembly.fa"

# Set up the CheckM2 command
singularity exec --bind $WORKDIR $IMG checkm2 predict --allmodels --lowmem --database_path $DB --remove_intermediates --force  -i "$FASTA"  --threads 4 -o $OUTDIR
```

The output from CheckM2 will look like: 

```
Name    Completeness_General    Contamination   Completeness_Specific   Completeness_Model_Used Translation_Table_Used  Coding_Density  Contig_N50      Average_Gene_Length     Genome_Size     GC_Content      Total_Coding_Sequences  Additional_Notes
SAMD00127152    100.0   0.09    100.0   Neural Network (Specific Model) 11      0.875   143489  303.8069048574869       5180815 0.5     4982    None
```

## Route 2 - Present Your Own Thresholds

If you have established quality control thresholds for a species of interest based on your own data and analyses, we welcome you to present these thresholds for inclusion in future releases of QualiBact. Please provide:

- Species name
- Quality control thresholds for relevant metrics (e.g., N50, total length, number of contigs, GC content, completeness, contamination) as a CSV. The table should include columns for metric name and threshold values. See example below.
- Description of the dataset used (summary table) to establish these thresholds. See example below.
- Any supporting analyses or visualizations

An example of the threshold table is shown below.

| Species                  | Metric                 | Lower Bounds | Upper Bounds |
|--------------------------|------------------------|--------------|--------------|
| Acinetobacter baumannii  | N50                    | 17000.0      |              |
| Acinetobacter baumannii  | no_of_contigs          |              | 490          |
| Acinetobacter baumannii  | GC_Content             | 38           | 40           |
| Acinetobacter baumannii  | Completeness           | 96.0         |              |
| Acinetobacter baumannii  | Contamination          |              | 7            |
| Acinetobacter baumannii  | Total_Coding_Sequences | 3400         | 4500         |
| Acinetobacter baumannii  | Genome_Size            | 3600000      | 4600000      |

An example of the summary table is shown below.

| metric                  | mean        | std        | median    | q1        | q3        | iqr       | min     | max       | FINAL_LOWER | FINAL_UPPER | species                 | count |
|-------------------------|-------------|------------|-----------|-----------|-----------|-----------|---------|-----------|----------|----------|--------------------------|-------|
| N50                     | 142216.91   | 76223.46   | 134688.50 | 96516.00  | 164093.75 | 67577.75  | 9210.00 | 718672.00 | 17467.69 | 466321.33 | Acinetobacter baumannii | 26690 |
| number                  | 120.38      | 66.22      | 105.00    | 83.00     | 136.00    | 53.00     | 19.00   | 779.00    | 34.00    | 482.00   | Acinetobacter baumannii | 26690 |
| longest                 | 339276.47   | 165020.98  | 301308.50 | 250723.00 | 373248.00 | 122525.00 | 44374.00| 1648648.00| 73316.14 | 1110621.82 | Acinetobacter baumannii | 26690 |
| GC_Content              | 0.3910        | 0.00       | 0.3910      | 0.3901      | 0.3902      | 0.00      | 0.3800    | 0.4000      | 0.39     | 0.40     | Acinetobacter baumannii | 26690 |
| Completeness_Specific   | 100.00      | 0.04       | 100.00    | 99.99     | 100.00    | 0.01      | 94.33   | 100.00    | 96.86    | 100.00   | Acinetobacter baumannii | 26690 |
| Contamination           | 0.19        | 0.20       | 0.13      | 0.08      | 0.24      | 0.16      | 0.00    | 4.32      | 0.00     | 6.63     | Acinetobacter baumannii | 26690 |
| Total_Coding_Sequences  | 3790.81     | 133.14     | 3785.00   | 3704.00   | 3868.00   | 164.00    | 3232.00 | 4545.00   | 3452.00  | 4445.00  | Acinetobacter baumannii | 26690 |
| Genome_Size             | 3956786.76  | 110442.03  | 3953434.50| 3884469.75| 4019485.25| 135015.50 | 3216153| 4532195   | 3638126  | 4566577  | Acinetobacter baumannii | 26690 |


You can look to the qualibact-v1.0 thresholds as an example of how to present your data.

**As part of your submission, please also include the list of contributors, so we can appropriately attribute them. Please also include a description of the dataset you are submitting: number of genomes, how they were selected, and where they were sourced.**

## Getting Help

If you have questions about:
- **Data formats**: Check our example in qualibact-v1.0 thresholds. 
- **Technical issues**: Open an issue on [Github](https://github.com/cgps-group/qualibact)
- **Collaboration opportunities**: Contact `nabil.alikhan@cgps.group`

Thank you for contributing to improving bacterial genome quality assessment!
