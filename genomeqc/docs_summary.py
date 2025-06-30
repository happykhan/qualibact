from pathlib import Path

def create_summary_page(summary_dir, docs_dir):
    """Create a summary page with main data and criteria tables"""
    docs_dir = Path(docs_dir)
    summary_path = docs_dir / "summary.md"
    
    lines = [
        "# Summary\n",
        "## The Criteria Tables",
        "**This is what you want**. \nDownload the complete quality criteria table:\n",
    ] 
    
    # Show the first few rows of DOCS_DIR/summary/filtered_metrics.csv
    filtered_metrics_path = summary_dir / "filtered_metrics.csv"
    if filtered_metrics_path.exists():
        import pandas as pd  # Import again to ensure it's available
        try:
            lines.append(f"\n[📋 Download complete filtered metrics](summary/filtered_metrics.csv){{.md-button}}\n")
            df_metrics = pd.read_csv(filtered_metrics_path)
            # Replace NaN with empty string for better display
            df_metrics.fillna('', inplace=True)
            lines.append("Here are the first few rows of the quality metrics:\n")
            
            if not df_metrics.empty:
                # Show first 5 rows with key columns
                headers = " | ".join(df_metrics.columns[:6])  # Show first 6 columns
                lines.append(f"| {headers} |")
                lines.append("|" + "---|" * min(6, len(df_metrics.columns)))
                
                for _, row in df_metrics.head(5).iterrows():
                    row_data = " | ".join(str(val)[:20] for val in row[:6])  # Truncate long values
                    lines.append(f"| {row_data} |")
                
                lines.append(f"\nShowing 5 of {len(df_metrics)} rows.")
            
        except Exception as e:
            lines.append(f"\n⚠️ Error reading filtered metrics: {e}\n")
    else:
        lines.append("\n⚠️ Filtered metrics file not found\n")
    lines += [
        "### Summary Statistics",
        "Statistics on distribution for each metric, for each species:\n",
        "[Download Summary Data (CSV)](all_metrics_selected_summary.csv){.md-button}\n",
        
    ]
    
    # Tabulate the results in DOCS_DIR/summary/species_counts.csv
    species_counts_path = summary_dir / "species_counts.csv"
    if species_counts_path.exists():
        import pandas as pd
        try:
            df_counts = pd.read_csv(species_counts_path)
            lines.append("\n### Species Count Summary")
            lines.append("Breakdown of genomes filtered and retained by using these metrics:\n")
            
            # Add table headers
            if not df_counts.empty and len(df_counts.columns) >= 3:
                headers = " | ".join(df_counts.columns)
                lines.append(f"| {headers} |")
                lines.append("|" + "---|" * len(df_counts.columns))
                
                # Add data rows (limit to first 20 for readability)
                for _, row in df_counts.head(20).iterrows():
                    row_data = " | ".join(str(val).replace('_', ' ') for val in row)
                    lines.append(f"| {row_data} |")
                
                if len(df_counts) > 20:
                    lines.append(f"| ... and {len(df_counts) - 20} more rows | | |")
            
            lines.append(f"\n[📊 Download complete species counts table](summary/species_counts.csv){{.md-button}}\n")
        except Exception as e:
            lines.append(f"\n⚠️ Error reading species counts: {e}\n")
    else:
        lines.append("\n⚠️ Species counts file not found\n")


    # Show links to all png files in DOCS_DIR/summary/
    if summary_dir.exists():
        png_files = list(summary_dir.glob("*.png"))
        if png_files:
            lines.append("## Summary Visualizations")
            lines.append("Main summary plots and visualizations:\n")
            
            for png_file in sorted(png_files):
                plot_name = png_file.stem.replace('_', ' ').title()
                lines.append(f"- [{plot_name}](summary/{png_file.name})")
        else:
            lines.append("## Summary Visualizations")
            lines.append("No PNG files found in summary directory.\n")

    # Show links to all images in DOCS_DIR/summary/plots
    plots_dir = summary_dir / "plots" if summary_dir.exists() else None
    if plots_dir and plots_dir.exists():
        plot_images = list(plots_dir.glob("*.png"))
        if plot_images:
            lines.append("## Additional Summary Plots")
            lines.append("Detailed analysis plots from the summary analysis:\n")
            
            for plot_file in sorted(plot_images):
                plot_name = plot_file.stem.replace('_', ' ').title()
                lines.append(f"- [{plot_name}](summary/plots/{plot_file.name})")
        else:
            lines.append("## Additional Summary Plots")
            lines.append("No additional plots found in summary/plots directory.\n")
    else:
        lines.append("## Additional Summary Plots")
        lines.append("Summary plots directory not found.\n")

    
    summary_path.write_text("\n".join(lines))
    print("Created summary page")