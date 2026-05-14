import { useEffect, useState } from 'react';
import { getReport } from '../api';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const SEV_COLORS = { critical: '#EF4444', high: '#F97316', medium: '#EAB308', low: '#6B7280' };

export default function ReportPanel({ scanId, scanComplete }) {
  const [report, setReport] = useState(null);

  useEffect(() => {
    if (!scanId || !scanComplete) return;
    getReport(scanId).then(data => setReport(data)).catch(() => {});
  }, [scanId, scanComplete]);

  const copyCode = (code) => {
    navigator.clipboard.writeText(code).catch(() => {});
  };

  if (!report) {
    return (
      <div className="report-panel">
        <h2>📊 Report</h2>
        <div className="report-empty">
          {scanComplete ? 'Loading report...' : 'Complete a scan to generate the report.'}
        </div>
      </div>
    );
  }

  const s = report.summary;

  return (
    <div className="report-panel">
      <h2>📊 Report — {report.report_id}</h2>
      <div className="report-metrics">
        <div className="metric-card">
          <div className="metric-value">{s.gaps_found}</div>
          <div className="metric-label">Gaps Found</div>
        </div>
        <div className="metric-card metric-critical">
          <div className="metric-value">{s.critical_findings}</div>
          <div className="metric-label">Critical</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{s.coverage_before_percent?.toFixed(1)}%</div>
          <div className="metric-label">Coverage Before</div>
        </div>
        <div className="metric-card metric-success">
          <div className="metric-value">{s.estimated_coverage_after_percent?.toFixed(1)}%</div>
          <div className="metric-label">Coverage After</div>
        </div>
      </div>

      {report.findings?.length > 0 && (
        <div className="report-section">
          <h3>Findings ({report.findings.length})</h3>
          {report.findings
            .sort((a, b) => {
              const order = { critical: 0, high: 1, medium: 2, low: 3 };
              return (order[a.severity] ?? 4) - (order[b.severity] ?? 4);
            })
            .map(f => (
              <div key={f.id} className="report-finding-row">
                <span className="severity-badge" style={{ background: SEV_COLORS[f.severity] }}>
                  {f.severity}
                </span>
                <span className="finding-page-label">{f.page}</span>
                <span className="finding-desc">{f.anomaly}</span>
              </div>
            ))}
        </div>
      )}

      {report.generated_tests?.length > 0 && (
        <div className="report-section">
          <h3>Generated Tests ({report.generated_tests.length})</h3>
          {report.generated_tests.map(t => (
            <div key={t.finding_id} className="test-block">
              <div className="test-header">
                <span className="test-name">{t.test_function_name}</span>
                <span className="severity-badge" style={{ background: SEV_COLORS[t.severity] }}>
                  {t.severity}
                </span>
                <button className="copy-btn" onClick={() => copyCode(t.test_code)}>
                  📋 Copy
                </button>
              </div>
              <SyntaxHighlighter language="python" style={oneDark} customStyle={{ borderRadius: '8px', fontSize: '12px' }}>
                {t.test_code}
              </SyntaxHighlighter>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
