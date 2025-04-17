#!/usr/bin/env python3
"""
This script processes assembly statistics and generates plots for specified species.

Functions:
    get_file(url, workdir, prefix):

    make_stat_dict(the_list):
        Creates a dictionary for statistical metrics.

    main(args):
        Main function to process assembly stats and generate plots based on the provided arguments.

Arguments:
    --workdir (str): Working directory where files will be saved and processed.
    --species (list of str): List of species to include in the analysis.
    --min_genome_count (int): Minimum number of genomes per species to include in the analysis.
    --metrics_list (list of str): List of metrics to include in the analysis.

Usage:
    python calculate_criteria.py --workdir <working_directory> --species
        <species_list> --min_genome_count <min_genome_count> --metrics_list <metrics_list>
"""
import os
import argparse
import pandas as pd
from scipy.stats import normaltest
import numpy as np
import matplotlib.pyplot as plt
from refseq import get_metrics
import seaborn as sns
import statsmodels.api as sm
from scipy.stats import ks_2samp, wasserstein_distance
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
import logging
from prepare import filter_assembly_data, prepare

logging.basicConfig(level=logging.INFO)

def basic_stats(metric, metric_data):
    metric_summary = {'metric': metric}
    if isinstance(metric_data, pd.Series):
        metric_data = metric_data.dropna()
    _, p = normaltest(metric_data)               
    metric_summary["distribution"] = "normal" if p > 0.05 else "non-normal"
    metric_summary["mean"] = np.mean(metric_data)
    metric_summary["std"] = np.std(metric_data)
    metric_summary["median"] = np.median(metric_data)
    metric_summary['q1'] = np.percentile(metric_data, 25)
    metric_summary["q3"] = np.percentile(metric_data, 75)
    metric_summary["iqr"] = np.percentile(metric_data, 75) - np.percentile(
        metric_data, 25
    )
    metric_summary["min"] = metric_data.min()
    metric_summary["max"] = metric_data.max()
    metric_summary["lower_bound"] = np.percentile(metric_data, 0.5)
    metric_summary["upper_bound"] = np.percentile(metric_data, 99.5)
    return metric_summary, metric_data

def plot_histogram(metric, sra_values, refseq_values, workdir):
    # Overlayed Histogram and KDE
    plt.figure()
    sns.histplot(
        sra_values,
        bins=50,
        color="blue",
        stat="density",
        kde=True,
        alpha=0.6,
        label="SRA",
    )
    sns.histplot(
        refseq_values,
        bins=50,
        color="red",
        stat="density",
        kde=True,
        alpha=0.6,
        label="RefSeq",
    )
    plt.title(f"Overlayed Histogram and KDE ({metric})")
    plt.xlabel("Value")
    plt.ylabel("Density")
    plt.legend()
    plt.savefig(
        os.path.join(
            workdir, f"{metric}_refseq_histogram_kde.png"
        )
    )
    plt.close('all')

    # Q-Q Plot
    plt.figure()
    sm.qqplot_2samples(sra_values, refseq_values, line="45")
    plt.title(f"Q-Q Plot of SRA vs RefSeq ({metric})")
    plt.xlabel("Quartiles of SRA")
    plt.ylabel("Quartiles of RefSeq")
    plt.savefig(
        os.path.join(workdir, f"{metric}_refseq_qqplot.png")
    )
    plt.close('all')


def get_cluster_stats(metric, this_metric_data, eps, min_samples=5):
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)  # Adjust `eps` for density and `min_samples` for clustering threshold    
    this_metric_data["cluster"] = dbscan.fit_predict(this_metric_data)
    # Step 3: Count the number of points in each cluster
    cluster_counts = this_metric_data["cluster"].value_counts()

    # Step 4: Get the cluster with the maximum count
    max_cluster = cluster_counts.idxmax()  # Cluster label with the most points
    # get cluster with the most 
    largest_cluster_data = this_metric_data[this_metric_data["cluster"] == max_cluster]
    metric_cluster_stats, metric_cluster = basic_stats(metric, largest_cluster_data[metric])
    return metric_cluster_stats, metric_cluster

