import os
import shutil
import glob
import pandas as pd
import collections
from tqdm import tqdm
from qualibact.species_util import DEF_METRIC_LIST
from qualibact.summary_util import plot_summary_plot

def get_rejection_reasons(row, metrics_df):
    reasons = []
    species = row['species_sylph'] if 'species_sylph' in row else row.get('species', None)
    if not species:
        return ['Unknown species']
    species_metrics = metrics_df[metrics_df['species'] == species.replace(' ', '_')]
    for _, metric_row in species_metrics.iterrows():
        metric = metric_row['metric']
        lower = metric_row['lower_bounds']
        upper = metric_row['upper_bounds']
        value = row.get(metric)
        if pd.isnull(value):
            continue
        try:
            value = float(value)
        except Exception:
            continue
        if pd.notnull(lower) and value < float(lower):
            reasons.append(f"{metric} below {lower}")
        if pd.notnull(upper) and value > float(upper):
            reasons.append(f"{metric} above {upper}")
    return reasons if reasons else ['Unknown/other']

def main(outdir='output_qualibact'):
    # 1. Make summary dir
    output_dir = os.path.join(outdir, 'GENUS_SUMMARY')
    os.makedirs(output_dir, exist_ok=True)

    # 2. Find all genus folders with 2+ species, ignoring GENUS_SUMMARY and all_summary
    genus_to_folders = collections.defaultdict(list)
    for src in glob.glob('output_qualibact/*/'):
        folder = os.path.basename(os.path.normpath(src))
        if folder in ('GENUS_SUMMARY', 'all_summary'):
            continue
        genus = folder.split('_')[0]
        genus_to_folders[genus].append(folder)

    # 3. For each genus with 2+ species, make a summary
    for genus, folders in tqdm(genus_to_folders.items(), desc="Processing genera"):
        if len(folders) < 2 and genus not in ['Acinetobacter']:
            continue
        genus_dir = os.path.join(output_dir, genus)
        os.makedirs(genus_dir, exist_ok=True)

        # Extract genus rows from species_counts.csv and filtered_metrics.csv
        for csv_name, out_name in [
            ('species_counts.csv', f'{genus}_species_counts.csv'),
            ('filtered_metrics.csv', f'{genus}_metrics.csv')
        ]:
            src_csv = f'output_qualibact/all_summary/{csv_name}'
            out_csv = os.path.join(genus_dir, out_name)
            if os.path.exists(src_csv):
                df = pd.read_csv(src_csv)
                df_genus = df[df.iloc[:,0].astype(str).str.startswith(genus, na=False)]
                df_out = pd.concat([df.head(0), df_genus])
                df_out.to_csv(out_csv, index=False)

        # For each species folder in this genus, copy files as before
        for folder in folders:
            src = os.path.join('output_qualibact', folder)
            dest = os.path.join(genus_dir, folder)
            os.makedirs(dest, exist_ok=True)
            files = [
                'Genome_Size_refseq_qqplot.png',
                'Genome_Size_refseq_histogram_kde.png',
                f"{folder.replace('_', ' ')}_CDS_vs_Genome_Size.png",
                f"{folder}_filtered_out_genomes.csv",
                f"{folder}_high_quality_genomes.csv",
                'summary.csv',
                f"filtered_plots/{folder.replace('_', ' ')}_all_total_length_N50.png",
                f"filtered_plots/{folder.replace('_', ' ')}_sample_total_length_N50.png",
                f"filtered_plots/{folder.replace('_', ' ')}_filt_total_length_N50.png",
            ]
            for file in files:
                src_file = os.path.join(src, file)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dest)
            # Annotate filtered_out_genomes.csv with rejection reasons if present
            filtered_csv = os.path.join(dest, f"{folder}_filtered_out_genomes.csv")
            metrics_csv = os.path.join(genus_dir, f"{genus}_metrics.csv")
            if os.path.isfile(filtered_csv) and os.path.isfile(metrics_csv):
                metrics_df = pd.read_csv(metrics_csv)
                df = pd.read_csv(filtered_csv)
                df['rejection_reason'] = df.apply(lambda row: "; ".join(get_rejection_reasons(row, metrics_df)), axis=1)
                df.to_csv(filtered_csv, index=False)
        # Add a README.txt to each genus folder explaining the contents
        make_readme(genus, genus_dir)
        # make some of the box and whisker plots for the genus
        # make box plots of each metric
        plot_dir = os.path.join(genus_dir, 'plots')
        os.makedirs(plot_dir, exist_ok=True)
        # the all_summary_df is a merge of all the summary.csv files for each species in the genus
        # Merge all summary.csv files for each species in the genus into all_summary_df
        summary_dfs = []
        for folder in folders:
            summary_path = os.path.join(genus_dir, folder, 'summary.csv')
            if os.path.isfile(summary_path):
                df = pd.read_csv(summary_path)
                df['species'] = folder  # Add species info
                # make species the first column
                cols = ['species'] + [col for col in df.columns if col != 'species']
                df = df[cols]
                summary_dfs.append(df)
        if summary_dfs:
            all_summary_df = pd.concat(summary_dfs, ignore_index=True)
            all_summary_path = os.path.join(genus_dir, f'{genus}_all_summary.csv')
            all_summary_df.to_csv(all_summary_path, index=False)
            # create a simpler file, with just the count and refseq count 
            final_df = all_summary_df[['species', 'count', 'metric', 'refseq_count']]
            final_df = final_df.drop_duplicates()
            final_df_path = os.path.join(genus_dir, f'{genus}_refseq_sra_count_summary.csv')
            final_df.to_csv(final_df_path, index=False)
            for metric in tqdm(DEF_METRIC_LIST + ['Genome_Size', 'Total_Coding_Sequences'], desc="Plotting metrics"):
                plot_summary_plot(metric, all_summary_df, plot_dir)        


