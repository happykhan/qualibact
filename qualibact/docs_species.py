
from pathlib import Path
import pandas as pd
from rich import print
import os 

def create_species_list_page(output_dir, genera_dict):
    """Create a markdown page listing all species with links to their pages"""
    output_dir = Path(output_dir)
    species_list_path = output_dir / "species.md"
    
    with open(species_list_path, 'w') as f:
        f.write("# Species Overview\n\n")
        f.write("This page lists all species analyzed in QualiBact. Click on a species name to view its detailed page. Click the genus name for another page. \n\n")
        for genus, species_dirs in sorted(genera_dict.items()):
            # Write genus header with link to genus page
            f.write(f"## [*{genus}*]({genus}/index.md)\n\n") 
            for species_dir in species_dirs:
                species_safe_name = species_dir.name
                species_name = species_safe_name.replace("_", " ")
                # Link to the species page
                f.write(f"- [*{species_name}*]({genus}/{species_safe_name}/index.md)\n")
        f.write("\n\n")
        f.write("For more details on the methods used to derive these metrics, please see the [Methods](methods.md) page.\n")
        f.write("For a summary of the metrics and criteria used, please see the [Summary](summary.md) page.\n")       

    
    print(f"[bold green]Species list page created at: {species_list_path}[/bold green]")




