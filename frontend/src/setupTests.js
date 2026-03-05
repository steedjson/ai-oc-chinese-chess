import '@testing-library/jest-dom';

// Mock Ant Design components if needed
jest.mock('antd', () => {
  const actualAntd = jest.requireActual('antd');
  return {
    ...actualAntd,
    Card: ({ children, title, className, ...props }) => (
      <div className={className} {...props}>
        {title && <div className="ant-card-title">{title}</div>}
        <div className="ant-card-body">{children}</div>
      </div>
    ),
    Row: ({ children, gutter, style, ...props }) => (
      <div className="ant-row" style={style} {...props}>{children}</div>
    ),
    Col: ({ children, xs, sm, md, style, ...props }) => (
      <div className="ant-col" style={style} {...props}>{children}</div>
    ),
    Statistic: ({ title, value, prefix, suffix, precision, valueStyle }) => (
      <div className="ant-statistic" style={valueStyle}>
        {prefix && <span className="ant-statistic-prefix">{prefix}</span>}
        <div className="ant-statistic-title">{title}</div>
        <div className="ant-statistic-content">
          {typeof value === 'number' && precision !== undefined 
            ? value.toFixed(precision) 
            : value}
          {suffix && <span className="ant-statistic-suffix">{suffix}</span>}
        </div>
      </div>
    ),
    Progress: ({ percent, strokeColor, size, status }) => (
      <div className="ant-progress" data-percent={percent}>
        <div className="ant-progress-bg" style={{ width: `${percent}%`, background: Array.isArray(strokeColor) ? strokeColor[0] : strokeColor }} />
      </div>
    ),
  };
});

jest.mock('@ant-design/icons', () => ({
  UserOutlined: () => <span data-icon="user" />,
  FundOutlined: () => <span data-icon="fund" />,
  TrophyOutlined: () => <span data-icon="trophy" />,
  RiseOutlined: () => <span data-icon="rise" />,
}));