def make_readme(genus, genus_dir):
    """
    Create a README.md file in the genus summary directory with explanations of the summary, metrics, and species count files.
    """
    readme_path = os.path.join(genus_dir, 'README.md')
    content = f"""# {genus} Summary

This directory contains a summary of genome QC and filtering results for the genus **{genus}**.

In the main {genus} directory, you will find:
- {genus}_species_counts.csv: A summary of species, the original number of assemblies, and the number of assemblies that passed quality filters, and the number of assemblies that were filtered out.
- {genus}_metrics.csv: The assembly quality control metrics, and the recommended thresholds for filtering genomes in this genus. **USE THESE THRESHOLDS FOR YOUR OWN DATA** 
- {genus}_all_summary.csv: A summary of all assemblies in the genus, including counts and reference counts. Grouped by species.
- {genus}_refseq_sra_count_summary.csv: A simplified summary of counts and reference genomes counts for each species in the genus.

# Method 
The method for filtering genomes is as follows:

1. For each species in the genus, we calculate quality control metrics such as N50, GC content, completeness, and contamination.
2. We apply Isolation Forest outlier detection to these metrics to identify outliers.
3. We remove final outliers with a 99.5 and 0.5 percentile threshold for each metric.
4. We compare these(GC and genome size) metrics to reference genomes from RefSeq to determine appropriate thresholds for filtering (i.e. the ranges will include Refseq+SRA but exclude SRA outliers).
5. We produce a range of plots and table to support the filtering process.

# Species specific contents
There is also a subdirectory for each species in the genus, containing the following files:

- `<species>_filtered_out_genomes.csv`: Assemblies for each species that did not pass quality filters, with a `rejection_reason` column explaining why each was rejected.
- `<species>_high_quality_genomes.csv`: Assemblies for each species that passed all quality filters.
- `summary.csv`: Summary statistics for all assemblies in the species.
- `Genome_Size_refseq_qqplot.png`: Quantile-quantile plot comparing genome sizes to RefSeq genomes.
- `Genome_Size_refseq_histogram_kde.png`: Histogram and KDE plot of genome sizes compared to RefSeq genomes.
- `<species>_CDS_vs_Genome_Size.png`: Scatter plot of CDS length vs genome size for the species.
- `<species>_all_total_length_N50.png`: N50 vs total_length plot for all genomes in the species (before outlier detection).
- `<species>_sample_total_length_N50.png`: N50 vs total_length plot for a subsample of genomes to illustrate the difference between outliers and non-outliers.
- `<species>_filt_total_length_N50.png`: N50 vs total_length plot for genomes that passed QC filtering. 

## About `summary.csv`
This file contains the quality control thresholds and statistical summaries used to filter genomes for each species in the genus. Columns:

- `metric`: Metric name (e.g., `N50`, `GC_Content`, `Completeness`, etc.)
- `distribution`: normal or not. Usually it's not normal. 
- `mean`, `std`, `median`, `q1`, `q3`, `iqr`, `min`, `max`: Descriptive statistics for the metric in the dataset
- `lower_bound`, `upper_bound`: upper and lower bound of SRA data
- `MY_LOWER`, `MY_UPPER`: upper and lower bounds, adjusted to include RefSeq genomes (where applicable)
- `species`: Species name (e.g., `Klebsiella_pneumoniae`)
- `count`: Number of genomes included for the species
- `refseq_distribution`, `refseq_mean`, `refseq_std`, `refseq_median`, `refseq_q1`, `refseq_q3`, `refseq_iqr`, `refseq_min`, `refseq_max`, `refseq_lower_bound`, `refseq_upper_bound`: Reference statistics from RefSeq genomes
- `KS_statistic`, `KS_p_value`: Kolmogorov-Smirnov test statistics comparing sra and refseq distributions. I am trying to detect if the distributions diverge.
- `Wasserstein_Distance`: Wasserstein distance between sra and refseq distributions. I am trying to detect if the distributions diverge.

## How to use
- The bulk of this information is to justify the thresholds presented in {genus}_metrics.csv. 
- If you trust me, just apply the thresholds in {genus}_metrics.csv to your own data.

"""
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
        


if __name__ == "__main__":
    main()
