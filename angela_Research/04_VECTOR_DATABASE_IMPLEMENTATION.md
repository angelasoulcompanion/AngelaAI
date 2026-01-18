# 4. VECTOR DATABASE IMPLEMENTATION GUIDE

## Overview
Comprehensive guide to selecting and implementing vector databases for your consciousness architecture, comparing Pinecone, Weaviate, and Chroma.

---

## DECISION MATRIX

| Factor | Pinecone | Weaviate | Chroma |
|--------|----------|----------|--------|
| **Setup** | Fully managed | Open source | Lightweight |
| **Latency** | <50ms | ~100ms | ~200ms |
| **Scale** | 100M+ vectors | 100M+ vectors | 1M-10M vectors |
| **Cost** | $0.40/month (free tier) | Deployment costs | Free |
| **Deployment** | Cloud only | On-prem + Cloud | Local/Docker |
| **Hybrid Search** | Yes (partial) | Yes (full) | Limited |
| **Onboarding** | Easiest | Moderate | Easiest for prototyping |
| **Production Ready** | ✅ Enterprise | ✅ Enterprise | ⚠️ Good for MVP |
| **Best For** | Speed-to-market | Full control | Rapid prototyping |

---

## ARCHITECTURE RECOMMENDATION FOR CONSCIOUSNESS

For your project, I recommend: **Hybrid approach**

```
┌─────────────────────────────────────────────────────┐
│           YOUR AI CONSCIOUSNESS LAYER                │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────┐      ┌──────────────────┐    │
│  │ FOCUS MEMORY    │      │ FRESH MEMORY     │    │
│  │ (Redis, <7)     │      │ (PostgreSQL)     │    │
│  └─────────────────┘      └──────────────────┘    │
│                                                       │
│  ┌────────────────────────────────────────────────┐ │
│  │      WEAVIATE (Hybrid Search Engine)           │ │
│  │                                                 │ │
│  ├─────────────────┬──────────────────────────┬──┤ │
│  │ LONG_TERM       │ PROCEDURAL_MEMORY        │GUT
│  │ (Vector Index)  │ (Vector Index)           │   │
│  └─────────────────┴──────────────────────────┴──┤ │
│                                                     │ │
│  ┌─────────────────────────────────────────────┐ │
│  │ PostgreSQL Metadata & Analytics            │ │
│  │ (Decay tracking, routing decisions)        │ │
│  └─────────────────────────────────────────────┘ │
│                                                       │
│  ┌────────────────────────────────────────────┐   │
│  │  SHOCK MEMORY (Critical event store)       │   │
│  │  PostgreSQL with full audit trail          │   │
│  └────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Why this combination?**
- ✅ Weaviate for flexibility (on-prem or cloud)
- ✅ Hybrid search (semantic + keyword)
- ✅ GraphQL API for complex queries
- ✅ Multi-tenancy support (multiple agents)
- ✅ Hooks into PostgreSQL for rich metadata
- ✅ Can run locally for privacy

---

## IMPLEMENTATION: WEAVIATE

### 1. SETUP & INSTALLATION

```bash
# Using Docker (recommended for development)
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  --name weaviate \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -e ENABLE_MODULES='text2vec-openai' \
  -e OPENAI_APIKEY='your-openai-key' \
  semitechnologies/weaviate:latest

# For production, use Kubernetes or managed Weaviate Cloud
```

### 2. SCHEMA DEFINITION

```python
import weaviate
from weaviate.auth import AuthApiKey
import os

client = weaviate.Client(
    url="http://localhost:8080",
    auth_client_secret=AuthApiKey(api_key="weaviate-key"),  # For cloud
    additional_headers={"X-OpenAI-Api-Key": os.environ["OPENAI_APIKEY"]}
)

# Define Long-Term Memory schema
long_term_schema = {
    "classes": [
        {
            "class": "LongTermMemory",
            "description": "Successful experiences and established knowledge",
            "vectorizer": "text2vec-openai",  # Auto-vectorize on insert
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-3-small",
                    "vectorizePropertyName": False,
                    "properties": ["content", "memoryType"]
                }
            },
            "properties": [
                {
                    "name": "agentId",
                    "dataType": ["uuid"],
                    "description": "Agent that owns this memory"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "The actual memory content",
                    "vectorizePropertyName": True
                },
                {
                    "name": "memoryType",
                    "dataType": ["string"],
                    "description": "Type: experience, fact, pattern, skill"
                },
                {
                    "name": "successScore",
                    "dataType": ["number"],
                    "description": "Success rate (0-1)"
                },
                {
                    "name": "accessCount",
                    "dataType": ["int"],
                    "description": "Times this memory was accessed"
                },
                {
                    "name": "confidence",
                    "dataType": ["number"],
                    "description": "Certainty level (0-1)"
                },
                {
                    "name": "currentPhase",
                    "dataType": ["string"],
                    "description": "Decay phase: episodic, semantic, pattern, intuitive"
                },
                {
                    "name": "lastAccessed",
                    "dataType": ["date"],
                    "description": "When this was last retrieved"
                },
                {
                    "name": "createdAt",
                    "dataType": ["date"],
                    "description": "When this memory formed"
                },
                {
                    "name": "tags",
                    "dataType": ["string[]"],
                    "description": "Semantic tags for filtering"
                }
            ]
        }
    ]
}

