'use client';

import { useState } from 'react';
import Link from 'next/link';

interface SpeciesData {
  species: string;
  qc_schemes: string[];
  preferred_qc_scheme: string | null;
}

interface SpeciesFilterProps {
  speciesList: SpeciesData[];
}

export default function SpeciesFilter({ speciesList }: SpeciesFilterProps) {
  const [filter, setFilter] = useState('');

  // Normalise both sides: collapse underscores AND spaces to a single
  // form so "Staphylococcus coagulans", "staphylococcus_coagulans",
  // and "Staph coag" all match the same canonical key.
  const norm = (s: string) => s.toLowerCase().replace(/[_\s]+/g, ' ').trim();
  const needle = norm(filter);
  const filteredSpecies = needle
    ? speciesList.filter(item => norm(item.species).includes(needle))
    : speciesList;

  const grouped = filteredSpecies.reduce((acc, item) => {
    const genus = item.species.split('_')[0];
    if (!acc[genus]) acc[genus] = [];
    acc[genus].push(item);
    return acc;
  }, {} as Record<string, SpeciesData[]>);

  const sortedGenera = Object.keys(grouped).sort();
  const sortedGrouped = sortedGenera.map(genus => ({
    genus,
    species: grouped[genus].sort((a, b) => a.species.localeCompare(b.species))
  }));

  return (
    <>
      <input
        type="text"
        placeholder="Filter by genus or species..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full p-2 border border-neutral-300 rounded mb-4 dark:border-neutral-600 dark:bg-neutral-800 dark:text-white"
      />
      <p className="mb-6 text-neutral-700 dark:text-neutral-300">
        Showing {filteredSpecies.length} of {speciesList.length} species.
        {' '}If your species does not appear here, please review the{' '}
        <Link href="/organism-requests" className="text-brand-600 dark:text-brand-400 underline">
          organism requests page
        </Link>{' '}
        for details on upcoming additions.
      </p>
      {sortedGrouped.map(({ genus, species }) => (
        <div key={genus} className="mb-6">
          <h2 className="text-2xl font-semibold font-header mb-2">
            <Link href={`/${genus}`} className="text-brand-600 hover:underline dark:text-brand-400 italic font-header">{genus}</Link>
          </h2>
          <ul className="list-disc list-inside">
            {species.map((speciesData) => {
              const genusFromSpecies = speciesData.species.split('_')[0];
              return (
                <li key={speciesData.species}>
                  <Link href={`/${genusFromSpecies}/${speciesData.species}`} className="text-brand-600 hover:underline dark:text-brand-400 italic">{speciesData.species.replace(/_/g, ' ')}</Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </>
  );
}
