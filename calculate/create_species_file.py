from prepare import prepare, filter_assembly_data

def create_species_file(args):

    workdir = args.workdir
    min_genome_count = args.min_genome_count
    assembly_stats = prepare(workdir)    
    # Handle species with underscores
    # Rename species according to ^([A-Za-z]+)_?[A-Za-z]*\s([a-z]+) 
    assembly_stats = filter_assembly_data(assembly_stats, min_genome_count=min_genome_count)
    # Get list of species
    species_list = assembly_stats["species_sylph"].unique()
    # Sort species list
    species_list.sort()
    # Create species file
    species_file = f"{workdir}/species.tsv"
    with open(species_file, "w", encoding="utf-8") as f:
        for species in species_list:
            f.write(f"{species}\n")
    # Create species file with counts
    species_counts = assembly_stats["species_sylph"].value_counts()
    species_counts = species_counts.reset_index()
    species_counts.columns = ["species_sylph", "count"]
    # Sort species counts
    species_counts = species_counts.sort_values(by="count", ascending=False)
    # Write species counts to file
    species_counts_file = f"{workdir}/species_counts.tsv"
    with open(species_counts_file, "w", encoding="utf-8") as f:
        species_counts.to_csv(f, sep="\t", index=False)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Create species file")
    parser.add_argument("--workdir", type=str, default='calculate_workdir', help="Working directory")
    parser.add_argument("--min_genome_count", type=int, default=1000, help="Minimum genome count")
    args = parser.parse_args()
    create_species_file(args)
