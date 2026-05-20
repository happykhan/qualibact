import MarkdownRenderer from '@/components/MarkdownRenderer';
import fs from 'fs';
import path from 'path';

const faqContent = fs.readFileSync(path.join(process.cwd(), 'content', 'faq.md'), 'utf8');

export default function FAQ() {
  return (
    <div className="py-8">
      <div>
        <MarkdownRenderer content={faqContent} />
      </div>
    </div>
  );
}