def create_species_page(species_dir: Path, output_dir: Path, species_safe_name: str, refseq_count: int, species_counts: pd.DataFrame, filter_metrics: pd.DataFrame):
    """Create a markdown page for the species"""
    output_dir = Path(output_dir)
    species_name = species_safe_name.replace("_", " ")
    species_page_path = output_dir / f"index.md"

    # Species page content. 
    # Link to Methods page /methods 
    print(species_counts)

    with open(species_page_path, 'w') as f:
        f.write(f"# *{species_name}*\n\n")
        f.write(f"This is the QualiBact page for *{species_name}*. For detailed methods on how these thresholds were calculated, please see [Methods](../../methods.md).\nThe suggested thresholds are: \n\n")
        # Show table of the metrics
        f.write(
            filter_metrics.drop(columns=["species"])
            .fillna("")
            .to_markdown(index=False)
        )
       # If any png in the directory has a space, replace it with an underscore
        for png_file in (output_dir ).glob("*.png"):
            if " " in png_file.name:
                new_name = png_file.name.replace(" ", "_")
                new_path = png_file.parent / new_name
                png_file.rename(new_path)        
        # Add download link to metrics file
        metrics_filename = f"{species_safe_name}_metrics.csv"
        f.write(f"\n\n[Download metrics CSV]({metrics_filename}){{.md-button}}\n\n")
        original_count = species_counts['original_count'].values[0] if not species_counts.empty else 0
        filtered_out_count = species_counts['filtered_out_count'].values[0] if not species_counts.empty else 0
        finally_count = species_counts['final_count'].values[0] if not species_counts.empty else 0
        f.write(f"\nThese thresholds are based on **{refseq_count}** genomes from RefSeq and **{original_count}** genomes from ATB / SRA.\n")
        f.write(f"\nThese thresholds were applied to all the bacteria dataset, which resulted in removing **{filtered_out_count}** and retaining **{finally_count}**.\n")
        f.write(f"The list of genomes retained (i.e. high quality) and the list of genomes rejected (filtered) can be downloaded below. These files are in `.xz` format. The rejected genomes file, also includes the reason why.\n")
        # Download link to high quality genomes
        hq_genomes_file = species_dir / f"{species_safe_name}_high_quality_genomes.csv.xz"
        hq_genomes_link = f"{hq_genomes_file.name}"
        f.write(f"\n[Download high quality genomes list]({hq_genomes_link})\n\n")
        filtered_genomes_file = species_dir / f"{species_safe_name}_filtered_out_genomes.csv.xz"
        filtered_genomes_link = f"{filtered_genomes_file.name}"
        f.write(f"\n[Download rejected genomes list]({filtered_genomes_link})\n\n")
        # A link to full summary tables 
        f.write("\n\n## Summary Tables\n")
        f.write("These tables provide a summary of the distribution of each metric, including SDeviation, Mean, Median, and Percentiles.\n\n")
        f.write(f"[Download full summary tables](summary.csv)\n\n")
        f.write(f"[Download simple summary tables](selected_summary.csv)\n\n")        
        # Link to methods page
        # Show plots 
        # Link to other plots 
        # Show image of Genome_Size_refseq_histogram_kde.png 
        genome_size_plot = species_dir / "Genome_Size_refseq_histogram_kde.png"
        # What is the filename of the CDS plot ??
        cds_plot = species_dir / f"{species_safe_name}_CDS_vs_Genome_Size.png"
        if not os.path.exists(cds_plot):   
            cds_plot = species_dir / f"{species_name}_CDS_vs_Genome_Size.png"
        if not os.path.exists(cds_plot):
            cds_plot = species_dir / "CDS_vs_Genome_Size.png"

        if os.path.exists(genome_size_plot):
            f.write("## Plots and Visualizations\n\n")
            f.write("This plot is a histogram comparing genome sizes between the SRA and RefSeq datasets. Each bar represents the density of genomes within a specific size range for both datasets. By comparing the shapes and positions of the bars, you can identify differences in genome size distributions, such as shifts, peaks, or outliers. This visualization helps reveal whether one dataset tends to have larger or smaller genomes, or if there are notable differences in variability or coverage between SRA and RefSeq.\n\n")
            f.write(f"![Genome Size Distribution]({genome_size_plot.name})\n\n")
        if os.path.exists(species_dir / "Genome_Size_refseq_qqplot.png"):
            genome_size_qq_plot = species_dir / "Genome_Size_refseq_qqplot.png"
            f.write("This plot is a QQ (quantile-quantile) plot, which compares the distribution of the SRA data with RefSeq. Points falling along the diagonal line indicate that the data follows the expected distribution. Deviations from the line suggest departures from normality, such as skewness or outliers. This helps assess whether the dataset is consistently distributed or if there are systematic differences.\n\n")
            f.write(f"![Genome Size QQ Plot]({genome_size_qq_plot.name})\n\n")
        if os.path.exists(cds_plot):
            f.write("This plot shows the relationship between the number of coding sequences (CDS) and genome size. It helps to visualize how genome size correlates with the number of genes. This should be linear - as the genome size increases, the number of coding sequences should also increase. Any secondary trend lines or non-linear behaviour indicates bone fide seperate populations within the retained genomes, or some remaining contaminant. \n\n")
            f.write(f"![CDS vs Genome Size]({cds_plot.name})\n\n")
        if os.path.exists(species_dir / "GC_Content_refseq_histogram_kde.png"):
            # Add Links to remaining plots
            f.write("### Additional Plots\n\n")
            f.write("These plots provide additional insights into the genome characteristics:\n\n")
            f.write(f"- [GC Content Histogram](GC_Content_refseq_histogram_kde.png)\n")
            f.write(f"- [GC Content QQ Plot](GC_Content_refseq_qqplot.png)\n")
            f.write(f"- [Total Coding Sequences Histogram](Total_Coding_Sequences_refseq_histogram_kde.png)\n")
            f.write(f"- [Total Coding Sequences QQ Plot](Total_Coding_Sequences_refseq_qqplot.png)\n")
            f.write(f"- [Genome Size Histogram](Genome_Size_refseq_histogram_kde.png)\n")
            f.write(f"- [Genome Size QQ Plot](Genome_Size_refseq_qqplot.png)\n")
        f.write("## Illustrating the filtering process\n")
        f.write("These plots illustrate the data, pre and post filtering to demostrate what type of outliers have been removed. While this was applied to all metrics, we will demonstrate using total assembly length and N50.\n\n")
        # Show filtered plots
        f.write("N50 vs total length for all genomes in the dataset.\n\n")
        f.write(f"![ALL Total Length vs N50]({species_dir.name}_all_total_length_N50.png)\n\n")
        f.write("N50 vs total length for genomes in the dataset, coloured according to whether they are an anomaly or not.\n\n")        
        f.write(f"![Sampled Total Length vs N50]({species_dir.name}_sample_total_length_N50.png)\n\n")
        f.write("N50 vs total length post filtering on the dataset.\n\n")
        f.write(f"![Filtered Total Length vs N50]({species_dir.name}_filt_total_length_N50.png)\n\n")                
        # Show reamining plots
        f.write("### Additional Plots\n\n")
        f.write("These plots provide additional insights into the genome characteristics:\n\n")
        f.write(f"- [N50 vs number of contigs, all genomes]({species_dir.name}_all_N50_number.png)\n")
        f.write(f"- [N50 vs number of contigs, sampled genomes]({species_dir.name}_sample_N50_number.png)\n")
        f.write(f"- [N50 vs number of contigs, filtered genomes]({species_dir.name}_filt_N50_number.png)\n")
        f.write(f"- [GC Content vs Total Length, all genomes]({species_dir.name}_all_total_length_GC_Content.png)\n")
        f.write(f"- [GC Content vs Total Length, sampled genomes]({species_dir.name}_sample_total_length_GC_Content.png)\n")
        f.write(f"- [GC Content vs Total Length, filtered genomes]({species_dir.name}_filt_total_length_GC_Content.png)\n") 
        f.write(f"- [Longest Contig vs Total Length, all genomes]({species_dir.name}_all_total_length_longest.png)\n")
        f.write(f"- [Longest Contig vs Total Length, sampled genomes]({species_dir.name}_sample_total_length_longest.png)\n")
        f.write(f"- [Longest Contig vs Total Length, filtered genomes]({species_dir.name}_filt_total_length_longest.png)\n")

        