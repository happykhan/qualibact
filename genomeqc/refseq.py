import os 
import json
import subprocess
import logging
import time 

def run_datasets_summary(taxon, outdir, assembly_source="RefSeq", assembly_level="complete", reference=False):
    bin_dir = os.environ.get("GENOMEQC_BIN", "bin")
    os.makedirs(outdir, exist_ok=True)
    output_json = os.path.join(outdir, f"{taxon}.json")
    if os.path.exists(output_json) and os.path.getsize(output_json) > 0:
        with open(output_json, "r", encoding="utf-8") as f:
            return json.load(f)
    command = [
        f"{bin_dir}/datasets", "summary", "genome", "taxon", f'{taxon}',
        "--assembly-source", assembly_source,
        "--assembly-level", assembly_level
    ]
    if reference:
        command.append("--reference")
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    try:
        with open(output_json, "w") as f:
            f.write(result.stdout)
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON output for {taxon}")
        return None


def extract_metrics(report):
    extracted_data = {}

    # Need to calcukate GC_Content 
    extracted_data['GC_Content'] = round(
        float(report['assembly_stats']['gc_count']) / float(report['assembly_stats']['atgc_count']), 6
    )
    extracted_data['Genome_Size'] = int(report['assembly_stats']['total_sequence_length'])
    extracted_data['total_length'] = int(report['assembly_stats']['total_sequence_length'])
    
    extracted_data["Total_Coding_Sequences"] = int(report['annotation_info']['stats']['gene_counts']['total'])
    # Extract CheckM information
    checkm_info = report.get("checkm_info", {})
    extracted_data["Completeness_Specific"] = checkm_info.get("completeness", None)
    extracted_data["Contamination"] = checkm_info.get("contamination", None)
    
    return extracted_data

def get_metrics(taxon, outdir):

    json_data = run_datasets_summary(taxon, outdir)

    metrics_dict = {
        "GC_Content": [],
        "Genome_Size": [],
        "total_length": [],
        "Total_Coding_Sequences": [],
        "Completeness_Specific": [],
        "Contamination": []
    }
    while json_data is None:
        time.sleep(5)
        json_data = run_datasets_summary(taxon, outdir)
    if json_data is None or "reports" not in json_data:
        logging.error(f"No reports found for taxon {taxon} in the JSON data.")
        return metrics_dict

    for dat in json_data["reports"]:
        extracted_metrics = extract_metrics(dat)
        for key, value in extracted_metrics.items():
            if value is not None:
                metrics_dict[key].append(value)
    return metrics_dict 