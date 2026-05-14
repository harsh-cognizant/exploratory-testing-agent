import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const RISK_COLORS = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#22C55E',
};
const COVERED_COLOR = '#6B7280';

export default function CoverageGraph({ scanId, scanning, onNodeSelect }) {
  const svgRef = useRef(null);
  const simRef = useRef(null);
  const [graphData, setGraphData] = useState(null);

  useEffect(() => {
    if (!scanId) return;
    let active = true;
    const fetchGraph = async () => {
      try {
        const res = await fetch(`/graph?scan_id=${scanId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (active) setGraphData(data);
      } catch { /* ignore */ }
    };
    fetchGraph();
    const interval = scanning ? setInterval(fetchGraph, 3000) : null;
    return () => { active = false; if (interval) clearInterval(interval); };
  }, [scanId, scanning]);

  useEffect(() => {
    if (!graphData || !svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth || 700;
    const height = svgRef.current.clientHeight || 500;
    svg.selectAll('*').remove();

    const g = svg.append('g');

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
      .force('link', d3.forceLink(validEdges).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-250))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    simRef.current = sim;

    // Edges
    const link = g.append('g').attr('class', 'links')
      .selectAll('line')
      .data(validEdges)
      .join('line')
      .attr('stroke', '#334155')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.5);

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
      .on('click', (e, d) => onNodeSelect?.(d));

    node.append('circle')
      .attr('r', d => 8 + (d.risk_score || 0) * 12)
      .attr('fill', d => d.covered ? COVERED_COLOR : (RISK_COLORS[d.risk_band] || COVERED_COLOR))
      .attr('stroke', '#0f172a')
      .attr('stroke-width', 2)
      .append('title')
      .text(d => `${d.label}\nRisk: ${d.risk_score?.toFixed(2)} (${d.risk_band})\n${d.covered ? 'Covered' : 'Gap'}`);

    // Memory indicator
    node.filter(d => d.has_memory)
      .append('circle')
      .attr('r', 4)
      .attr('cx', d => 8 + (d.risk_score || 0) * 12 - 2)
      .attr('cy', d => -(8 + (d.risk_score || 0) * 12 - 2))
      .attr('fill', '#8B5CF6')
      .attr('stroke', '#0f172a')
      .attr('stroke-width', 1);

    // Labels
    node.append('text')
      .text(d => d.label?.split(' ')[0] || d.id)
      .attr('x', 0)
      .attr('y', d => (8 + (d.risk_score || 0) * 12) + 16)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px');

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
          <span>{graphData.stats.total_nodes} nodes</span>
          <span className="stat-covered">{graphData.stats.covered} covered</span>
          <span className="stat-gaps">{graphData.stats.gaps} gaps</span>
          <span>{graphData.stats.coverage_percent?.toFixed(1)}% coverage</span>
        </div>
      )}
      <svg ref={svgRef} className="graph-svg" />
    </div>
  );
}
