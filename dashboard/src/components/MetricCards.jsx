export default function MetricCards({ scanStatus, graphStats }) {
  const cards = [
    {
      icon: '🌐',
      label: 'Nodes Discovered',
      value: graphStats?.total_nodes ?? scanStatus?.nodes_total ?? '—',
    },
    {
      icon: '✅',
      label: 'Covered',
      value: graphStats?.covered ?? '—',
      color: '#22C55E',
    },
    {
      icon: '🔴',
      label: 'Coverage Gaps',
      value: graphStats?.gaps ?? '—',
      color: '#EF4444',
    },
    {
      icon: '🐛',
      label: 'Findings',
      value: scanStatus?.findings_so_far ?? '—',
      color: '#F97316',
    },
    {
      icon: '📊',
      label: 'Coverage %',
      value: graphStats?.coverage_percent != null ? `${graphStats.coverage_percent.toFixed(1)}%` : '—',
    },
    {
      icon: '🔄',
      label: 'Progress',
      value: scanStatus?.progress_percent != null ? `${scanStatus.progress_percent}%` : '—',
    },
  ];

  return (
    <div className="metric-cards-row">
      {cards.map((c, i) => (
        <div key={i} className="metric-card-sm">
          <div className="mc-icon">{c.icon}</div>
          <div className="mc-value" style={c.color ? { color: c.color } : {}}>
            {c.value}
          </div>
          <div className="mc-label">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
