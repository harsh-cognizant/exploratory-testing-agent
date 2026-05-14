import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const RISK_COLORS = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#22C55E',
};
const COVERED_COLOR = '#6B7280';

// Distinct shapes per node type for visual specificity
const NODE_SHAPES = {
  page: 'circle',
  form: 'rect',
  button: 'diamond',
  api: 'hexagon',
  state: 'triangle',
};

// Icons per node type
const NODE_ICONS = {
  page: '🌐',
  form: '📝',
  button: '🔘',
  api: '⚡',
  state: '📌',
};

function drawNodeShape(selection, type, size) {
  const shapeType = NODE_SHAPES[type] || 'circle';

  if (shapeType === 'circle') {
    selection.append('circle')
      .attr('r', size)
      .attr('class', 'node-shape');
  } else if (shapeType === 'rect') {
    selection.append('rect')
      .attr('x', -size)
      .attr('y', -size)
      .attr('width', size * 2)
      .attr('height', size * 2)
      .attr('rx', 4)
      .attr('class', 'node-shape');
  } else if (shapeType === 'diamond') {
    const s = size * 1.2;
    selection.append('polygon')
      .attr('points', `0,${-s} ${s},0 0,${s} ${-s},0`)
      .attr('class', 'node-shape');
  } else if (shapeType === 'hexagon') {
    const s = size;
    const points = [];
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i - Math.PI / 2;
      points.push(`${s * Math.cos(angle)},${s * Math.sin(angle)}`);
    }
    selection.append('polygon')
      .attr('points', points.join(' '))
      .attr('class', 'node-shape');
  } else if (shapeType === 'triangle') {
    const s = size * 1.3;
    selection.append('polygon')
      .attr('points', `0,${-s} ${s * 0.87},${s * 0.5} ${-s * 0.87},${s * 0.5}`)
      .attr('class', 'node-shape');
  }
}

