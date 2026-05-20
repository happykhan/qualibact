/**
 * Resolves static asset URLs.
 *
 * When NEXT_PUBLIC_STATIC_URL is set (e.g. to a Cloudflare R2 public URL),
 * all /static/... paths are rewritten to load from the CDN.
 * Otherwise paths are returned as-is (served from public/).
 */
const CDN_BASE = process.env.NEXT_PUBLIC_STATIC_URL || '';

export function staticUrl(path: string): string {
  if (!CDN_BASE) return path;
  // path is expected to start with /static/...
  return `${CDN_BASE}${path}`;
}