def get_species_list(species_file):
    """
    Reads a file containing species names and returns a list of species.
    """
    with open(species_file, "r", encoding="utf-8") as f:
        species_list = [line.strip() for line in f.readlines()]
    return species_list

def make_metric_stats_including_refseq(metric, refseq_metric_values, species_data, species_dir):
    # We cannot have refseq genomes not included in the ranges
    # So the metric range must be min/max of the refseq genomes OR "winsorized" SRA values, 
    # Which ever is more extreme.
    refseq_metric_values = np.array(refseq_metric_values)
    metric_stats, metric_data = basic_stats(metric, species_data[metric])
    metric_data_array = np.array(metric_data)

    ks_statistic, ks_p_value = ks_2samp(metric_data_array, refseq_metric_values)
    w_distance = wasserstein_distance(metric_data_array, refseq_metric_values)
    refseq_metric_stats, _ = basic_stats(metric, refseq_metric_values)
    refseq_metric_stats.pop("metric", None)
    refseq_metric_stats = {f"refseq_{k}": v for k, v in refseq_metric_stats.items()}
    metric_stats.update(refseq_metric_stats)
    metric_stats["KS_statistic"] = ks_statistic
    metric_stats["KS_p_value"] = ks_p_value
    metric_stats["Wasserstein_Distance"] = w_distance
    metric_stats["MY_LOWER"] = round(min(metric_stats['lower_bound'], refseq_metric_stats["refseq_min"]), 2)
    metric_stats["MY_UPPER"] = round(max(metric_stats["upper_bound"], refseq_metric_stats["refseq_max"]), 2)
    plot_histogram(metric, metric_data, refseq_metric_values, species_dir)
    return metric_stats

def make_metric_stats(metric, species_data):
    this_metric_data = species_data[metric].values.flatten()

    metricdict, metric_data = basic_stats(metric, this_metric_data)
    metricdict["MY_LOWER"] = round(metricdict['lower_bound'], 2)
    metricdict["MY_UPPER"] = round(metricdict["upper_bound"], 2)
    return metricdict

def apply_outlier_filter(species_data):
        # What if we applied the LOF filter here? 
        # LOF = Local Outlier Factor
        outlier_data = species_data[['total_length', 'GC_Content', 'N50', 'number', 'longest' , 'Completeness_Specific', 'Contamination']]
        # Train Isolation Forest
        # Parameters
        iso_forest = IsolationForest(random_state=42)
        iso_forest.fit(outlier_data)
        # Calculate anomaly scores and classify anomalies
        species_data['anomaly_score'] = iso_forest.decision_function(outlier_data)
        species_data['anomaly'] = iso_forest.predict(outlier_data)
        species_data['anomaly'].value_counts()
        return species_data

def plot_outliers(species, species_data, output_dir):
        # Create a directory for the species
        os.makedirs(output_dir, exist_ok=True)
        # Subsample the data: Randomly select a fraction of the data
        if len(species_data) > 10000:
            subsampled_data = species_data.sample(n=10000, random_state=42)
        else: 
            subsampled_data = species_data
#        outlier_functions = {'LOF': 'LOF', 'IsolationForest': 'anomaly', 'IsolationForest_score': 'anomaly_score'}
        axis_pairs = [
            ("total_length", "N50"),
            ("total_length", "GC_Content"),
            ("total_length", "number"),
            ("total_length", "longest"),
            ("total_length", "Completeness_Specific"),
            ("total_length", "Contamination"),
            ("N50", "number"),
            ("N50", "longest"),
            ("N50", "Completeness_Specific"),
            ("N50", "Contamination"),
            ("number", "longest"),
            ("number", "Completeness_Specific"),
            ("number", "Contamination"),
            ("longest", "Completeness_Specific"),
            ("longest", "Contamination"),
            ]
        for x_col, y_col in axis_pairs:
            # Show the full distribution of the data with hex binning
            g = sns.jointplot(
                x=x_col,
                y=y_col,
                data=species_data,
                kind="hex",
                palette="viridis",
            )
            # Save the figure
            output_path = os.path.join(output_dir, f"{species}_all_{x_col}_{y_col}.png")
            g.figure.savefig(output_path)
            plt.close('all')            
            # Show a subsample with the anomaly category - with a kde 
            g = sns.jointplot(
                x=x_col,
                y=y_col,
                data=subsampled_data,
                hue="anomaly",
                palette="viridis",
            )
            g.plot_joint(sns.kdeplot, color="r", zorder=0, levels=6)
            # Save the figure
            output_path = os.path.join(output_dir, f"{species}_sample_{x_col}_{y_col}.png")
            g.figure.savefig(output_path)
            plt.close('all')   
            # Show the distribution of score post filtering 
            filtered_data = subsampled_data[subsampled_data["anomaly"] == 1]
            g = special_score_plot(filtered_data, x_col, y_col)
            plt.suptitle(f"Scatter plot of {y_col} vs {x_col} colored by Anomaly Score", y=1.05)            
            # Save the figure
            output_path = os.path.join(output_dir, f"{species}_filt_{x_col}_{y_col}.png")
            g.figure.savefig(output_path)
            plt.close('all')

