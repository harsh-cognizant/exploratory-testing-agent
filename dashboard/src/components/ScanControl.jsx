import { useState, useCallback } from 'react';
import { startScan, getScanStatus } from '../api';

export default function ScanControl({ onScanStart, onScanUpdate, onScanComplete }) {
  const [appUrl, setAppUrl] = useState('http://localhost:3001');
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [scanId, setScanId] = useState(null);

  const handleScan = useCallback(async () => {
    setScanning(true);
    setProgress(0);
    setStatusText('Starting scan...');
    try {
      const data = await startScan(appUrl);
      const id = data.scan_id;
      setScanId(id);
      onScanStart?.(id);

      const poll = setInterval(async () => {
        try {
          const status = await getScanStatus(id);
          setProgress(status.progress_percent || 0);
          const nodeText = status.current_node ? ` → ${status.current_node}` : '';
          const personaText = status.current_persona ? ` (${status.current_persona})` : '';
          setStatusText(`${status.status}${nodeText}${personaText}`);
          onScanUpdate?.(status);

          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(poll);
            setScanning(false);
            setStatusText(status.status === 'completed' ? '✓ Scan complete' : '✗ Scan failed');
            onScanComplete?.(id, status.status);
          }
        } catch {
          clearInterval(poll);
          setScanning(false);
          setStatusText('✗ Connection lost');
        }
      }, 2000);
    } catch (err) {
      setScanning(false);
      setStatusText(`✗ Error: ${err.message}`);
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
            <span>{statusText}</span>
            <span className="progress-pct">{progress}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
