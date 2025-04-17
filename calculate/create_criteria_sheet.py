import csv

def standard_metrics(species):
    output_criteria = [] 
    output_criteria.append({
        "species": species,
        "assembly_type": "all",
        "software": "Checkm",
        "field": "Marker lineage",
        "operator": "regex",
        "value": f"^{species}.+",
        "special_field": "species_field"
    })
    # Add Speciator and Sylph criteria for the species
    output_criteria.append({
        "species": species,
        "assembly_type": "all",
        "software": "Speciator",
        "field": "speciesName",
        "operator": "regex",
        "value": f"^{species}",
        "special_field": "species_field"
    })
    output_criteria.append({
        "species": species,
        "assembly_type": "all",
        "software": "Speciator",
        "field": "confidence",
        "operator": "regex",
        "value": "^good$",
        "special_field": ""
    })
    genus_name = species.split(" ")[0]  # Split species on space and take the first part
    output_criteria.append({
        "species": species,
        "assembly_type": "all",
        "software": "Speciator",
        "field": "genusName",
        "operator": "regex",
        "value": f"^{genus_name}",
        "special_field": ""
    })
    output_criteria.append({
        "species": species,
        "assembly_type": "all",
        "software": "Sylph",
        "field": "number_of_genomes",
        "operator": "=",
        "value": 1,
        "special_field": ""
    })
    output_criteria.append({
        "species": species,
        "assembly_type": "all",
        "software": "Sylph",
        "field": "species_name",
        "operator": "regex",
        "value": "^.+",
        "special_field": "species_field"
    })
    output_criteria.append({
        "species": species,
        "assembly_type": "short",
        "software": "Ariba",
        "field": "percent",
        "operator": "=",
        "value": 100,
        "special_field": ""
    })
    output_criteria.append({
        "species": species,
        "assembly_type": "all", 
        "software": "Quast",
        "field": "Ns per 100 kbp",
        "operator": "<=",
        "value": 1000,
        "special_field": ""
    })    
    return output_criteria

output_criteria = [] 
# Create the "all" default criteria
fieldnames = ["species", "assembly_type", "software", "field", "operator", "value", "special_field"]
default_criteria = [
    ["all", "all", "Checkm", "Completeness", ">=", 80, ""],
    ["all", "all", "Checkm", "Contamination", "<=", 20, ""],
    ["all", "all", "Checkm", "Marker lineage", "regex", "^.+", "species_field"],
    ["all", "all", "Checkm", "GC", ">=", 25, ""],
    ["all", "all", "Checkm", "GC", "<=", 75, ""],
    ["all", "all", "Checkm", "Genome size (bp)", ">=", 500000, ""],
    ["all", "all", "Checkm", "Genome size (bp)", "<=", 1200000, ""],
    ["all", "short", "Checkm", "# contigs", "<=", 900, ""],
    ["all", "short", "Checkm", "N50 (scaffolds)", ">", 15000, ""],
    ["all", "short", "Quast", "N50", ">", 15000, ""],
    ["all", "short", "Quast", "# contigs (>= 0 bp)", "<", 900, ""],
    ["all", "all", "Quast", "Total length (>= 0 bp)", ">", 500000, ""],
    ["all", "all", "Quast", "Total length (>= 0 bp)", "<", 1200000, ""],
    ["all", "all", "Quast", "GC (%)", ">", 25, ""],
    ["all", "all", "Quast", "GC (%)", "<", 75, ""],
    ["all", "all", "Quast", "Ns per 100 kbp", "<=", 1000, ""],
    ["all", "all", "Speciator", "speciesName", "regex", "^.+", "species_field"],
    ["all", "all", "Speciator", "confidence", "regex", "^good$", ""],
    ["all", "all", "Speciator", "genusName", "regex", "^.+", ""],
    ["all", "all", "Sylph", "number_of_genomes", "=", 1, ""],
    ["all", "all", "Sylph", "species_name", "regex", "^.+", "species_field"],
    ["all", "short", "Ariba", "percent", "=", 100, ""],
]
for default in default_criteria:
    # Append the default criteria to output_criteria
    output_criteria.append(dict(zip(fieldnames, default)))


