import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import fs from 'fs';
import path from 'path';
import MetricCarousel from '@/components/MetricCarousel';
import { staticUrl } from '@/lib/static-url';

interface GenusPageProps {
  params: Promise<{ genus: string }>;
}

interface SpeciesData {
  species: string;
  qc_schemes: string[];
  preferred_qc_scheme: string | null;
}

function loadSiteIndex() {
  const dataPath = path.join(process.cwd(), 'public', 'website_summary.json');
  if (!fs.existsSync(dataPath)) return null;
  return JSON.parse(fs.readFileSync(dataPath, 'utf8'));
}

export async function generateStaticParams() {
  const siteData = loadSiteIndex();
  if (!siteData) return [];
  const genera = new Set<string>();
  Object.keys(siteData?.species || {}).forEach((species) => {
    const genus = species.split('_')[0];
    if (genus) genera.add(genus);
  });
  return Array.from(genera).map((genus) => ({ genus }));
}

export async function generateMetadata({ params }: GenusPageProps): Promise<Metadata> {
  const { genus } = await params;
  return {
    title: `${genus} Overview`,
    description: `Quality control thresholds and metrics for ${genus} species bacterial genome assemblies.`,
  };
}

export default async function GenusPage({ params }: GenusPageProps) {
  const { genus } = await params;
  const siteData = loadSiteIndex();
  if (!siteData) {
    notFound();
  }
  const mapped: Record<string, SpeciesData> = {};
  Object.entries(siteData?.species || {}).forEach(([key, value]: [string, any]) => {
    mapped[key] = {
      species: key,
      qc_schemes: value?.qc_schemes || [],
      preferred_qc_scheme: value?.preferred_qc_scheme ?? null,
    };
  });
  const allSpecies: Record<string, SpeciesData> = mapped;

  const genusSpecies = Object.values(allSpecies).filter(speciesData =>
    speciesData && speciesData.species && speciesData.species.startsWith(genus + '_')
  );

  if (genusSpecies.length === 0) {
    notFound();
  }

  // Use manifest data for genus plots (R2 files)
  const genusManifest = siteData?.genera?.[genus];
  const gcPlots: string[] = [];
  const contPlots: string[] = [];
  const n50Plots: string[] = [];
  const longestPlots: string[] = [];

  const plotFiles: { name: string; urlPrefix: string }[] = [];
  if (genusManifest?.subdir_plots?.length > 0) {
    for (const p of genusManifest.subdir_plots) {
      plotFiles.push({ name: p, urlPrefix: `/static/genus/${genus}/plots` });
    }
  } else if (genusManifest?.plots?.length > 0) {
    for (const p of genusManifest.plots) {
      plotFiles.push({ name: p, urlPrefix: `/static/genus/${genus}` });
    }
  }

  // Ordered list of (metric token in filename, human label) for the
  // metric_range_*.png files the engine emits at the genus level.
  // Order here is the order the carousel will show them in.
  const METRIC_RANGE_DISPLAY: { token: string; label: string }[] = [
    { token: 'Genome_Size', label: 'Genome size' },
    { token: 'GC_Content', label: 'GC content' },
    { token: 'Total_Coding_Sequences', label: 'Total coding sequences' },
    { token: 'Completeness_Specific', label: 'Completeness' },
    { token: 'Contamination', label: 'Contamination' },
    { token: 'N50', label: 'N50' },
    { token: 'number', label: 'Number of contigs' },
    { token: 'longest', label: 'Longest contig' },
  ];

  const metricItems: { metric: string; image: string }[] = [];
  for (const { token, label } of METRIC_RANGE_DISPLAY) {
    const filename = `metric_range_${token}.png`;
    const match = plotFiles.find((p) => p.name === filename);
    if (match) {
      metricItems.push({ metric: label, image: staticUrl(`${match.urlPrefix}/${match.name}`) });
    }
  }
  // Boxplot fallbacks for the small set of genera that still ship the
  // legacy `{Metric}_boxplot_*.png` shape rather than `metric_range_*.png`.
  // Only filled in when the modern range plot is missing for that metric.
  for (const { token, label } of METRIC_RANGE_DISPLAY) {
    if (metricItems.some((m) => m.metric === label)) continue;
    const boxplot = plotFiles.find((p) => p.name.startsWith(`${token}_boxplot_`));
    if (boxplot) {
      metricItems.push({ metric: label, image: staticUrl(`${boxplot.urlPrefix}/${boxplot.name}`) });
    }
  }

  return (
    <div className="py-8">
      <div>
        <h1 className="text-3xl font-bold font-header mb-6 font-header"><em>{genus}</em> Overview</h1>
        <p className="mb-8 text-neutral-600 dark:text-neutral-400">
          This page provides an overview of the genus, including links to species-specific pages and general information.
        </p>

        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 font-header">Species in this Genus</h2>
          <ul className="list-disc list-inside space-y-2">
            {genusSpecies.map((speciesData) => {
              const speciesName = speciesData.species.replace(/_/g, ' ');
              return (
                <li key={speciesData.species}>
                  <a
                    href={`/${genus}/${speciesData.species}`}
                    className="text-brand-600 hover:underline dark:text-brand-400"
                  >
                    Species page: <em>{speciesName}</em>
                  </a>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 font-header">Genus Data</h2>
          <p className="mb-4 text-neutral-600 dark:text-neutral-400">
            Download the species counts and summary metrics for this genus:
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href={staticUrl(`/static/genus/${genus}/${genus}_counts.csv`)}
              className="btn btn-primary"
            >
              Download species counts
            </a>
            <a
              href={staticUrl(`/static/genus/${genus}/${genus}_metrics.csv`)}
              className="btn btn-ghost"
            >
              Download genus metrics
            </a>
          </div>
        </div>

        {genusSpecies.length > 1 && metricItems.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 font-header">Genus Visualizations</h2>
            <p className="mb-4 text-neutral-600 dark:text-neutral-400">
              These plots show the main summary visualizations for this genus:
            </p>
            <div className="grid grid-cols-1 gap-6">
              <MetricCarousel items={metricItems} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
