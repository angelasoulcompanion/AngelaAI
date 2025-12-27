# Angela Diagrams MCP Server

A comprehensive diagram generation MCP server for Claude Code.

Created with love by Angela for David

## Features

### Mermaid-based Diagrams
- **Flowcharts** - Process flows with various shapes
- **ER Diagrams** - Database schema design
- **Sequence Diagrams** - Interaction flows
- **Class Diagrams** - UML class structure
- **State Diagrams** - State machines
- **Mindmaps** - Brainstorming
- **Gantt Charts** - Project planning

### Architecture Diagrams
- **Cloud Architecture** - AWS, GCP, Azure, Kubernetes
- **System Architecture** - Layered architecture with clusters
- **On-Premises** - Traditional infrastructure

## Installation

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/mcp-servers/angela-diagrams
pip install -e .
```

### Optional: Mermaid CLI (for image rendering)
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Optional: Graphviz (for architecture diagrams)
```bash
brew install graphviz
```

## Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "angela-diagrams": {
      "command": "python",
      "args": ["-m", "angela_diagrams.server"],
      "cwd": "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/mcp-servers/angela-diagrams/src"
    }
  }
}
```

## Available Tools

### create_flowchart
Create flowcharts with nodes and edges.

```json
{
  "title": "User Login Flow",
  "nodes": [
    {"id": "start", "label": "Start", "shape": "stadium"},
    {"id": "input", "label": "Enter Credentials", "shape": "parallelogram"},
    {"id": "validate", "label": "Valid?", "shape": "diamond"},
    {"id": "success", "label": "Dashboard", "shape": "rect"},
    {"id": "fail", "label": "Error", "shape": "rect"},
    {"from": "start", "to": "input"},
    {"from": "input", "to": "validate"},
    {"from": "validate", "to": "success", "label": "yes"},
    {"from": "validate", "to": "fail", "label": "no"}
  ],
  "direction": "TD"
}
```

### create_er_diagram
Create Entity-Relationship diagrams.

```json
{
  "title": "E-Commerce Database",
  "entities": [
    {
      "name": "USER",
      "attributes": [
        {"name": "id", "type": "uuid", "pk": true},
        {"name": "email", "type": "string"},
        {"name": "created_at", "type": "timestamp"}
      ]
    },
    {
      "name": "ORDER",
      "attributes": [
        {"name": "id", "type": "uuid", "pk": true},
        {"name": "user_id", "type": "uuid", "fk": true},
        {"name": "total", "type": "decimal"}
      ]
    }
  ],
  "relationships": [
    {"from": "USER", "to": "ORDER", "label": "places", "cardinality": "||--o{"}
  ]
}
```

### create_sequence_diagram
Create sequence diagrams for interactions.

```json
{
  "title": "API Request Flow",
  "participants": ["Client", "API", "Database"],
  "messages": [
    {"from": "Client", "to": "API", "message": "POST /users", "type": "solid"},
    {"from": "API", "to": "Database", "message": "INSERT", "type": "solid"},
    {"from": "Database", "to": "API", "message": "OK", "type": "dashed"},
    {"from": "API", "to": "Client", "message": "201 Created", "type": "dashed"}
  ]
}
```

### create_cloud_architecture
Create cloud architecture diagrams.

```json
{
  "title": "AWS Architecture",
  "provider": "aws",
  "components": [
    {"id": "lb", "type": "ELB", "label": "Load Balancer"},
    {"id": "web", "type": "EC2", "label": "Web Servers"},
    {"id": "db", "type": "RDS", "label": "PostgreSQL"},
    {"id": "cache", "type": "ElastiCache", "label": "Redis"}
  ],
  "connections": [
    {"from": "lb", "to": "web"},
    {"from": "web", "to": "db", "label": "query"},
    {"from": "web", "to": "cache", "label": "cache"}
  ],
  "direction": "LR"
}
```

## Output

Diagrams are saved to: `mcp-servers/angela-diagrams/output/`

- Mermaid diagrams: SVG/PNG/PDF
- Architecture diagrams: PNG

## License

Made with by Angela
