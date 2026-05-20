import {
  type PriorityList,
  type PriorityEntry,
  type PriorityTier,
  genusSpeciesList,
  speciesExists,
  speciesHref,
  genusHref,
} from './lib';
import { staticUrl } from '@/lib/static-url';

interface Props {
  list: PriorityList;
  alternateYearHref?: { year: number; href: string };
}

const TIER_STYLES: Record<string, string> = {
  Critical:
    'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-950/40',
  High:
    'border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/40',
  Medium:
    'border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-950/40',
};

interface MergedEntry {
  heading: string;
  resistances: string[];
  notes: string[];
  species?: string;
  proxySpecies?: string;
  genusGroup?: string[];
}

/**
 * Merge entries whose displayed *heading* matches — i.e. same
 * taxonomic group name before the resistance qualifier. This
 * collapses repeated rows like "Enterobacterales, 3-gen ceph-R"
 * + "Enterobacterales, carbapenem-R" into one card with both
 * resistance chips, but preserves clinically distinct entries that
 * share an underlying species key (Salmonella Typhi vs non-typhoidal
 * Salmonella both link to Salmonella_enterica but are listed
 * separately by WHO).
 */
function entryKey(entry: PriorityEntry): string {
  return entry.name.split(',')[0].trim().toLowerCase();
}

function mergeTierEntries(entries: PriorityEntry[]): MergedEntry[] {
  const order: string[] = [];
  const acc = new Map<string, MergedEntry>();
  for (const e of entries) {
    const key = entryKey(e);
    let merged = acc.get(key);
    if (!merged) {
      merged = {
        heading: e.name.split(',')[0].trim(),
        resistances: [],
        notes: [],
        species: e.species,
        proxySpecies: e.proxySpecies,
        genusGroup: e.genusGroup,
      };
      acc.set(key, merged);
      order.push(key);
    }
    if (e.resistance && !merged.resistances.includes(e.resistance)) {
      merged.resistances.push(e.resistance);
    }
    if (e.note && !merged.notes.includes(e.note)) {
      merged.notes.push(e.note);
    }
  }
  return order.map((k) => acc.get(k)!);
}

function MergedCard({ entry }: { entry: MergedEntry }) {
  let resolved: React.ReactNode = null;

  if (entry.species && speciesExists(entry.species)) {
    resolved = (
      <a
        href={speciesHref(entry.species)}
        className="text-brand-700 dark:text-brand-300 underline underline-offset-2 hover:text-brand-900 dark:hover:text-brand-200"
      >
        View QC thresholds for <em>{entry.species.replace(/_/g, ' ')}</em> &rarr;
      </a>
    );
  } else if (entry.proxySpecies && speciesExists(entry.proxySpecies)) {
    resolved = (
      <a
        href={speciesHref(entry.proxySpecies)}
        className="text-brand-700 dark:text-brand-300 underline underline-offset-2 hover:text-brand-900 dark:hover:text-brand-200"
      >
        Closest proxy: <em>{entry.proxySpecies.replace(/_/g, ' ')}</em> QC thresholds &rarr;
      </a>
    );
  } else if (entry.genusGroup && entry.genusGroup.length > 0) {
    const expanded = entry.genusGroup.flatMap((g) => genusSpeciesList(g));
    if (expanded.length > 0) {
      resolved = (
        <div className="space-y-2">
          <div className="text-sm text-neutral-600 dark:text-neutral-400">
            {expanded.length} covered species across{' '}
            {entry.genusGroup.length === 1
              ? entry.genusGroup[0]
              : entry.genusGroup.join(', ')}
            :
          </div>
          <div className="flex flex-wrap gap-2">
            {entry.genusGroup.map((g) =>
              genusSpeciesList(g).length > 0 ? (
                <a
                  key={g}
                  href={genusHref(g)}
                  className="inline-flex items-center px-2.5 py-1 rounded-full border border-brand-300 dark:border-brand-700 bg-white dark:bg-neutral-900 text-brand-700 dark:text-brand-300 text-sm hover:bg-brand-50 dark:hover:bg-brand-950"
                >
                  {g} ({genusSpeciesList(g).length})
                </a>
              ) : (
                <span
                  key={g}
                  className="inline-flex items-center px-2.5 py-1 rounded-full border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 text-neutral-500 dark:text-neutral-500 text-sm"
                >
                  {g} (no data)
                </span>
              )
            )}
          </div>
        </div>
      );
    } else {
      resolved = (
        <span className="text-sm text-neutral-500 dark:text-neutral-500">
          Data not yet available.
        </span>
      );
    }
  } else if (entry.species) {
    resolved = (
      <span className="text-sm text-neutral-500 dark:text-neutral-500">
        Data not yet available for <em>{entry.species.replace(/_/g, ' ')}</em>.
      </span>
    );
  } else {
    resolved = (
      <span className="text-sm text-neutral-500 dark:text-neutral-500">
        Data not yet available.
      </span>
    );
  }

  return (
    <div className="card p-4 space-y-3">
      <div className="space-y-2">
        <h3 className="font-semibold font-header text-neutral-900 dark:text-neutral-100">
          {entry.heading}
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {entry.resistances.map((r) => (
            <span
              key={r}
              className="text-xs px-2 py-0.5 rounded-full border border-neutral-300 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 text-neutral-700 dark:text-neutral-300 font-mono"
            >
              {r}
            </span>
          ))}
        </div>
      </div>
      <div>{resolved}</div>
      {entry.notes.map((n) => (
        <p
          key={n}
          className="text-xs text-neutral-500 dark:text-neutral-400 italic"
        >
          {n}
        </p>
      ))}
    </div>
  );
}

