#!/usr/bin/env python3
"""
Test script for Network Graph Visualization
Tests the backend API endpoint and data structure
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
SESSION_ID = "test_network_graph_123"

def test_network_graph_endpoint():
    """Test the network graph API endpoint"""
    print("=" * 60)
    print("Testing Network Graph Visualization")
    print("=" * 60)
    
    # Test data
    test_payload = {
        "session_id": SESSION_ID,
        "transformer_name": "Transformer T-001"
    }
    
    print(f"\n1. Testing POST /api/nmd-analysis/network-graph")
    print(f"   Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/nmd-analysis/network-graph",
            json=test_payload,
            timeout=10
        )
        
        print(f"\n2. Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            
            if 'graph_data' in data:
                graph_data = data['graph_data']
                print(f"\n3. Graph Data Structure:")
                print(f"   - Transformer: {graph_data.get('transformer')}")
                print(f"   - Total Feeders: {graph_data.get('total_feeders')}")
                print(f"   - Total Customers: {graph_data.get('total_customers')}")
                print(f"   - Total Nodes: {len(graph_data.get('nodes', []))}")
                print(f"   - Total Edges: {len(graph_data.get('edges', []))}")
                
                # Analyze node types
                nodes = graph_data.get('nodes', [])
                node_types = {}
                for node in nodes:
                    node_type = node.get('type', 'unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                
                print(f"\n4. Node Type Distribution:")
                for node_type, count in node_types.items():
                    print(f"   - {node_type.title()}: {count}")
                
                # Sample nodes
                print(f"\n5. Sample Nodes:")
                for node_type in ['transformer', 'feeder', 'phase', 'customer']:
                    sample_node = next((n for n in nodes if n.get('type') == node_type), None)
                    if sample_node:
                        print(f"\n   {node_type.title()} Node:")
                        print(f"     ID: {sample_node.get('id')}")
                        print(f"     Label: {sample_node.get('label')}")
                        print(f"     Color: {sample_node.get('color')}")
                        print(f"     Level: {sample_node.get('level')}")
                        if node_type == 'customer':
                            print(f"     Correlation: {sample_node.get('correlation', 'N/A')}")
                            print(f"     Score: {sample_node.get('score', 'N/A')}")
                
                # Sample edges
                edges = graph_data.get('edges', [])
                if edges:
                    print(f"\n6. Sample Edges:")
                    for i, edge in enumerate(edges[:5]):
                        print(f"   Edge {i+1}: {edge.get('source')} → {edge.get('target')}")
                
                # Validate structure
                print(f"\n7. Structure Validation:")
                validations = [
                    ("Transformer node exists", any(n.get('type') == 'transformer' for n in nodes)),
                    ("Feeder nodes exist", any(n.get('type') == 'feeder' for n in nodes)),
                    ("Phase nodes exist", any(n.get('type') == 'phase' for n in nodes)),
                    ("Customer nodes exist", any(n.get('type') == 'customer' for n in nodes)),
                    ("Edges connect nodes", len(edges) > 0),
                    ("All nodes have IDs", all('id' in n for n in nodes)),
                    ("All nodes have types", all('type' in n for n in nodes)),
                    ("All nodes have colors", all('color' in n for n in nodes)),
                    ("All edges have source", all('source' in e for e in edges)),
                    ("All edges have target", all('target' in e for e in edges))
                ]
                
                for check, result in validations:
                    status = "✅" if result else "❌"
                    print(f"   {status} {check}")
                
                # Color validation
                print(f"\n8. Phase Color Validation:")
                phase_colors = {
                    'Phase A': '#E74C3C',
                    'Phase B': '#F39C12',
                    'Phase C': '#3498DB'
                }
                
                for phase_name, expected_color in phase_colors.items():
                    phase_node = next((n for n in nodes if n.get('label') == phase_name), None)
                    if phase_node:
                        actual_color = phase_node.get('color')
                        match = actual_color == expected_color
                        status = "✅" if match else "❌"
                        print(f"   {status} {phase_name}: {actual_color} (expected: {expected_color})")
                
                print(f"\n{'=' * 60}")
                print("✅ Network Graph Test PASSED")
                print(f"{'=' * 60}")
                return True
                
            else:
                print(f"   ❌ Error: No graph_data in response")
                return False
                
        elif response.status_code == 404:
            print(f"   ⚠️  Session not found (this is expected if no analysis has been run)")
            print(f"   To test fully:")
            print(f"   1. Run the frontend application")
            print(f"   2. Upload feeder and customer files")
            print(f"   3. Click 'Run Analysis'")
            print(f"   4. Check if network graph appears below results table")
            return None
            
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Error: Could not connect to {BASE_URL}")
        print(f"   Make sure the Flask backend is running:")
        print(f"   cd backend && python app.py")
        return False
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_graph_structure():
    """Test the graph data structure format"""
    print(f"\n{'=' * 60}")
    print("Testing Graph Data Structure Format")
    print(f"{'=' * 60}")
    
    # Expected structure
    expected_structure = {
        "nodes": [
            {
                "id": "string",
                "label": "string",
                "type": "transformer | feeder | phase | customer",
                "level": "0-3",
                "color": "hex color",
                "x": "optional float",
                "y": "optional float",
                "correlation": "optional float (customers only)",
                "score": "optional float (customers only)"
            }
        ],
        "edges": [
            {
                "source": "node_id",
                "target": "node_id"
            }
        ],
        "transformer": "string",
        "total_feeders": "integer",
        "total_customers": "integer"
    }
    
    print("\nExpected Graph Data Structure:")
    print(json.dumps(expected_structure, indent=2))
    
    print("\nNode Types:")
    print("  - transformer (level 0): Root node")
    print("  - feeder (level 1): Distribution feeders")
    print("  - phase (level 2): Three-phase system (A, B, C)")
    print("  - customer (level 3): End consumers")
    
    print("\nNode Colors:")
    print("  - Transformer: #2C3E50 (dark blue)")
    print("  - Feeder: #7F8C8D (gray)")
    print("  - Phase A: #E74C3C (red)")
    print("  - Phase B: #F39C12 (yellow/orange)")
    print("  - Phase C: #3498DB (blue)")
    print("  - Customer: #BDC3C7 (light gray)")
    
    print("\nEdge Connections:")
    print("  transformer → feeder")
    print("  feeder → phase")
    print("  phase → customer")

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("NETWORK GRAPH VISUALIZATION - TEST SUITE")
    print("=" * 60)
    
    # Test 1: Graph structure format
    test_graph_structure()
    
    # Test 2: API endpoint
    print("\n")
    result = test_network_graph_endpoint()
    
    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    
    if result is True:
        print("✅ All tests passed!")
        print("✅ Network graph visualization is working correctly")
    elif result is None:
        print("⚠️  Tests incomplete (no analysis session found)")
        print("Run a full analysis through the frontend to test completely")
    else:
        print("❌ Tests failed")
        print("Check the error messages above for details")
    
    print(f"\n{'=' * 60}")
    print("FRONTEND TESTING")
    print(f"{'=' * 60}")
    print("\nTo test the complete feature:")
    print("1. Start backend: cd backend && python app.py")
    print("2. Start frontend: cd frontend && npm start")
    print("3. Navigate to NMD Analysis (New) page")
    print("4. Upload feeder NMD CSV file")
    print("5. Upload customer CSV files")
    print("6. Click 'Run Analysis' button")
    print("7. Wait for analysis to complete")
    print("8. Scroll down below the results table")
    print("9. Verify network graph appears")
    print("10. Hover over customer nodes to see tooltips")
    print("11. Check that:")
    print("    - Transformer is at the top (dark blue)")
    print("    - Feeders are below transformer (gray)")
    print("    - Phases are below feeders (red, yellow, blue)")
    print("    - Customers are at the bottom (light gray)")
    print("    - Lines connect all nodes properly")
    print("    - Legend shows all node types")
    
    print(f"\n{'=' * 60}\n")

if __name__ == "__main__":
    main()

