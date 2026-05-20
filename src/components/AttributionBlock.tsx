import { attributionsFor } from '@/app/contributors/lib';

interface Props {
  species: string;
  scheme: string;
  /** When true, render inline (no outer card border) so the block can sit
   *  inside another card without nested borders. */
  embedded?: boolean;
}

export default function AttributionBlock({ species, scheme, embedded = false }: Props) {
  const attributions = attributionsFor(species, scheme);
  if (attributions.length === 0) return null;

  const outerClass = embedded
    ? 'space-y-3 pt-3 mt-1 border-t border-neutral-200 dark:border-neutral-700'
    : 'card p-4 space-y-3 border-l-4 border-brand-300 dark:border-brand-700';

  return (
    <section className={outerClass}>
      <h3 className="font-semibold font-header text-neutral-900 dark:text-neutral-100">
        Acknowledgements
      </h3>
      {attributions.map((a, idx) => (
        <div key={`${a.species}-${a.scheme}-${idx}`} className="space-y-2 text-sm">
          {a.contributors.length > 0 && (
            <p className="text-neutral-700 dark:text-neutral-300">
              Threshold values and rationale for{' '}
              <em>{a.species.replace(/_/g, ' ')}</em> ({a.scheme}) contributed by:
            </p>
          )}
          {a.contributors.length > 0 && (
            <ul className="space-y-1 ml-1">
              {a.contributors.map((c) => (
                <li key={c.id} className="text-neutral-800 dark:text-neutral-200">
                  <strong className="font-medium">{c.name}</strong>
                  {c.affiliation && (
                    <span className="text-neutral-600 dark:text-neutral-400">
                      , {c.affiliation}
                      {c.country ? `, ${c.country}` : ''}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
          {a.funding.length > 0 && (
            <p className="text-xs text-neutral-500 dark:text-neutral-400 italic">
              Supported by:{' '}
              {a.funding.map((f, i) => (
                <span key={f.id}>
                  {i > 0 && '; '}
                  {f.name}
                  {f.note ? ` (${f.note})` : ''}
                </span>
              ))}
              .
            </p>
          )}
          {a.note && (
            <p className="text-xs text-neutral-500 dark:text-neutral-400 italic">{a.note}</p>
          )}
        </div>
      ))}
    </section>
  );
}
