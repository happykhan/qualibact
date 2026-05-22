import type { Metadata } from 'next';
import fs from 'fs';
import path from 'path';
import MarkdownRenderer from '@/components/MarkdownRenderer';

export const metadata: Metadata = {
  title: 'Changelog',
  description: 'Release notes and recent changes to QualiBact thresholds, schemes, and tooling.',
};

const content = fs.readFileSync(
  path.join(process.cwd(), 'content', 'changelog.md'),
  'utf8',
);

export default function ChangelogPage() {
  return (
    <div className="py-8 max-w-3xl mx-auto">
      <MarkdownRenderer content={content} />
    </div>
  );
}
