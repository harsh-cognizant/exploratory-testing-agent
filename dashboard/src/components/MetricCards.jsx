export default function MetricCards({ scanStatus, graphStats }) {
  // Coverage data comes from TWO sources:
  //   1. graphStats  — from /graph endpoint (via CoverageGraph or App polling)
  //   2. scanStatus  — from /scan/{id}/status endpoint (polled every 2s by ScanControl)
  // We prefer graphStats when available; fall back to scanStatus fields.
  const covered = graphStats?.covered ?? scanStatus?.covered_nodes ?? null;
  const gaps = graphStats?.gaps ?? scanStatus?.gap_nodes ?? null;
  const coveragePct = graphStats?.coverage_percent ?? scanStatus?.coverage_percent ?? null;

  const cards = [
    {
      icon: '🌐',
      label: 'Nodes Discovered',
      value: graphStats?.total_nodes ?? scanStatus?.nodes_total ?? '—',
    },
    {
      icon: '✅',
      label: 'Covered',
      value: covered != null ? covered : '—',
      color: '#22C55E',
    },
    {
      icon: '🔴',
      label: 'Coverage Gaps',
      value: gaps != null ? gaps : '—',
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
      value: coveragePct != null ? `${Number(coveragePct).toFixed(1)}%` : '—',
    },
    {
      icon: '🔄',
      label: 'Progress',
      value: scanStatus?.progress_percent != null ? `${scanStatus.progress_percent}%` : '—',
      animatedWidth: scanStatus?.progress_percent != null ? scanStatus.progress_percent : null,
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
          {c.animatedWidth != null && (
            <div className="mc-progress-mini">
              <div
                className="mc-progress-mini-fill"
                style={{ width: `${c.animatedWidth}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