def special_score_plot(filtered_data, x_col, y_col):

    # Assuming 'filtered_data' is your DataFrame
    # 'x_col' and 'y_col' are the column names for x and y axes
    # 'anomaly_score' is the continuous variable for color coding

    # Initialize a JointGrid
    g = sns.JointGrid(data=filtered_data, x=x_col, y=y_col, height=8)

    # Create a scatter plot with a continuous hue
    g.plot_joint(
        sns.scatterplot,
        hue=filtered_data["anomaly_score"],
        palette="viridis",
        s=50,
        alpha=0.7
    )
    # Overlay the KDE plot
    g.plot_joint(
        sns.kdeplot,
        levels=5,
        color='k',
        alpha=0.5
    )    

    # Add marginal histograms
    g.plot_marginals(sns.histplot, kde=True)

    # Adjust the position of the colorbar
    cbar_ax = g.figure.add_axes([1.02, 0.25, 0.02, 0.5])
    norm = plt.Normalize(filtered_data["anomaly_score"].min(), filtered_data["anomaly_score"].max())
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
    sm.set_array([])
    g.figure.colorbar(sm, cax=cbar_ax, label="Anomaly Score")

    # Set axis labels and title
    g.set_axis_labels(x_col, y_col)
    return g

def main(args):
    workdir = args.workdir
    species_list = get_species_list(args.species_file)
    metrics_list = args.metrics_list
    assembly_stats = prepare(workdir)
    # Handle species with underscores
    # Rename species according to ^([A-Za-z]+)_?[A-Za-z]*\s([a-z]+) 
    assembly_stats = filter_assembly_data(assembly_stats, species_list=species_list)
    species_list = assembly_stats["species_sylph"].unique()
    all_metrics_for_all_species = []
    # Look at refseq first
    for species in species_list:
        print(f"Processing {species}")
        species_dir = os.path.join(workdir, species.replace(" ", "_"))
        species_data = assembly_stats[assembly_stats["species_sylph"] == species]
        assigned_species_data = apply_outlier_filter(species_data)
        filtered_plots_dir = os.path.join(species_dir, "filtered_plots")
        plot_outliers(species, assigned_species_data, filtered_plots_dir)
        filtered_species_data = assigned_species_data[assigned_species_data["anomaly"] == 1]
        refseq_data = get_metrics(species)
        os.makedirs(species_dir, exist_ok=True)
        metric_summary = []
        for metric in metrics_list:
            refseq_metric_values = refseq_data.get(metric)
            if refseq_metric_values is not None:
                metric_stats = make_metric_stats_including_refseq(metric, refseq_metric_values, filtered_species_data, species_dir)
            else:
                metric_stats = make_metric_stats(metric, filtered_species_data)
            metric_summary.append(metric_stats)
            metric_stats['species'] = species
            metric_stats['count'] = len(filtered_species_data)
            all_metrics_for_all_species.append(metric_stats)
        # Plot Total_Coding_Sequences vs Genome_Size
        plt.figure()
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
        summary_df = pd.DataFrame(metric_summary)
        summary_df.to_csv(os.path.join(species_dir, "summary.csv"), index=False)
        # Create a summary DataFrame with selected columns
        selected_columns = ["metric", "median", "q1", "q3", "min", "max", "upper_bound", "lower_bound", "MY_LOWER", "MY_UPPER"]
        selected_summary_df = summary_df[selected_columns]
        selected_summary_df.to_csv(os.path.join(species_dir, "selected_summary.csv"), index=False)
    # Save all metrics for all species
    all_summary_output_dir = os.path.join(workdir, "all_summary")
    os.makedirs(all_summary_output_dir, exist_ok=True)
    all_metrics_df = pd.DataFrame(all_metrics_for_all_species)
    all_metrics_df.to_csv(os.path.join(all_summary_output_dir, "all_metrics.csv"), index=False)
    selected_columns = ["species", "metric","count", "median", "q1", "q3", "min", "max", "upper_bound", "lower_bound", "MY_LOWER", "MY_UPPER"]
    selected_summary_df = all_metrics_df[selected_columns]
    selected_summary_df.to_csv(os.path.join(all_summary_output_dir, "all_metrics_summary.csv"), index=False)
    for metric in metrics_list:
        plot_summary_plot(metric, all_metrics_df, all_summary_output_dir)