# Input data
with open('calculate_workdir/all_summary/all_metrics_summary.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    input_data = [row for row in reader]

species_list = []
for row in input_data:
    species = row['species']
    species_list.append(species)
    new_metric = {'species': species}
    if row['metric'] == "N50":
        # QUAST N50
        n50 = float(row['MY_LOWER'])
        # Round to lower 1000 
        n50 = int(n50 - (n50 % 1000))
        new_metric['field'] = "N50"
        new_metric['assembly_type'] = "short"
        new_metric['software'] = "Quast"
        new_metric['operator'] = ">="
        new_metric['value'] = n50
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        new_metric = {'species': species}
        new_metric['field'] = "N50 (scaffolds)"
        new_metric['assembly_type'] = "short"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = ">="
        new_metric['value'] = n50
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
    elif row['metric'] == "Genome_Size":
        # QUAST total length
        total_length = float(row['MY_LOWER'])
        # Round to lower 100000 
        total_length = int(total_length - (total_length % 100000))
        new_metric = {'species': species}
        new_metric['field'] = "Total length (>= 0 bp)"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Quast"
        new_metric['operator'] = ">="
        new_metric['value'] = total_length
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)         
        new_metric = {'species': species}
        new_metric['field'] = "Genome size (bp)"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = ">="
        new_metric['value'] = total_length
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)          
        total_length = float(row['MY_UPPER'])
        # Round to upper 100000 
        total_length = int(total_length + (100000 - (total_length % 100000)) % 100000)
        new_metric = {'species': species}
        new_metric['field'] = "Total length (>= 0 bp)"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Quast"
        new_metric['operator'] = "<="
        new_metric['value'] = total_length
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)         
        new_metric = {'species': species}
        new_metric['field'] = "Genome size (bp)"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = "<="
        new_metric['value'] = total_length
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)       
    if row['metric'] == "Completeness_Specific":
        # CheckM completeness
        completeness = float(row['MY_LOWER'])
        new_metric['field'] = "Completeness"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = ">="
        new_metric['value'] = completeness
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
    elif row['metric'] == "Contamination":
        # CheckM contamination
        contamination = float(row['MY_UPPER'])
        new_metric['field'] = "Contamination"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = "<="
        new_metric['value'] = contamination
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
    elif row['metric'] == "GC_Content":
        # CheckM GC
        gc = round(float(row['MY_LOWER']) * 100, 2)
        new_metric['field'] = "GC"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = ">="
        new_metric['value'] = gc
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        new_metric = {'species': species}
        # Quast GC 
        new_metric['field'] = "GC (%)"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Quast"
        new_metric['operator'] = ">="
        new_metric['value'] = gc
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        new_metric = {'species': species}

        gc = round(float(row['MY_UPPER']) * 100, 2)
        new_metric['field'] = "GC"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = "<="
        new_metric['value'] = gc
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        new_metric = {'species': species}
        new_metric['field'] = "GC (%)"
        new_metric['assembly_type'] = "all"
        new_metric['software'] = "Quast"
        new_metric['operator'] = "<="
        new_metric['value'] = gc
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
    elif row["metric"] == "number":
        # CheckM number of contigs
        number = int(float(row['MY_UPPER']) + (100 - (float(row['MY_UPPER']) % 100)) % 100)
        new_metric['field'] = "# contigs"
        new_metric['assembly_type'] = "short"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = "<="
        new_metric['value'] = number
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        new_metric = {'species': species}
        # Quast number of contigs
        new_metric['field'] = "# contigs (>= 0 bp)"
        new_metric['assembly_type'] = "short"
        new_metric['software'] = "Quast"
        new_metric['operator'] = "<="
        new_metric['value'] = number
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        number = int(float(row["MY_LOWER"]))
        new_metric = {'species': species}
        new_metric['field'] = "# contigs"
        new_metric['assembly_type'] = "short"
        new_metric['software'] = "Checkm"
        new_metric['operator'] = ">="
        new_metric['value'] = number
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        new_metric = {'species': species}
        # Quast number of contigs
        new_metric['field'] = "# contigs (>= 0 bp)"
        new_metric['assembly_type'] = "short"
        new_metric['software'] = "Quast"
        new_metric['operator'] = ">="
        new_metric['value'] = number
        new_metric['special_field'] = ""
        output_criteria.append(new_metric)
        new_metric = {'species': species}
        


        

species_list = list(set(species_list))  
for spec in species_list:
    # Add the standard metrics for each species
    output_criteria.extend(standard_metrics(spec))                 

# Output results
with open("criteria.csv", "w", newline="", encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(sorted(output_criteria, key=lambda x: [x[field] for field in fieldnames]))
