import gzip 
import re 
import pandas as pd
import os
import logging 

# Function to extract genus and species
def rename_species(name):
    pattern = r"^([A-Za-z]+)_?[A-Za-z]*\s([a-z]+)"
    match = re.search(pattern, name)
    if match:
        return f"{match.group(1)} {match.group(2)}"  # Genus species format
    return name  # Return unchanged if no match


def get_df(pq_table_path, workdir, metadata_path, min_genome_count=None, species_list=None, force=False):
    filtered_file = os.path.join(workdir, "assembly_stats_filtered.parquet")
    if not os.path.exists(pq_table_path) or force or not os.path.exists(filtered_file):
        full_df = create_full_df(metadata_path)
        full_df, full_df_filtered = filter_assembly_data(full_df, min_genome_count, species_list)
        # Save the dataframe to a parquet file
        full_df.to_parquet(pq_table_path, index=False)  
        logging.info("Parquet file created at %s", pq_table_path)
        full_df_filtered.to_parquet(
            os.path.join(workdir, "assembly_stats_filtered.parquet"), index=False
        )
        # Create a table of species and their counts for full_df
        species_counts = full_df['species_sylph'].value_counts().reset_index()
        species_counts.columns = ['species_sylph', 'count']
        # Write to csv
        species_counts = species_counts.rename(columns={'species_sylph': 'species'})
        species_counts.to_csv(
            os.path.join(workdir, "species_counts.csv"), index=False
        )
    else:
        full_df = pd.read_parquet(pq_table_path)
        logging.info("Parquet file loaded from %s", pq_table_path)
        full_df_filtered = pd.read_parquet(filtered_file)
    return full_df, full_df_filtered

def filter_assembly_data(assembly_stats, min_genome_count=None, species_list=None):
    # remove rows where species_sylph is NaN
    assembly_stats = assembly_stats[~assembly_stats["species_sylph"].isna()]
    assembly_stats["species_sylph"] = assembly_stats["species_sylph"].apply(rename_species)
    # Rename Clostridioides difficile to Clostridium difficile
    assembly_stats["species_sylph"] = assembly_stats["species_sylph"].replace(
        "Clostridioides difficile", "Clostridium difficile"
    )        
    # Species that dont work 
    excluded_species = ["Salmonella diarizonae", "Sarcina perfringens", "Salmonella houtenae"]
    assembly_stats = assembly_stats[~assembly_stats["species_sylph"].isin(excluded_species)]
    # filter on species list
    if species_list is not None:
        # Remove any species that are not in the list
        assembly_stats = assembly_stats[assembly_stats["species_sylph"].isin(species_list)]
    assembly_stats = assembly_stats[~assembly_stats["species_sylph"].str.contains(";")]
    # filter species == unknown
    assembly_stats = assembly_stats[
        ~assembly_stats["species_sylph"].str.contains("unknown")
    ]    
    if min_genome_count is not None:
        # Do not include rows where number per species < MIN_GENOME_COUNT
        assembly_stats_filtered = assembly_stats.copy().groupby("species_sylph").filter(
            lambda x: len(x) >= min_genome_count
        )
    else:
        assembly_stats_filtered = assembly_stats.copy()
    return assembly_stats, assembly_stats_filtered


def create_full_df(workdir, gc_content_file='/well/aanensen/shared/atb/gc/merged_gc_results.tsv.gz'):
    assembly_stats_path = os.path.join(workdir, "assembly-stats.tsv.gz")
    checkm_path = os.path.join(workdir, "checkm2.tsv.gz")
    sylph_path = os.path.join(workdir, "sylph.tsv.gz")
    file_list_path = os.path.join(workdir, "file_list.all.latest.tsv.gz")
    # Check these files exist
    if not os.path.exists(assembly_stats_path) or not os.path.exists(checkm_path) or not os.path.exists(sylph_path):
        # print a file locations 
        logging.error(
            "Required files not found in the metadata path. "
            "Checked paths:\n"
            "  assembly_stats_path: %s\n"
            "  checkm_path: %s\n"
            "  sylph_path: %s\n"
            "Please ensure that assembly_stats.tsv.gz, checkm2.tsv.gz, and sylph.tsv.gz are present.",
            assembly_stats_path, checkm_path, sylph_path
        )
        raise FileNotFoundError(
            "Required files not found in the metadata path. Please ensure that assembly_stats.tsv.gz, "
            "checkm2.tsv.gz, and sylph.tsv.gz are present." )
            
    assembly_stats = None
    # Read the extracted file list
    with gzip.open(file_list_path, "rt") as f:
        file_list = pd.read_csv(f, sep="\t")
    with gzip.open(checkm_path, "rt") as f:
        checkm_stats = pd.read_csv(f, sep="\t")
    with gzip.open(assembly_stats_path, "rt") as f:
        assembly_stats = pd.read_csv(f, sep="\t")

    # Merge assembly_stats with file_list on 'sample'
    assembly_stats = assembly_stats.merge(
        file_list[["sample", "species_sylph"]], on="sample", how="left"
    )
    
    # Merge with checkm_stats on 'sample' (left) and 'Sample' (right)
    assembly_stats = assembly_stats.merge(
        checkm_stats[
            [
                "Sample",
                "GC_Content",
                "Completeness_Specific",
                "Contamination",
                "Contig_N50",
                "Total_Coding_Sequences",
                "Genome_Size",
            ]
        ],
        left_on="sample",
        right_on="Sample",
        how="left"
    )
    # Need to replace GC_Content with the GC content file  in gc_content_file. Merge on 'Sample'
    if os.path.exists(gc_content_file):
        with gzip.open(gc_content_file, "rt") as f:
            gc_content = pd.read_csv(f, sep="\t")
        # Merge with gc_content on 'Sample'
        # if gc_content column is GC_conent, rename it to GC_Content
        if "GC_content" in gc_content.columns:
            gc_content.rename(columns={"GC_content": "GC_Content"}, inplace=True)
        # Divide the GC_Content by 100 to convert it to a percentage
        if "GC_Content" in gc_content.columns:
            gc_content["GC_Content"] = gc_content["GC_Content"] / 100.
        assembly_stats = assembly_stats.merge(
            gc_content[["Sample", "GC_Content"]],
            on="Sample",
            how="left",
            suffixes=("", "_gc")
        )
        # Drop the old GC_Content column
        assembly_stats.drop(columns=["GC_Content"], inplace=True)        
        # Rename the new GC_Content column
        assembly_stats.rename(columns={"GC_Content_gc": "GC_Content"}, inplace=True)


    return assembly_stats