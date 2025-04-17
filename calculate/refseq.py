import json
import subprocess
import os 
import time

def run_datasets_summary(taxon, assembly_source="RefSeq", assembly_level="complete", reference=False):
    os.makedirs("output_json", exist_ok=True)
    output_json = os.path.join("output_json", f"{taxon}.json")
    if os.path.exists(output_json) and os.path.getsize(output_json) > 0:
        with open(output_json, "r", encoding="utf-8") as f:
            return json.load(f)
    command = [
        "bin/datasets", "summary", "genome", "taxon", f'{taxon}',
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

    extracted_data['GC_Content'] = float(report['assembly_stats']['gc_percent'] / 100.00)
    extracted_data['Genome_Size'] = int(report['assembly_stats']['total_sequence_length'])
    extracted_data['total_length'] = int(report['assembly_stats']['total_sequence_length'])
    
    extracted_data["Total_Coding_Sequences"] = int(report['annotation_info']['stats']['gene_counts']['total'])
    # Extract CheckM information
    checkm_info = report.get("checkm_info", {})
    extracted_data["Completeness_Specific"] = checkm_info.get("completeness", None)
    extracted_data["Contamination"] = checkm_info.get("contamination", None)
    
    return extracted_data

def get_metrics(taxon):
    json_data = run_datasets_summary(taxon)

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
        json_data = run_datasets_summary(taxon)

    for dat in json_data["reports"]:
        extracted_metrics = extract_metrics(dat)
        for key, value in extracted_metrics.items():
            if value is not None:
                metrics_dict[key].append(value)
    return metrics_dict 