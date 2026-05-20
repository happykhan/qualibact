"use client";
import Image from 'next/image';
import React from 'react';
import { useState } from 'react';

interface CdsGenomePlotProps {
  src: string;
  alt?: string;
  maxWidth?: string | number;
}

export default function CdsGenomePlot({ src, alt, maxWidth }: CdsGenomePlotProps) {
  const [modalImage, setModalImage] = useState<string | null>(null);
  if (!src) return null;

  const handleDownload = (url: string) => {
    window.open(url, '_blank');
  };

  const containerStyle = maxWidth ? { maxWidth } : {};

  return (
    <div className="space-y-3" style={containerStyle}>
      <button type="button" onClick={() => setModalImage(src)} className="relative w-full rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 overflow-hidden cursor-zoom-in" style={{ aspectRatio: '16/9' }}>
        <Image src={src} alt={alt || 'CDS vs Genome Size'} fill style={{ objectFit: 'contain' }} sizes="(max-width: 768px) 100vw, 50vw" />
      </button>
      <div className="flex items-center justify-between  text-neutral-700 dark:text-neutral-300">
        <span className="font-header font-semibold">CDS vs Genome Size</span>
        <button
          onClick={() => handleDownload(src)}
          className="btn btn-ghost px-3 py-1"
          title="Download CDS vs Genome Size plot"
        >
          Download
        </button>
      </div>
      <p className=" text-neutral-600 dark:text-neutral-400">
        This plot shows the relationship between the number of coding sequences (CDS) and genome size — how the number of genes scales with assembly length. The relationship should be roughly linear: as genome size increases, the number of coding sequences should rise proportionally. A secondary trend line or non-linear behaviour can indicate either <em>bona fide</em> sub-populations within the retained genomes (e.g. distinct sub-clades) or residual contamination that survived filtering.
      </p>
      {modalImage && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={() => setModalImage(null)}>
          <div className="relative max-w-5xl w-full" onClick={e => e.stopPropagation()}>
            <button className="absolute top-2 right-2 btn btn-ghost px-2 py-1" onClick={() => setModalImage(null)}>Close</button>
            <div className="relative w-full" style={{ aspectRatio: '16/9' }}>
              <Image src={modalImage} alt="Expanded CDS vs Genome Size plot" fill sizes="100vw" style={{ objectFit: 'contain' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
