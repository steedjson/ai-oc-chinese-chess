import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { TrendChart } from '../TrendChart';

describe('TrendChart', () => {
  const mockData = [
    { date: '2024-01-01', count: 10 },
    { date: '2024-01-02', count: 15 },
    { date: '2024-01-03', count: 8 },
    { date: '2024-01-04', count: 20 },
  ];

  it('should render without crashing', () => {
    const { container } = render(<TrendChart data={mockData} xKey="date" yKey="count" />);
    expect(container).toBeInTheDocument();
  });

  it('should render with empty data', () => {
    const { container } = render(<TrendChart data={[]} xKey="date" yKey="count" />);
    expect(container).toBeInTheDocument();
  });

  it('should render with single data point', () => {
    const singleData = [{ date: '2024-01-01', count: 10 }];
    const { container } = render(<TrendChart data={singleData} xKey="date" yKey="count" />);
    expect(container).toBeInTheDocument();
  });

  it('should handle large dataset', () => {
    const largeData = Array.from({ length: 100 }, (_, i) => ({
      date: `2024-01-${i + 1}`,
      count: i * 10,
    }));
    const { container } = render(<TrendChart data={largeData} xKey="date" yKey="count" />);
    expect(container).toBeInTheDocument();
  });

  it('should accept custom color prop', () => {
    const { container } = render(
      <TrendChart data={mockData} xKey="date" yKey="count" color="#ff0000" />
    );
    expect(container).toBeInTheDocument();
  });
});
