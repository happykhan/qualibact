import type { Metadata } from 'next';
import { Suspense } from 'react';
import CompareClient from './CompareClient';

export const metadata: Metadata = {
  title: 'Compare',
  description:
    'Compare QualiBact QC thresholds across species or across QC scheme versions of the same species.',
};

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="py-8 text-neutral-500">Loading…</div>}>
      <CompareClient />
    </Suspense>
  );
}
