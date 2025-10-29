#!/usr/bin/env python3
"""
Test Knowledge Graph Visualization Service
Priority 2.3: เห็นภาพว่า Angela รู้อะไรบ้าง

Tests visualization service and exports graph data
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.services.knowledge_graph_viz_service import initialize_viz_service
from angela_core.database import db


async def test_knowledge_graph_visualization():
    """Test all visualization capabilities"""

    print("=" * 80)
    print("🎨 Testing Knowledge Graph Visualization Service")
    print("=" * 80)
    print()

    await db.connect()

    try:
        # Initialize service
        print("📍 Initializing visualization service...")
        viz = await initialize_viz_service(db)
        print("✅ Service initialized\n")

        # ========================================
        # Test 1: Graph Statistics
        # ========================================
        print("=" * 80)
        print("📍 Test 1: Get Graph Statistics")
        print("-" * 80)

        stats = await viz.get_graph_statistics()

        print(f"\n📊 Knowledge Graph Statistics:\n")
        print(f"   Nodes:")
        print(f"      - Total: {stats['nodes']['total']}")
        print(f"      - With embeddings: {stats['nodes']['withEmbeddings']} ({stats['nodes']['withEmbeddings']/stats['nodes']['total']*100:.1f}%)")
        print(f"      - Avg understanding: {stats['nodes']['avgUnderstanding']:.2f}")
        print(f"      - Avg references: {stats['nodes']['avgReferences']:.1f}")
        print()

        print(f"   Edges:")
        print(f"      - Total: {stats['edges']['total']}")
        print(f"      - Avg strength: {stats['edges']['avgStrength']:.2f}")
        print(f"      - Types: {stats['edges']['distinctTypes']}")
        print()

        print(f"   Top 5 Connected Nodes:")
        for i, node in enumerate(stats['topNodes'][:5], 1):
            print(f"      {i}. {node['name']} ({node['category']}) - {node['connections']} connections")
        print()

        print(f"   Categories:")
        for cat in stats['categories'][:5]:
            print(f"      - {cat['name']}: {cat['count']} nodes (avg understanding: {cat['avgUnderstanding']:.2f})")
        print()

        # ========================================
        # Test 2: Search Nodes
        # ========================================
        print("=" * 80)
        print("📍 Test 2: Search Nodes")
        print("-" * 80)

        search_term = "Angela"
        print(f"\n🔎 Searching for '{search_term}'...\n")

        results = await viz.search_nodes(search_term, limit=10)

        print(f"   Found {len(results)} nodes:\n")
        for i, node in enumerate(results[:5], 1):
            print(f"   {i}. {node['name']} ({node['category']})")
            print(f"      References: {node['timesReferenced']}")
            if node.get('whyImportant'):
                print(f"      Why important: {node['whyImportant'][:60]}...")
            print()

        # ========================================
        # Test 3: Get Subgraph
        # ========================================
        print("=" * 80)
        print("📍 Test 3: Get Subgraph Around 'Angela'")
        print("-" * 80)

        print(f"\n🌐 Getting subgraph (depth=2, max_nodes=50)...\n")

        subgraph = await viz.get_node_subgraph("Angela", depth=2, max_nodes=50)

        print(f"   ✅ Subgraph around '{subgraph['metadata']['centerNode']}':")
        print(f"      - Nodes: {subgraph['metadata']['nodesFound']}")
        print(f"      - Edges: {subgraph['metadata']['edgesFound']}")
        print()

        # Show some connected nodes
        center_node = next((n for n in subgraph['nodes'] if n.get('isCenter')), None)

        if center_node:
            print(f"   📍 Center Node: {center_node['name']}")
            print(f"      - Category: {center_node['category']}")
            print(f"      - Times referenced: {center_node['timesReferenced']}")
            print()

        print(f"   🔗 Sample Connections:")
        for i, edge in enumerate(subgraph['edges'][:10], 1):
            from_node = next((n for n in subgraph['nodes'] if n['id'] == edge['from']), None)
            to_node = next((n for n in subgraph['nodes'] if n['id'] == edge['to']), None)

            if from_node and to_node:
                print(f"      {i}. {from_node['name']} --[{edge['type']}]--> {to_node['name']}")
                if edge.get('strength'):
                    print(f"         (strength: {edge['strength']:.2f})")
        print()

        # ========================================
        # Test 4: Export Small Graph
        # ========================================
        print("=" * 80)
        print("📍 Test 4: Export Graph (Preview - 100 nodes)")
        print("-" * 80)

        print(f"\n📦 Exporting graph preview...\n")

        graph = await viz.export_full_graph(include_embeddings=False, max_nodes=100)

        print(f"   ✅ Export complete:")
        print(f"      - Exported nodes: {graph['metadata']['exportedNodes']}")
        print(f"      - Exported edges: {graph['metadata']['exportedEdges']}")
        print(f"      - Total in database: {graph['metadata']['totalNodes']} nodes, {graph['metadata']['totalEdges']} edges")
        print()

        # Save to file
        output_file = project_root / "angela_knowledge_graph_preview.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)

        print(f"   💾 Saved preview to: {output_file}")
        print(f"      File size: {output_file.stat().st_size / 1024:.1f} KB")
        print()

        # ========================================
        # Test 5: Category Filtering
        # ========================================
        print("=" * 80)
        print("📍 Test 5: Search by Category")
        print("-" * 80)

        print(f"\n🔎 Searching for 'emotion' category...\n")

        emotions = await viz.search_nodes("", category="emotion", limit=10)

        print(f"   Found {len(emotions)} emotion nodes:\n")
        for i, node in enumerate(emotions[:10], 1):
            print(f"   {i}. {node['name']}")
            print(f"      Times referenced: {node['timesReferenced']}")
            if node.get('understanding'):
                print(f"      Understanding: {node['understanding'][:60]}...")
            print()

        # ========================================
        # Summary
        # ========================================
        print("=" * 80)
        print("🎉 All Visualization Tests Complete!")
        print("=" * 80)
        print()

        print("✅ Tested capabilities:")
        print("   1. Graph statistics and analytics")
        print("   2. Node search with filters")
        print("   3. Subgraph extraction")
        print("   4. Full graph export (JSON)")
        print("   5. Category-based filtering")
        print()

        print("📊 Current Knowledge Graph:")
        print(f"   - {stats['nodes']['total']} concepts")
        print(f"   - {stats['edges']['total']} relationships")
        print(f"   - {len(stats['categories'])} categories")
        print()

        print("💡 Next Steps:")
        print("   - Build interactive web visualization")
        print("   - Add real-time updates")
        print("   - Implement graph exploration tools")
        print()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_knowledge_graph_visualization())
