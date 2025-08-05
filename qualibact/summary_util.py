import os 
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from tqdm import tqdm


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
                # convert underscore to space
                species = species.replace("_", " ")
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

def tidy_summary(all_metrics_df_summary, output_dir):
    # Load the CSV file
    df = all_metrics_df_summary

    # Define metrics of interest (renamed 'number' to 'no_of_contigs')
    metrics_of_interest = ["N50", "no_of_contigs", "GC_Content", "Genome_Size", "Completeness", "Contamination", "Total_Coding_Sequences"]

    # Replace 'number' with 'no_of_contigs' in the 'metric' column if needed
    df['metric'] = df['metric'].replace('number', 'no_of_contigs')
    df['metric'] = df['metric'].replace('Completeness_Specific', 'Completeness')
    # Filter the DataFrame
    filtered_df = df[df['metric'].isin(metrics_of_interest)]

    # Select the desired columns
    result_df = filtered_df[['species', 'metric', 'MY_LOWER', 'MY_UPPER']]

    # Rename columns
    result_df = result_df.rename(columns={'MY_LOWER': 'lower_bounds', 'MY_UPPER': 'upper_bounds'})

    # Display the result
    # For N50, round to nearest thousand, lower_bounds round down, upper_bounds round up
    n50_mask = result_df['metric'] == 'N50'
    result_df.loc[n50_mask, 'lower_bounds'] = np.floor(result_df.loc[n50_mask, 'lower_bounds'] / 1000) * 1000
    result_df.loc[n50_mask, 'lower_bounds'] = result_df.loc[n50_mask, 'lower_bounds'].astype(int)
    # For N50, set upper_bounds to blank
    result_df.loc[n50_mask, 'upper_bounds'] = ''
    # For completeness, set upper_bounds to blank
    completeness_mask = result_df['metric'] == 'Completeness'
    result_df.loc[completeness_mask, 'upper_bounds'] = ''
    # For completeness, round lower_bounds to nearest whole number
    result_df.loc[completeness_mask, 'lower_bounds'] = result_df.loc[completeness_mask, 'lower_bounds'].apply(lambda x: int(np.floor(float(x))) if x != '' else '')

    # For contamination, set lower_bounds to blank
    contamination_mask = result_df['metric'] == 'Contamination'
    result_df.loc[contamination_mask, 'lower_bounds'] = ''
    # For contamination, round upper_bounds to nearest whole number
    result_df.loc[contamination_mask, 'upper_bounds'] = result_df.loc[contamination_mask, 'upper_bounds'].apply(lambda x: int(np.ceil(float(x))) if x != '' else '')
    # For total coding sequences, round to nearest 100, lower_bounds round down, upper_bounds round up
    tcs_mask = result_df['metric'] == 'Total_Coding_Sequences'
    result_df.loc[tcs_mask, 'lower_bounds'] = result_df.loc[tcs_mask, 'lower_bounds'].apply(lambda x: int(np.floor(float(x) / 100) * 100) if x != '' else '')
    result_df.loc[tcs_mask, 'upper_bounds'] = result_df.loc[tcs_mask, 'upper_bounds'].apply(lambda x: int(np.ceil(float(x) / 100) * 100) if x != '' else '')

    # For no_of_contigs, set lower_bounds to blank and ensure upper_bounds is rounded up to nearest 10 and integer
    contigs_mask = result_df['metric'] == 'no_of_contigs'
    result_df.loc[contigs_mask, 'lower_bounds'] = ''
    result_df.loc[contigs_mask, 'upper_bounds'] = result_df.loc[contigs_mask, 'upper_bounds'].apply(lambda x: int(np.ceil(float(x) / 10) * 10) if x != '' else '')

    # For GC_Content, multiply lower_bounds and upper_bounds by 100
    # Only do this for non-empty lower_bounds/upper_bounds

    gc_mask = result_df['metric'] == 'GC_Content'
    result_df.loc[gc_mask, 'lower_bounds'] = result_df.loc[gc_mask, 'lower_bounds'].apply(lambda x: int(np.floor(float(x)*100)) if x != '' else '')
    result_df.loc[gc_mask, 'upper_bounds'] = result_df.loc[gc_mask, 'upper_bounds'].apply(lambda x: int(np.ceil(float(x)*100)) if x != '' else '')

    # For Genome_Size, round to nearest 100000, lower_bounds round down, upper_bounds round up
    gs_mask = result_df['metric'] == 'Genome_Size'
    result_df.loc[gs_mask, 'lower_bounds'] = result_df.loc[gs_mask, 'lower_bounds'].apply(lambda x: int(np.floor(float(x) / 100000) * 100000) if x != '' else '')
    result_df.loc[gs_mask, 'upper_bounds'] = result_df.loc[gs_mask, 'upper_bounds'].apply(lambda x: int(np.ceil(float(x) / 100000) * 100000) if x != '' else '')

    result_df.to_csv(os.path.join(output_dir, "filtered_metrics.csv"), index=False)

    # For each metric, plot the range (lower_bounds to upper_bounds) for each species
    metrics = result_df['metric'].unique()

    for metric in tqdm(metrics, desc="Plotting metrics"):
        df_metric = result_df[result_df['metric'] == metric].copy()
        # Convert bounds to numeric, coerce errors to NaN (for blank fields)
        df_metric['lower_bounds'] = pd.to_numeric(df_metric['lower_bounds'], errors='coerce')
        df_metric['upper_bounds'] = pd.to_numeric(df_metric['upper_bounds'], errors='coerce')
        # Sort by plotting value (x value) for N50 and no_of_contigs, otherwise by lower_bounds
        if metric in  ['N50', 'Completeness']:
            df_metric = df_metric.sort_values(by='lower_bounds', na_position='last')
        elif metric in ['no_of_contigs', 'Contamination']:
            df_metric = df_metric.sort_values(by='upper_bounds', na_position='last')
        else:
            df_metric = df_metric.sort_values(by='lower_bounds', na_position='last')
        plt.figure(figsize=(12, max(6, len(df_metric) // 2)))
        sns.set(style="whitegrid", font_scale=1.1)
        plt.title(f"Ranges for {metric} across species", fontsize=16, fontweight='bold')
        plt.xlabel("Value", fontsize=14)
        plt.ylabel("Species", fontsize=14)
        if metric in ['N50', 'Completeness']:
            # For N50, plot only the lower_bound as a point
            sns.scatterplot(x='lower_bounds', y='species', data=df_metric, s=80, color=sns.color_palette("deep")[0], marker='o', edgecolor='black', zorder=3)
        elif metric in ['no_of_contigs', 'Contamination']:
            # For no_of_contigs, plot only the upper_bound as a point
            sns.scatterplot(x='upper_bounds', y='species', data=df_metric, s=80, color=sns.color_palette("deep")[0], marker='o', edgecolor='black', zorder=3)
        else:
            # Plot a horizontal line for each species using seaborn for color palette
            for idx, row in df_metric.iterrows():
                y = row['species']
                if not np.isnan(row['lower_bounds']) and not np.isnan(row['upper_bounds']):
                    plt.hlines(y, row['lower_bounds'], row['upper_bounds'], color=sns.color_palette("deep")[0], linewidth=3)
                    plt.plot([row['lower_bounds'], row['upper_bounds']], [y, y], '|', color=sns.color_palette("deep")[2], markersize=18)
                elif not np.isnan(row['lower_bounds']):
                    plt.plot(row['lower_bounds'], y, '|', color=sns.color_palette("deep")[2], markersize=18)
                elif not np.isnan(row['upper_bounds']):
                    plt.plot(row['upper_bounds'], y, '|', color=sns.color_palette("deep")[2], markersize=18)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"metric_range_{metric}.png"), dpi=150)
        plt.close()
    return result_df