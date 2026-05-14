import { useState, useCallback } from 'react';
import ScanControl from './components/ScanControl';
import MetricCards from './components/MetricCards';
import CoverageGraph from './components/CoverageGraph';
import RiskQueue from './components/RiskQueue';
import FindingsFeed from './components/FindingsFeed';
import MemoryPanel from './components/MemoryPanel';
import ReportPanel from './components/ReportPanel';
import './App.css';

export default function App() {
  const [scanId, setScanId] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanComplete, setScanComplete] = useState(false);
  const [scanStatus, setScanStatus] = useState(null);
  const [graphStats, setGraphStats] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeTab, setActiveTab] = useState('graph');

  const handleScanStart = useCallback((id) => {
    setScanId(id);
    setScanning(true);
    setScanComplete(false);
    setSelectedNode(null);
  }, []);

  const handleScanUpdate = useCallback((status) => {
    setScanStatus(status);
  }, []);

  const handleScanComplete = useCallback((id, status) => {
    setScanning(false);
    setScanComplete(status === 'completed');
  }, []);

  const handleNodeSelect = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <span className="logo-icon">🤖</span>
          <h1>Exploratory Testing Agent</h1>
        </div>
        <div className="header-subtitle">
          AI-Powered Coverage Gap Discovery & Autonomous Web Testing
        </div>
      </header>

      <div className="app-body">
        <div className="top-section">
          <ScanControl
            onScanStart={handleScanStart}
            onScanUpdate={handleScanUpdate}
            onScanComplete={handleScanComplete}
          />
          <MetricCards scanStatus={scanStatus} graphStats={graphStats} />
        </div>

        <nav className="tab-nav">
          {[
            { key: 'graph', label: '🗺️ Graph' },
            { key: 'queue', label: '⚡ Queue' },
            { key: 'findings', label: '🐛 Findings' },
            { key: 'memory', label: '🧠 Memory' },
            { key: 'report', label: '📊 Report' },
          ].map(t => (
            <button
              key={t.key}
              className={`tab-btn ${activeTab === t.key ? 'active' : ''}`}
              onClick={() => setActiveTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="main-content">
          <div className="panel-area">
            {activeTab === 'graph' && (
              <CoverageGraph scanId={scanId} scanning={scanning} onNodeSelect={handleNodeSelect} />
            )}
            {activeTab === 'queue' && <RiskQueue scanId={scanId} />}
            {activeTab === 'findings' && (
              <FindingsFeed scanId={scanId} scanning={scanning} onFindingSelect={handleNodeSelect} />
            )}
            {activeTab === 'memory' && <MemoryPanel />}
            {activeTab === 'report' && <ReportPanel scanId={scanId} scanComplete={scanComplete} />}
          </div>

          {selectedNode && (
            <aside className="detail-sidebar">
              <h3>Node Detail</h3>
              <button className="close-btn" onClick={() => setSelectedNode(null)}>✕</button>
              <div className="detail-field"><span className="detail-label">ID:</span> {selectedNode.id || selectedNode.node_id}</div>
              <div className="detail-field"><span className="detail-label">Label:</span> {selectedNode.label}</div>
              <div className="detail-field"><span className="detail-label">URL:</span> {selectedNode.url || selectedNode.page}</div>
              <div className="detail-field"><span className="detail-label">Type:</span> {selectedNode.type || selectedNode.anomaly_type}</div>
              <div className="detail-field"><span className="detail-label">Risk:</span> {selectedNode.risk_score?.toFixed(3)} ({selectedNode.risk_band || selectedNode.severity})</div>
              {selectedNode.covered !== undefined && (
                <div className="detail-field"><span className="detail-label">Covered:</span> {selectedNode.covered ? 'Yes' : 'No'}</div>
              )}
              {selectedNode.gap_reason && (
                <div className="detail-field"><span className="detail-label">Gap:</span> {selectedNode.gap_reason}</div>
              )}
              {selectedNode.anomaly && (
                <div className="detail-field"><span className="detail-label">Anomaly:</span> {selectedNode.anomaly}</div>
              )}
              {selectedNode.has_memory && (
                <div className="detail-field memory-indicator">🧠 Has memory from past scans</div>
              )}
            </aside>
          )}
        </div>
      </div>

      <footer className="app-footer">
        Exploratory Testing Agent — Built by Harsh Kumar Shaw
      </footer>
    </div>
  );
}
