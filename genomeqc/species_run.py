# Script to run genomeqc for a specific species
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from genomeqc.species_util import apply_outlier_filter, plot_outliers, make_metric_stats, make_metric_stats_including_refseq
from genomeqc.refseq import get_metrics
from tqdm import tqdm
import logging 

METRICS_LIST = [
    "N50",
    "number",
    "longest",
    "GC_Content",
    "Completeness_Specific",
    "Contamination",
    "Total_Coding_Sequences",
    "Genome_Size",
]

def species_run(
    species: str,
    species_dir: str,

):
    """
    Run genomeqc for a specific species.
    
    Args:
        species (str): The species to run genomeqc for.
        output_dir (str): Directory to save results.
        batch (bool): Whether to run in batch mode.
        max_jobs (int): Maximum number of jobs to run.
        submit (bool): Whether to submit jobs to SLURM.
        tsv_gz_path (str): Path to the TSV file with assembly info.
        archive_dir (str): Directory for archived files.
        parquet_path (str): Path to the Parquet file with assembly info.
    """
    # Placeholder for actual implementation
    print(f"Processing {species}")
    metrics_list = METRICS_LIST
    # in species dir open the parquet file. 
    # it should be named {species}_assembly_stats.parquet
    safe_species = species.replace(" ", "_").replace("/", "_")
    species_data_path = os.path.join(species_dir, f"{safe_species}_assembly_stats.parquet")
    if not os.path.exists(species_data_path):
        raise FileNotFoundError(f"Species data file {species_data_path} does not exist.")
    # Read the species data
    species_data = pd.read_parquet(species_data_path)
    logging.info("Loaded species data for %s with %d records.", species, len(species_data))
    # Apply outlier filter and plot outliers
    logging.info("Applying outlier filter for species %s", species)
    assigned_species_data = apply_outlier_filter(species_data)
    filtered_plots_dir = os.path.join(species_dir, "filtered_plots")
    logging.info("Ploting outliers for species %s", species)
    plot_outliers(species, assigned_species_data, filtered_plots_dir)
    filtered_species_data = assigned_species_data[assigned_species_data["anomaly"] == 1]
    refseq_data = get_metrics(species, species_dir)
    os.makedirs(species_dir, exist_ok=True)
    metric_summary = []
    for metric in tqdm(metrics_list, desc=f"Processing metrics for {species}"):
        refseq_metric_values = refseq_data.get(metric)
        if refseq_metric_values is not None and len(refseq_metric_values) > 0:  # Handle case where values are empty list
            metric_stats = make_metric_stats_including_refseq(metric, refseq_metric_values, filtered_species_data, species_dir)
        else:
            metric_stats = make_metric_stats(metric, filtered_species_data)
        metric_summary.append(metric_stats)
        metric_stats['species'] = species
        metric_stats['count'] = len(filtered_species_data)
        metric_stats['refseq_count'] = len(refseq_metric_values) if refseq_metric_values is not None else 0
    # Plot Total_Coding_Sequences vs Genome_Size
    plt.figure()
    logging.info("Plotting Total_Coding_Sequences vs Genome_Size for species %s", species)
    subsample = filtered_species_data.sample(n=min(20000, len(filtered_species_data)), random_state=42)
    sns.scatterplot(
        x="Genome_Size",
        y="Total_Coding_Sequences",
        data=subsample,
        hue="Completeness_Specific",
        palette="viridis",
    )
    plt.savefig(os.path.join(species_dir, f"{species}_CDS_vs_Genome_Size.png"))
    plt.close('all')
    # write the summary to a file
    # Convert the list of dictionaries to a DataFrame and save it as a CSV file
    logging.info("Saving metric summary for species %s", species)
    summary_df = pd.DataFrame(metric_summary)
    summary_df.to_csv(os.path.join(species_dir, "summary.csv"), index=False)
    # Create a summary DataFrame with selected columns
    logging.info("Selecting columns for summary DataFrame for species %s", species)
    selected_columns = ["metric", "median", "q1", "q3", "min", "max", "upper_bound", "lower_bound", "MY_LOWER", "MY_UPPER"]
    selected_summary_df = summary_df[selected_columns]
    selected_summary_df.to_csv(os.path.join(species_dir, "selected_summary.csv"), index=False)
    logging.info("Completed processing for species %s", species)