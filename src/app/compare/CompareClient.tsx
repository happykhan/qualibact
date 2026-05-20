'use client';

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import SpeciesSelector from '@/components/SpeciesSelector';

interface Threshold {
  metric: string;
  lower: string | number | null;
  upper: string | number | null;
}

interface SpeciesData {
  preferred_qc_scheme?: string;
  qc_schemes?: string[];
  schemes?: Record<string, { thresholds?: Threshold[] }>;
}

type Mode = 'species' | 'versions';

function formatBound(
  lower: string | number | null | undefined,
  upper: string | number | null | undefined
): string {
  const has = (v: unknown) => v !== null && v !== undefined && v !== '';
  const l = has(lower) ? String(lower) : '-';
  const u = has(upper) ? String(upper) : '-';
  if (l === '-' && u === '-') return '-';
  if (l === '-') return `≤ ${u}`;
  if (u === '-') return `≥ ${l}`;
  return `${l} – ${u}`;
}

export default function CompareClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const mode: Mode = searchParams.get('mode') === 'versions' ? 'versions' : 'species';
  const selectedFromUrl = (searchParams.get('species') ?? '').split(',').filter(Boolean);

  const [manifestSpecies, setManifestSpecies] = useState<Record<string, SpeciesData>>({});
  const [loading, setLoading] = useState(true);

  // Hydrate from the published /api/v2/ endpoints so the compare view
  // sees the same source as Kleborate / external consumers. Combines
  // index.json (registry + preferred scheme) and thresholds.json
  // (per-(species, scheme) bound rows) into the SpeciesData shape the
  // rest of this component already speaks.
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch('/api/v2/index.json').then((r) => r.json()),
      fetch('/api/v2/thresholds.json').then((r) => r.json()),
    ])
      .then(([indexJson, thresholdsJson]) => {
        if (cancelled) return;
        const combined: Record<string, SpeciesData> = {};
        for (const entry of indexJson?.species ?? []) {
          const sp: string = entry?.species;
          if (!sp) continue;
          const schemesList: string[] = (entry?.schemes ?? [])
            .map((s: { scheme?: string }) => s?.scheme)
            .filter(Boolean);
          const thresholdSchemes: Record<string, { thresholds?: Threshold[] }> = {};
          const thrSchemes = thresholdsJson?.species?.[sp]?.schemes ?? {};
          for (const s of schemesList) {
            thresholdSchemes[s] = {
              thresholds: thrSchemes[s]?.thresholds ?? [],
            };
          }
          combined[sp] = {
            preferred_qc_scheme: entry?.preferred_scheme ?? undefined,
            qc_schemes: schemesList,
            schemes: thresholdSchemes,
          };
        }
        setManifestSpecies(combined);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function updateParams(updates: Record<string, string | null>) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(updates)) {
      if (v === null || v === '') params.delete(k);
      else params.set(k, v);
    }
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }

  function setMode(m: Mode) {
    updateParams({ mode: m === 'species' ? null : m, species: null });
  }

  function setSelected(list: string[]) {
    updateParams({ species: list.length ? list.join(',') : null });
  }

  const speciesOptions = useMemo(
    () =>
      Object.keys(manifestSpecies)
        .map((k) => ({ value: k, label: k.replace(/_/g, ' ') }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    [manifestSpecies]
  );

  const multiSchemeSpecies = useMemo(
    () =>
      Object.entries(manifestSpecies)
        .filter(([, info]) => {
          const schemes = info.qc_schemes ?? Object.keys(info.schemes ?? {});
          return schemes.length >= 2;
        })
        .map(([k]) => ({ value: k, label: k.replace(/_/g, ' ') }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    [manifestSpecies]
  );

  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold font-header mb-2">Compare</h1>
      <p className="text-neutral-600 dark:text-neutral-400 mb-6">
        Look at QualiBact QC thresholds side by side. Pick a set of species to
        compare them against each other, or pick a single species to see how
        its thresholds have changed across QC scheme versions.
      </p>

      {/* Mode tabs */}
      <div className="inline-flex rounded-full border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 p-1 mb-6">
        {(['species', 'versions'] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            aria-pressed={mode === m}
            className={[
              'px-4 py-1.5 text-sm font-medium rounded-full transition-colors',
              mode === m
                ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 shadow-sm'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100',
            ].join(' ')}
          >
            {m === 'species' ? 'Compare species' : 'Compare versions'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="animate-pulse text-neutral-500 dark:text-neutral-400">
          Loading threshold data…
        </div>
      ) : mode === 'species' ? (
        <CompareSpeciesView
          options={speciesOptions}
          manifest={manifestSpecies}
          selected={selectedFromUrl}
          setSelected={setSelected}
        />
      ) : (
        <CompareVersionsView
          options={multiSchemeSpecies}
          manifest={manifestSpecies}
          selectedSpecies={selectedFromUrl[0] ?? ''}
          setSelectedSpecies={(s) => setSelected(s ? [s] : [])}
        />
      )}
    </div>
  );
}

/* ---------------- Compare species ---------------- */

interface OptionsListItem {
  value: string;
  label: string;
}

function CompareSpeciesView({
  options,
  manifest,
  selected,
  setSelected,
}: {
  options: OptionsListItem[];
  manifest: Record<string, SpeciesData>;
  selected: string[];
  setSelected: (l: string[]) => void;
}) {
  const validSelected = useMemo(() => selected.filter((s) => manifest[s]), [selected, manifest]);

  // Build per-metric rows: union of all metrics across the selected species,
  // each cell pulls from the species' preferred-scheme thresholds.
  const { metrics, byCell } = useMemo(() => {
    const metricSet = new Set<string>();
    const cell = new Map<string, Threshold>();
    for (const sp of validSelected) {
      const info = manifest[sp];
      if (!info) continue;
      const preferred = info.preferred_qc_scheme ?? Object.keys(info.schemes ?? {})[0];
      const scheme = preferred ? info.schemes?.[preferred] : undefined;
      for (const t of scheme?.thresholds ?? []) {
        if (!t.metric) continue;
        metricSet.add(t.metric);
        cell.set(`${sp}::${t.metric}`, t);
      }
    }
    return { metrics: [...metricSet].sort(), byCell: cell };
  }, [validSelected, manifest]);

  return (
    <>
      <div className="mb-6 max-w-xl">
        <SpeciesSelector
          options={options}
          selected={validSelected}
          onChange={setSelected}
          max={4}
        />
        <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
          Select 2 to 4 species to compare. Values come from each species&apos;
          preferred QC scheme.
        </p>
      </div>

      {validSelected.length === 1 && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400">
          Pick at least one more species to compare.
        </p>
      )}

      {validSelected.length >= 2 && metrics.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-700">
                <th className="px-4 py-3 text-left font-semibold">Metric</th>
                {validSelected.map((sp) => {
                  const info = manifest[sp];
                  const preferred = info?.preferred_qc_scheme;
                  return (
                    <th key={sp} className="px-4 py-3 text-left font-semibold">
                      <em>{sp.replace(/_/g, ' ')}</em>
                      {preferred && (
                        <span className="block text-xs font-normal font-mono text-neutral-500 dark:text-neutral-400 mt-0.5">
                          {preferred}
                        </span>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric, i) => (
                <tr
                  key={metric}
                  className={i % 2 === 0 ? '' : 'bg-neutral-50 dark:bg-neutral-800/50'}
                >
                  <td className="px-4 py-2 font-mono">{metric}</td>
                  {validSelected.map((sp) => {
                    const row = byCell.get(`${sp}::${metric}`);
                    return (
                      <td key={sp} className="px-4 py-2 font-mono">
                        {row ? formatBound(row.lower, row.upper) : '-'}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {validSelected.length >= 2 && metrics.length === 0 && (
        <p className="text-neutral-500 dark:text-neutral-400">
          No threshold data available for the selected species.
        </p>
      )}
    </>
  );
}

/* ---------------- Compare versions ---------------- */

function CompareVersionsView({
  options,
  manifest,
  selectedSpecies,
  setSelectedSpecies,
}: {
  options: OptionsListItem[];
  manifest: Record<string, SpeciesData>;
  selectedSpecies: string;
  setSelectedSpecies: (s: string) => void;
}) {
  const speciesInfo = selectedSpecies ? manifest[selectedSpecies] : undefined;

  const schemes = useMemo(() => {
    if (!speciesInfo) return [];
    // Order: preferred first, then the rest in qc_schemes order
    const preferred = speciesInfo.preferred_qc_scheme;
    const all = (speciesInfo.qc_schemes ?? Object.keys(speciesInfo.schemes ?? {})).slice();
    if (preferred) {
      const idx = all.indexOf(preferred);
      if (idx > 0) {
        all.splice(idx, 1);
        all.unshift(preferred);
      }
    }
    return all;
  }, [speciesInfo]);

  const { metrics, byCell, diffRows } = useMemo(() => {
    if (!speciesInfo) return { metrics: [] as string[], byCell: new Map<string, Threshold>(), diffRows: new Set<string>() };
    const metricSet = new Set<string>();
    const cell = new Map<string, Threshold>();
    for (const scheme of schemes) {
      const ts = speciesInfo.schemes?.[scheme]?.thresholds ?? [];
      for (const t of ts) {
        if (!t.metric) continue;
        metricSet.add(t.metric);
        cell.set(`${scheme}::${t.metric}`, t);
      }
    }
    const metricList = [...metricSet].sort();
    const diff = new Set<string>();
    for (const m of metricList) {
      const formatted = schemes.map((s) => {
        const row = cell.get(`${s}::${m}`);
        return row ? formatBound(row.lower, row.upper) : '-';
      });
      if (new Set(formatted).size > 1) diff.add(m);
    }
    return { metrics: metricList, byCell: cell, diffRows: diff };
  }, [speciesInfo, schemes]);

  return (
    <>
      <div className="mb-6 max-w-xl">
        <label
          htmlFor="versions-species"
          className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1"
        >
          Species
        </label>
        <select
          id="versions-species"
          value={selectedSpecies}
          onChange={(e) => setSelectedSpecies(e.target.value)}
          className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 rounded text-neutral-900 dark:text-neutral-100"
        >
          <option value="">— pick a species —</option>
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
          Only species with multiple published QC scheme versions appear here
          ({options.length} of {Object.keys(manifest).length} species so far).
          Rows where bounds differ across versions are highlighted.
        </p>
      </div>

      {selectedSpecies && schemes.length < 2 && (
        <p className="text-neutral-500 dark:text-neutral-400">
          <em>{selectedSpecies.replace(/_/g, ' ')}</em> only has one published
          scheme — nothing to compare.
        </p>
      )}

      {selectedSpecies && schemes.length >= 2 && metrics.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-700">
                <th className="px-4 py-3 text-left font-semibold">Metric</th>
                {schemes.map((s) => (
                  <th key={s} className="px-4 py-3 text-left font-semibold">
                    <span className="font-mono text-xs sm:text-sm">{s}</span>
                    {s === speciesInfo?.preferred_qc_scheme && (
                      <span className="block text-xs font-normal text-[var(--gx-accent)] mt-0.5">
                        preferred
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric, i) => {
                const isDiff = diffRows.has(metric);
                return (
                  <tr
                    key={metric}
                    className={[
                      i % 2 === 0 ? '' : 'bg-neutral-50 dark:bg-neutral-800/50',
                      isDiff ? 'outline outline-1 outline-[var(--gx-accent-15)]' : '',
                    ].join(' ')}
                  >
                    <td className="px-4 py-2 font-mono">
                      {metric}
                      {isDiff && (
                        <span
                          className="ml-2 inline-block px-1.5 py-0.5 rounded text-[10px] font-sans uppercase tracking-wide text-[var(--gx-accent)] border border-[var(--gx-accent-15)] bg-[var(--gx-accent-dim)]"
                          title="Values differ across versions"
                        >
                          changed
                        </span>
                      )}
                    </td>
                    {schemes.map((s) => {
                      const row = byCell.get(`${s}::${metric}`);
                      return (
                        <td key={s} className="px-4 py-2 font-mono">
                          {row ? formatBound(row.lower, row.upper) : '-'}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selectedSpecies && schemes.length >= 2 && metrics.length === 0 && (
        <p className="text-neutral-500 dark:text-neutral-400">
          No threshold data available across versions for{' '}
          <em>{selectedSpecies.replace(/_/g, ' ')}</em>.
        </p>
      )}
    </>
  );
}
