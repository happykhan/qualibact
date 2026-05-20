'use client';

import { useState } from 'react';

const CITATION = `QualiBact: Species-specific quality control of bacterial de novo genome assemblies. https://qualibact.org`;

export default function CitationCopy() {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(CITATION);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = CITATION;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className="mt-8 p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
      <h3 className="font-header font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Cite QualiBact</h3>
      <p className="text-sm text-neutral-700 dark:text-neutral-300 font-mono mb-3">{CITATION}</p>
      <button
        onClick={handleCopy}
        className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700 transition-colors text-sm"
      >
        {copied ? (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Copied
          </>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            Copy citation
          </>
        )}
      </button>
    </div>
  );
}
