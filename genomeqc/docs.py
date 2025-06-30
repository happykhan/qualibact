import os
import shutil
from pathlib import Path
from rich import print
from rich.progress import track
from genomeqc.docs_util import create_methods_page, create_index_page, write_mkdocs_yml, get_rejection_reasons
from genomeqc.docs_summary import create_summary_page
from genomeqc.docs_species import create_species_page, create_species_list_page
import json
import pandas as pd
import lzma
from genomeqc.species_util import DEF_METRIC_LIST
from genomeqc.summary_util import plot_summary_plot


def fix_filtered_out_genomes(filtered_csv: Path, output_file: Path, metrics_df: pd.DataFrame):
        df = pd.read_csv(filtered_csv)
        df['rejection_reason'] = df.apply(lambda row: "; ".join(get_rejection_reasons(row, metrics_df)), axis=1)
        with lzma.open(output_file, "wt") as f:
            df.to_csv(f, index=False)


def files_to_fetch(species_dir: Path, output_dir: Path, metrics_df: pd.DataFrame):
    # get files that end with CDS_vs_Genome_Size.png
    files_to_copy = []
    files_to_compress = []
    for file in species_dir.glob("*_CDS_vs_Genome_Size.png"):
        files_to_copy.append(os.path.join(species_dir, file.name))
    for file in species_dir.glob("*_filtered_out_genomes.csv"):
        files_to_compress.append(os.path.join(species_dir, file.name))
    for file in species_dir.glob("*_high_quality_genomes.csv"):
        files_to_compress.append(os.path.join(species_dir, file.name))
    # get files 
    files_to_copy.append(os.path.join(species_dir, "GC_Content_refseq_histogram_kde.png"))
    files_to_copy.append(os.path.join(species_dir, "GC_Content_refseq_qqplot.png"))
    files_to_copy.append(os.path.join(species_dir, "Genome_Size_refseq_histogram_kde.png"))
    files_to_copy.append(os.path.join(species_dir, "Genome_Size_refseq_qqplot.png"))
    files_to_copy.append(os.path.join(species_dir, "selected_summary.csv"))
    files_to_copy.append(os.path.join(species_dir, "summary.csv"))
    files_to_copy.append(os.path.join(species_dir, "Total_Coding_Sequences_refseq_histogram_kde.png"))
    files_to_copy.append(os.path.join(species_dir, "Total_Coding_Sequences_refseq_qqplot.png"))
    files_to_compress = [file for file in files_to_compress if os.path.exists(file)]
    # filtered_plots folder 
    filtered_plots_dir = species_dir / "filtered_plots"
    species_name = species_dir.name.replace("_", " ")
    if filtered_plots_dir.exists():
        # Copy specific plot files from filtered_plots directory
        patterns = [
            f"{species_name}_*_total_length_GC_Content.png",
            f"{species_name}_*_total_length_longest.png",
            f"{species_name}_*_total_length_N50.png",
            f"{species_name}_*_total_length_number.png",
            f"{species_name}_*_N50_number.png",
        ]
        for pattern in patterns:
            for file in filtered_plots_dir.glob(pattern):
                files_to_copy.append(str(file))
    # Warn if any of the files are missing
    missing_files = [file for file in files_to_copy if not os.path.exists(file)]
    if missing_files:
        print(f"[bold red]Warning: The following files are missing in {species_dir}:[/bold red]")
        for missing_file in missing_files:
            print(f" - {missing_file}")
    else:
        print(f"[bold green]All expected files found in {species_dir}.[/bold green]")

    for files in files_to_compress:
        output_file = os.path.join(output_dir, os.path.basename(files) + ".xz")
        if os.path.exists(output_file):
            print(f"[bold yellow]Skipping existing compressed file: {output_file}[/bold yellow]")
            continue
        # Zip these up  xz -c output_genomeqc/Salmonella_enterica/Salmonella_enterica_high_quality_genomes.csv  -9 -T 4
        if files.endswith("_filtered_out_genomes.csv"):
            fix_filtered_out_genomes(files, Path(output_file), metrics_df)
        else:
            with open(files, "rb") as f_in, open(output_file, "wb") as f_out:
                f_out.write(lzma.compress(f_in.read(), preset=9))
    for files in files_to_copy:
        shutil.copy(files, output_dir)
    return files_to_copy