export default function CoverageGraph({ scanId, scanning, onNodeSelect, onGraphStats }) {
  const svgRef = useRef(null);
  const simRef = useRef(null);
  const tooltipRef = useRef(null);
  const [graphData, setGraphData] = useState(null);

  useEffect(() => {
    if (!scanId) return;
    let active = true;
    const fetchGraph = async () => {
      try {
        const res = await fetch(`/graph?scan_id=${scanId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (active) {
          setGraphData(data);
          // Propagate stats up to parent (fixes MetricCards)
          if (data.stats && onGraphStats) {
            onGraphStats(data.stats);
          }
        }
      } catch { /* ignore */ }
    };
    fetchGraph();
    const interval = scanning ? setInterval(fetchGraph, 3000) : null;
    return () => { active = false; if (interval) clearInterval(interval); };
  }, [scanId, scanning, onGraphStats]);

  useEffect(() => {
    if (!graphData || !svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth || 700;
    const height = svgRef.current.clientHeight || 500;
    svg.selectAll('*').remove();

    const g = svg.append('g');

    // Create tooltip div if not exists
    let tooltip = d3.select(tooltipRef.current);

    // Zoom
    svg.call(d3.zoom().scaleExtent([0.3, 4]).on('zoom', (e) => {
      g.attr('transform', e.transform);
    }));

    const nodes = (graphData.nodes || []).map(n => ({ ...n }));
    const edges = (graphData.edges || []).map(e => ({
      source: e.source,
      target: e.target,
      type: e.type,
    }));

    // Ensure links reference valid node ids
    const nodeIds = new Set(nodes.map(n => n.id));
    const validEdges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));

    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(validEdges).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-350))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    simRef.current = sim;

    // Edge type styling
    const edgeColors = {
      navigation: '#4B5EAA',
      contains: '#334155',
    };

    // Arrowhead markers
    const defs = svg.append('defs');
    ['navigation', 'contains'].forEach(type => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', edgeColors[type] || '#334155');
    });

    // Edges with arrows
    const link = g.append('g').attr('class', 'links')
      .selectAll('line')
      .data(validEdges)
      .join('line')
      .attr('stroke', d => edgeColors[d.type] || '#334155')
      .attr('stroke-width', d => d.type === 'navigation' ? 2 : 1.2)
      .attr('stroke-opacity', d => d.type === 'navigation' ? 0.7 : 0.4)
      .attr('stroke-dasharray', d => d.type === 'contains' ? '4,3' : 'none')
      .attr('marker-end', d => `url(#arrow-${d.type})`);

    // Nodes
    const node = g.append('g').attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      )
      .on('click', (e, d) => onNodeSelect?.(d))
      .on('mouseenter', (e, d) => {
        tooltip
          .style('opacity', 1)
          .style('left', `${e.offsetX + 14}px`)
          .style('top', `${e.offsetY - 10}px`)
          .html(buildTooltipHtml(d));
      })
      .on('mousemove', (e) => {
        tooltip
          .style('left', `${e.offsetX + 14}px`)
          .style('top', `${e.offsetY - 10}px`);
      })
      .on('mouseleave', () => {
        tooltip.style('opacity', 0);
      });

    // Glow filter for uncovered high-risk nodes
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Draw type-specific shapes
    node.each(function (d) {
      const sel = d3.select(this);
      const nodeSize = 10 + (d.risk_score || 0) * 14;
      const fillColor = d.covered ? COVERED_COLOR : (RISK_COLORS[d.risk_band] || COVERED_COLOR);
      const nodeType = d.type || 'page';

      drawNodeShape(sel, nodeType, nodeSize);

      sel.select('.node-shape')
        .attr('fill', fillColor)
        .attr('stroke', d.covered ? '#374151' : '#0f172a')
        .attr('stroke-width', 2)
        .attr('opacity', d.covered ? 0.7 : 1);

      // Add glow to uncovered critical/high nodes
      if (!d.covered && (d.risk_band === 'critical' || d.risk_band === 'high')) {
        sel.select('.node-shape').attr('filter', 'url(#glow)');
      }

      // Coverage status ring
      if (!d.covered) {
        sel.append('circle')
          .attr('r', nodeSize + 4)
          .attr('fill', 'none')
          .attr('stroke', RISK_COLORS[d.risk_band] || '#EAB308')
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '3,3')
          .attr('opacity', 0.6);
      }
    });

    // Memory indicator badge
    node.filter(d => d.has_memory)
      .append('circle')
      .attr('r', 5)
      .attr('cx', d => 10 + (d.risk_score || 0) * 14 - 2)
      .attr('cy', d => -(10 + (d.risk_score || 0) * 14 - 2))
      .attr('fill', '#8B5CF6')
      .attr('stroke', '#0f172a')
      .attr('stroke-width', 1.5);

    // Type icon (small emoji above node)
    node.append('text')
      .text(d => NODE_ICONS[d.type] || '📌')
      .attr('x', 0)
      .attr('y', d => -(12 + (d.risk_score || 0) * 14 + 4))
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('pointer-events', 'none');

    // Labels — show full label, truncated to 20 chars max for readability
    node.append('text')
      .text(d => {
        const label = d.label || d.id;
        return label.length > 22 ? label.substring(0, 20) + '…' : label;
      })
      .attr('x', 0)
      .attr('y', d => (12 + (d.risk_score || 0) * 14) + 16)
      .attr('text-anchor', 'middle')
      .attr('fill', '#cbd5e1')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('pointer-events', 'none');

    // URL sub-label for page nodes
    node.filter(d => d.type === 'page')
      .append('text')
      .text(d => d.url || '')
      .attr('x', 0)
      .attr('y', d => (12 + (d.risk_score || 0) * 14) + 28)
      .attr('text-anchor', 'middle')
      .attr('fill', '#64748b')
      .attr('font-size', '9px')
      .attr('font-family', 'monospace')
      .attr('pointer-events', 'none');

    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => { sim.stop(); };
  }, [graphData, onNodeSelect]);

  return (
    <div className="coverage-graph-panel">
      <h2>🗺️ Coverage Graph</h2>
      {graphData?.stats && (
        <div className="graph-stats-bar">
          <span>🔵 {graphData.stats.total_nodes} nodes</span>
          <span className="stat-covered">✅ {graphData.stats.covered} covered</span>
          <span className="stat-gaps">🔴 {graphData.stats.gaps} gaps</span>
          <span>📊 {graphData.stats.coverage_percent?.toFixed(1)}% coverage</span>
        </div>
      )}
      {/* Legend */}
      <div className="graph-legend">
        <span className="legend-item"><span className="legend-shape legend-circle" />Page</span>
        <span className="legend-item"><span className="legend-shape legend-rect" />Form</span>
        <span className="legend-item"><span className="legend-shape legend-diamond" />Button</span>
        <span className="legend-item"><span className="legend-shape legend-hex" />API</span>
        <span className="legend-item"><span className="legend-dash" />Gap</span>
        <span className="legend-item"><span className="legend-solid" />Covered</span>
      </div>
      <div className="graph-container" style={{ position: 'relative' }}>
        <svg ref={svgRef} className="graph-svg" />
        <div ref={tooltipRef} className="graph-tooltip" />
      </div>
    </div>
  );
}

function buildTooltipHtml(d) {
  const coverageClass = d.covered ? 'tooltip-covered' : 'tooltip-gap';
  const coverageText = d.covered ? '✅ Covered' : '🔴 Gap';
  return `
    <div class="tooltip-title">${d.label || d.id}</div>
    <div class="tooltip-row"><span class="tooltip-key">Type:</span> ${NODE_ICONS[d.type] || '📌'} ${d.type || 'unknown'}</div>
    <div class="tooltip-row"><span class="tooltip-key">URL:</span> <code>${d.url || '—'}</code></div>
    <div class="tooltip-row"><span class="tooltip-key">Risk:</span> <span style="color:${RISK_COLORS[d.risk_band] || '#6B7280'}">${d.risk_score?.toFixed(3)} (${d.risk_band || '—'})</span></div>
    <div class="tooltip-row ${coverageClass}">${coverageText}</div>
    ${d.gap_reason ? `<div class="tooltip-row"><span class="tooltip-key">Gap reason:</span> ${d.gap_reason}</div>` : ''}
    ${d.has_memory ? '<div class="tooltip-row tooltip-memory">🧠 Has memory from past scans</div>' : ''}
  `;
}
