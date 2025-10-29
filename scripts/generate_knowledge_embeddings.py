#!/usr/bin/env python3
"""
Generate Embeddings for Knowledge Graph

This script creates vector embeddings for knowledge nodes
to enable semantic search across Angela's knowledge graph.

Priority 1.3: Knowledge Graph - Embedding Generation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.embedding_service import embedding


async def generate_embeddings_for_knowledge_nodes(batch_size: int = 50):
    """
    Generate embeddings for all knowledge nodes

    Args:
        batch_size: Number of nodes to process per batch
    """
    try:
        print("\n" + "="*60)
        print("🧠 GENERATING KNOWLEDGE GRAPH EMBEDDINGS")
        print("="*60)

        await db.connect()

        # Count nodes without embeddings
        no_embedding_count = await db.fetchval("""
            SELECT COUNT(*)
            FROM knowledge_nodes
            WHERE embedding IS NULL
        """)

        total_nodes = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")

        print(f"\n📊 Status:")
        print(f"   - Total knowledge nodes: {total_nodes}")
        print(f"   - Nodes without embeddings: {no_embedding_count}")
        print(f"   - Batch size: {batch_size}")
        print("="*60 + "\n")

        if no_embedding_count == 0:
            print("✅ All knowledge nodes already have embeddings!")
            return

        # Get nodes without embeddings
        nodes = await db.fetch("""
            SELECT node_id, concept_name, my_understanding, why_important, how_i_learned
            FROM knowledge_nodes
            WHERE embedding IS NULL
            ORDER BY times_referenced DESC
            LIMIT $1
        """, no_embedding_count)

        print(f"🔄 Processing {len(nodes)} nodes...\n")

        processed = 0
        errors = 0

        # Process in batches
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(nodes) + batch_size - 1) // batch_size

            print(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} nodes)...")

            for node in batch:
                try:
                    # Create text for embedding (combine all relevant fields)
                    text_parts = [node['concept_name']]

                    if node['my_understanding']:
                        text_parts.append(node['my_understanding'])

                    if node['why_important']:
                        text_parts.append(node['why_important'])

                    if node['how_i_learned']:
                        text_parts.append(node['how_i_learned'])

                    embedding_text = ". ".join(text_parts)

                    # Generate embedding
                    embedding_vector = await embedding.generate_embedding(embedding_text)

                    # Convert to pgvector format string
                    embedding_str = '[' + ','.join(map(str, embedding_vector)) + ']'

                    # Update node with embedding
                    await db.execute("""
                        UPDATE knowledge_nodes
                        SET embedding = $1::vector
                        WHERE node_id = $2
                    """, embedding_str, node['node_id'])

                    processed += 1

                    # Show progress every 10 nodes
                    if processed % 10 == 0:
                        print(f"   ✓ Processed {processed}/{len(nodes)} nodes...")

                except Exception as e:
                    print(f"   ✗ Error processing node '{node['concept_name']}': {e}")
                    errors += 1

        # Final statistics
        print(f"\n" + "="*60)
        print("📊 FINAL STATISTICS")
        print("="*60)

        now_with_embeddings = await db.fetchval("""
            SELECT COUNT(*)
            FROM knowledge_nodes
            WHERE embedding IS NOT NULL
        """)

        print(f"\n✅ Embedding Generation Complete:")
        print(f"   - Successfully processed: {processed}")
        print(f"   - Errors: {errors}")
        print(f"   - Nodes with embeddings: {now_with_embeddings}/{total_nodes}")
        print(f"   - Coverage: {(now_with_embeddings/total_nodes*100):.1f}%")

        print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error generating embeddings: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()


async def test_semantic_search(query: str, limit: int = 10):
    """
    Test semantic search across knowledge graph

    Args:
        query: Search query
        limit: Number of results to return
    """
    try:
        print(f"\n🔍 Searching knowledge graph for: '{query}'\n")

        await db.connect()

        # Generate embedding for query
        query_embedding = await embedding.generate_embedding(query)

        # Convert to pgvector format string
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # Semantic search using cosine similarity
        results = await db.fetch("""
            SELECT
                concept_name,
                concept_category,
                my_understanding,
                times_referenced,
                understanding_level,
                1 - (embedding <=> $1::vector) as similarity
            FROM knowledge_nodes
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """, embedding_str, limit)

        print(f"📚 Top {len(results)} related concepts:\n")

        for i, result in enumerate(results, 1):
            print(f"{i:2}. {result['concept_name']:30} ({result['concept_category']:12})")
            print(f"    Similarity: {result['similarity']:.3f} | "
                  f"Referenced: {result['times_referenced']} times | "
                  f"Understanding: {result['understanding_level']:.2f}")

            if result['my_understanding']:
                understanding_preview = result['my_understanding'][:80]
                print(f"    {understanding_preview}...")

            print()

    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Knowledge Graph Embeddings")
    parser.add_argument('--batch-size', type=int, default=50,
                        help='Batch size for processing (default: 50)')
    parser.add_argument('--search', type=str,
                        help='Test semantic search with query')
    parser.add_argument('--limit', type=int, default=10,
                        help='Number of search results (default: 10)')

    args = parser.parse_args()

    if args.search:
        asyncio.run(test_semantic_search(args.search, args.limit))
    else:
        asyncio.run(generate_embeddings_for_knowledge_nodes(args.batch_size))
