import React, { useEffect, useRef } from 'react';

const NetworkGraph = ({ graphData, width = 1200, height = 800 }) => {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      return;
    }

    const svg = svgRef.current;
    svg.innerHTML = ''; // Clear previous content

    const { nodes, edges } = graphData;

    // Calculate layout positions - transformer, feeders, and customers
    const levelHeight = height / 4;
    const levelYPositions = {
      0: levelHeight * 0.5,    // Transformer
      1: levelHeight * 1.5,    // Feeders
      2: levelHeight * 2.5     // Customers
    };

    // Create position map for nodes
    const nodePositions = {};
    
    // Position transformer at center
    const transformerNode = nodes.find(n => n.type === 'transformer');
    if (transformerNode) {
      nodePositions[transformerNode.id] = { x: width / 2, y: levelYPositions[0] };
    }

    // Position feeders evenly
    const feederNodes = nodes.filter(n => n.type === 'feeder');
    const feederSpacing = width / (feederNodes.length + 1);
    feederNodes.forEach((node, index) => {
      nodePositions[node.id] = {
        x: feederSpacing * (index + 1),
        y: levelYPositions[1]
      };
    });

    // Position customers under their feeders
    const customerNodes = nodes.filter(n => n.type === 'customer');
    const customersByFeeder = {};
    
    customerNodes.forEach(node => {
      const parentEdge = edges.find(e => e.target === node.id && e.source.startsWith('feeder_'));
      if (parentEdge) {
        if (!customersByFeeder[parentEdge.source]) {
          customersByFeeder[parentEdge.source] = [];
        }
        customersByFeeder[parentEdge.source].push(node);
      }
    });

    Object.entries(customersByFeeder).forEach(([feederId, customers]) => {
      if (nodePositions[feederId]) {
        const parentX = nodePositions[feederId].x;
        const customerSpacing = 80;
        const totalWidth = customerSpacing * (customers.length - 1);
        const startX = parentX - (totalWidth / 2);
        
        customers.forEach((node, index) => {
          nodePositions[node.id] = {
            x: startX + (customerSpacing * index),
            y: levelYPositions[2]
          };
        });
      }
    });

    // Create SVG elements
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    svg.appendChild(g);

    // Draw edges first (so they appear behind nodes)
    edges.forEach(edge => {
      const sourcePos = nodePositions[edge.source];
      const targetPos = nodePositions[edge.target];
      
      if (sourcePos && targetPos) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sourcePos.x);
        line.setAttribute('y1', sourcePos.y);
        line.setAttribute('x2', targetPos.x);
        line.setAttribute('y2', targetPos.y);
        line.setAttribute('stroke', '#7F8C8D');
        line.setAttribute('stroke-width', '1.5');
        line.setAttribute('opacity', '0.6');
        g.appendChild(line);
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      const pos = nodePositions[node.id];
      if (!pos) return;

      // Node circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', pos.x);
      circle.setAttribute('cy', pos.y);
      
      // Size based on type
      const radius = node.type === 'transformer' ? 30 : 
                     node.type === 'feeder' ? 25 : 
                     node.type === 'phase' ? 20 : 15;
      circle.setAttribute('r', radius);
      circle.setAttribute('fill', node.color || '#95A5A6');
      circle.setAttribute('stroke', '#2C3E50');
      circle.setAttribute('stroke-width', '2');
      circle.style.cursor = 'pointer';
      
      // Tooltip
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      let tooltipText = node.label;
      if (node.type === 'customer' && node.correlation) {
        tooltipText += `\nCorrelation: ${node.correlation.toFixed(3)}\nScore: ${node.score.toFixed(3)}`;
      }
      title.textContent = tooltipText;
      circle.appendChild(title);
      
      g.appendChild(circle);

      // Node label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', pos.x);
      text.setAttribute('y', pos.y + radius + 15);
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('font-size', node.type === 'transformer' ? '14' : 
                                     node.type === 'feeder' ? '12' : '10');
      text.setAttribute('font-weight', node.type === 'transformer' || node.type === 'feeder' ? 'bold' : 'normal');
      text.setAttribute('fill', '#2C3E50');
      text.textContent = node.label;
      g.appendChild(text);
    });

  }, [graphData, width, height]);

  if (!graphData || !graphData.nodes) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#7F8C8D' }}>
        <p>No network graph data available</p>
      </div>
    );
  }

  return (
    <div style={{ 
      width: '100%', 
      overflowX: 'auto', 
      backgroundColor: '#ECF0F1', 
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px'
    }}>
      <h3 style={{ marginBottom: '15px', color: '#2C3E50' }}>
        Network Hierarchy: {graphData.transformer}
      </h3>
      <div style={{ 
        display: 'flex', 
        gap: '15px', 
        marginBottom: '15px',
        fontSize: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '15px', height: '15px', borderRadius: '50%', backgroundColor: '#2C3E50' }}></div>
          <span>Transformer</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '15px', height: '15px', borderRadius: '50%', backgroundColor: '#7F8C8D' }}></div>
          <span>Feeder</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '15px', height: '15px', borderRadius: '50%', backgroundColor: '#BDC3C7' }}></div>
          <span>Customer</span>
        </div>
      </div>
      <svg 
        ref={svgRef}
        width={width}
        height={height}
        style={{ border: '1px solid #BDC3C7', backgroundColor: 'white', borderRadius: '4px' }}
      />
      <div style={{ marginTop: '10px', fontSize: '12px', color: '#7F8C8D' }}>
        Total Feeders: {graphData.total_feeders} | Total Customers: {graphData.total_customers}
      </div>
    </div>
  );
};

export default NetworkGraph;

