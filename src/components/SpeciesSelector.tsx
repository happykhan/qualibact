'use client';

import { useState, useRef, useEffect } from 'react';

interface SpeciesOption {
  value: string;
  label: string;
}

interface SpeciesSelectorProps {
  options: SpeciesOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  max?: number;
  placeholder?: string;
}

export default function SpeciesSelector({
  options,
  selected,
  onChange,
  max = 4,
  placeholder = 'Search and select species...',
}: SpeciesSelectorProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filtered = options.filter(
    (o) =>
      o.label.toLowerCase().includes(query.toLowerCase()) &&
      !selected.includes(o.value)
  );

  function toggle(value: string) {
    if (selected.includes(value)) {
      onChange(selected.filter((s) => s !== value));
    } else if (selected.length < max) {
      onChange([...selected, value]);
      setQuery('');
    }
  }

  return (
    <div ref={wrapperRef} className="relative">
      {/* Selected chips */}
      <div className="flex flex-wrap gap-2 mb-2">
        {selected.map((s) => {
          const opt = options.find((o) => o.value === s);
          return (
            <span
              key={s}
              className="inline-flex items-center gap-1 px-3 py-1 bg-brand-100 dark:bg-brand-800 text-brand-700 dark:text-brand-200 rounded-full text-sm"
            >
              <em>{opt?.label ?? s.replace(/_/g, ' ')}</em>
              <button
                onClick={() => toggle(s)}
                className="ml-1 hover:text-red-500"
                aria-label={`Remove ${opt?.label ?? s}`}
              >
                &times;
              </button>
            </span>
          );
        })}
      </div>

      {/* Search input */}
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={selected.length >= max ? `Max ${max} selected` : placeholder}
        disabled={selected.length >= max}
        className="w-full p-2 border border-neutral-300 rounded dark:border-neutral-600 dark:bg-neutral-800 dark:text-white disabled:opacity-50"
      />

      {/* Dropdown */}
      {isOpen && filtered.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full max-h-60 overflow-auto bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded shadow-lg">
          {filtered.slice(0, 50).map((opt) => (
            <li key={opt.value}>
              <button
                type="button"
                onClick={() => {
                  toggle(opt.value);
                  setIsOpen(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-brand-50 dark:hover:bg-brand-900 text-sm"
              >
                <em>{opt.label}</em>
              </button>
            </li>
          ))}
          {filtered.length > 50 && (
            <li className="px-3 py-2 text-sm text-neutral-500">
              ...and {filtered.length - 50} more. Type to narrow results.
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
