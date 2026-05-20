"use client";
import React, { useEffect, useState, useCallback } from 'react';
import Image from 'next/image';

interface MetricItem {
  metric: string;
  image: string; // URL relative to /public
}

interface MetricCarouselProps {
  items: MetricItem[];
  /** Maximum width in pixels for the carousel image container; optional */
  maxWidth?: number;
}

export default function MetricCarousel({ items, maxWidth }: MetricCarouselProps) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    // reset index when items changes (e.g., new metrics list)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIndex(0);
  }, [items]);

  const prev = useCallback(() => setIndex((i) => (i - 1 + items.length) % items.length), [items.length]);
  const next = useCallback(() => setIndex((i) => (i + 1) % items.length), [items.length]);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'ArrowLeft') prev();
      else if (e.key === 'ArrowRight') next();
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [prev, next, items]);

  if (!items || items.length === 0) {
    return <div className="border border-neutral-300 dark:border-neutral-700 rounded p-4">No plots available</div>;
  }

  const current = items[index];

  const handleDownload = () => {
    window.open(current.image, '_blank');
  };

  return (
    <div className="rounded-xl p-4 bg-white dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800 shadow-card">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold" aria-live="polite">{current.metric.replace(/_/g, ' ')} Distribution</h3>
        <div className="flex items-center gap-2">
          <button aria-label={`Previous metric, ${current.metric}`} onClick={prev} className="px-3 py-1 bg-neutral-100 dark:bg-neutral-700 rounded hover:bg-neutral-200 dark:hover:bg-neutral-600" title="Previous metric">⬅</button>
          <button aria-label={`Next metric, ${current.metric}`} onClick={next} className="px-3 py-1 bg-neutral-100 dark:bg-neutral-700 rounded hover:bg-neutral-200 dark:hover:bg-neutral-600" title="Next metric">➡</button>
          <button aria-label={`Download plot for ${current.metric}`} onClick={handleDownload} className="px-3 py-1 bg-brand-600 text-white rounded hover:bg-brand-700" title="Download current plot">⤓</button>
        </div>
      </div>
      <div className="w-full flex items-center justify-center">
        <div style={maxWidth ? { maxWidth: `${maxWidth}px`, width: '100%' } : undefined} className={`mx-auto w-full px-2`}>
          <div className="w-full rounded border border-neutral-200 dark:border-neutral-700 overflow-hidden bg-white dark:bg-neutral-800 relative" style={{ aspectRatio: '16/9' }}>
              <Image src={current.image} alt={`${current.metric} plot ${index + 1}`} fill style={{ objectFit: 'contain' }} sizes="(max-width: 768px) 100vw, 50vw" />
          </div>
        </div>
      </div>
      <div className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">{`${index + 1} / ${items.length}`}</div>
    </div>
  );
}
