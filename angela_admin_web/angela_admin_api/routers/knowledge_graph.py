from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# ✅ [Batch-25]: Migrated to Clean Architecture with DI
from angela_core.infrastructure.persistence.repositories import KnowledgeRepository
from angela_core.presentation.api.dependencies import get_knowledge_repo

router = APIRouter()

# =====================================================================
# Response Models
# =====================================================================

class KnowledgeNode(BaseModel):
    id: str
    name: str
    category: str
    understanding: Optional[str] = None
    whyImportant: Optional[str] = None
    understandingLevel: Optional[float] = None
    timesReferenced: int
    createdAt: str

class KnowledgeEdge(BaseModel):
    id: str
    source: str  # Changed from 'from' to 'source' for D3.js compatibility
    target: str  # Changed from 'to' to 'target' for D3.js compatibility
    type: str
    strength: Optional[float] = None
    explanation: Optional[str] = None

class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]
    metadata: Dict[str, Any]

class GraphStats(BaseModel):
    totalNodes: int
    totalEdges: int
    categories: List[str]
    avgUnderstanding: Optional[float] = None
    mostReferenced: Optional[Dict[str, Any]] = None

# =====================================================================
# API Endpoints
# =====================================================================

@router.get("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    max_nodes: Optional[int] = 200,
    repo: KnowledgeRepository = Depends(get_knowledge_repo)
):
    """Get knowledge graph data with nodes and edges (Clean Architecture)"""
    try:
        # ✅ [Batch-25]: Using KnowledgeRepository.get_graph_with_edges()
        graph_data = await repo.get_graph_with_edges(max_nodes=max_nodes)

        # Build nodes list
        nodes = [
            KnowledgeNode(
                id=str(row['node_id']),
                name=row['concept_name'],
                category=row['concept_category'] or 'uncategorized',
                understanding=row['my_understanding'],
                whyImportant=row['why_important'],
                understandingLevel=float(row['understanding_level']) if row['understanding_level'] else None,
                timesReferenced=row['times_referenced'] or 0,
                createdAt=row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
            )
            for row in graph_data['nodes']
        ]

        # Build edges list (use 'source' and 'target' for D3.js compatibility)
        edges = [
            KnowledgeEdge(
                id=str(row['relationship_id']),
                source=str(row['from_node_id']),
                target=str(row['to_node_id']),
                type=row['relationship_type'] or 'related',
                strength=float(row['strength']) if row['strength'] else None,
                explanation=row['my_explanation']
            )
            for row in graph_data['edges']
        ]

        # Metadata
        metadata = {
            "totalNodes": len(nodes),
            "totalEdges": len(edges),
            "exportedNodes": len(nodes),
            "exportedEdges": len(edges),
            "exportedAt": "now"
        }

        return KnowledgeGraphResponse(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch knowledge graph: {str(e)}")

@router.get("/knowledge-graph/stats", response_model=GraphStats)
async def get_graph_statistics(
    repo: KnowledgeRepository = Depends(get_knowledge_repo)
):
    """Get knowledge graph statistics (Clean Architecture)"""
    try:
        # ✅ [Batch-25]: Using KnowledgeRepository.get_graph_statistics()
        stats = await repo.get_graph_statistics()

        return GraphStats(
            totalNodes=stats['total_nodes'],
            totalEdges=stats['total_edges'],
            categories=stats['categories'],
            avgUnderstanding=stats['avg_understanding'],
            mostReferenced=stats['most_referenced']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph stats: {str(e)}")

@router.get("/knowledge-graph/search")
async def search_nodes(
    q: str,
    category: Optional[str] = None,
    repo: KnowledgeRepository = Depends(get_knowledge_repo)
):
    """Search knowledge nodes (Clean Architecture)"""
    try:
        # ✅ [Batch-25]: Using KnowledgeRepository.search_nodes()
        nodes = await repo.search_nodes(
            query_text=q,
            category=category,
            limit=50
        )

        # Convert to response format
        return [
            {
                "id": str(row['node_id']),
                "name": row['concept_name'],
                "category": row['concept_category'],
                "understanding": row['my_understanding'],
                "understandingLevel": float(row['understanding_level']) if row['understanding_level'] else None,
                "timesReferenced": row['times_referenced']
            }
            for row in nodes
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search nodes: {str(e)}")

@router.get("/knowledge-graph/subgraph")
async def get_node_subgraph(
    node_name: str,
    depth: int = 2,
    repo: KnowledgeRepository = Depends(get_knowledge_repo)
):
    """Get subgraph around a specific node (Clean Architecture)"""
    try:
        # ✅ [Batch-25]: Using KnowledgeRepository.get_subgraph()
        subgraph = await repo.get_subgraph(
            node_name=node_name,
            depth=depth
        )

        # Check if node was found
        if not subgraph['center_node']:
            raise HTTPException(status_code=404, detail=f"Node '{node_name}' not found")

        # Build nodes list
        nodes = [
            KnowledgeNode(
                id=str(row['node_id']),
                name=row['concept_name'],
                category=row['concept_category'] or 'uncategorized',
                understanding=row['my_understanding'],
                whyImportant=row.get('why_important'),
                understandingLevel=float(row['understanding_level']) if row['understanding_level'] else None,
                timesReferenced=row['times_referenced'] or 0,
                createdAt=row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
            )
            for row in subgraph['nodes']
        ]

        # Build edges list
        edges = [
            KnowledgeEdge(
                id=str(row['relationship_id']),
                source=str(row['from_node_id']),
                target=str(row['to_node_id']),
                type=row['relationship_type'] or 'related',
                strength=float(row['strength']) if row['strength'] else None,
                explanation=row['my_explanation']
            )
            for row in subgraph['edges']
        ]

        return KnowledgeGraphResponse(
            nodes=nodes,
            edges=edges,
            metadata={
                "totalNodes": len(nodes),
                "totalEdges": len(edges),
                "centerNode": node_name,
                "depth": depth
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subgraph: {str(e)}")
