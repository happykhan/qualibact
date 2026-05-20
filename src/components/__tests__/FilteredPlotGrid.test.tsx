import React from 'react';
import { render, screen } from '@testing-library/react';
import FilteredPlotGrid from '../FilteredPlotGrid';

describe('FilteredPlotGrid', () => {
  it('groups plots by metric and displays All/Sample/Filtered columns', () => {
    const items = [
      { filename: 'Escherichia coli_all_longest_Completeness_Specific.png', path: '/a/all1.png' },
      { filename: 'Escherichia coli_sample_longest_Completeness_Specific.png', path: '/a/sample1.png' },
      { filename: 'Escherichia coli_filt_longest_Completeness_Specific.png', path: '/a/filt1.png' },
    ];
    render(<FilteredPlotGrid items={items} />);

    expect(screen.getByText(/Longest vs Completeness Specific/i)).toBeInTheDocument();
    expect(screen.getByText(/All/i)).toBeInTheDocument();
    expect(screen.getByText(/Sample/i)).toBeInTheDocument();
    expect(screen.getByText(/Filtered/i)).toBeInTheDocument();
    expect(screen.getByText(/Escherichia coli_all_longest_Completeness_Specific.png/)).toBeInTheDocument();
  });
});
