import type { Metadata } from 'next';
import PriorityListView from '../PriorityList';
import { getList } from '../lib';

export const metadata: Metadata = {
  title: 'WHO priority pathogens (2017)',
  description:
    'Historical 2017 WHO Bacterial Priority Pathogens List with QualiBact genome assembly QC thresholds where available.',
};

export default function PriorityPathogens2017Page() {
  const list = getList(2017);
  return (
    <PriorityListView
      list={list}
      alternateYearHref={{ year: 2024, href: '/priority-pathogens/' }}
    />
  );
}
