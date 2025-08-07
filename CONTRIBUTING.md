# Contributing to QualiBact

We welcome contributions to QualiBact! Major contributions to source code, manuscript development, metric validation and adoption, and providing additional data for calibrating quality thresholds will be granted authorship on publications. Pull requests are welcome through GitHub.

## We Need More Data!

Currently, the QC thresholds are based on [AllTheBacteria](https://github.com/AllTheBacteria/AllTheBacteria) data, which used Shovill as the genome assembly software. We are aware that the choice of assembler will affect certain metrics (such as N50 and number of contigs).

To address this limitation and improve the robustness of our quality thresholds, we are actively seeking contributions of:

- **Genome assembly statistics**
- **Nucleotide composition data** for genome assemblies
- **Metadata** describing assembly methods and parameters
- **OPTIONAL: CheckM2 quality assessment results** 

### Data Requirements

Please provide the following files for each dataset:

1. **Nucleotide counts** (TSV format, compressed as .xz or .gz). 
2. **Metadata description** TSV file with assembly/sequencing details.
3. **Genome assembly stats** TSV file with genome assembly stats, like N50. 
4. **CheckM2 results** (TSV format, compressed as .xz or .gz) - This is optional. 

You can email links to these files to: **nabil.alikhan@cgps.group**

**File Naming Convention**

- **Nucleotide counts**: `nucleotide_counts_[dataset_name].tsv.xz`
- **Metadata**: `metadata_[dataset_name].tsv.xz`
- **Assembly stats**: `assembly_stats_[dataset_name].tsv.xz`
- **CheckM2 results**: `checkm2_results_[dataset_name].tsv.xz`

## Metadata Requirements
Please include the following information in your metadata file:
- Assembly software/pipeline and version
- Assembly parameters used
- Sequencing platform and technology
- Species name
- Data source and accession numbers (if applicable)

That would be another csv file like:
```
filename            platform    instrument     species               accession       software    version    custom_parameters    Notes
SAMN40089455.fa     Illumina    NextSeq550     Salmonella enterica   SAMN40089455    SKESA       1.1        None                 SKESA, default parameters
SAMN40089456.fa     Illumina    NextSeq550     Escherichia coli      SAMN40089456    SPAdes      2.3        --isolate            SPAdes
my_reads_pri.fa     ONT         MinIon         Escherichia coli      NA              Flye        1.3        None                 None
```

The Filename should match what you have provided in the other files.

## Genome assembly statistics 

We require the following metrics:

| **Metric**     | **Description**                                                       |
| -------------- | --------------------------------------------------------------------- |
| `total_length` | Total number of base pairs across all contigs/scaffolds               |
| `number`       | Total number of contigs/scaffolds                                     |
| `mean_length`  | Average contig length (`total_length / number`)                       |
| `longest`      | Length of the longest contig                                          |
| `shortest`     | Length of the shortest contig                                         |
| `N_count`      | Total number of ambiguous bases (`N`) in the assembly                 |
| `Gaps`         | Number of separate gaps (usually inferred from stretches of Ns)       |
| `N50`          | Contig length such that 50% of the assembly is in contigs ≥ this size |
| `N50n`         | Number of contigs ≥ N50 in length                                     |
| `N70`          | Contig length such that 70% of the assembly is in contigs ≥ this size |
| `N70n`         | Number of contigs ≥ N70 in length                                     |
| `N90`          | Contig length such that 90% of the assembly is in contigs ≥ this size |
| `N90n`         | Number of contigs ≥ N90 in length                                     |

DO NOT APPLY A MINIMUM CONTIG SIZE FILTER. 

For the sake of consistency, please use `assembly-stats` as described by [AllTheBacteria](https://github.com/AllTheBacteria/AllTheBacteria/tree/main/reproducibility/All-samples/assembly-stats).
Assembly-stats is available on conda and biocontainers, you can also [download the source from GitHub](https://github.com/sanger-pathogens/assembly-stats) and compile it yourself. 
It is very easy to use, this will run on all files in the folder matching the wildcard:

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


## Nucleotide Composition Analysis

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

## Running CheckM2 - Optional

I am aware that CheckM2 can be a tall order, with thousands of genomes, and hence for the sake of submission this is an option inclusion. 

To ensure consistency with existing analyses, please follow the same protocol used by [AllTheBacteria](https://github.com/AllTheBacteria/AllTheBacteria/tree/main/reproducibility/All-samples/checkm2):

### Requirements
- **CheckM2 version 1.0.1**
- **CheckM2 database**: uniref100.KO.1.dmnd

### Singularity Container
We recommend using the same singularity container used by AllTheBacteria:

**Container download:**
```bash
wget -O checkm2.1.0.1--pyh7cba7a3_0.img https://osf.io/download/7vpy3/
```
- **Source**: https://osf.io/7vpy3

**CheckM2 database download:**
```bash
wget -O uniref100.KO.1.dmnd https://osf.io/download/x5vtj/
```
- **Source**: https://osf.io/x5vtj

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

## Getting Help

If you have questions about:
- **Data formats**: Check our example files in the repository
- **Technical issues**: Open an issue on GitHub
- **Collaboration opportunities**: Contact nabil.alikhan@cgps.group

Thank you for contributing to improving bacterial genome quality assessment!