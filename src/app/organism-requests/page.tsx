import MarkdownRenderer from '@/components/MarkdownRenderer';
import fs from 'fs';
import path from 'path';

export default function OrganismRequests() {
  // Read on each render so dev-server hot-reload picks up content changes.
  // Build-time static export reads it once during the build, which is fine.
  const requestsContent = fs.readFileSync(
    path.join(process.cwd(), 'content', 'organism-requests.mdx'),
    'utf8'
  );
  return (
    <div className="py-8">
      <div>
        <MarkdownRenderer content={requestsContent} />
      </div>
    </div>
  );
}