# Create schema
client.schema.create(long_term_schema)


# Define Procedural Memory schema
procedural_schema = {
    "classes": [
        {
            "class": "ProceduralMemory",
            "description": "Automated routines and habits",
            "vectorizer": "text2vec-openai",
            "properties": [
                {
                    "name": "agentId",
                    "dataType": ["uuid"]
                },
                {
                    "name": "procedureName",
                    "dataType": ["string"],
                    "vectorizePropertyName": True
                },
                {
                    "name": "procedureSteps",
                    "dataType": ["text"],
                    "vectorizePropertyName": True
                },
                {
                    "name": "executionCount",
                    "dataType": ["int"]
                },
                {
                    "name": "successRate",
                    "dataType": ["number"]
                },
                {
                    "name": "automaticity",
                    "dataType": ["number"],
                    "description": "0-1: how automatic (0=needs thought, 1=automatic)"
                },
                {
                    "name": "lastExecuted",
                    "dataType": ["date"]
                }
            ]
        }
    ]
}

client.schema.create(procedural_schema)


# Define Gut Pattern schema (Collective Unconscious)
gut_schema = {
    "classes": [
        {
            "class": "GutPattern",
            "description": "Collective intuitions and patterns",
            "vectorizer": "text2vec-openai",
            "properties": [
                {
                    "name": "patternDescription",
                    "dataType": ["text"],
                    "vectorizePropertyName": True
                },
                {
                    "name": "frequencyScore",
                    "dataType": ["number"]
                },
                {
                    "name": "successCorrelation",
                    "dataType": ["number"]
                },
                {
                    "name": "instinctStrength",
                    "dataType": ["number"]
                },
                {
                    "name": "sourcesCount",
                    "dataType": ["int"]
                },
                {
                    "name": "agentsContributed",
                    "dataType": ["int"]
                }
            ]
        }
    ]
}

client.schema.create(gut_schema)
```

### 3. INSERTING MEMORIES

```python
def insert_long_term_memory(client, memory_data: dict):
    """Insert a memory into long-term storage."""
    
    data_object = {
        "agentId": memory_data["agent_id"],
        "content": memory_data["content"],
        "memoryType": memory_data["type"],
        "successScore": memory_data["success_score"],
        "accessCount": 1,
        "confidence": memory_data["confidence"],
        "currentPhase": "episodic",
        "lastAccessed": memory_data["timestamp"],
        "createdAt": memory_data["timestamp"],
        "tags": memory_data.get("tags", [])
    }
    
    result = client.data_object.create(
        class_name="LongTermMemory",
        data_object=data_object
    )
    
    return result


def batch_insert_memories(client, memories: list):
    """Insert multiple memories efficiently."""
    
    with client.batch as batch:
        for memory in memories:
            batch.add_data_object(
                data_object=memory,
                class_name="LongTermMemory"
            )
    
    print(f"Inserted {len(memories)} memories")


# Example usage
memory = {
    "agent_id": "agent-001",
    "content": "Successfully deployed microservice with 99.9% uptime",
    "type": "experience",
    "success_score": 0.95,
    "confidence": 0.9,
    "timestamp": "2025-10-29T10:00:00Z",
    "tags": ["deployment", "success", "infrastructure"]
}

insert_long_term_memory(client, memory)
```

### 4. SEMANTIC SEARCH

```python
def semantic_search(client, query: str, top_k: int = 5):
    """
    Search memories by semantic meaning.
    """
    
    response = client.query.get(
        "LongTermMemory",
        ["content", "memoryType", "successScore", "confidence"]
    ).with_near_text(
        {"concepts": [query]}
    ).with_limit(top_k).do()
    
    return response["data"]["Get"]["LongTermMemory"]


# Example
results = semantic_search(
    client,
    "deployment strategies",
    top_k=10
)

for result in results:
    print(f"Content: {result['content']}")
    print(f"Type: {result['memoryType']}")
    print(f"Success: {result['successScore']}\n")
```

### 5. HYBRID SEARCH (Semantic + Keyword)

```python
def hybrid_search(client, query: str, alpha: float = 0.5, top_k: int = 10):
    """
    Combine semantic and keyword search.
    
    alpha: 0.0 = pure keyword BM25, 1.0 = pure semantic, 0.5 = balanced
    """
    
    response = client.query.get(
        "LongTermMemory",
        ["content", "memoryType", "successScore", "confidence", "_score"]
    ).with_hybrid(
        query=query,
        alpha=alpha  # Balance between keyword and semantic
    ).with_limit(top_k).do()
    
    return response["data"]["Get"]["LongTermMemory"]


