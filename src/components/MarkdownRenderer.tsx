import { remark } from 'remark';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import rehypeSlug from 'rehype-slug';
import matter from 'gray-matter';

interface MarkdownRendererProps {
  content: string;
}

export default async function MarkdownRenderer({ content }: MarkdownRendererProps) {
  // Remove YAML frontmatter if present
  const parsed = matter(content || '');
  let mdBody = parsed.content || '';

  // If there's a frontmatter title, strip any top-level H1 that repeats it
  const title = parsed.data && parsed.data.title ? String(parsed.data.title).trim() : undefined;
  if (title) {
    // Remove a leading H1 that matches the title (case-insensitive)
    const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const titleRegex = new RegExp('^\\s*#\\s*' + escapedTitle + '\\s*\\n+', 'i');
    mdBody = mdBody.replace(titleRegex, '');
  }

  const processedContent = await remark()
    .use(remarkGfm)
    .use(remarkRehype)
    .use(rehypeSlug)
    .use(rehypeStringify)
    .process(mdBody);

  const contentHtml = processedContent.toString();

  return (
    <div
      className="prose max-w-full w-full leading-relaxed"
      dangerouslySetInnerHTML={{ __html: contentHtml }}
    />
  );
}
