# This method will prepare the dataframes required for the genomeqc module (speccheck)
import os
import logging
import pandas as pd
from genomeqc.prepare_util import create_full_df, filter_assembly_data, get_df
from genomeqc.refseq import run_datasets_summary    
from tqdm import tqdm


def prepare_genomeqc_dataframes(workdir, metadata_path, submit=False):
    # Merge the metadata dataframes from atb. 
    # Filter the inccorect species records.
    # Creat the final filtered dataframe
    # Retrieve refseq statistics
    pq_table_path = os.path.join(workdir, "assembly_stats.parquet")
    os.makedirs(workdir, exist_ok=True)
    assembly_full_df, assembly_filtered_df = get_df(
        pq_table_path=pq_table_path,
        workdir=workdir,
        metadata_path=metadata_path,
        min_genome_count=100,  # Minimum number of genomes per species
    )
    logging.info("Dataframe loaded with %d rows", len(assembly_filtered_df))
    logging.info("Ignoring full dataframe with %d rows", len(assembly_full_df))
    species_list = assembly_filtered_df["species_sylph"].unique().tolist()
    for species in tqdm(species_list, desc="Processing species"):
        # make a dir for species
        safe_species = species.replace(" ", "_").replace("/", "_")
        species_dir = os.path.join(workdir, safe_species)
        os.makedirs(species_dir, exist_ok=True)
        # Separate the filtered dataframe by species, make separate files.
        species_df = assembly_filtered_df[
            assembly_filtered_df["species_sylph"] == species
        ].copy()
        # Write the species dataframe to a parquet file
        species_df.to_parquet(
            os.path.join(species_dir, f"{safe_species}_assembly_stats.parquet"), index=False
        )
        # get the refseq statistics
        run_datasets_summary(
            taxon=species,
            outdir=species_dir,
            assembly_source="RefSeq",
            assembly_level="complete",
        )
        # Make a batch script to run genomeqc for this species (SLURM job)
        batch_script_path = os.path.join(species_dir, f"run_genomeqc_{safe_species}.sh")
        python_path = os.path.abspath(os.environ.get("GENOMEQC_PYTHONPATH", "python3"))

        with open(batch_script_path, "w") as f:
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(parent_dir, "genomeqc-run.py")
            abs_species_dir = os.path.abspath(species_dir)
            # genomeqc-run.py calculate "Escherichia coli" output_genomeqc/Escherichia_coli/ 
            f.write(f"""#!/bin/bash
#SBATCH --job-name=genomeqc_{safe_species}
#SBATCH --output={abs_species_dir}/genomeqc_{safe_species}.out
#SBATCH --error={abs_species_dir}/genomeqc_{safe_species}.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1

{python_path} {script_path} calculate "{species}" {abs_species_dir} 
""")
        os.chmod(batch_script_path, 0o755)
        if submit:
            os.system(f"sbatch {batch_script_path}")
    