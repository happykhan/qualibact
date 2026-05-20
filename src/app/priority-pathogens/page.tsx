import type { Metadata } from 'next';
import PriorityListView from './PriorityList';
import { getList } from './lib';

export const metadata: Metadata = {
  title: 'WHO priority pathogens',
  description:
    'Recommended genome assembly QC thresholds for the species on the WHO Bacterial Priority Pathogens List (2024).',
};

export default function PriorityPathogensPage() {
  const list = getList(2024);
  return (
    <PriorityListView
      list={list}
      alternateYearHref={{ year: 2017, href: '/priority-pathogens/2017/' }}
    />
  );
}
