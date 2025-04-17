# GenomeQC

A Python script for analyzing microbial genome assembly statistics across multiple species. It compares allthebacteria assemblies to NCBI RefSeq assemblies and generates detailed statistics, outlier detection with **Isolation Forest**, and visualizations.

This is the criteria used in Speccheck: https://github.com/happykhan/speccheck


## 📊 Features

- Parses genome assembly statistics.
- Compares user assemblies to RefSeq for multiple metrics.
- Detects outliers using Isolation Forest and DBSCAN.
- Generates:
  - Histograms with KDE
  - Q-Q plots
  - Joint distribution plots
  - Anomaly score visualizations
  - Summary CSVs for each species

## 🚀 Usage

### Command Line

```bash
python calculate_criteria.py \
    --workdir <working_directory> \
    --species_file <species_file.txt> \
    --min_genome_count <min_count> \
```

## 📤 Output

- Per-species plots (`*.png`) and CSV summaries (`summary.csv`, `selected_summary.csv`)
- Combined summary tables across species (`all_metrics.csv`, `all_metrics_summary.csv`)
- Outlier visualizations with anomaly scores and joint KDEs

## 📦 Dependencies

- Python ≥ 3.7
- pandas
- numpy
- seaborn
- matplotlib
- scipy
- scikit-learn

Install them with:

```bash
pip install -r requirements.txt
```

## 📬 Contributing

If you find issues or have suggestions, feel free to open an issue or submit a pull request!
