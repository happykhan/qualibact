export default function Loading() {
  return (
    <div className="py-8 animate-pulse">
      <div className="container mx-auto space-y-8">
        <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded w-2/5" />
        <div className="card p-6 space-y-4">
          <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-1/4" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4" />
          <div className="flex gap-3">
            <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-32" />
            <div className="h-10 bg-neutral-200 dark:bg-neutral-700 rounded w-32" />
          </div>
        </div>
        <div className="card p-6 space-y-4">
          <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-1/3" />
          <div className="h-48 bg-neutral-200 dark:bg-neutral-700 rounded" />
        </div>
      </div>
    </div>
  );
}
