"use client";
import React, { useState, useEffect } from 'react';
import NextImage from 'next/image';

const CDN_BASE = process.env.NEXT_PUBLIC_STATIC_URL || '';
function staticUrl(path: string): string {
  if (!CDN_BASE) return path;
  return `${CDN_BASE}${path}`;
}

const EXPECTED_METRICS = [
  'GC_Content', 'Completeness_Specific', 'Contamination', 'Genome_Size', 'Total_Coding_Sequences', 'N50', 'number', 'longest'
];

interface MetricRefseqPlotGroupProps {
  species: string; // underscored species name, e.g. Acinetobacter_baumannii
  version: string;
  maxWidth?: number; // optional maximum width to constrain the images
  // Preloaded metrics from server, as an optimization and to avoid client-side fetch
  initialMetrics?: { metric: string; hist?: string; qq?: string }[];
}

/**
 * Renders a small navigation for refseq plots (histogram + qq) for each metric.
 * Scans the directory /<species>/<version>/ for <Metric>_refseq_histogram_kde.png and <Metric>_refseq_qqplot.png
 */
export default function MetricRefseqPlotGroup({ species, version, maxWidth, initialMetrics }: MetricRefseqPlotGroupProps) {
  const basePath = staticUrl(`/static/species/${species}/${version}`);
  // We don't have server-side listing here (client component), so we rely on a list of expected metrics
  // (kept outside effects for readability; stable identity is ensured by module-level constant)

  // Build list of available metrics - include only metrics which have at least one image (hist or qq)
  const [availableMetrics, setAvailableMetrics] = useState<{ metric: string; hist?: string; qq?: string }[]>(initialMetrics || []);
  // If initial metrics are provided, we can avoid network fetch in many cases
  const [index, setIndex] = useState(0);
  const [modalImage, setModalImage] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    async function checkMetrics() {
      // If initial metrics were already provided by server rendering, no need to fetch or HEAD check
      if (initialMetrics && initialMetrics.length > 0) return;
      const manifestUrl = `${basePath}/refseq_metrics.json`;
      try {
        const mres = await fetch(manifestUrl);
        if (mres.ok) {
            type RefseqMetric = { metric: string; hist?: string; qq?: string };
            const mm: { metrics?: RefseqMetric[] } = await mres.json();
          const mapped = (mm.metrics || []).map((x: RefseqMetric) => ({
            metric: x.metric,
            hist: x.hist ? staticUrl(x.hist) : undefined,
            qq: x.qq ? staticUrl(x.qq) : undefined,
          }));
          if (alive) setAvailableMetrics(mapped);
          return;
        }
        } catch (_err) {
        // ignore and fallback
      }
      const results: { metric: string; hist?: string; qq?: string }[] = [];
      await Promise.all(EXPECTED_METRICS.map(async (metric) => {
        const hist = `${basePath}/${metric}_refseq_histogram_kde.png`;
        const qq = `${basePath}/${metric}_refseq_qqplot.png`;
        let histOk = false;
        let qqOk = false;
        try {
          const h = await fetch(hist, { method: 'HEAD' });
          histOk = h.ok;
        } catch (_e) {
          histOk = false;
        }
        try {
          const q = await fetch(qq, { method: 'HEAD' });
          qqOk = q.ok;
        } catch (_e) {
          qqOk = false;
        }
        if (histOk || qqOk) {
          results.push({ metric, hist: histOk ? hist : undefined, qq: qqOk ? qq : undefined });
        }
      }));
      if (alive && results.length > 0) setAvailableMetrics(results);
    }
    checkMetrics();
    return () => { alive = false; };
  }, [species, version, basePath, initialMetrics]);

  // We compute currentIndex derived from index & available metrics without mutating state
  const metricCount = availableMetrics.length;
  const currentIndex = Math.max(0, Math.min(index, Math.max(0, metricCount - 1)));
  const current = metricCount > 0 ? availableMetrics[currentIndex] : undefined;

  const prev = React.useCallback(() => setIndex(i => (i - 1 + Math.max(1, metricCount)) % Math.max(1, metricCount)), [metricCount]);
  const next = React.useCallback(() => setIndex(i => (i + 1) % Math.max(1, metricCount)), [metricCount]);

  const handleDownload = (url: string) => {
    window.open(url, '_blank');
  };

  // No current metric to display -> hide component completely so we don't render
  // a header or empty frame for pages with no refseq plots.
  if (!current) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className=" text-neutral-700 dark:text-neutral-300 font-semibold">{current.metric.replace(/_/g, ' ')} (RefSeq)</div>
        <div className="flex items-center gap-2">
          <button onClick={prev} className="btn btn-ghost px-2 py-1">Prev</button>
          <button onClick={next} className="btn btn-ghost px-2 py-1">Next</button>
          <div className=" text-neutral-500 dark:text-neutral-400">{`${index + 1} / ${availableMetrics.length}`}</div>
        </div>
      </div>
      <div
        style={maxWidth ? { maxWidth: `${maxWidth}px` } : undefined}
        className="mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        {current.hist ? (
          <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-3 flex flex-col gap-2">
            <button type="button" onClick={() => setModalImage(current.hist!)} className="relative w-full h-56 md:h-72 cursor-zoom-in">
              <NextImage src={current.hist!} alt={`${current.metric} histogram`} fill sizes="(max-width: 768px) 100vw, 50vw" style={{ objectFit: 'contain' }} />
            </button>
            <div className="flex items-center justify-between  text-neutral-600 dark:text-neutral-400">
              <span className="font-header font-semibold">Histogram (SRA vs RefSeq)</span>
              <button onClick={() => handleDownload(current.hist!)} className="btn btn-ghost px-2 py-1">Download</button>
            </div>
            <p className=" text-neutral-600 dark:text-neutral-400">
              Histogram comparing SRA to RefSeq; each bar shows genome density across value ranges to highlight shifts, peaks, or outliers.
            </p>
          </div>
        ) : <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4  text-neutral-600 dark:text-neutral-400">No histogram available</div>}
        {current.qq ? (
          <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-3 flex flex-col gap-2">
            <button type="button" onClick={() => setModalImage(current.qq!)} className="relative w-full h-56 md:h-72 cursor-zoom-in">
              <NextImage src={current.qq!} alt={`${current.metric} qqplot`} fill sizes="(max-width: 768px) 100vw, 50vw" style={{ objectFit: 'contain' }} />
            </button>
            <div className="flex items-center justify-between  text-neutral-600 dark:text-neutral-400">
              <span className="font-header font-semibold">QQ plot (SRA vs RefSeq)</span>
              <button onClick={() => handleDownload(current.qq!)} className="btn btn-ghost px-2 py-1">Download</button>
            </div>
            <p className=" text-neutral-600 dark:text-neutral-400">
              QQ (quantile-quantile) plot comparing SRA and RefSeq. Points along the diagonal follow the expected distribution; deviations indicate skew, outliers, or other systematic differences.
            </p>
          </div>
        ) : <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4  text-neutral-600 dark:text-neutral-400">No qqplot available</div>}
      </div>
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