def get_refseq_counts(species_dir: Path):
    """Calculate number of genomes in the refseq"""
    # Json name has a space 
    space_name = species_dir.name.replace("_", " ")
    species_json = species_dir / f"{space_name}.json"
    if species_json.exists():
        with open(species_json, 'r') as f:
            data = json.load(f)
            return data.get("total_count", 0)
    print(f"[bold red]Warning: {species_json} not found. Returning 0.[/bold red]")
    return 0

def create_genus_overview_page(genus_dir: Path , all_species_count_df, all_summary_df, species_list):
    """Create a genus overview page"""
    # Create genus plots, if number of species is greater than 1
    genus_summary_df = all_summary_df[all_summary_df['species'].str.startswith(genus_dir.name)]
    output_path = Path(genus_dir) / "index.md"
    
    lines = [
        f"# *{genus_dir.name.title()}* Overview\n",    
        "This page provides an overview of the genus, including links to species-specific pages and general information.\n\n",
    ]
    genus_count_df = all_species_count_df[all_species_count_df['species'].str.startswith(genus_dir.name)]
    for species_dir in sorted(species_list, key=lambda x: os.path.basename(x).lower()):
        species_safe_name = os.path.basename(species_dir)
        species_name = os.path.basename(species_dir).replace("_", " ")
        lines.append(f"- [Species page: {species_name}]({species_safe_name}/index.md)\n")
    if not genus_count_df.empty:
        lines.append("## Genus Species Count Summary\n")
        lines.append("Breakdown of genomes filtered and retained by using these metrics:\n\n")
        
        # Convert the DataFrame to markdown using pandas
        genus_count_md = genus_count_df.head(20).to_markdown(index=False)
        lines.append(genus_count_md + "\n")
        if len(genus_count_df) > 20:
            lines.append(f"\n... and {len(genus_count_df) - 20} more rows\n")
        
        lines.append(f"\n\n[📊 Download species counts table](species_counts.csv){{.md-button}}\n")
        # Write the species counts to a CSV file
        genus_count_df.to_csv(genus_dir / "species_counts.csv", index=False)
    if not genus_summary_df.empty:
        lines.append("## Genus Summary Metrics\n")
        lines.append("This section provides a summary of the metrics for the genus:\n\n")
        
        # Convert the DataFrame to markdown using pandas
        genus_summary_md = genus_summary_df.head(20).to_markdown(index=False)
        lines.append(genus_summary_md + "\n")
        if len(genus_summary_df) > 20:
            lines.append(f"\n... and {len(genus_summary_df) - 20} more rows\n")
        
        lines.append(f"\n\n[📊 Download genus summary metrics table](genus_summary_metrics.csv){{.md-button}}\n")
        # Write the genus summary to a CSV file
        genus_summary_df.to_csv(genus_dir / "genus_summary_metrics.csv", index=False)
        # Find all png files in genus_dir
        png_files = list(genus_dir.glob("*.png"))
        if png_files:
            lines.append("## Genus Visualizations\n")
            lines.append("These plots show the main summary visualizations for this genus, including distributions of key genomic metrics such as genome size, GC content, number of contigs, and other relevant statistics. The boxplot for each species is based on the distribution (i.e. median, q1, q3, min and max) of the filtered genomes. The red line is the lower threshold and the blue line is the upper threshold. Use these plots to compare and explore the diversity and characteristics of genomes within this genus:\n\n")
            for png_file in sorted(png_files):
                metric_name = png_file.stem.split('_')[0].title()
                lines.append(f"- [Distribution of {metric_name} for this genus]({png_file.name})\n")            
            # Show GC_Content, Genome_size and number of contigs
            for png_file in sorted(png_files):
                if png_file.name.startswith("GC_Content") or png_file.name.startswith("Genome_Size") or png_file.name.startswith("number"):
                    metric_name = png_file.stem.split('_')[0].title()
                    lines.append(f"![Distribution of {metric_name}]({png_file.name})\n")

    with open(output_path, "w") as f:
        f.writelines(lines)
    
    print(f"[bold green]Created genus overview page: {output_path}[/bold green]")

