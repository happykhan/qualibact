import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

interface OverrideEntry {
  species: string;
  scheme: string;
  metric: string;
  lower?: number;
  upper?: number;
  reason?: string;
}

function loadOverrides(): OverrideEntry[] {
  const file = path.join(process.cwd(), 'content', 'threshold-rationale.yml');
  if (!fs.existsSync(file)) return [];
  const parsed = yaml.load(fs.readFileSync(file, 'utf8')) as
    | { overrides?: OverrideEntry[] }
    | null;
  return parsed?.overrides ?? [];
}

function formatValue(v: number | undefined): string {
  if (v === undefined || v === null) return '';
  if (Math.abs(v) >= 1000) return v.toLocaleString('en', { maximumFractionDigits: 0 });
  return v.toLocaleString('en', { maximumFractionDigits: 4 });
}

export default function ThresholdRationaleTable() {
  const overrides = loadOverrides();
  if (overrides.length === 0) return null;

  return (
    <div className="my-6 space-y-3">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700">
          <thead>
            <tr className="bg-neutral-50 dark:bg-neutral-700">
              <th className="px-3 py-2 text-left border-b">Species</th>
              <th className="px-3 py-2 text-left border-b">Scheme</th>
              <th className="px-3 py-2 text-left border-b">Metric</th>
              <th className="px-3 py-2 text-left border-b">Lower</th>
              <th className="px-3 py-2 text-left border-b">Upper</th>
              <th className="px-3 py-2 text-left border-b">Reason</th>
            </tr>
          </thead>
          <tbody>
            {overrides.map((o, i) => (
              <tr
                key={`${o.species}-${o.scheme}-${o.metric}-${i}`}
                className={i % 2 === 0 ? 'bg-white dark:bg-neutral-800' : 'bg-neutral-50 dark:bg-neutral-700'}
              >
                <td className="px-3 py-2 border-b italic">{o.species.replace(/_/g, ' ')}</td>
                <td className="px-3 py-2 border-b">{o.scheme}</td>
                <td className="px-3 py-2 border-b font-mono text-xs">{o.metric}</td>
                <td className="px-3 py-2 border-b">{formatValue(o.lower)}</td>
                <td className="px-3 py-2 border-b">{formatValue(o.upper)}</td>
                <td className="px-3 py-2 border-b text-neutral-700 dark:text-neutral-300">{o.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm text-neutral-600 dark:text-neutral-400">
        Source file:{' '}
        <a
          href="/api/v2/threshold-rationale.yml"
          className="underline"
          download="threshold-rationale.yml"
        >
          /api/v2/threshold-rationale.yml
        </a>
      </p>
    </div>
  );
}
