import { useEffect, useState } from 'react';
import { getQueue } from '../api';

const BAND_COLORS = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#22C55E',
};

export default function RiskQueue({ scanId }) {
  const [queue, setQueue] = useState([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (!scanId) return;
    getQueue(scanId, filter || undefined).then(data => setQueue(data.queue || [])).catch(() => {});
  }, [scanId, filter]);

  return (
    <div className="risk-queue-panel">
      <h2>⚡ Risk Queue</h2>
      <div className="risk-filter-row">
        {['', 'critical', 'high', 'medium', 'low'].map(band => (
          <button
            key={band}
            className={`risk-filter-btn ${filter === band ? 'active' : ''}`}
            style={band ? { borderColor: BAND_COLORS[band] } : {}}
            onClick={() => setFilter(band)}
          >
            {band || 'All'}
          </button>
        ))}
      </div>
      <div className="queue-list">
        {queue.map(item => (
          <div key={item.node_id} className="queue-item">
            <span className="queue-rank">#{item.rank}</span>
            <span className="queue-badge" style={{ background: BAND_COLORS[item.risk_band] }}>
              {item.risk_band}
            </span>
            <span className="queue-node">{item.node_id}</span>
            <span className="queue-score">{item.risk_score.toFixed(3)}</span>
          </div>
        ))}
        {queue.length === 0 && <div className="queue-empty">No items. Run a scan first.</div>}
      </div>
    </div>
  );
}