def create_genus_plots(metrics_df, plot_dir):
    """Create placeholder plots for genus overview"""
    # This function can be expanded to generate actual plots if needed
    for metric in DEF_METRIC_LIST + ['Genome_Size', 'Total_Coding_Sequences']:
        plot_summary_plot(metric, metrics_df, plot_dir)       

def generate_docs(calculate_dir, docs_dir: Path = Path("docs")):
    """Generate documentation structure"""
    species_dirs = [Path(d) for d in Path(calculate_dir).iterdir() if d.is_dir() and d.name != "all_summary"]
    all_summary_file = Path(calculate_dir) / "all_summary" / "filtered_metrics.csv"
    all_summary_df = pd.read_csv(all_summary_file)
    all_species_count_file = Path(calculate_dir) / "all_summary" / "species_counts.csv"
    all_species_count_df = pd.read_csv(all_species_count_file)
    all_stats_df = pd.read_csv(Path(calculate_dir) / "all_summary" / "all_metrics_summary.csv")
    os.makedirs(docs_dir, exist_ok=True)
    print("[bold cyan]🏠 Creating main pages...[/bold cyan]")
    create_index_page(docs_dir)
    print("[bold cyan]📋 Creating methods page...[/bold cyan]")
    create_methods_page(docs_dir)

    # Group species into genera
    genera_dict = {}
    for species_dir in species_dirs:
        species_safe_name = os.path.basename(species_dir)
        genus = species_safe_name.split('_')[0]
        genera_dict.setdefault(genus, []).append(species_dir)
    print("[bold cyan]📁 Creating documentation structure...[/bold cyan]")
    
    for genus, species_list in track(genera_dict.items(), description="Processing genera..."):
        # Create genus overview page
        os.makedirs(Path(docs_dir) / genus, exist_ok=True)
        genus_summary_df = all_stats_df[all_stats_df['species'].str.startswith(genus)]
        if len(species_list) > 1:
            create_genus_plots(genus_summary_df, Path(docs_dir) / genus)
        create_genus_overview_page(Path(docs_dir) / genus, all_species_count_df, all_summary_df, species_list)
        for species_dir in species_list:
            species_safe_name = os.path.basename(species_dir)
            species_name = os.path.basename(species_dir).replace("_", " ")
            output_dir = Path(docs_dir) / genus / species_safe_name
            output_dir.mkdir(parents=True, exist_ok=True)
            # from all_summary/
            # filtered_metrics (for that species)
            # species_count (for that species)
            species_counts = all_species_count_df[all_species_count_df['species'] == species_safe_name]
            refseq_count = get_refseq_counts(species_dir)
            filter_metrics = all_summary_df[all_summary_df['species'] == species_safe_name].copy()
            # Warn if filter_metrics is empty
            if filter_metrics.empty:
                print(all_summary_df.head())
                print(f"[bold red]Warning: No metrics found for species {species_name} in {species_dir}.[/bold red]")
                continue
            filter_metrics.to_csv(output_dir / f"{species_safe_name}_metrics.csv", index=False)        
            # species_dir/ 
            files_to_fetch(species_dir, output_dir, filter_metrics) 
            # Create spacies page 
            create_species_page(species_dir, output_dir, species_safe_name, refseq_count, species_counts, filter_metrics)
    create_species_list_page(docs_dir, genera_dict)
    # Copy all_summary dirs to docs_dir
    print("[bold cyan]📊 Creating summary page...[/bold cyan]")
    # Copy calculate_dir / all_summary to docs_dir / summary
    all_summary_dir = Path(calculate_dir) / "all_summary"
    docs_dir = Path(docs_dir)
    summary_dir = docs_dir / "summary"
    # Delete existing summary directory if it exists
    if summary_dir.exists():
        print(f"[bold yellow]Deleting existing summary directory: {summary_dir}[/bold yellow]")
        shutil.rmtree(summary_dir)
    shutil.copytree(all_summary_dir, summary_dir)
    create_summary_page(summary_dir, docs_dir)
    print("[bold cyan]⚙️ Writing mkdocs.yml configuration...[/bold cyan]")
    write_mkdocs_yml()    
    print("[bold green]✅ MkDocs site generated. Run [yellow]mkdocs serve[/yellow] to preview.[/bold green]")
    

    

    
    
    

