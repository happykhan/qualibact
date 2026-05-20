import MarkdownRenderer from '@/components/MarkdownRenderer';
import CitationCopy from '@/components/CitationCopy';
import fs from 'fs';
import path from 'path';

export default function Home() {
  const homeContent = fs.readFileSync(
    path.join(process.cwd(), 'content', 'index.md'),
    'utf8',
  );
  return (
    <div className="py-8">
      <div>
        <MarkdownRenderer content={homeContent} />
        <CitationCopy />
      </div>
    </div>
  );
}
