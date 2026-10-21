#!/usr/bin/env python3
"""Repair the recorded H. haemolyticus lower-bound pin, preserving published rows.

The committed tree omits bulk R2 engine files, so use existing published manifests
and the standard metrics parser/API writers instead of rebuilding absent sources.
Source: Margo Diricks, Haemophilus subgroup correspondence, 14 November 2025:
'Lower bound of genome length ... change it to 1.75 Mbp.'
"""
import copy
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import build_manifests as pipeline

SPECIES = 'Haemophilus_haemolyticus'
SCHEME = 'qualibact-v1.1'

def main():
    manifests = [json.loads(p.read_text()) for p in sorted(pipeline.SPECIES_ROOT.glob('*/*/manifest.json'))]
    # Match the standard builder's published-pair filter; directories may include
    # empty species that are intentionally absent from the API.
    manifests = [m for m in manifests if m.get('counts',{}).get('genome_count',0)>0
                 or any(t.get('final_lower') is not None or t.get('final_upper') is not None
                        for t in m.get('thresholds',[]))]
    before = copy.deepcopy(manifests)
    target = next(m for m in manifests if (m['species'], m['scheme']) == (SPECIES, SCHEME))
    baseline = next(m for m in manifests if (m['species'], m['scheme']) == (SPECIES, 'qualibact-v1.0'))
    computed = next(t for t in baseline['thresholds'] if t['metric'] == 'Genome_Size')
    expected = dict(final_lower=1750000.0, final_upper=computed['final_upper'],
                    warn_lower=computed['warn_lower'], warn_upper=computed['warn_upper'])
    assert expected == dict(final_lower=1750000.0, final_upper=2100000.0,
                            warn_lower=1800000.0, warn_upper=2100000.0)
    metrics_path = pipeline.SPECIES_ROOT / SPECIES / SCHEME / f'{SPECIES}_metrics.csv'
    with metrics_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['species','metric','FINAL_lower','FINAL_upper','WARN_lower','WARN_upper','source'])
        for row in target['thresholds']:
            if row['metric']=='longest':continue
            values = dict(expected if row['metric']=='Genome_Size' else row)
            # Preserve the engine's seven-criterion, directional download contract.
            # API compatibility fields on unused sides are not classifier bounds.
            if row['metric'] in ['N50','Completeness_Specific']:
                values['final_upper']=values['warn_upper']=None
            if row['metric'] in ['no_of_contigs','Contamination']:
                values['final_lower']=values['warn_lower']=None
            metric='Completeness' if row['metric']=='Completeness_Specific' else row['metric']
            writer.writerow([SPECIES.replace('_',' '),metric,
                *[values[k] for k in ['final_lower','final_upper','warn_lower','warn_upper']],row['source']])
    parsed = pipeline.read_metrics_csv(metrics_path.parent, SPECIES)
    for row in target['thresholds']:
        if row['metric'] == 'Genome_Size':
            row.update(parsed['Genome_Size'])
            row['lower'],row['upper'] = row['final_lower'],row['final_upper']
            assert row['final_lower'] <= row['warn_lower'] <= row['warn_upper'] <= row['final_upper']
    # All other thresholds and all source summary/metadata fields must be retained.
    for old,new in zip(before,manifests):
        for a,b in zip(old['thresholds'],new['thresholds']):
            if (new['species'],new['scheme'],b['metric']) != (SPECIES,SCHEME,'Genome_Size'):
                assert a==b,(new['species'],new['scheme'],b['metric'])
        for key in old:
            if key!='thresholds':assert old[key]==new[key]
    counts_path=pipeline.REPO_ROOT/'scripts/baselines/hhaem-v1.1-classification-counts.json'
    if counts_path.exists():
        counts=json.loads(counts_path.read_text())
        assert sum(counts[k] for k in ['pass_count','warn_count','fail_count'])==counts['total']==158
        for key in ['pass_count','warn_count','fail_count']:target['counts'][key]=counts[key]
    # Preserve the committed summary catalogue; replace only this scheme's
    # three classification counts, not its derivation count or any other row.
    summary_path=pipeline.SUMMARY_DIR/'species_counts.csv'
    original_bytes=summary_path.read_bytes()
    lines=original_bytes.decode().splitlines(keepends=True)
    header=next(csv.reader([lines[0]]))
    changed=[]
    for index,line in enumerate(lines[1:],start=1):
        cells=next(csv.reader([line]))
        row=dict(zip(header,cells))
        if (row.get('species'),row.get('scheme')) != (SPECIES.replace('_',' '),SCHEME):continue
        before_row=row.copy()
        for field in ['pass_count','warn_count','fail_count']:row[field]=str(target['counts'][field])
        assert all(row[k]==v for k,v in before_row.items() if k not in ['pass_count','warn_count','fail_count'])
        output=io.StringIO(newline='')
        csv.writer(output,lineterminator='\r\n' if line.endswith('\r\n') else '\n').writerow([row[k] for k in header])
        lines[index]=output.getvalue()
        changed.append(index)
    assert len(changed)==1
    revised=''.join(lines).encode()
    old_lines=original_bytes.decode().splitlines(keepends=True)
    assert all(a==b for index,(a,b) in enumerate(zip(old_lines,lines)) if index not in changed)
    summary_path.write_bytes(revised)
    assert pipeline._csv_to_xlsx(summary_path,summary_path.with_suffix('.xlsx'),'species_counts')>0
    target['generated_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    pipeline.write_per_species_manifests([target])
    pairs={}
    for m in manifests:pairs.setdefault(m['species'],[]).append(m['scheme'])
    preferred={sp:pipeline.infer_preferred(scs) for sp,scs in pairs.items()}
    external_before = {p: p.read_bytes() for p in (pipeline.API_DIR/'external').glob('*.json')}
    pipeline.write_aggregates_from_pairs(manifests,pairs,preferred,target['generated_at'])
    for path, payload in external_before.items():
        old_json=json.loads(payload);new_json=json.loads(path.read_text())
        old_json.pop('generated_at',None);new_json.pop('generated_at',None)
        assert old_json==new_json
        path.write_bytes(payload)
    pipeline.write_genus_csvs(manifests)
    pipeline._csv_to_xlsx(pipeline.API_DIR/'thresholds.csv',pipeline.API_DIR/'thresholds.xlsx','thresholds')
    rationale = pipeline.REPO_ROOT/'content/threshold-rationale.yml'
    (pipeline.API_DIR/'threshold-rationale.yml').write_bytes(rationale.read_bytes())
    print('PASS: corrected lower pin; inherited computed WARN bounds; every other published threshold unchanged.')

if __name__=='__main__':main()
