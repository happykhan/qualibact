'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

// Bump the key whenever a new announcement is published. The banner
// re-shows for everyone after the bump, even if they dismissed the
// previous one.
const KEY = 'qb-announce:2026-05-21-v1.1';

export default function AnnouncementBanner() {
  // Render nothing until the client side has had a chance to check
  // localStorage; avoids a flash of the banner on every page load for
  // already-dismissed users.
  const [ready, setReady] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setReady(true);
    try {
      const dismissed = window.localStorage.getItem(KEY) === '1';
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setVisible(!dismissed);
    } catch {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setVisible(true);
    }
  }, []);

  if (!ready || !visible) return null;

  return (
    <div
      role="region"
      aria-label="Site update"
      className="bg-[color:var(--gx-accent)]/10 dark:bg-[color:var(--gx-accent)]/20 border-b border-[color:var(--gx-accent)]/30"
    >
      <div className="container py-2 px-4 flex items-center gap-3 text-sm">
        <span
          aria-hidden="true"
          className="inline-flex h-5 px-2 items-center rounded-full bg-[color:var(--gx-accent)] text-[color:var(--gx-text-inverted)] text-xs font-semibold uppercase tracking-wide flex-shrink-0"
        >
          new
        </span>
        <p className="flex-1 text-neutral-800 dark:text-neutral-100">
          <strong>21 May 2026 release —</strong>{' '}
          v1.1 thresholds (expert overrides for 15 species), a redrawn PASS / WARN / FAIL three-tier
          system, engine-flag banners on each species page, and a new{' '}
          <code className="font-mono text-xs">/api/v2/</code> threshold API.{' '}
          <Link
            href="/changelog/"
            className="underline underline-offset-2 hover:text-[color:var(--gx-accent)] font-medium"
          >
            See the full changelog →
          </Link>
        </p>
        <button
          type="button"
          aria-label="Dismiss announcement"
          onClick={() => {
            try {
              window.localStorage.setItem(KEY, '1');
            } catch {
              /* ignore */
            }
            setVisible(false);
          }}
          className="flex-shrink-0 rounded p-1 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-neutral-50 hover:bg-neutral-200/50 dark:hover:bg-neutral-700/40"
        >
          <svg
            className="w-4 h-4"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l8 8M14 6l-8 8" />
          </svg>
        </button>
      </div>
    </div>
  );
}
