'use client';

import { useState } from 'react';

interface Item {
  species: string;
  scheme: string;
  href: string;
}

interface Props {
  items: Item[];
  initialVisible?: number;
}

export default function ContributorContributions({ items, initialVisible = 3 }: Props) {
  const [expanded, setExpanded] = useState(false);
  if (items.length === 0) return null;
  const shouldCollapse = items.length > initialVisible;
  const visible = shouldCollapse && !expanded ? items.slice(0, initialVisible) : items;
  const hiddenCount = items.length - initialVisible;
  return (
    <div className="space-y-1">
      <p className="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-500 font-medium">
        Contributions
      </p>
      <ul className="space-y-1">
        {visible.map((a, i) => (
          <li key={`${a.species}-${a.scheme}-${i}`} className="text-sm">
            <a
              href={a.href}
              className="text-brand-700 dark:text-brand-300 underline underline-offset-2 hover:text-brand-900 dark:hover:text-brand-200"
            >
              <em>{a.species.replace(/_/g, ' ')}</em>
            </a>
            <span className="text-neutral-500 dark:text-neutral-500"> · {a.scheme}</span>
          </li>
        ))}
      </ul>
      {shouldCollapse && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-xs font-medium text-brand-700 dark:text-brand-300 hover:text-brand-900 dark:hover:text-brand-200 underline-offset-2 hover:underline"
          aria-expanded={expanded}
        >
          {expanded ? 'Show fewer' : `+ ${hiddenCount} more`}
        </button>
      )}
    </div>
  );
}