# Example: Find memories about security that are both semantically similar
# and contain the keyword "security"
results = hybrid_search(client, "security measures", alpha=0.7, top_k=5)
```

### 6. COMPLEX FILTERING WITH GRAPHQL

```python
def filtered_memory_search(client, agent_id: str, min_success: float = 0.7):
    """
    Search with multiple filters.
    """
    
    response = client.query.get(
        "LongTermMemory",
        ["content", "successScore", "accessCount"]
    ).with_where(
        {
            "operator": "And",
            "operands": [
                {
                    "path": ["agentId"],
                    "operator": "Equal",
                    "valueString": agent_id
                },
                {
                    "path": ["successScore"],
                    "operator": "GreaterThan",
                    "valueNumber": min_success
                },
                {
                    "path": ["currentPhase"],
                    "operator": "NotEqual",
                    "valueString": "forgotten"
                }
            ]
        }
    ).with_limit(100).do()
    
    return response["data"]["Get"]["LongTermMemory"]


# Example
successful_memories = filtered_memory_search(
    client,
    agent_id="agent-001",
    min_success=0.8
)
```

### 7. AGGREGATION QUERIES

```python
def get_memory_statistics(client, agent_id: str) -> dict:
    """
    Get aggregate statistics about an agent's memories.
    """
    
    response = client.query.aggregate(
        "LongTermMemory"
    ).with_where(
        {
            "path": ["agentId"],
            "operator": "Equal",
            "valueString": agent_id
        }
    ).with_fields(
        "meta { count }",
        "successScore { mean, maximum, minimum }",
        "accessCount { sum, mean }",
        "confidence { mean }"
    ).do()
    
    return response["data"]["Aggregate"]["LongTermMemory"][0]


# Example
stats = get_memory_statistics(client, "agent-001")
print(f"Total memories: {stats['meta']['count']}")
print(f"Avg success rate: {stats['successScore']['mean']:.2%}")
print(f"Total accesses: {stats['accessCount']['sum']}")
```

---

## IMPLEMENTATION: PINECONE (ALTERNATIVE)

For comparison, here's a Pinecone implementation:

```python
import pinecone
from sentence_transformers import SentenceTransformer

# Initialize
pinecone.init(
    api_key="your-api-key",
    environment="us-west1-gcp"
)

# Create index
index_name = "consciousness-memories"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        name=index_name,
        dimension=384,  # sentence-transformers dimension
        metric="cosine",
        spec=pinecone.ServerlessSpec(
            cloud="aws",
            region="us-west-1"
        )
    )

index = pinecone.Index(index_name)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Insert memory with metadata
def insert_into_pinecone(memory_data: dict):
    embedding = model.encode(memory_data["content"])
    
    index.upsert([(
        memory_data["memory_id"],
        embedding,
        {
            "agent_id": memory_data["agent_id"],
            "content": memory_data["content"],
            "type": memory_data["type"],
            "success_score": memory_data["success_score"],
            "confidence": memory_data["confidence"]
        }
    )])

# Search
def search_pinecone(query: str, top_k: int = 5):
    query_embedding = model.encode(query)
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results
```

### Pinecone vs Weaviate Comparison for Your Project

| Aspect | Pinecone | Weaviate |
|--------|----------|----------|
| **Vectorization** | External (you manage) | Built-in (automatic) |
| **Metadata Filtering** | Good | Excellent (GraphQL) |
| **Hybrid Search** | Limited | Full support |
| **Self-hosting** | ❌ Cloud only | ✅ Docker/K8s |
| **Cost at Scale** | ~$0.40/month baseline | Self-hosted = only compute |
| **Learning Curve** | Very easy | Moderate |
| **Best Use Case** | Production, simplicity | Full control, flexibility |

**Recommendation**: Start with **Weaviate** because:
1. You want hybrid search (keyword + semantic)
2. You need complex GraphQL queries
3. You might want to run on-prem for privacy
4. You want built-in vectorization

---

## MONITORING & MAINTENANCE

### Health Checks

```python
def health_check(client):
    """Verify Weaviate is running."""
    try:
        meta = client.get_meta()
        print(f"Weaviate Status: {meta}")
        return True
    except Exception as e:
        print(f"Weaviate Error: {e}")
        return False


# For Pinecone
def pinecone_health():
    index = pinecone.Index("consciousness-memories")
    stats = index.describe_index_stats()
    print(f"Vectors: {stats.total_vector_count}")
    return stats
```

### Query Performance

```python
def benchmark_search(client, query: str, iterations: int = 100):
    """Measure search latency."""
    import time
    
    times = []
    for _ in range(iterations):
        start = time.time()
        results = semantic_search(client, query, top_k=5)
        times.append(time.time() - start)
    
    avg_latency = sum(times) / len(times)
    p95_latency = sorted(times)[int(len(times) * 0.95)]
    
    print(f"Avg latency: {avg_latency*1000:.1f}ms")
    print(f"P95 latency: {p95_latency*1000:.1f}ms")
    print(f"Target: <50ms for production")
```

---

## NEXT STEPS

1. ✅ Vector DB architecture designed
2. ✅ Schema defined for all memory tiers
3. ✅ Insertion/retrieval code provided
4. ✅ Hybrid search demonstrated
5. ⏭️ Philosophical framework for consciousness (file 05)

For production deployment, ensure:
- ✅ Replication enabled (backup)
- ✅ Monitoring/alerting on query latency
- ✅ Regular index optimization
- ✅ Backup strategy for embeddings