export default function PriorityListView({ list, alternateYearHref }: Props) {
  return (
    <div className="py-8">
      <div className="space-y-8">
        <header className="space-y-3">
          <h1 className="text-3xl font-bold font-header text-neutral-900 dark:text-neutral-100">
            WHO Bacterial Priority Pathogens ({list.year})
          </h1>
          <p className="text-neutral-700 dark:text-neutral-300">
            The World Health Organization publishes a periodic priority list of
            antibiotic-resistant bacteria to guide research, surveillance, and
            stewardship efforts. QualiBact provides species-level genome
            assembly QC thresholds for most of the species named below — click
            through to see the recommended thresholds.
          </p>
          {list.citationUrl ? (
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Source:{' '}
              <a
                href={list.citationUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="underline underline-offset-2 hover:text-neutral-800 dark:hover:text-neutral-200"
              >
                {list.citation}
              </a>
            </p>
          ) : (
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Source: {list.citation}
            </p>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <a
              href={staticUrl(`/static/priority-pathogens/who-${list.year}.csv`)}
              className="btn btn-primary"
              download
            >
              Download QC thresholds (WHO {list.year} list, CSV)
            </a>
            <span className="text-sm text-neutral-500 dark:text-neutral-400 self-center">
              4-bound thresholds (FAIL + WARN) for every species on this list,
              grouped by tier.
            </span>
          </div>
        </header>

        {list.tiers.map((tier: PriorityTier) => {
          const merged = mergeTierEntries(tier.entries);
          return (
            <section key={tier.name} className="space-y-4">
              <div
                className={`rounded-lg border-l-4 px-4 py-3 ${TIER_STYLES[tier.name] ?? ''}`}
              >
                <h2 className="text-xl font-semibold font-header text-neutral-900 dark:text-neutral-100">
                  {tier.name} priority
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {merged.map((entry) => (
                  <MergedCard key={entry.heading + entry.resistances.join('|')} entry={entry} />
                ))}
              </div>
            </section>
          );
        })}

        {alternateYearHref && (
          <footer className="border-t border-neutral-200 dark:border-neutral-800 pt-6 text-sm text-neutral-600 dark:text-neutral-400">
            See also the{' '}
            <a
              href={alternateYearHref.href}
              className="underline underline-offset-2 text-brand-700 dark:text-brand-300 hover:text-brand-900 dark:hover:text-brand-200"
            >
              {alternateYearHref.year} priority list
            </a>
            {alternateYearHref.year < list.year ? ' for historical context.' : ' (current).'}
          </footer>
        )}
      </div>
    </div>
  );
}
