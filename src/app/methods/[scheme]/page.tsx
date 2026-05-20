import { notFound } from 'next/navigation';
import fs from 'fs';
import path from 'path';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import ThresholdRationaleTable from '@/components/ThresholdRationaleTable';

interface SchemePageProps {
  params: Promise<{ scheme: string }>;
}

function listMethodFiles() {
  const methodsDir = path.join(process.cwd(), 'content', 'methods');
  if (!fs.existsSync(methodsDir)) return [];
  return fs
    .readdirSync(methodsDir)
    .filter((file) => file.endsWith('.md') || file.endsWith('.mdx'));
}

export async function generateStaticParams() {
  return listMethodFiles().map((file) => ({
    scheme: file.replace(/\.mdx?$/i, ''),
  }));
}

export default async function SchemeMethodsPage({ params }: SchemePageProps) {
  const { scheme } = await params;
  const methodsDir = path.join(process.cwd(), 'content', 'methods');
  const candidates = [`${scheme}.mdx`, `${scheme}.md`];
  const filePath = candidates
    .map((name) => path.join(methodsDir, name))
    .find((p) => fs.existsSync(p));

  if (!filePath) notFound();

  const content = fs.readFileSync(filePath, 'utf8');
  const title = scheme.replace(/-/g, ' ');

  // The rationale table documents which thresholds were hand-pinned and
  // why. The actual override mechanism lives in the engine now (the
  // {Species}_metrics.csv `source: pinned` column); this table is the
  // audit trail. v1.0 = raw engine output (no overrides), so it's
  // rendered on v1.1 where every override actually lives.
  const showOverrides = scheme === 'qualibact-v1.1';

  return (
    <div className="py-8">
      <div className="space-y-4">
        <h1 className="text-3xl font-header font-bold mb-4">{title} methods</h1>
        <MarkdownRenderer content={content} />
        {showOverrides && (
          <section>
            <h3 className="text-lg font-header font-semibold mt-6 mb-2">
              Hand-pinned threshold rationale
            </h3>
            <ThresholdRationaleTable />
          </section>
        )}
      </div>
    </div>
  );
}
