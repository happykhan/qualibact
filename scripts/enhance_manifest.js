#!/usr/bin/env node
/**
 * Enhances website_summary.json with file inventories needed for CDN/R2 deployment.
 * Adds:
 *   - filtered_plot_files per species/scheme (so server components don't need fs.readdirSync)
 *   - genera section with plot filenames per genus
 *   - has_cds_plot, has_species_json per scheme
 *
 * Run: node scripts/enhance_manifest.js
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const MANIFEST = path.join(ROOT, 'public', 'website_summary.json');
const STATIC = path.join(ROOT, 'public', 'static');

const data = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));

// Enhance species schemes
for (const [species, info] of Object.entries(data.species || {})) {
  for (const [scheme, schemeData] of Object.entries(info.schemes || {})) {
    const schemeDir = path.join(STATIC, 'species', species, scheme);

    // filtered_plot_files
    const filteredDir = path.join(schemeDir, 'filtered_plots');
    if (fs.existsSync(filteredDir)) {
      schemeData.filtered_plot_files = fs.readdirSync(filteredDir)
        .filter(f => /\.(png|jpg|jpeg)$/i.test(f))
        .sort();
    } else {
      schemeData.filtered_plot_files = [];
    }

    // has_cds_plot
    const cdsFile = `${species}_CDS_vs_Genome_Size.png`;
    const cdsAlt = `${species.replace(/_/g, ' ')}_CDS_vs_Genome_Size.png`;
    schemeData.has_cds_plot = fs.existsSync(path.join(schemeDir, cdsFile))
      || fs.existsSync(path.join(schemeDir, cdsAlt));

    // has_species_json (the large RefSeq reports JSON)
    const jsonCandidates = [
      path.join(schemeDir, `${species}.json`),
      path.join(schemeDir, `${species.replace(/_/g, ' ')}.json`),
    ];
    const foundJson = jsonCandidates.find(f => fs.existsSync(f));
    schemeData.has_species_json = !!foundJson;
    if (foundJson) {
      schemeData.species_json_filename = path.basename(foundJson);
    }

    // has_refseq_gz (compressed RefSeq table)
    const gzFile = path.join(schemeDir, `${species}_refseq_genomes.csv.gz`);
    const xzFile = path.join(schemeDir, `${species}_refseq_genomes.csv.xz`);
    schemeData.has_refseq_archive = fs.existsSync(gzFile) || fs.existsSync(xzFile);
  }
}

// Build genera section
const genera = {};
const genusDir = path.join(STATIC, 'genus');
if (fs.existsSync(genusDir)) {
  for (const genus of fs.readdirSync(genusDir)) {
    const gPath = path.join(genusDir, genus);
    if (!fs.statSync(gPath).isDirectory()) continue;
    const files = fs.readdirSync(gPath);
    const plots = files.filter(f => /\.(png|jpg|jpeg)$/i.test(f)).sort();
    genera[genus] = { plots };

    // Check for plots subdirectory
    const plotsSubdir = path.join(gPath, 'plots');
    if (fs.existsSync(plotsSubdir)) {
      genera[genus].subdir_plots = fs.readdirSync(plotsSubdir)
        .filter(f => /\.(png|jpg|jpeg)$/i.test(f)).sort();
    }
  }
}
data.genera = genera;

fs.writeFileSync(MANIFEST, JSON.stringify(data, null, 2));
console.log('Enhanced website_summary.json with file inventories.');
console.log(`  Species: ${Object.keys(data.species).length}`);
console.log(`  Genera: ${Object.keys(genera).length}`);
