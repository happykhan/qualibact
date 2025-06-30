import os 
import logging 
import pandas as pd
from tqdm import tqdm

from genomeqc.species_util import DEF_METRIC_LIST
from genomeqc.summary_util import plot_summary_plot, tidy_summary
from genomeqc.final_package import main as final_package_main

def summary(output_dir):
    # Go back through output directory and summarize the results
    # each dir is an species dir.
    species_dirs = [d for d in os.listdir(output_dir) 
                    if os.path.isdir(os.path.join(output_dir, d)) and d not in ['all_summary', 'GENUS_SUMMARY']]
    all_summary_dir = os.path.join(output_dir, 'all_summary')
    os.makedirs(all_summary_dir, exist_ok=True)
    all_summary = []
    all_selected_summary = []
    missing_summary_files = []
    for species in tqdm(species_dirs, desc="Processing species"):
        species_path = os.path.join(output_dir, species)
        # Check if the species directory contains the expected files
        summary_file = os.path.join(species_path, 'summary.csv')
        selected_summary_file = os.path.join(species_path, 'selected_summary.csv')
        assmbly_stats_file = os.path.join(species_path, f'{species}_assembly_stats.parquet')
        if (not os.path.exists(summary_file) or 
            not os.path.exists(selected_summary_file) or 
            not os.path.exists(assmbly_stats_file)):
            logging.error("Missing required file: %s or %s or %s in %s", 
                          summary_file, 
                          selected_summary_file, 
                          assmbly_stats_file, 
                          species_path)
            missing_summary_files.append(species)
            continue
        # get csv
        summary_table = pd.read_csv(summary_file)
        summary_table['species'] = species
        all_summary.append(summary_table)

        selected_summary = pd.read_csv(selected_summary_file)
        selected_summary['species'] = species
        # check selected_summary has species column
        if 'species' not in selected_summary.columns:
            logging.error(
                "Selected summary file %s does not contain 'species' column",
                selected_summary_file
            )
            missing_summary_files.append(species)
            continue
        all_selected_summary.append(selected_summary)
    # merge all the dataframes into one for each list 
    all_summary_df = pd.concat(all_summary, ignore_index=True)
    all_selected_summary_df = pd.concat(all_selected_summary, ignore_index=True)
    logging.error("Missing summary files for species: %s", ", ".join(missing_summary_files))
    # check if all_summary
    # save the merged dataframes
    all_summary_df.to_csv(os.path.join(all_summary_dir, 'all_metrics_summary.csv'), index=False)
    all_selected_summary_df.to_csv(os.path.join(all_summary_dir, 'all_metrics_selected_summary.csv'), index=False)
    # make the simplified criteria table - with the number adjusted to be tidy 
    final_df = tidy_summary(all_summary_df, all_summary_dir)
    # Then we need to apply these cut offs to the selected assembly_stats_file and make a final list of accepted genomes
    # Make a summary table, of original record count, filtered out record count, and final record count
    counts = [] 
    for species in tqdm(species_dirs, desc="Processing species for final selection"):
        if species in missing_summary_files:
            continue
        species_path = os.path.join(output_dir, species)
        assmbly_stats_file = os.path.join(species_path, f'{species}_assembly_stats.parquet')
        # read the assembly stats file
        assembly_stats_df = pd.read_parquet(assmbly_stats_file)
        
        # rename the columns to match the final_df
        assembly_stats_df.rename(columns={
            'number': 'no_of_contigs',
            'Completeness_Specific': 'Completeness'
        }, inplace=True)
        assembly_stats_df['GC_Content'] = (assembly_stats_df['GC_Content'] * 100).round(0)
        assembly_stats_df_ori = assembly_stats_df.copy()
        metric_list = final_df['metric'].unique().tolist()
        species_thresholds = final_df[final_df['species'] == species]
        
        for metric in metric_list:
            if metric in assembly_stats_df.columns:
                # get the lower and upper bounds for this metric
                lower_bound = species_thresholds[species_thresholds['metric'] == metric]['lower_bounds'].values[0]
                upper_bound = species_thresholds[species_thresholds['metric'] == metric]['upper_bounds'].values[0]
                # filter the assembly stats df for this metric
                if lower_bound != '' and upper_bound != '':
                    assembly_stats_df = assembly_stats_df[(assembly_stats_df[metric] >= lower_bound) & (assembly_stats_df[metric] <= upper_bound)]
                elif lower_bound != '':
                    assembly_stats_df = assembly_stats_df[assembly_stats_df[metric] >= lower_bound]
                elif upper_bound != '':
                    assembly_stats_df = assembly_stats_df[assembly_stats_df[metric] <= upper_bound]                
            else:
                logging.warning(
                    "Metric %s not found in species %s assembly stats file %s", metric, species, assmbly_stats_file)
        # Create another csv file, of the records that were filtered out
        filtered_out_df = assembly_stats_df_ori[~assembly_stats_df_ori.index.isin(assembly_stats_df.index)]
        if not filtered_out_df.empty:
            logging.debug(
                "Writing filtered out genomes for species %s to %s (%d)", species, os.path.join(species_path, f'{species}_rejected_genomes.csv'), len(filtered_out_df))
            filtered_out_df.to_csv(os.path.join(species_path, f'{species}_filtered_out_genomes.csv'), index=False)
        else:
            logging.debug("No genomes were filtered out for species %s", species)              
        # write species_raw df to a new file - csv 
        if len(assembly_stats_df) == 0:
            logging.warning("No genomes passed the quality criteria for species %s", species)
            continue
        logging.debug(
            "Writing high quality genomes for species %s to %s (%d)", species, os.path.join(species_path, f'{species}_high_quality_genomes.csv'), len(assembly_stats_df))
        assembly_stats_df.to_csv(os.path.join(species_path, f'{species}_high_quality_genomes.csv'), index=False)
        counts.append({
            'species': species,
            'original_count': len(assembly_stats_df_ori),
            'filtered_out_count': len(filtered_out_df),
            'final_count': len(assembly_stats_df)
        })
    # save the counts to a csv file
    # check if counts has original_count, filtered_out_count, final_count
    if not all(key in counts[0] for key in ['original_count', 'filtered_out_count', 'final_count']):
        logging.error("Counts dictionary does not have the required keys.")
    else:
        counts_df = pd.DataFrame(counts)
        # Sort the counts_df by 'original_count' in descending order before saving
        counts_df = counts_df.sort_values(by='original_count', ascending=False)
        counts_df.to_csv(os.path.join(all_summary_dir, 'species_counts.csv'), index=False)
        logging.debug("Species counts saved to %s", os.path.join(all_summary_dir, 'species_counts.csv'))
    # make box plots of each metric
    plot_dir = os.path.join(all_summary_dir, 'plots')
    os.makedirs(plot_dir, exist_ok=True)
    for metric in tqdm(DEF_METRIC_LIST, desc="Plotting summary box plots metrics"):
        plot_summary_plot(metric, all_summary_df, plot_dir)
    
    