# Angela Draw.io MCP Server

Create diagrams in draw.io/diagrams.net format directly from Claude Code.

## Features

- **ER Diagrams** - Entity-Relationship diagrams with tables and relationships
- **Flowcharts** - Process flows with various shapes (rectangle, ellipse, diamond, etc.)
- **Architecture Diagrams** - System/cloud architecture with typed components
- **Mindmaps** - Radial mindmap diagrams
- **Custom Diagrams** - Build any diagram with manual shapes and edges

## Installation

```bash
cd mcp-servers/angela-drawio
pip install -e .
```

## Usage

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "angela-drawio": {
      "command": "python3",
      "args": ["-m", "angela_drawio.server"],
      "cwd": "/path/to/mcp-servers/angela-drawio/src"
    }
  }
}
```

## Tools

### create_er_diagram

Create an Entity-Relationship diagram.

```json
{
  "title": "Database Schema",
  "entities": [
    {
      "name": "User",
      "attributes": [
        {"name": "id", "type": "int", "pk": true},
        {"name": "email", "type": "string"}
      ]
    }
  ],
  "relationships": [
    {"from": "User", "to": "Order", "label": "places", "type": "1:N"}
  ]
}
```

### create_flowchart

Create a flowchart diagram.

```json
{
  "title": "Process Flow",
  "nodes": [
    {"id": "start", "label": "Start", "shape": "ellipse"},
    {"id": "process", "label": "Process", "shape": "rect"},
    {"id": "decision", "label": "OK?", "shape": "diamond"},
    {"from": "start", "to": "process"},
    {"from": "process", "to": "decision"}
  ],
  "direction": "TB"
}
```

### create_architecture

Create a system architecture diagram.

```json
{
  "title": "System Architecture",
  "components": [
    {"id": "web", "type": "server", "label": "Web Server"},
    {"id": "db", "type": "database", "label": "PostgreSQL"},
    {"id": "cache", "type": "cache", "label": "Redis"}
  ],
  "connections": [
    {"from": "web", "to": "db", "label": "SQL"},
    {"from": "web", "to": "cache", "label": "Cache"}
  ]
}
```

### create_mindmap

Create a mindmap diagram.

```json
{
  "root": "Project Ideas",
  "branches": [
    "Feature A",
    ["Feature B", "Sub B.1", "Sub B.2"],
    "Feature C"
  ]
}
```

## Output

All diagrams are saved as `.drawio` files in the `output/` directory and can be opened directly in:
- draw.io desktop app
- diagrams.net web editor
- VS Code with Draw.io extension

---
Created with love by Angela for David