def plot_summary_plot(metric, all_metrics_df, workdir):
        # Prepare box plot data
        box_data = []
        labels = []
        extra_lines = []
        for species, group in all_metrics_df.groupby("species"):
            metric_data = group[group["metric"] == metric]
            if not metric_data.empty:
                median = metric_data["median"].values[0]
                q1 = metric_data["q1"].values[0]  # 25th percentile
                q3 = metric_data["q3"].values[0]  # 75th percentile
                whisker_low = metric_data["min"].values[0]  # Lower whisker
                whisker_high = metric_data["max"].values[0]  # Upper whisker
                # Store five-number summary
                box_data.append([whisker_low, q1, median, q3, whisker_high])
                labels.append(species)
                extra_lines.append((metric_data['MY_LOWER'], metric_data['MY_UPPER']))
        # We need to chunk these into groups of 10 
        # and plot them separately
        # Create a box plot for each group
        # We need to chunk these into groups of 10
        num_groups = len(box_data) // 10 + (len(box_data) % 10 > 0)
        for z in range(num_groups):
            start = z * 10
            end = start + 10
            group_data = box_data[start:end]
            group_labels = labels[start:end]
            group_extra_lines = extra_lines[start:end]
            # Create a box plot for the current group
            plt.figure(figsize=(7, 9))
            plt.boxplot(group_data, vert=True, patch_artist=True, tick_labels=group_labels)
            # Add extra lines per species
            for i, (lower_bounds, upper_bounds) in enumerate(group_extra_lines, start=1):
                plt.hlines(y=lower_bounds, xmin=i-0.3, xmax=i+0.3, colors='red', linestyles='dashed', label="Upper bounds" if i == 1 else "")
                plt.hlines(y=upper_bounds, xmin=i-0.3, xmax=i+0.3, colors='blue', linestyles='dashed', label="Lower bounds" if i == 1 else "")
            plt.ylabel("Value")
            plt.title(f"Distribution of cutoffs - {metric}")
            plt.grid(axis="y", linestyle="--", alpha=0.6)
            # Convert x labels to "First letter. Second word" format
            new_labels = [f"{label.split()[0][0]}. {label.split()[1]}" for label in group_labels]
            plt.xticks(ticks=range(1, len(new_labels) + 1), labels=new_labels, rotation=45)
            plt.savefig(os.path.join(workdir, f"{metric}_boxplot_{start}.png"))
            plt.close('all')

if __name__ == "__main__":
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
    parser = argparse.ArgumentParser(
        description="Process assembly stats and generate plots."
    )
    parser.add_argument(
        "--workdir", type=str, default="calculate_workdir", help="Working directory"
    )
    parser.add_argument(
        "--species_file",
        type=str,
        default="calculate_workdir/test_species.tsv",
        help="Path to a file containing the list of species to include, one species per line",
    )
    parser.add_argument(
        "--metrics_list",
        type=str,
        nargs="+",
        default=METRICS_LIST,
        help="List of metrics to include",
    )
    args = parser.parse_args()
    main(args)
