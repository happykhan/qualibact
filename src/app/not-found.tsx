import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-4xl font-bold font-header mb-4">Page not found</h1>
      <p className="text-lg text-neutral-600 dark:text-neutral-400 mb-8">
        The page you are looking for does not exist or has been moved.
      </p>
      <div className="flex justify-center gap-4">
        <Link
          href="/"
          className="px-6 py-3 bg-brand-600 text-white rounded hover:bg-brand-700 transition-colors"
        >
          Go home
        </Link>
        <Link
          href="/species"
          className="px-6 py-3 border border-brand-600 text-brand-600 dark:text-brand-400 dark:border-brand-400 rounded hover:bg-brand-50 dark:hover:bg-brand-900 transition-colors"
        >
          Browse species
        </Link>
      </div>
    </div>
  );
}
