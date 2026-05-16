/**
 * TrendCharts tests — empty state and non-empty bucket rendering.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrendCharts } from './TrendCharts';
import type { TrendsResponse } from '@/lib/api';

describe('TrendCharts', () => {
  it('renders empty state when no trend buckets exist', () => {
    const data: TrendsResponse = { data: [] };

    render(<TrendCharts data={data} />);

    expect(screen.getByText(/no trend|no data|empty/i)).toBeInTheDocument();
  });

  it('renders trend buckets for non-empty data', () => {
    const data: TrendsResponse = {
      data: [
        { bucket: '2024-01-01T00:00:00', count: 5 },
        { bucket: '2024-01-02T00:00:00', count: 8 },
        { bucket: '2024-01-03T00:00:00', count: 3 },
      ],
    };

    render(<TrendCharts data={data} />);

    // Recharts renders an SVG with recharts-responsive-container
    const container = document.querySelector('.recharts-responsive-container');
    expect(container).toBeTruthy();
  });
});
