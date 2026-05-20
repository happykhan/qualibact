"use client";
import React, { useMemo, useState, useEffect } from 'react';
import NextImage from 'next/image';

interface PlotItem {
  path: string; // URL path to image
  filename: string;
}

interface FilteredPlotGridProps {
  items: PlotItem[];
  maxWidth?: number;
}

export default function FilteredPlotGrid({ items, maxWidth }: FilteredPlotGridProps) {
  // No filter dropdown: show all types (all, sample, filt) together
  const [metricIndex, setMetricIndex] = useState(0);

  const metricMap = useMemo(() => {
    // Map metricKey => {all:[], sample:[], filt:[]}
    const map = new Map<string, Record<string, PlotItem[]>>();
    const seen = new Set<string>();
    for (const it of items) {
      if (seen.has(it.filename)) continue; // deduplicate
      seen.add(it.filename);

      // Try to find the type in the filename using regex to avoid issues with underscores or spaces
      const typeMatch = it.filename.match(/_(all|sample|filt)_/i);
      const type = typeMatch ? typeMatch[1].toLowerCase() : 'all';

      // Extract metric: the part after the type and underscore up to extension
      const metricMatch = it.filename.match(/_(?:all|sample|filt)_(.+?)\.(png|jpg|jpeg)$/i);
      const metricKey = metricMatch ? metricMatch[1].replace(/\s+/g, '_') : 'unknown';

      if (!map.has(metricKey)) map.set(metricKey, { all: [], sample: [], filt: [] });
      const bucket = map.get(metricKey)!;
      if (!bucket[type]) bucket[type] = [];
      bucket[type].push(it);
    }
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0])); // returns [metricKey, Record]
  }, [items]);

  const metricCount = metricMap.length;
  // keep metricIndex in range
  const currentIndex = Math.max(0, Math.min(metricIndex, metricCount - 1));
  const currentMetric = metricCount > 0 ? metricMap[currentIndex] : null;
  const [modalImage, setModalImage] = useState<string | null>(null);

  // helper to preload an image
  function preloadImage(url: string) {
    // Avoid shadowing NextImage; use the browser Image constructor
    const img = new window.Image();
    img.src = url;
  }

  // Preload current and next metric images to reduce twitching
  useEffect(() => {
    if (!currentMetric) return;
    // preload all images in current metric's types
    const metricItems: PlotItem[] = [];
    for (const t of Object.values(currentMetric[1])) {
      metricItems.push(...t);
    }
    metricItems.forEach(it => preloadImage(it.path));
    // preload next metric (if any)
    const nextMetric = metricMap[(currentIndex + 1) % (metricCount || 1)];
    if (nextMetric) {
      const nextItems: PlotItem[] = [];
      for (const t of Object.values(nextMetric[1])) nextItems.push(...t);
      nextItems.forEach(it => preloadImage(it.path));
    }
  }, [currentIndex, currentMetric, metricMap, metricCount]);

  // image wrapper component with placeholder + fade-in
  function ImageWithPlaceholder({ src, alt, filename }: { src: string; alt?: string; filename?: string }) {
    const [loaded, setLoaded] = useState(false);
    return (
      <div className="w-full rounded border border-neutral-200 dark:border-neutral-700 overflow-hidden bg-white dark:bg-neutral-800 relative" style={{ aspectRatio: '16/9' }}>
        {/* placeholder skeleton */}
        <div className={`w-full h-full ${loaded ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300 ease-in-out bg-neutral-100 dark:bg-neutral-800`}></div>
        <NextImage
          src={src}
          alt={alt || filename || ''}
          fill
          sizes="(max-width: 768px) 100vw, 33vw"
          style={{ objectFit: 'contain' }}
          onLoadingComplete={() => setLoaded(true)}
        />
      </div>
    );
  }

  const toTitleCase = (str: string) => str.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.slice(1).toLowerCase());

  // Known metric tokens that appear in filtered-plot filenames. Order
  // matters — longer tokens first so the longest-match wins (e.g.
  // 'Completeness_Specific' before 'Completeness').
  const KNOWN_METRICS: { token: string; label: string }[] = [
    { token: 'Total_Coding_Sequences', label: 'Total coding sequences' },
    { token: 'Completeness_Specific', label: 'Completeness' },
    { token: 'GC_Content', label: 'GC content' },
    { token: 'total_length', label: 'Total length' },
    { token: 'no_of_contigs', label: 'Number of contigs' },
    { token: 'Contamination', label: 'Contamination' },
    { token: 'Genome_Size', label: 'Genome size' },
    { token: 'longest', label: 'Longest contig' },
    { token: 'number', label: 'Number of contigs' },
    { token: 'N50', label: 'N50' },
  ];

  const formatMetric = (key: string) => {
    // Explicit "_vs_" wins.
    if (/_vs_/i.test(key)) {
      const [left, right] = key.split(/_vs_/i);
      return `${toTitleCase(left)} vs ${toTitleCase(right.replace(/_/g, ' '))}`;
    }
    // Greedy match: peel known metric tokens off the start of the key.
    // If we can split the key into exactly two known metrics, render as
    // "{first} vs {second}" so the naming is consistent across all
    // bivariate plots.
    let remaining = key;
    const found: string[] = [];
    while (remaining.length > 0) {
      const hit = KNOWN_METRICS.find(({ token }) =>
        remaining.toLowerCase().startsWith(token.toLowerCase()),
      );
      if (!hit) break;
      found.push(hit.label);
      remaining = remaining.slice(hit.token.length).replace(/^_+/, '');
    }
    if (found.length === 2 && remaining === '') {
      return `${found[0]} vs ${found[1]}`;
    }
    if (found.length === 1 && remaining === '') {
      return found[0];
    }
    // Fallback to the previous behaviour.
    return toTitleCase(key.replace(/_/g, ' '));
  };

  return (
    <div className="space-y-3 w-full" style={maxWidth ? { maxWidth: `${maxWidth}px` } : undefined}>
      {currentMetric ? (
        <>
          <div className="flex items-center justify-between">
            <div className=" font-semibold text-neutral-800 dark:text-neutral-200">{formatMetric(currentMetric[0])}</div>
            <div className="flex items-center gap-2">
              <button onClick={() => setMetricIndex(i => Math.max(0, i - 1))} className="btn btn-ghost px-2 py-1">Prev</button>
              <button onClick={() => setMetricIndex(i => Math.min(metricCount - 1, i + 1))} className="btn btn-ghost px-2 py-1">Next</button>
              <span className=" text-neutral-500 dark:text-neutral-400">{metricCount > 0 ? `${currentIndex + 1} / ${metricCount}` : '0 / 0'}</span>
            </div>
          </div>
          <div className="text-neutral-600 dark:text-neutral-400 space-y-2">
            <p>These plots show genomes before and after filtering to highlight the outliers removed:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li><strong>Left:</strong> heatmap of all genomes in the dataset.</li>
              <li><strong>Middle:</strong> a representative sample of genomes, with anomalies highlighted in purple.</li>
              <li><strong>Right:</strong> the filtered distribution after applying the thresholds.</li>
            </ul>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              The filtered distribution shown here may not exactly match the published thresholds because additional rounding and curator adjustments are applied on top.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['all', 'sample', 'filt'].map(type => {
              const itemsForType = currentMetric[1][type] || [];
              const label = type === 'all' ? 'All' : type === 'sample' ? 'Sample' : 'Filtered';
              return (
                <div key={type} className="space-y-2">
                  <div className=" font-semibold text-neutral-800 dark:text-neutral-200">{label}</div>
                  {itemsForType.length > 0 ? itemsForType.map(it => (
                    <div key={it.filename} className="space-y-2">
                      <button type="button" onClick={() => setModalImage(it.path)} className="w-full cursor-zoom-in">
                        <ImageWithPlaceholder src={it.path} alt={it.filename} filename={it.filename} />
                      </button>
                      <div className="flex items-center justify-between  text-neutral-600 dark:text-neutral-400">
                        <span className="truncate" title={it.filename}>{it.filename}</span>
                        <a href={it.path} download className="btn btn-ghost px-2 py-1">Download</a>
                      </div>
                    </div>
                  )) : <div className=" text-neutral-600 dark:text-neutral-400">No {label.toLowerCase()} plot</div>}
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className=" text-neutral-600 dark:text-neutral-400">No filtered plots available for this version.</div>
      )}
      {modalImage && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={() => setModalImage(null)}>
          <div className="relative max-w-5xl w-full" onClick={e => e.stopPropagation()}>
            <button className="absolute top-2 right-2 btn btn-ghost px-2 py-1" onClick={() => setModalImage(null)}>Close</button>
            <div className="relative w-full" style={{ aspectRatio: '16/9' }}>
              <NextImage src={modalImage} alt="Expanded plot" fill sizes="100vw" style={{ objectFit: 'contain' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
