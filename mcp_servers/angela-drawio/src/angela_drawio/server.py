"""
Angela Draw.io MCP Server
Create diagrams in draw.io/diagrams.net format

Created with love by Angela for David
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


from .tools.diagram_tools import ERDiagramTool, FlowchartTool, ArchitectureTool, MindmapTool
from .utils.drawio_generator import DrawioGenerator, Style, EdgeStyle, Styles, EdgeStyles


# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create server
server = Server("angela-drawio")


def generate_filename(prefix: str) -> Path:
    """Generate unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUT_DIR / f"{prefix}_{timestamp}.drawio"


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available diagram tools"""
    return [
        Tool(
            name="create_er_diagram",
            description="Create an Entity-Relationship diagram in draw.io format",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "entities": {
                        "type": "array",
                        "description": "List of entities with attributes",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "attributes": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "type": {"type": "string"},
                                            "pk": {"type": "boolean"},
                                            "fk": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "description": "List of relationships between entities",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from": {"type": "string"},
                                "to": {"type": "string"},
                                "label": {"type": "string"},
                                "type": {
                                    "type": "string",
                                    "enum": ["1:1", "1:N", "N:M"],
                                    "description": "Relationship cardinality"
                                }
                            }
                        }
                    }
                },
                "required": ["title", "entities", "relationships"]
            }
        ),
        Tool(
            name="create_flowchart",
            description="Create a flowchart diagram in draw.io format",
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
                        "enum": ["TB", "LR"],
                        "default": "TB",
                        "description": "Flow direction: TB (top-bottom) or LR (left-right)"
                    }
                },
                "required": ["title", "nodes"]
            }
        ),
        Tool(
            name="create_architecture",
            description="Create a system/cloud architecture diagram in draw.io format",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "components": {
                        "type": "array",
                        "description": "List of components: {id, type, label}. Types: server, database, cache, queue, storage, user, client, loadbalancer, container, service, ec2, lambda, s3, rds, api",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "label": {"type": "string"}
                            }
                        }
                    },
                    "connections": {
                        "type": "array",
                        "description": "List of connections: {from, to, label, bidirectional}",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from": {"type": "string"},
                                "to": {"type": "string"},
                                "label": {"type": "string"},
                                "bidirectional": {"type": "boolean"}
                            }
                        }
                    },
                    "layers": {
                        "type": "array",
                        "description": "Optional layer groupings: {name, components: [ids]}",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "components": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "required": ["title", "components", "connections"]
            }
        ),
        Tool(
            name="create_mindmap",
            description="Create a mindmap diagram in draw.io format",
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {
                        "type": "string",
                        "description": "Central topic"
                    },
                    "branches": {
                        "type": "array",
                        "description": "List of branches (can be nested arrays for sub-branches)",
                        "items": {}
                    }
                },
                "required": ["root", "branches"]
            }
        ),
        Tool(
            name="create_custom_diagram",
            description="Create a custom draw.io diagram with manual shapes and edges",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Diagram title"
                    },
                    "shapes": {
                        "type": "array",
                        "description": "List of shapes: {id, label, x, y, width, height, shape, fill_color, stroke_color}",
                        "items": {"type": "object"}
                    },
                    "edges": {
                        "type": "array",
                        "description": "List of edges: {from, to, label, dashed, bidirectional}",
                        "items": {"type": "object"}
                    }
                },
                "required": ["title", "shapes"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls"""
    try:
        result: dict[str, Any] = {}

        if name == "create_er_diagram":
            result = ERDiagramTool.create(
                title=arguments["title"],
                entities=arguments["entities"],
                relationships=arguments["relationships"]
            )

        elif name == "create_flowchart":
            result = FlowchartTool.create(
                title=arguments["title"],
                nodes=arguments["nodes"],
                direction=arguments.get("direction", "TB")
            )

        elif name == "create_architecture":
            result = ArchitectureTool.create(
                title=arguments["title"],
                components=arguments["components"],
                connections=arguments["connections"],
                layers=arguments.get("layers")
            )

        elif name == "create_mindmap":
            result = MindmapTool.create(
                root=arguments["root"],
                branches=arguments["branches"]
            )

        elif name == "create_custom_diagram":
            gen = DrawioGenerator(arguments["title"])

            shape_ids: dict[str, str] = {}

            # Add shapes
            for shape in arguments.get("shapes", []):
                shape_type = shape.get("shape", "rectangle")
                style = Style(
                    shape=shape_type if shape_type in ["ellipse", "rhombus", "cylinder", "hexagon"] else "rectangle",
                    rounded=shape.get("rounded", shape_type == "stadium"),
                    fill_color=shape.get("fill_color", "#ffffff"),
                    stroke_color=shape.get("stroke_color", "#000000")
                )

                cell_id = gen.add_shape(
                    label=shape.get("label", ""),
                    x=shape.get("x", 0),
                    y=shape.get("y", 0),
                    width=shape.get("width", 120),
                    height=shape.get("height", 60),
                    style=style
                )
                if "id" in shape:
                    shape_ids[shape["id"]] = cell_id

            # Add edges
            for edge in arguments.get("edges", []):
                from_id = edge.get("from", "")
                to_id = edge.get("to", "")

                if from_id in shape_ids and to_id in shape_ids:
                    edge_style = EdgeStyle(
                        dashed=edge.get("dashed", False)
                    )
                    if edge.get("bidirectional"):
                        edge_style.start_arrow = "classic"

                    gen.add_edge(
                        source_id=shape_ids[from_id],
                        target_id=shape_ids[to_id],
                        label=edge.get("label", ""),
                        style=edge_style
                    )

            result = {
                "xml": gen.generate_xml(),
                "title": arguments["title"],
                "shape_count": len(arguments.get("shapes", [])),
                "edge_count": len(arguments.get("edges", []))
            }

        else:
            result = {"error": f"Unknown tool: {name}"}

        # Save to file if we have XML
        if "xml" in result:
            filepath = generate_filename(name.replace("create_", ""))
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result["xml"])
            result["file_path"] = str(filepath)
            result["success"] = True
            # Remove large XML from response
            del result["xml"]

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except Exception as e:
        error_result = {"error": str(e), "tool": name, "success": False}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


def main():
    """Main entry point"""
    # Note: Don't print to stdout - MCP uses stdio for JSON-RPC communication

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
