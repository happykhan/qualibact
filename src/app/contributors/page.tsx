import type { Metadata } from 'next';
import Link from 'next/link';
import ContributorContributions from '@/components/ContributorContributions';
import {
  getContributors,
  contributionsByContributor,
  type Contributor,
  type Attribution,
} from './lib';

export const metadata: Metadata = {
  title: 'Contributors',
  description:
    'Domain experts who have contributed thresholds, dataset re-curation, or species-specific rationale to QualiBact.',
};

function speciesHref(species: string): string {
  const [genus] = species.split('_');
  return `/${genus}/${species}`;
}

interface CardProps {
  contributor: Contributor;
  contributions: Attribution[];
}

function ContributorCard({ contributor, contributions }: CardProps) {
  return (
    <div className="card p-4 space-y-3">
      <div>
        <h3 className="font-semibold font-header text-neutral-900 dark:text-neutral-100">
          {contributor.name}
        </h3>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          {contributor.affiliation}
          {contributor.country ? `, ${contributor.country}` : ''}
        </p>
      </div>
      <ContributorContributions
        items={contributions.map((a) => ({
          species: a.species,
          scheme: a.scheme,
          href: speciesHref(a.species),
        }))}
      />
    </div>
  );
}

export default function ContributorsPage() {
  const contributors = getContributors();
  const reverse = contributionsByContributor();
  const sorted = [...contributors].sort((a, b) =>
    a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }),
  );

  return (
    <div className="py-8">
      <div className="space-y-8">
        <header className="space-y-3">
          <h1 className="text-3xl font-bold font-header text-neutral-900 dark:text-neutral-100">
            Contributors
          </h1>
          <p className="text-neutral-700 dark:text-neutral-300">
            QualiBact thresholds are refined by an open community of domain
            experts. The people listed below have contributed threshold
            values, dataset re-curation, or species-specific rationale to
            specific (species, scheme) pairs.
          </p>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Are you missing from this list? Contributions land via the
            expert-feedback survey or direct correspondence — see the{' '}
            <Link
              href="/organism-requests/"
              className="underline underline-offset-2 hover:text-neutral-800 dark:hover:text-neutral-200"
            >
              requests page
            </Link>{' '}
            for how to get involved.
          </p>
        </header>

        {sorted.length === 0 ? (
          <p className="text-neutral-500 dark:text-neutral-400">
            No contributors recorded yet.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sorted.map((c) => (
              <ContributorCard
                key={c.id}
                contributor={c}
                contributions={reverse[c.id] ?? []}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
