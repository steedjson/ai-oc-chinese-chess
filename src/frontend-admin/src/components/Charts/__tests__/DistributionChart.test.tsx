import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { DistributionChart } from '../DistributionChart';

describe('DistributionChart', () => {
  const mockData = [
    { name: 'PVP 对局', value: 70 },
    { name: '人机对局', value: 30 },
  ];

  it('should render without crashing', () => {
    const { container } = render(<DistributionChart data={mockData} />);
    expect(container).toBeInTheDocument();
  });

  it('should render with empty data', () => {
    const { container } = render(<DistributionChart data={[]} />);
    expect(container).toBeInTheDocument();
  });

  it('should render with single data point', () => {
    const singleData = [{ name: 'Single', value: 100 }];
    const { container } = render(<DistributionChart data={singleData} />);
    expect(container).toBeInTheDocument();
  });

  it('should accept custom colors prop', () => {
    const customColors = ['#ff0000', '#00ff00'];
    const { container } = render(
      <DistributionChart data={mockData} colors={customColors} />
    );
    expect(container).toBeInTheDocument();
  });

  it('should handle large dataset', () => {
    const largeData = Array.from({ length: 10 }, (_, i) => ({
      name: `Item ${i + 1}`,
      value: i * 10,
    }));
    const { container } = render(<DistributionChart data={largeData} />);
    expect(container).toBeInTheDocument();
  });
});
