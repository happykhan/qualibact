from sklearn.ensemble import IsolationForest
import os 
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ks_2samp, wasserstein_distance
from scipy.stats import normaltest
from tqdm import tqdm
import statsmodels.api as sm

DEF_METRIC_LIST = ['total_length', 'GC_Content', 'N50', 'number', 'longest' , 'Completeness_Specific', 'Contamination']


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


def apply_outlier_filter(species_data: pd.DataFrame, metrics_list=DEF_METRIC_LIST, random_state=42) -> pd.DataFrame:
        outlier_data = species_data[metrics_list]
        # Train Isolation Forest
        # Parameters
        iso_forest = IsolationForest(random_state=random_state)
        iso_forest.fit(outlier_data)
        # Calculate anomaly scores and classify anomalies
        species_data['anomaly_score'] = iso_forest.decision_function(outlier_data)
        species_data['anomaly'] = iso_forest.predict(outlier_data)
        species_data['anomaly'].value_counts()
        return species_data


def basic_stats(metric, metric_data):
    metric_summary = {'metric': metric}
    if isinstance(metric_data, pd.Series):
        metric_data = metric_data.dropna()
    if len(metric_data) > 8:
        _, p = normaltest(metric_data)               
        metric_summary["distribution"] = "normal" if p > 0.05 else "non-normal"
    else:
        metric_summary["distribution"] = "insufficient_data"
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


def special_score_plot(filtered_data:pd.DataFrame, x_col: str, y_col: str):

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
    cbar_ax = g.figure.add_axes([1.02, 0.25, 0.02, 0.5]) # type: ignore[reportCallIssue]
    norm = plt.Normalize(filtered_data["anomaly_score"].min(), filtered_data["anomaly_score"].max()) # type: ignore[reportCallIssue]
    smz = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
    smz.set_array([])
    g.figure.colorbar(smz, cax=cbar_ax, label="Anomaly Score")

    # Set axis labels and title
    g.set_axis_labels(x_col, y_col)
    return g

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
        for x_col, y_col in tqdm(axis_pairs, desc="Plotting axis pairs"):
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
            # Only plot KDE if there is variance in the data for both axes
            if subsampled_data[x_col].nunique() > 1 and subsampled_data[y_col].nunique() > 1:
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
    rounding = 2
    if metric == "GC_Content":
         rounding = 4
    metric_stats["MY_LOWER"] = round(min(metric_stats['lower_bound'], refseq_metric_stats["refseq_min"]), rounding)
    metric_stats["MY_UPPER"] = round(max(metric_stats["upper_bound"], refseq_metric_stats["refseq_max"]), rounding)
    plot_histogram(metric, metric_data, refseq_metric_values, species_dir)
    return metric_stats

def make_metric_stats(metric, species_data):
    this_metric_data = species_data[metric].values.flatten()

    metricdict, metric_data = basic_stats(metric, this_metric_data)
    metricdict["MY_LOWER"] = round(metricdict['lower_bound'], 2)
    metricdict["MY_UPPER"] = round(metricdict["upper_bound"], 2)
    return metricdict