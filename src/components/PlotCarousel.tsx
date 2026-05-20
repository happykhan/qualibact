"use client";
import React, { useEffect, useState, useCallback } from 'react';
import Image from 'next/image';

interface PlotCarouselProps {
  metric: string;
  images: string[]; // URLs relative to /public
}

export default function PlotCarousel({ metric, images }: PlotCarouselProps) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    // reset index when images change
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIndex(0);
  }, [images]);

  const prev = useCallback(() => {
    setIndex((i) => (i - 1 + images.length) % images.length);
  }, [images.length]);

  const next = useCallback(() => {
    setIndex((i) => (i + 1) % images.length);
  }, [images.length]);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'ArrowLeft') {
        prev();
      } else if (e.key === 'ArrowRight') {
        next();
      }
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [prev, next]);

  if (!images || images.length === 0) {
    return (
      <div className="border border-neutral-300 dark:border-neutral-700 rounded p-4">No plots available</div>
    );
  }

  const current = images[index];

  const handleDownload = () => {
    window.open(current, '_blank');
  };

  return (
    <div className="border border-neutral-200 dark:border-neutral-700 rounded p-3 bg-white dark:bg-neutral-800">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-lg font-semibold">{metric.replace(/_/g, ' ')} Distribution</h4>
        <div className="flex items-center gap-2">
          <button
            className="px-3 py-1 bg-neutral-100 dark:bg-neutral-700 rounded hover:bg-neutral-200 dark:hover:bg-neutral-600"
            onClick={prev}
            title="Previous plot"
          >
            ⬅
          </button>
          <button
            className="px-3 py-1 bg-neutral-100 dark:bg-neutral-700 rounded hover:bg-neutral-200 dark:hover:bg-neutral-600"
            onClick={next}
            title="Next plot"
          >
            ➡
          </button>
          <button
            className="px-3 py-1 bg-brand-600 text-white rounded hover:bg-brand-700"
            onClick={handleDownload}
            title="Download current plot"
          >
            ⤓
          </button>
        </div>
      </div>

      <div className="w-full flex items-center justify-center">
        <div className="w-full rounded border border-neutral-200 dark:border-neutral-700 overflow-hidden bg-white dark:bg-neutral-800 relative" style={{ aspectRatio: '16/9' }}>
          <Image src={current} alt={`${metric} plot ${index + 1}`} fill style={{ objectFit: 'contain' }} sizes="(max-width: 768px) 100vw, 50vw" />
        </div>
      </div>
      <div className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">{`${index + 1} / ${images.length}`}</div>
    </div>
  );
}
