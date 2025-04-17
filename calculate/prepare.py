import gzip 
import re 
import pandas as pd
import os
import requests

# Function to extract genus and species
def rename_species(name):
    pattern = r"^([A-Za-z]+)_?[A-Za-z]*\s([a-z]+)"
    match = re.search(pattern, name)
    if match:
        return f"{match.group(1)} {match.group(2)}"  # Genus species format
    return name  # Return unchanged if no match


def get_file(url, workdir, prefix):
    """
    Downloads a file from a given URL and saves it to a specified directory with a given prefix.

    Args:
        url (str): The URL to download the file from.
        workdir (str): The directory where the file should be saved.
        prefix (str): The prefix to use for the saved file's name.

    Returns:
        str: The path to the downloaded file.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request.
        OSError: If there is an issue writing the file to disk.
    """
    # Download the file list
    file_list_path = f"{workdir}/{prefix}.tsv.gz"
    if not os.path.exists(file_list_path):
        file_list_response = requests.get(url, timeout=10)
        with open(file_list_path, "wb") as f:
            f.write(file_list_response.content)
    return file_list_path


def filter_assembly_data(assembly_stats, min_genome_count=None, species_list=None):
    assembly_stats["species_sylph"] = assembly_stats["species_sylph"].apply(rename_species)
    # Rename Clostridioides difficile to Clostridium difficile
    assembly_stats["species_sylph"] = assembly_stats["species_sylph"].replace(
        "Clostridioides difficile", "Clostridium difficile"
    )        
    # Species that dont work 
    excluded_species = ["Salmonella diarizonae", "Sarcina perfringens"]
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
        assembly_stats = assembly_stats.groupby("species_sylph").filter(
            lambda x: len(x) >= min_genome_count
        )
    return assembly_stats


def prepare(workdir):
    """
    Prepares and processes the assembly statistics by downloading and merging necessary files.

    Args:
        workdir (str): The working directory where files will be downloaded and processed.

    Returns:
        pd.DataFrame: A DataFrame containing the merged assembly statistics with additional species and checkm information.

    The function performs the following steps:
    1. Reads the list of all available files from 'all_atb_files.tsv'.
    2. Extracts URLs for the latest file list, assembly stats, and checkm stats.
    3. Downloads the files from the extracted URLs.
    4. Reads and processes the downloaded files.
    5. Merges the assembly stats with species information from the file list.
    6. Merges the assembly stats with checkm statistics.
    """
    # The rest of the code should be inside this main function
    # Fetch the file list from allthebacteria,
    all_atb_files = pd.read_csv(f"{workdir}/all_atb_files.tsv", sep="\t")

    # open all_atb_files.tsv and get link for file list. url where filename is File_Lists/file_list.all.latest.tsv.gz
    # get latest assembly stats url where filename is Aggregated/Latest_2024-08/assembly-stats.tsv.gz

    file_list_url = all_atb_files.loc[
        all_atb_files["filename"] == "File_Lists/file_list.all.latest.tsv.gz", "url"
    ].values[0]
    assembly_stats_url = all_atb_files.loc[
        all_atb_files["filename"].str.contains(
            "Aggregated/Latest_2024-08/assembly-stats.tsv.gz"
        ),
        "url",
    ].values[0]
    checkm_url = all_atb_files.loc[
        all_atb_files["filename"].str.contains(
            "Aggregated/Latest_2024-08/checkm2.tsv.gz"
        ),
        "url",
    ].values[0]

    # download the file and get the list of files
    file_list_path = get_file(file_list_url, workdir, "file_list")
    # download assembly stats file and get the assembly stats
    assembly_stats_path = get_file(assembly_stats_url, workdir, "assembly_stats")
    # download checkm file and get the checkm stats
    checkm_path = get_file(checkm_url, workdir, "checkm")
    assembly_stats = None
    # Read the extracted file list
    with gzip.open(file_list_path, "rt") as f:
        file_list = pd.read_csv(f, sep="\t")
    with gzip.open(checkm_path, "rt") as f:
        checkm_stats = pd.read_csv(f, sep="\t")
    with gzip.open(assembly_stats_path, "rt") as f:
        assembly_stats = pd.read_csv(f, sep="\t")
        # add species column to the assembly stats from the file list
        assembly_stats = assembly_stats.merge(
            file_list[["sample", "species_sylph"]], on="sample"
        )
        # add checkm column to the assembly stats from the checkm stats
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
        )
    return assembly_stats