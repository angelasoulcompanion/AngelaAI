"""
Mermaid Diagram Tools
Supports: Flowchart, ER Diagram, Sequence, Class, State, Mindmap, Gantt
"""

from typing import Optional
from ..utils.renderer import DiagramRenderer


class MermaidTools:
    """Tools for generating Mermaid diagrams"""

    def __init__(self):
        self.renderer = DiagramRenderer()

    async def create_flowchart(
        self,
        title: str,
        nodes: list[dict],
        direction: str = "TD"
    ) -> dict:
        """
        Create a flowchart diagram

        Args:
            title: Diagram title
            nodes: List of nodes with structure:
                [
                    {"id": "A", "label": "Start", "shape": "stadium"},
                    {"id": "B", "label": "Process", "shape": "rect"},
                    {"id": "C", "label": "Decision?", "shape": "diamond"},
                    {"from": "A", "to": "B", "label": "next"},
                    {"from": "B", "to": "C"},
                    {"from": "C", "to": "D", "label": "yes"},
                ]
                Shapes: rect, stadium, diamond, circle, parallelogram, hexagon
            direction: TD (top-down), LR (left-right), BT, RL

        Returns:
            dict with mermaid code and render result
        """
        # Build node definitions
        node_defs = []
        edges = []

        shape_map = {
            "rect": ("[", "]"),
            "stadium": ("([", "])"),
            "diamond": ("{", "}"),
            "circle": ("((", "))"),
            "parallelogram": ("[/", "/]"),
            "hexagon": ("{{", "}}"),
            "database": ("[(", ")]"),
            "subroutine": ("[[", "]]"),
        }

        for item in nodes:
            if "from" in item and "to" in item:
                # This is an edge
                label = f"|{item['label']}|" if item.get("label") else ""
                arrow = item.get("arrow", "-->")
                edges.append(f"    {item['from']} {arrow}{label} {item['to']}")
            else:
                # This is a node
                node_id = item["id"]
                label = item.get("label", node_id)
                shape = item.get("shape", "rect")
                left, right = shape_map.get(shape, ("[", "]"))
                node_defs.append(f"    {node_id}{left}\"{label}\"{right}")

        code = f"""---
title: {title}
---
flowchart {direction}
{chr(10).join(node_defs)}
{chr(10).join(edges)}"""

        result = await self.renderer.render_mermaid(code)
        result["diagram_type"] = "flowchart"
        result["title"] = title
        return result

    async def create_er_diagram(
        self,
        title: str,
        entities: list[dict],
        relationships: list[dict]
    ) -> dict:
        """
        Create an Entity-Relationship diagram

        Args:
            title: Diagram title
            entities: List of entities:
                [
                    {
                        "name": "USER",
                        "attributes": [
                            {"name": "id", "type": "uuid", "pk": True},
                            {"name": "email", "type": "string"},
                            {"name": "created_at", "type": "timestamp"}
                        ]
                    }
                ]
            relationships: List of relationships:
                [
                    {"from": "USER", "to": "ORDER", "label": "places", "cardinality": "||--o{"}
                ]
                Cardinality: ||--|| (one-to-one), ||--o{ (one-to-many), }o--o{ (many-to-many)

        Returns:
            dict with mermaid code and render result
        """
        lines = [f"---", f"title: {title}", "---", "erDiagram"]

        # Add entities
        for entity in entities:
            lines.append(f"    {entity['name']} {{")
            for attr in entity.get("attributes", []):
                pk = "PK" if attr.get("pk") else ""
                fk = "FK" if attr.get("fk") else ""
                key = pk or fk
                key_str = f" {key}" if key else ""
                lines.append(f"        {attr['type']} {attr['name']}{key_str}")
            lines.append("    }")

        # Add relationships
        for rel in relationships:
            card = rel.get("cardinality", "||--o{")
            label = rel.get("label", "relates")
            lines.append(f"    {rel['from']} {card} {rel['to']} : {label}")

        code = "\n".join(lines)
        result = await self.renderer.render_mermaid(code)
        result["diagram_type"] = "er_diagram"
        result["title"] = title
        return result

    async def create_sequence_diagram(
        self,
        title: str,
        participants: list[str],
        messages: list[dict]
    ) -> dict:
        """
        Create a sequence diagram

        Args:
            title: Diagram title
            participants: List of participant names ["Client", "Server", "Database"]
            messages: List of messages:
                [
                    {"from": "Client", "to": "Server", "message": "HTTP Request", "type": "solid"},
                    {"from": "Server", "to": "Database", "message": "Query", "type": "solid"},
                    {"from": "Database", "to": "Server", "message": "Result", "type": "dashed"},
                    {"from": "Server", "to": "Client", "message": "Response", "type": "dashed"}
                ]
                Types: solid (->>) , dashed (-->>), solid_arrow (->>), dashed_arrow (-->>)

        Returns:
            dict with mermaid code and render result
        """
        lines = ["sequenceDiagram", f"    title {title}"]

        # Add participants
        for p in participants:
            lines.append(f"    participant {p}")

        # Add messages
        arrow_map = {
            "solid": "->>",
            "dashed": "-->>",
            "solid_arrow": "->>+",
            "dashed_arrow": "-->>-",
            "solid_open": "->",
            "dashed_open": "-->",
        }

        for msg in messages:
            arrow = arrow_map.get(msg.get("type", "solid"), "->>")
            lines.append(f"    {msg['from']}{arrow}{msg['to']}: {msg['message']}")

        code = "\n".join(lines)
        result = await self.renderer.render_mermaid(code)
        result["diagram_type"] = "sequence"
        result["title"] = title
        return result

    async def create_class_diagram(
        self,
        title: str,
        classes: list[dict],
        relationships: list[dict]
    ) -> dict:
        """
        Create a class diagram

        Args:
            title: Diagram title
            classes: List of classes:
                [
                    {
                        "name": "Animal",
                        "attributes": ["+String name", "-int age"],
                        "methods": ["+eat()", "+sleep()", "#makeSound()"]
                    }
                ]
                Visibility: + public, - private, # protected
            relationships: List of relationships:
                [
                    {"from": "Dog", "to": "Animal", "type": "inheritance"},
                    {"from": "Person", "to": "Dog", "type": "association", "label": "owns"}
                ]
                Types: inheritance (<|--), composition (*--), aggregation (o--),
                       association (-->), dependency (..)

        Returns:
            dict with mermaid code and render result
        """
        lines = ["classDiagram", f"    class {title}"]

        # Add classes
        for cls in classes:
            lines.append(f"    class {cls['name']} {{")
            for attr in cls.get("attributes", []):
                lines.append(f"        {attr}")
            for method in cls.get("methods", []):
                lines.append(f"        {method}")
            lines.append("    }")

        # Add relationships
        rel_map = {
            "inheritance": "<|--",
            "composition": "*--",
            "aggregation": "o--",
            "association": "-->",
            "dependency": "..",
            "realization": "<|..",
        }

        for rel in relationships:
            arrow = rel_map.get(rel.get("type", "association"), "-->")
            label = f" : {rel['label']}" if rel.get("label") else ""
            lines.append(f"    {rel['to']} {arrow} {rel['from']}{label}")

        code = "\n".join(lines)
        result = await self.renderer.render_mermaid(code)
        result["diagram_type"] = "class"
        result["title"] = title
        return result

    async def create_state_diagram(
        self,
        title: str,
        states: list[dict],
        transitions: list[dict]
    ) -> dict:
        """
        Create a state diagram

        Args:
            title: Diagram title
            states: List of states:
                [
                    {"name": "Idle", "description": "Waiting for input"},
                    {"name": "Processing"},
                    {"name": "Complete", "type": "final"}
                ]
            transitions: List of transitions:
                [
                    {"from": "[*]", "to": "Idle"},
                    {"from": "Idle", "to": "Processing", "label": "start"},
                    {"from": "Processing", "to": "Complete", "label": "done"},
                    {"from": "Complete", "to": "[*]"}
                ]
        """
        lines = ["stateDiagram-v2", f"    %% {title}"]

        # Add state descriptions
        for state in states:
            if state.get("description"):
                lines.append(f"    {state['name']} : {state['description']}")

        # Add transitions
        for trans in transitions:
            label = f" : {trans['label']}" if trans.get("label") else ""
            lines.append(f"    {trans['from']} --> {trans['to']}{label}")

        code = "\n".join(lines)
        result = await self.renderer.render_mermaid(code)
        result["diagram_type"] = "state"
        result["title"] = title
        return result

    async def create_mindmap(
        self,
        root: str,
        branches: list
    ) -> dict:
        """
        Create a mindmap diagram

        Args:
            root: Root node text
            branches: Nested list of branches:
                [
                    "Branch 1",
                    ["Branch 2", ["Sub 2.1", "Sub 2.2"]],
                    ["Branch 3", ["Sub 3.1"]]
                ]
        """
        def build_branch(items, indent=1):
            lines = []
            for item in items:
                if isinstance(item, str):
                    lines.append("  " * indent + item)
                elif isinstance(item, list):
                    if len(item) >= 1:
                        lines.append("  " * indent + item[0])
                        if len(item) > 1:
                            lines.extend(build_branch(item[1:], indent + 1))
            return lines

        lines = ["mindmap", f"  root(({root}))"]
        lines.extend(build_branch(branches))

        code = "\n".join(lines)
        result = await self.renderer.render_mermaid(code)
        result["diagram_type"] = "mindmap"
        return result

    async def create_gantt(
        self,
        title: str,
        sections: list[dict]
    ) -> dict:
        """
        Create a Gantt chart

        Args:
            title: Chart title
            sections: List of sections with tasks:
                [
                    {
                        "name": "Phase 1",
                        "tasks": [
                            {"name": "Task 1", "id": "t1", "duration": "5d", "start": "2024-01-01"},
                            {"name": "Task 2", "id": "t2", "duration": "3d", "after": "t1"}
                        ]
                    }
                ]
        """
        lines = [
            "gantt",
            f"    title {title}",
            "    dateFormat YYYY-MM-DD"
        ]

        for section in sections:
            lines.append(f"    section {section['name']}")
            for task in section.get("tasks", []):
                task_id = task.get("id", "")
                duration = task.get("duration", "1d")

                if task.get("start"):
                    timing = f"{task['start']}, {duration}"
                elif task.get("after"):
                    timing = f"after {task['after']}, {duration}"
                else:
                    timing = duration

                id_str = f" :{task_id}," if task_id else " :"
                lines.append(f"    {task['name']}{id_str} {timing}")

        code = "\n".join(lines)
        result = await self.renderer.render_mermaid(code)
        result["diagram_type"] = "gantt"
        result["title"] = title
        return result

    async def render_raw_mermaid(
        self,
        code: str,
        output_format: str = "svg",
        theme: str = "default"
    ) -> dict:
        """
        Render raw Mermaid code directly

        Args:
            code: Raw Mermaid diagram code
            output_format: svg, png, pdf
            theme: default, dark, forest, neutral

        Returns:
            dict with render result
        """
        result = await self.renderer.render_mermaid(code, output_format, theme)
        result["diagram_type"] = "custom"
        return result
