import MarkdownRenderer from '@/components/MarkdownRenderer';
import fs from 'fs';
import path from 'path';

const contributingContent = fs.readFileSync(path.join(process.cwd(), 'content', 'contributing.md'), 'utf8');

export default function Contributing() {
  return (
    <div className="py-8">
      <div>
        <MarkdownRenderer content={contributingContent} />
      </div>
    </div>
  );
}