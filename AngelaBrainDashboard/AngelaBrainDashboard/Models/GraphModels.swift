//
//  GraphModels.swift
//  Angela Brain Dashboard
//
//  Codable models for /api/graph/* endpoints — Knowledge Graph visualization
//

import Foundation

// MARK: - Graph Stats

struct GraphStats: Codable {
    let pg: PGStats
    let neo4j: Neo4jStats

    struct PGStats: Codable {
        let knowledgeNodes: Int
        let relationships: Int
        let contextBindings: Int

        enum CodingKeys: String, CodingKey {
            case knowledgeNodes = "knowledge_nodes"
            case relationships
            case contextBindings = "context_bindings"
        }
    }

    struct Neo4jStats: Codable {
        let available: Bool
        let nodeCounts: [String: Int]?
        let totalRelationships: Int?
        let relationshipCounts: [String: Int]?

        enum CodingKeys: String, CodingKey {
            case available
            case nodeCounts = "node_counts"
            case totalRelationships = "total_relationships"
            case relationshipCounts = "relationship_counts"
        }
    }
}

// MARK: - Full Graph (for D3.js)

struct FullGraph: Codable {
    let nodes: [KGNode]
    let edges: [GraphEdge]
}

struct KGNode: Codable, Identifiable {
    var id: String { nodeId }
    let nodeId: String
    let conceptName: String
    let conceptCategory: String?
    let understandingLevel: Double
    let timesReferenced: Int
    let myUnderstanding: String?

    enum CodingKeys: String, CodingKey {
        case nodeId = "node_id"
        case conceptName = "concept_name"
        case conceptCategory = "concept_category"
        case understandingLevel = "understanding_level"
        case timesReferenced = "times_referenced"
        case myUnderstanding = "my_understanding"
    }
}

struct GraphEdge: Codable, Identifiable {
    var id: String { relationshipId }
    let relationshipId: String
    let fromNodeId: String
    let toNodeId: String
    let relationshipType: String?
    let strength: Double

    enum CodingKeys: String, CodingKey {
        case relationshipId = "relationship_id"
        case fromNodeId = "from_node_id"
        case toNodeId = "to_node_id"
        case relationshipType = "relationship_type"
        case strength
    }
}

// MARK: - Node Detail

struct NodeDetail: Codable {
    let nodeId: String
    let conceptName: String
    let conceptCategory: String?
    let myUnderstanding: String?
    let understandingLevel: Double?
    let timesReferenced: Int?
    let whyImportant: String?
    let createdAt: String?
    let updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case nodeId = "node_id"
        case conceptName = "concept_name"
        case conceptCategory = "concept_category"
        case myUnderstanding = "my_understanding"
        case understandingLevel = "understanding_level"
        case timesReferenced = "times_referenced"
        case whyImportant = "why_important"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// MARK: - Neighbor Node

struct NeighborNode: Codable, Identifiable {
    var id: String { nodeId }
    let nodeId: String
    let conceptName: String
    let conceptCategory: String?
    let understandingLevel: Double?
    let relationshipType: String?
    let strength: Double?
    let hops: Int?

    enum CodingKeys: String, CodingKey {
        case nodeId = "node_id"
        case conceptName = "concept_name"
        case conceptCategory = "concept_category"
        case understandingLevel = "understanding_level"
        case relationshipType = "relationship_type"
        case strength
        case hops
    }
}

// MARK: - Community

struct CommunityResponse: Codable {
    let totalCommunities: Int
    let totalNodes: Int
    let communities: [CommunityInfo]

    enum CodingKeys: String, CodingKey {
        case totalCommunities = "total_communities"
        case totalNodes = "total_nodes"
        case communities
    }
}

struct CommunityInfo: Codable, Identifiable {
    var id: Int { communityId }
    let communityId: Int
    let size: Int
    let topCategories: [String]
    let representativeName: String

    enum CodingKeys: String, CodingKey {
        case communityId = "community_id"
        case size
        case topCategories = "top_categories"
        case representativeName = "representative_name"
    }
}

// MARK: - Graph Search Result

struct GraphSearchResult: Codable {
    let query: String
    let queryType: String
    let entities: [String]
    let results: [GraphSearchItem]
    let graphSummary: String?
    let timeMs: Double?

    enum CodingKeys: String, CodingKey {
        case query
        case queryType = "query_type"
        case entities
        case results
        case graphSummary = "graph_summary"
        case timeMs = "time_ms"
    }
}

struct GraphSearchItem: Codable, Identifiable {
    var id: String { itemId }
    let itemId: String
    let content: String
    let source: String
    let score: Double
    let graphSource: Bool

    enum CodingKeys: String, CodingKey {
        case itemId = "id"
        case content, source, score
        case graphSource = "graph_source"
    }
}

// MARK: - Shortest Path

struct ShortestPath: Codable {
    let nodes: [[String: String]]?
    let edgeTypes: [String]?
    let pathLength: Int

    enum CodingKeys: String, CodingKey {
        case nodes
        case edgeTypes = "edge_types"
        case pathLength = "path_length"
    }
}

// MARK: - Knowledge Gaps

struct KnowledgeGaps: Codable {
    let isolatedNodes: [KGNode]
    let lowUnderstanding: [KGNode]
    let weakEdges: [WeakEdge]

    enum CodingKeys: String, CodingKey {
        case isolatedNodes = "isolated_nodes"
        case lowUnderstanding = "low_understanding"
        case weakEdges = "weak_edges"
    }
}

struct WeakEdge: Codable, Identifiable {
    var id: String { relationshipId }
    let relationshipId: String
    let fromNodeId: String
    let toNodeId: String
    let strength: Double
    let fromName: String
    let toName: String

    enum CodingKeys: String, CodingKey {
        case relationshipId = "relationship_id"
        case fromNodeId = "from_node_id"
        case toNodeId = "to_node_id"
        case strength
        case fromName = "from_name"
        case toName = "to_name"
    }
}
