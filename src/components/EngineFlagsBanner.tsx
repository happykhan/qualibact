interface FlagSignal {
  signal: string;
  flag: 'info' | 'warn' | 'error' | string;
  fraction?: number | null;
  count?: number | null;
  n?: number | null;
  interpretation?: string | null;
}

interface Props {
  severity?: 'info' | 'warn' | 'error' | null;
  fired?: FlagSignal[];
  /** Engine's low_count_flag (info|warn|error) — surfaced as a synthetic signal so the user sees the reason. */
  lowCountFlag?: string | null;
  /** Non-RefSeq genome count — what the engine actually evaluates against its low-count threshold. */
  nonRefseqCount?: number | null;
  /** Free-text caveats from content/species-notes.yml — rendered as additional bullet items. */
  notes?: string[];
}

const STYLES: Record<string, string> = {
  error:
    'border-red-400 bg-red-50 text-red-900 dark:border-red-700 dark:bg-red-950/40 dark:text-red-100',
  warn:
    'border-amber-400 bg-amber-50 text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100',
  info:
    'border-blue-400 bg-blue-50 text-blue-900 dark:border-blue-700 dark:bg-blue-950/40 dark:text-blue-100',
};

function SeverityIcon({ severity }: { severity: string }) {
  const common = 'w-5 h-5 flex-shrink-0';
  if (severity === 'error') {
    // Filled red circle with exclamation
    return (
      <svg className={common} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path
          fillRule="evenodd"
          d="M10 2a8 8 0 100 16 8 8 0 000-16zm.75 4a.75.75 0 00-1.5 0v4.5a.75.75 0 001.5 0V6zM10 13.5a1 1 0 100 2 1 1 0 000-2z"
          clipRule="evenodd"
        />
      </svg>
    );
  }
  if (severity === 'warn') {
    // Triangle with exclamation
    return (
      <svg className={common} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path
          fillRule="evenodd"
          d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.516-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 8a1 1 0 100-2 1 1 0 000 2z"
          clipRule="evenodd"
        />
      </svg>
    );
  }
  // info: filled blue circle with "i"
  return (
    <svg className={common} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zm-1 2.75a.75.75 0 00-.75.75v3.5a.75.75 0 001.5 0v-3.5a.75.75 0 00-.75-.75z"
        clipRule="evenodd"
      />
    </svg>
  );
}

const SIGNAL_LABEL: Record<string, string> = {
  frac_incomplete: 'Incomplete genomes',
  frac_short_genome: 'Genomes shorter than 70% of median',
  frac_oversized_genome: 'Genomes larger than 2× median',
  frac_high_contamination: 'Genomes with Contamination > 5%',
  max_contamination_over_100: 'Contamination > 100% (CheckM2 ceiling breach)',
  wide_gc_range: 'GC range wider than 5 percentage points',
  low_count_flag: 'Low genome count',
  final_bound_dragged: 'FAIL band dragged beyond WARN band by outliers',
};

/** Pretty-print any engine signal token that doesn't have an explicit
 *  label: drop underscores, sentence-case the first word. */
function signalDisplayName(signal: string): string {
  if (SIGNAL_LABEL[signal]) return SIGNAL_LABEL[signal];
  const spaced = signal.replace(/_/g, ' ').trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

const HEADLINE: Record<string, string> = {
  error:
    'The reference dataset for this species has substantial quality issues. Thresholds should be treated as indicative only.',
  warn:
    'The engine flagged the reference dataset for this species — review the signals below before relying on these thresholds.',
  info:
    'Informational flags from the engine. Thresholds are reliable but the issues below are worth knowing.',
};

function formatFraction(s: FlagSignal): string | null {
  if (s.fraction == null || s.n == null) return null;
  const pct = (s.fraction * 100).toFixed(1);
  return s.count != null ? `${pct}% (${s.count}/${s.n} genomes)` : `${pct}%`;
}

export default function EngineFlagsBanner({
  severity,
  fired,
  lowCountFlag,
  nonRefseqCount,
  notes,
}: Props) {
  // Build the displayed list of reasons. Start with the engine's quality
  // signals, then prepend a synthetic low-count entry when the engine's
  // low_count_flag is set so the user sees *why* the banner fired.
  // The engine evaluates low_count_flag against the non-RefSeq subset
  // (the "other genomes" feeding the distribution), not the total
  // including RefSeq references.
  const items: FlagSignal[] = [...(fired ?? [])];
  if (lowCountFlag) {
    // The engine fires this when its post-IsolationForest reference pool
    // is small (warn < 500, error < 100 — qualibact/flags.py). Below 500
    // the percentile bounds get noisy; below 100 they're driven by a
    // handful of samples.
    const ctx = typeof nonRefseqCount === 'number' && nonRefseqCount > 0
      ? `Only ${nonRefseqCount.toLocaleString('en-US')} genomes survived Isolation-Forest outlier filtering — the engine flags reference pools below 500 as warn, below 100 as error, because percentile-based bounds become unreliable at low n.`
      : null;
    items.unshift({
      signal: 'low_count_flag',
      flag: lowCountFlag,
      fraction: null,
      count: typeof nonRefseqCount === 'number' ? nonRefseqCount : null,
      n: null,
      interpretation: ctx,
    });
  }
  const notesList = notes ?? [];
  if (!severity && items.length === 0 && notesList.length === 0) return null;

  // Effective severity for styling: when there's no engine severity but
  // species-notes exist, fall through to a soft 'warn' background so
  // authored caveats still pop.
  const effSeverity = severity || (notesList.length ? 'warn' : 'info');
  if (effSeverity === 'info' && items.length === 0 && notesList.length === 0) return null;

  const style = STYLES[effSeverity] ?? STYLES.warn;
  const headline = HEADLINE[effSeverity] ?? HEADLINE.warn;

  return (
    <section
      className={`rounded-lg border-l-4 px-4 py-3 space-y-3 ${style}`}
      role={effSeverity === 'error' ? 'alert' : undefined}
    >
      <h3 className="font-semibold font-header flex items-center gap-2">
        <SeverityIcon severity={effSeverity} />
        <span>Engine quality flag: <span className="uppercase">{effSeverity}</span></span>
      </h3>
      {severity && <p className="text-sm">{headline}</p>}
      {items.length > 0 && (
        <ul className="space-y-1.5 text-sm">
          {items.map((s) => (
            <li key={s.signal} className="flex flex-col gap-0.5">
              <span>
                <strong>{signalDisplayName(s.signal)}</strong>
                {' '}
                <span className="text-xs font-mono uppercase opacity-75">
                  ({s.flag})
                </span>
                {formatFraction(s) && (
                  <span className="text-xs opacity-80"> — {formatFraction(s)}</span>
                )}
              </span>
              {s.interpretation && (
                <span className="text-xs opacity-80 italic">{s.interpretation}</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {notesList.length > 0 && (
        <div className="space-y-1.5 text-sm">
          {notesList.map((n, i) => (
            <p key={i}>{n}</p>
          ))}
        </div>
      )}
    </section>
  );
}
