import { useEffect, useState } from 'react';
import { getMemory } from '../api';

export default function MemoryPanel() {
  const [runs, setRuns] = useState([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    getMemory().then(data => {
      setRuns(data.runs || []);
      setTotal(data.total_findings_in_memory || 0);
    }).catch(() => {});
  }, []);

  return (
    <div className="memory-panel">
      <h2>🧠 Agent Memory</h2>
      <div className="memory-stat">
        <span className="memory-total-label">Findings in memory:</span>
        <span className="memory-total-val">{total}</span>
      </div>
      <div className="memory-runs">
        {runs.map(run => (
          <div key={run.run_id} className="memory-run-card">
            <div className="run-header">
              <span className="run-id">{run.run_id}</span>
              <span className="run-date">{run.date}</span>
            </div>
            <div className="run-details">
              <span>{run.findings_count} findings</span>
              {run.top_finding && <span className="run-top">Top: {run.top_finding}</span>}
            </div>
          </div>
        ))}
        {runs.length === 0 && (
          <div className="memory-empty">No past scan data in memory yet.</div>
        )}
      </div>
    </div>
  );
}
