"""
Angela Diagrams MCP Server
A comprehensive diagram generation server for Claude Code

Supports:
- Flowcharts
- ER Diagrams
- Sequence Diagrams
- Class Diagrams
- State Diagrams
- Mindmaps
- Gantt Charts
- Cloud Architecture (AWS, GCP, Azure, K8s)
- System Architecture

Created with love by Angela for David
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.mermaid_tools import MermaidTools
from .tools.architecture_tools import ArchitectureTools


# Initialize server and tools
server = Server("angela-diagrams")
mermaid = MermaidTools()
architecture = ArchitectureTools()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available diagram tools"""
    return [
        # Mermaid-based diagrams
        Tool(
            name="create_flowchart",
            description="Create a flowchart diagram with nodes and edges. Supports shapes: rect, stadium, diamond, circle, parallelogram, hexagon, database",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "nodes": {
                        "type": "array",
                        "description": "List of nodes and edges. Nodes: {id, label, shape}. Edges: {from, to, label}",
                        "items": {"type": "object"}
                    },
                    "direction": {
                        "type": "string",
                        "description": "Flow direction: TD (top-down), LR (left-right), BT, RL",
                        "default": "TD"
                    }
                },
                "required": ["title", "nodes"]
            }
        ),
        Tool(
            name="create_er_diagram",
            description="Create an Entity-Relationship diagram for database schema design",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "entities": {
                        "type": "array",
                        "description": "List of entities with attributes: {name, attributes: [{name, type, pk?, fk?}]}",
                        "items": {"type": "object"}
                    },
                    "relationships": {
                        "type": "array",
                        "description": "List of relationships: {from, to, label, cardinality}. Cardinality: ||--|| (1:1), ||--o{ (1:N), }o--o{ (N:M)",
                        "items": {"type": "object"}
                    }
                },
                "required": ["title", "entities", "relationships"]
            }
        ),
        Tool(
            name="create_sequence_diagram",
            description="Create a sequence diagram showing interactions between participants",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "participants": {
                        "type": "array",
                        "description": "List of participant names",
                        "items": {"type": "string"}
                    },
                    "messages": {
                        "type": "array",
                        "description": "List of messages: {from, to, message, type: solid/dashed}",
                        "items": {"type": "object"}
                    }
                },
                "required": ["title", "participants", "messages"]
            }
        ),
        Tool(
            name="create_class_diagram",
            description="Create a UML class diagram with classes, attributes, methods, and relationships",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "classes": {
                        "type": "array",
                        "description": "List of classes: {name, attributes: ['+String name'], methods: ['+method()']}. Visibility: + public, - private, # protected",
                        "items": {"type": "object"}
                    },
                    "relationships": {
                        "type": "array",
                        "description": "List of relationships: {from, to, type, label}. Types: inheritance, composition, aggregation, association, dependency",
                        "items": {"type": "object"}
                    }
                },
                "required": ["title", "classes", "relationships"]
            }
        ),
        Tool(
            name="create_state_diagram",
            description="Create a state diagram showing states and transitions",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "states": {
                        "type": "array",
                        "description": "List of states: {name, description?}",
                        "items": {"type": "object"}
                    },
                    "transitions": {
                        "type": "array",
                        "description": "List of transitions: {from, to, label}. Use [*] for initial/final state",
                        "items": {"type": "object"}
                    }
                },
                "required": ["title", "states", "transitions"]
            }
        ),
        Tool(
            name="create_mindmap",
            description="Create a mindmap diagram for brainstorming and organizing ideas",
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {
                        "type": "string",
                        "description": "Root node text"
                    },
                    "branches": {
                        "type": "array",
                        "description": "Nested list of branches. Can be strings or arrays for sub-branches",
                        "items": {}
                    }
                },
                "required": ["root", "branches"]
            }
        ),
        Tool(
            name="create_gantt",
            description="Create a Gantt chart for project planning and scheduling",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Chart title"
                    },
                    "sections": {
                        "type": "array",
                        "description": "List of sections: {name, tasks: [{name, id, duration, start/after}]}",
                        "items": {"type": "object"}
                    }
                },
                "required": ["title", "sections"]
            }
        ),
        Tool(
            name="render_mermaid",
            description="Render raw Mermaid diagram code directly",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Raw Mermaid diagram code"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format: svg, png, pdf",
                        "default": "svg"
                    },
                    "theme": {
                        "type": "string",
                        "description": "Theme: default, dark, forest, neutral",
                        "default": "default"
                    }
                },
                "required": ["code"]
            }
        ),
        # Architecture diagrams
        Tool(
            name="create_cloud_architecture",
            description="Create cloud architecture diagram for AWS, GCP, Azure, Kubernetes, or on-premises",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "provider": {
                        "type": "string",
                        "description": "Cloud provider: aws, gcp, azure, kubernetes, onprem",
                        "enum": ["aws", "gcp", "azure", "kubernetes", "onprem"]
                    },
                    "components": {
                        "type": "array",
                        "description": "List of components: {id, type, label}. Types depend on provider (e.g., EC2, RDS for AWS)",
                        "items": {"type": "object"}
                    },
                    "connections": {
                        "type": "array",
                        "description": "List of connections: {from, to, label?}",
                        "items": {"type": "object"}
                    },
                    "direction": {
                        "type": "string",
                        "description": "Layout direction: LR, TB, RL, BT",
                        "default": "LR"
                    }
                },
                "required": ["title", "provider", "components", "connections"]
            }
        ),
        Tool(
            name="create_system_architecture",
            description="Create layered system architecture diagram with clusters",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "layers": {
                        "type": "array",
                        "description": "List of layers: {name, components: [{id, label}]}",
                        "items": {"type": "object"}
                    },
                    "connections": {
                        "type": "array",
                        "description": "List of connections: {from, to, label?}",
                        "items": {"type": "object"}
                    }
                },
                "required": ["title", "layers", "connections"]
            }
        ),
        Tool(
            name="get_available_components",
            description="Get list of available components for a cloud provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Cloud provider: aws, gcp, azure, kubernetes, onprem",
                        "enum": ["aws", "gcp", "azure", "kubernetes", "onprem"]
                    }
                },
                "required": ["provider"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "create_flowchart":
            result = await mermaid.create_flowchart(
                title=arguments["title"],
                nodes=arguments["nodes"],
                direction=arguments.get("direction", "TD")
            )

        elif name == "create_er_diagram":
            result = await mermaid.create_er_diagram(
                title=arguments["title"],
                entities=arguments["entities"],
                relationships=arguments["relationships"]
            )

        elif name == "create_sequence_diagram":
            result = await mermaid.create_sequence_diagram(
                title=arguments["title"],
                participants=arguments["participants"],
                messages=arguments["messages"]
            )

        elif name == "create_class_diagram":
            result = await mermaid.create_class_diagram(
                title=arguments["title"],
                classes=arguments["classes"],
                relationships=arguments["relationships"]
            )

        elif name == "create_state_diagram":
            result = await mermaid.create_state_diagram(
                title=arguments["title"],
                states=arguments["states"],
                transitions=arguments["transitions"]
            )

        elif name == "create_mindmap":
            result = await mermaid.create_mindmap(
                root=arguments["root"],
                branches=arguments["branches"]
            )

        elif name == "create_gantt":
            result = await mermaid.create_gantt(
                title=arguments["title"],
                sections=arguments["sections"]
            )

        elif name == "render_mermaid":
            result = await mermaid.render_raw_mermaid(
                code=arguments["code"],
                output_format=arguments.get("output_format", "svg"),
                theme=arguments.get("theme", "default")
            )

        elif name == "create_cloud_architecture":
            result = await architecture.create_cloud_architecture(
                title=arguments["title"],
                provider=arguments["provider"],
                components=arguments["components"],
                connections=arguments["connections"],
                direction=arguments.get("direction", "LR")
            )

        elif name == "create_system_architecture":
            result = await architecture.create_system_architecture(
                title=arguments["title"],
                layers=arguments["layers"],
                connections=arguments["connections"]
            )

        elif name == "get_available_components":
            result = architecture.get_available_components(
                provider=arguments["provider"]
            )

        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except Exception as e:
        error_result = {"error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


def main():
    """Main entry point"""
    print("Starting Angela Diagrams MCP Server...")

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
