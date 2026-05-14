const API_BASE = '';

export async function startScan(appUrl) {
  const res = await fetch(`${API_BASE}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_url: appUrl }),
  });
  return res.json();
}

export async function getScanStatus(scanId) {
  const res = await fetch(`${API_BASE}/scan/${scanId}/status`);
  return res.json();
}

export async function getGraph(scanId) {
  const url = scanId ? `${API_BASE}/graph?scan_id=${scanId}` : `${API_BASE}/graph`;
  const res = await fetch(url);
  return res.json();
}

export async function getQueue(scanId, riskBand) {
  let url = `${API_BASE}/queue`;
  const params = new URLSearchParams();
  if (scanId) params.set('scan_id', scanId);
  if (riskBand) params.set('risk_band', riskBand);
  if (params.toString()) url += `?${params}`;
  const res = await fetch(url);
  return res.json();
}

export async function getFindings(scanId, severity) {
  let url = `${API_BASE}/findings`;
  const params = new URLSearchParams();
  if (scanId) params.set('scan_id', scanId);
  if (severity) params.set('severity', severity);
  if (params.toString()) url += `?${params}`;
  const res = await fetch(url);
  return res.json();
}

export async function getMemory() {
  const res = await fetch(`${API_BASE}/memory`);
  return res.json();
}

export async function getReport(scanId) {
  const url = scanId ? `${API_BASE}/report?scan_id=${scanId}` : `${API_BASE}/report`;
  const res = await fetch(url);
  if (res.status === 404 || res.status === 202) return null;
  return res.json();
}
