import { useEffect, useState } from 'react';
import { getFindings } from '../api';

const SEV_COLORS = { critical: '#EF4444', high: '#F97316', medium: '#EAB308', low: '#6B7280' };
const PERSONA_ICONS = { confused_user: '😵', power_user: '⚡', malicious_user: '🔓' };

export default function FindingsFeed({ scanId, scanning, onFindingSelect }) {
  const [findings, setFindings] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!scanId) return;
    let active = true;
    const fetchFindings = async () => {
      try {
        const data = await getFindings(scanId);
        if (active) {
          setFindings(data.findings || []);
          setSummary(data.summary || null);
        }
      } catch { /* ignore */ }
    };
    fetchFindings();
    const interval = scanning ? setInterval(fetchFindings, 3000) : null;
    return () => { active = false; if (interval) clearInterval(interval); };
  }, [scanId, scanning]);

  return (
    <div className="findings-feed-panel">
      <h2>🐛 Findings Feed</h2>
      {summary && (
        <div className="findings-summary-bar">
          <span>Total: {summary.total}</span>
          {summary.critical > 0 && <span style={{ color: SEV_COLORS.critical }}>Critical: {summary.critical}</span>}
          {summary.high > 0 && <span style={{ color: SEV_COLORS.high }}>High: {summary.high}</span>}
          {summary.medium > 0 && <span style={{ color: SEV_COLORS.medium }}>Medium: {summary.medium}</span>}
        </div>
      )}
      <div className="findings-list">
        {findings.map(f => (
          <div key={f.id} className="finding-card" onClick={() => onFindingSelect?.(f)}>
            <div className="finding-header">
              <span className="persona-badge">
                {PERSONA_ICONS[f.persona] || '👤'} {f.persona?.replace('_', ' ')}
              </span>
              <span className="severity-badge" style={{ background: SEV_COLORS[f.severity] }}>
                {f.severity}
              </span>
            </div>
            <div className="finding-page">{f.page}</div>
            <div className="finding-anomaly">{f.anomaly}</div>
            {f.screenshot_url && (
              <img
                src={f.screenshot_url}
                alt={`Finding ${f.id}`}
                className="finding-screenshot"
              />
            )}
            <div className="finding-steps">
              {f.reproduction_steps?.slice(0, 3).map((s, i) => (
                <div key={i} className="step">{i + 1}. {s}</div>
              ))}
            </div>
          </div>
        ))}
        {findings.length === 0 && (
          <div className="findings-empty">
            {scanning ? '⟳ Waiting for findings...' : 'No findings yet. Run a scan.'}
          </div>
        )}
      </div>
    </div>
  );
}
