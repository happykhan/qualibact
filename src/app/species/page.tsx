import fs from 'fs';
import path from 'path';
import SpeciesFilter from '@/components/SpeciesFilter';

interface SpeciesData {
  species: string;
  qc_schemes: string[];
  preferred_qc_scheme: string | null;
}

interface IndexEntry {
  species: string;
  preferred_scheme: string | null;
  schemes: { scheme: string }[];
}

function loadSpeciesList(): SpeciesData[] {
  const p = path.join(process.cwd(), 'public', 'api', 'v2', 'index.json');
  if (!fs.existsSync(p)) return [];
  const data = JSON.parse(fs.readFileSync(p, 'utf8')) as { species: IndexEntry[] };
  return data.species
    .map((entry) => ({
      species: entry.species,
      qc_schemes: entry.schemes.map((s) => s.scheme),
      preferred_qc_scheme: entry.preferred_scheme,
    }))
    .sort((a, b) => a.species.localeCompare(b.species));
}

export default function Species() {
  const speciesList = loadSpeciesList();
  return (
    <div className="py-8">
      <div>
        <h1 className="text-3xl font-bold font-header mb-6">All Species</h1>
        <SpeciesFilter speciesList={speciesList} />
      </div>
    </div>
  );
}
