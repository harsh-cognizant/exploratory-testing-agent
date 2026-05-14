import { useState, useCallback, useRef } from 'react';
import { startScan, getScanStatus } from '../api';

export default function ScanControl({ onScanStart, onScanUpdate, onScanComplete }) {
  const [appUrl, setAppUrl] = useState('http://localhost:3001');
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [scanId, setScanId] = useState(null);
  const [currentPhase, setCurrentPhase] = useState('');
  const pollRef = useRef(null);

  // Map internal stage names to user-friendly descriptions
  const PHASE_LABELS = {
    crawler: '🔍 Crawling pages…',
    graph_builder: '🗺️ Building coverage graph…',
    gap_analyser: '🔬 Analyzing coverage gaps…',
    risk_scorer: '⚡ Scoring risk levels…',
    explorer: '🧪 Exploring nodes…',
    memory: '🧠 Storing findings…',
    test_generator: '🧾 Generating tests…',
    report_builder: '📊 Compiling report…',
  };

  const handleScan = useCallback(async () => {
    setScanning(true);
    setProgress(0);
    setStatusText('Starting scan...');
    setCurrentPhase('');
    try {
      const data = await startScan(appUrl);
      const id = data.scan_id;
      setScanId(id);
      onScanStart?.(id);

      pollRef.current = setInterval(async () => {
        try {
          const status = await getScanStatus(id);

          // Update progress — ensure it only goes forward for smoother UX
          setProgress(prev => Math.max(prev, status.progress_percent || 0));

          // Determine which phase we're in
          const phase = status.current_node;
          const phaseLabel = PHASE_LABELS[phase] || (phase ? `Processing: ${phase}` : '');
          setCurrentPhase(phaseLabel);

          // Build rich status text
          const nodeText = status.current_node && !PHASE_LABELS[status.current_node]
            ? ` → ${status.current_node}` : '';
          const personaText = status.current_persona ? ` (${status.current_persona})` : '';
          const exploredText = status.nodes_explored > 0
            ? ` | ${status.nodes_explored}/${status.nodes_total} nodes` : '';

          setStatusText(`${status.status}${nodeText}${personaText}${exploredText}`);
          onScanUpdate?.(status);

          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollRef.current);
            pollRef.current = null;
            setScanning(false);
            setProgress(status.status === 'completed' ? 100 : progress);
            setStatusText(status.status === 'completed' ? '✓ Scan complete' : '✗ Scan failed');
            setCurrentPhase('');
            onScanComplete?.(id, status.status);
          }
        } catch {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setScanning(false);
          setStatusText('✗ Connection lost');
          setCurrentPhase('');
        }
      }, 2000);
    } catch (err) {
      setScanning(false);
      setStatusText(`✗ Error: ${err.message}`);
      setCurrentPhase('');
    }
  }, [appUrl, onScanStart, onScanUpdate, onScanComplete]);

  return (
    <div className="scan-control">
      <h2>🔍 Scan Control</h2>
      <div className="scan-input-row">
        <input
          id="scan-url-input"
          type="text"
          value={appUrl}
          onChange={(e) => setAppUrl(e.target.value)}
          placeholder="http://localhost:3001"
          disabled={scanning}
        />
        <button id="start-scan-btn" onClick={handleScan} disabled={scanning}>
          {scanning ? '⟳ Scanning...' : '▶ Start Scan'}
        </button>
      </div>
      {(scanning || statusText) && (
        <div className="scan-progress-area">
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="scan-status-text">
            <span>{currentPhase || statusText}</span>
            <span className="progress-pct">{progress}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
