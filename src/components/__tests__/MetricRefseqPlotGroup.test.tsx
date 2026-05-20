import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MetricRefseqPlotGroup from '../MetricRefseqPlotGroup';

describe('MetricRefseqPlotGroup', () => {
  it('renders initial metrics and supports next/prev', async () => {
    const metrics = [
      { metric: 'GC_Content', hist: '/a/GC_hist.png', qq: '/a/GC_qq.png' },
      { metric: 'Genome_Size', hist: '/a/GS_hist.png', qq: '/a/GS_qq.png' },
    ];
    render(<MetricRefseqPlotGroup species="Escherichia_coli" version="Super-v2" initialMetrics={metrics} />);

    // Should display the first metric name
    expect(screen.getByText(/GC Content/i)).toBeInTheDocument();

    const next = screen.getByRole('button', { name: /➡/i });
    await userEvent.click(next);
    expect(screen.getByText(/Genome Size/i)).toBeInTheDocument();

    const prev = screen.getByRole('button', { name: /⬅/i });
    await userEvent.click(prev);
    expect(screen.getByText(/GC Content/i)).toBeInTheDocument();
  });
});
