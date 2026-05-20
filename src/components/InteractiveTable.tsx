'use client';

import { useState, useMemo } from 'react';

interface Column<T extends Record<string, unknown> = Record<string, unknown>> {
  key: string;
  label: string;
  sortable?: boolean;
  type?: 'string' | 'number' | 'boolean';
  italic?: boolean;
  /** Built-in cell renderer. Use 'badge' for severity-style values
   *  (info / warn / error) — they render as coloured pills.
   *
   *  Function renderers were tried but they don't survive the
   *  server-to-client boundary in Next 16, so the renderer name is
   *  passed as a string and resolved inside this client component. */
  renderAs?: 'badge';
}

const SEVERITY_BADGE: Record<string, { label: string; tint: string }> = {
  error: { label: 'error', tint: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-100' },
  warn:  { label: 'warn',  tint: 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-100' },
  info:  { label: 'info',  tint: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-100' },
};

function renderBadge(value: unknown) {
  const v = typeof value === 'string' ? value.trim().toLowerCase() : '';
  if (!v) return '';
  const cfg = SEVERITY_BADGE[v];
  if (!cfg) return v;
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-mono uppercase ${cfg.tint}`}
      title={`Engine quality flag: ${v}`}
    >
      {cfg.label}
    </span>
  );
}

interface InteractiveTableProps<T extends Record<string, unknown> = Record<string, unknown>> {
  data: T[];
  columns: Column<T>[];
  searchPlaceholder?: string;
  className?: string;
  initialPageSize?: number;
}

type SortDirection = 'asc' | 'desc' | null;

export default function InteractiveTable<T extends Record<string, unknown> = Record<string, unknown>>({
  data,
  columns,
  searchPlaceholder = "Search...",
  className = "",
  initialPageSize,
}: InteractiveTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [showAll, setShowAll] = useState(false);

  // Filter data based on search term
  const filteredData = useMemo(() => {
    if (!searchTerm) return data;

    return data.filter(row =>
      columns.some(column => {
        const value = row[column.key];
        return value?.toString().toLowerCase().includes(searchTerm.toLowerCase());
      })
    );
  }, [data, searchTerm, columns]);

  // Sort filtered data
  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortColumn];
      const bValue = b[sortColumn];

      // Handle numeric values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      // Handle string values
      const aStr = String(aValue || '').toLowerCase();
      const bStr = String(bValue || '').toLowerCase();

      if (sortDirection === 'asc') {
        return aStr.localeCompare(bStr);
      } else {
        return bStr.localeCompare(aStr);
      }
    });
  }, [filteredData, sortColumn, sortDirection]);

  // Apply row cap unless the user has searched, sorted, or expanded.
  const isFiltered = searchTerm.trim().length > 0 || sortColumn !== null;
  const capActive = !showAll && !isFiltered && typeof initialPageSize === 'number' && sortedData.length > initialPageSize;
  const visibleData = capActive ? sortedData.slice(0, initialPageSize!) : sortedData;
  const hiddenCount = capActive ? sortedData.length - initialPageSize! : 0;

  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortDirection(null);
        setSortColumn(null);
      }
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) return '⇅';
    if (sortDirection === 'asc') return '▴';
    if (sortDirection === 'desc') return '▾';
    return '⇅';
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search Input */}
      <div className="flex items-center space-x-2">
        <input
          type="text"
          placeholder={searchPlaceholder}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-neutral-700 dark:text-white"
        />
        {searchTerm && (
          <button
            onClick={() => setSearchTerm('')}
            className="px-3 py-2 text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200"
          >
            Clear
          </button>
        )}
      </div>

      {/* Results count */}
      <div className="text-sm text-neutral-600 dark:text-neutral-400">
        {capActive
          ? `Showing first ${visibleData.length} of ${data.length} rows. Search or sort to filter, or expand below.`
          : `Showing ${sortedData.length} of ${data.length} rows${searchTerm ? ` (filtered from "${searchTerm}")` : ''}`}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700">
          <thead>
            <tr className="bg-neutral-50 dark:bg-neutral-700">
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-4 py-2 text-left border-b ${
                    column.sortable !== false ? 'cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-600' : ''
                  }`}
                  onClick={column.sortable !== false ? () => handleSort(column.key) : undefined}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.label}</span>
                    {column.sortable !== false && (
                      <span className="text-xs">{getSortIcon(column.key)}</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleData.map((row, index) => (
              <tr
                key={index}
                className={index % 2 === 0 ? 'bg-white dark:bg-neutral-800' : 'bg-neutral-50 dark:bg-neutral-700'}
              >
                {columns.map((column) => {
                  const value = row[column.key];
                  let displayValue: string;

                  // Handle special formatting based on column key
                  if (column.key === 'species' && typeof value === 'string') {
                    displayValue = value.replace(/_/g, ' ');
                  } else if (column.type === 'number' && typeof value === 'number') {
                    // Drop trailing zeros; comma-separate large numbers.
                    displayValue = value.toLocaleString('en', {
                      maximumFractionDigits: Math.abs(value) >= 1000 ? 0 : 4,
                    });
                  } else if (column.type === 'boolean' && typeof value === 'boolean') {
                    displayValue = value ? 'Yes' : 'No';
                  } else if (value === null || value === undefined || value === '') {
                    displayValue = '';
                  } else {
                    displayValue = value?.toString() || '';
                  }

                  const rendered = column.renderAs === 'badge'
                    ? renderBadge(value)
                    : null;
                  return (
                    <td key={column.key} className={`px-4 py-2 border-b ${column.italic ? 'italic' : ''}`}>
                      {rendered || displayValue}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {capActive && (
        <div className="text-center pt-2">
          <button
            onClick={() => setShowAll(true)}
            className="px-3 py-2 text-sm text-brand-600 dark:text-brand-400 hover:underline"
          >
            Show all {hiddenCount} more rows
          </button>
        </div>
      )}

      {sortedData.length === 0 && searchTerm && (
        <div className="text-center py-8 text-neutral-500 dark:text-neutral-400">
          No results found for &quot;{searchTerm}&quot;
        </div>
      )}
    </div>
  );
}
