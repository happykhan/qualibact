#!/usr/bin/env python3
"""
Merge all *_filtered_out_genomes.csv.xz files from docs folder into one table.

This script:
1. Finds all *_filtered_out_genomes.csv.xz files in the docs/<genus>/<species> directory structure
2. Reads compressed .xz files directly (pandas handles this automatically)
3. Adds 'genus' and 'species' columns based on the directory structure
4. Merges them into a single CSV file
5. Provides statistics about the merged data

Usage:
    python merge_filtered_out_genomes.py
"""

import pandas as pd
import os
from pathlib import Path
import sys

def find_filtered_out_files(base_dir):
    """Find all *_filtered_out_genomes.csv.xz files in the directory tree."""
    base_path = Path(base_dir)
    csv_files = list(base_path.glob('**/*_filtered_out_genomes.csv.xz'))
    return sorted(csv_files)

def extract_species_from_path(file_path):
    """Extract genus and species name from the file path.
    
    Expected path structure: docs/Genus/Genus_species/Genus_species_filtered_out_genomes.csv.xz
    """
    # Get the parent directory name (should be species name like "Escherichia_coli")
    species = file_path.parent.name
    # Get the grandparent directory name (should be genus name like "Escherichia")
    genus = file_path.parent.parent.name
    return genus, species

def merge_filtered_out_genomes(base_dir, output_file):
    """Merge all filtered out genomes CSV.XZ files into one."""
    
    print("=" * 80)
    print("Merging Filtered Out Genomes (from .csv.xz files)")
    print("=" * 80)
    
    # Find all CSV.XZ files
    csv_files = find_filtered_out_files(base_dir)
    print(f"\nFound {len(csv_files)} *_filtered_out_genomes.csv.xz files")
    
    if not csv_files:
        print("No files found!")
        return
    
    # List to store dataframes
    all_dfs = []
    species_counts = {}
    genus_counts = {}
    
    # Read and process each file
    print("\nProcessing files...")
    for i, csv_file in enumerate(csv_files, 1):
        genus, species = extract_species_from_path(csv_file)
        
        try:
            # Read the compressed CSV file (pandas handles .xz automatically)
            df = pd.read_csv(csv_file)
            
            # Add genus and species columns at the beginning
            if 'genus' not in df.columns:
                df.insert(0, 'genus', genus)
            if 'species_name' not in df.columns:
                df.insert(1, 'species_name', species)
            
            # Count genomes per species and genus
            species_counts[species] = len(df)
            genus_counts[genus] = genus_counts.get(genus, 0) + len(df)
            
            all_dfs.append(df)
            
            # Progress indicator
            if i % 50 == 0:
                print(f"  Processed {i}/{len(csv_files)} files...")
                
        except Exception as e:
            print(f"  Error processing {csv_file}: {e}")
            continue
    
    if not all_dfs:
        print("\nNo data to merge!")
        return
    
    # Concatenate all dataframes
    print(f"\nMerging {len(all_dfs)} dataframes...")
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Save to CSV
    print(f"Saving merged data to: {output_file}")
    merged_df.to_csv(output_file, index=False)
    
    # Print statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"\nTotal filtered out genomes: {len(merged_df):,}")
    print(f"Number of species: {len(species_counts)}")
    print(f"Number of genera: {len(genus_counts)}")
    print(f"\nColumns in merged file: {list(merged_df.columns)}")
    
    # Top 20 species by filtered out genomes
    print("\n" + "-" * 80)
    print("Top 20 Species by Number of Filtered Out Genomes:")
    print("-" * 80)
    sorted_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (species, count) in enumerate(sorted_species[:20], 1):
        print(f"{i:2d}. {species:50s} {count:6,} genomes")
    
    # Top 10 genera by filtered out genomes
    print("\n" + "-" * 80)
    print("Top 10 Genera by Number of Filtered Out Genomes:")
    print("-" * 80)
    sorted_genera = sorted(genus_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (genus, count) in enumerate(sorted_genera[:10], 1):
        print(f"{i:2d}. {genus:30s} {count:6,} genomes")
    
    # Summary statistics on key metrics (if available)
    if 'Completeness' in merged_df.columns:
        print("\n" + "-" * 80)
        print("Quality Metrics Distribution:")
        print("-" * 80)
        print(f"\nCompleteness:")
        print(f"  Mean: {merged_df['Completeness'].mean():.2f}%")
        print(f"  Median: {merged_df['Completeness'].median():.2f}%")
        print(f"  Min: {merged_df['Completeness'].min():.2f}%")
        print(f"  Max: {merged_df['Completeness'].max():.2f}%")
        
    if 'Contamination' in merged_df.columns:
        print(f"\nContamination:")
        print(f"  Mean: {merged_df['Contamination'].mean():.2f}%")
        print(f"  Median: {merged_df['Contamination'].median():.2f}%")
        print(f"  Min: {merged_df['Contamination'].min():.2f}%")
        print(f"  Max: {merged_df['Contamination'].max():.2f}%")
    
    if 'Genome_Size' in merged_df.columns:
        print(f"\nGenome Size:")
        print(f"  Mean: {merged_df['Genome_Size'].mean()/1e6:.2f} Mb")
        print(f"  Median: {merged_df['Genome_Size'].median()/1e6:.2f} Mb")
        print(f"  Min: {merged_df['Genome_Size'].min()/1e6:.2f} Mb")
        print(f"  Max: {merged_df['Genome_Size'].max()/1e6:.2f} Mb")
    
    print("\n" + "=" * 80)
    print(f"Successfully merged {len(merged_df):,} genomes into {output_file}")
    print("=" * 80)
    
    return merged_df

def main():
    """Main function."""
    # Define paths
    script_dir = Path(__file__).parent.absolute()
    base_dir = script_dir.parent / 'docs'
    output_file = script_dir.parent / 'all_filtered_out_genomes.csv'
    
    # Check if base directory exists
    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        sys.exit(1)
    
    # Run the merge
    merge_filtered_out_genomes(str(base_dir), str(output_file))

if __name__ == "__main__":
    main()
