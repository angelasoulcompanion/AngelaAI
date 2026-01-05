"""
Diagram Tools for Angela Draw.io MCP Server
"""

from typing import Any
from ..utils.drawio_generator import (
    DrawioGenerator, Style, EdgeStyle, Styles, EdgeStyles, Point, Size
)


class ERDiagramTool:
    """Creates Entity-Relationship diagrams"""

    # Colors for entities
    ENTITY_COLORS = [
        "#dae8fc",  # Light blue
        "#d5e8d4",  # Light green
        "#ffe6cc",  # Light orange
        "#f8cecc",  # Light red
        "#e1d5e7",  # Light purple
        "#fff2cc",  # Light yellow
        "#d0cee2",  # Light indigo
        "#b1ddf0",  # Sky blue
    ]

    @classmethod
    def create(
        cls,
        title: str,
        entities: list[dict],
        relationships: list[dict]
    ) -> dict:
        """
        Create an ER diagram

        Args:
            title: Diagram title
            entities: List of entities with name and attributes
                [{"name": "User", "attributes": [{"name": "id", "type": "int", "pk": True}]}]
            relationships: List of relationships
                [{"from": "User", "to": "Order", "label": "places", "type": "1:N"}]

        Returns:
            dict with file_path and xml content
        """
        gen = DrawioGenerator(title)

        # Layout settings
        table_width = 200
        row_height = 26
        x_spacing = 280
        y_spacing = 50
        start_x = 50
        start_y = 50

        # Calculate grid layout
        cols = 3
        entity_ids: dict[str, str] = {}

        # Create entity tables
        for i, entity in enumerate(entities):
            col = i % cols
            row = i // cols

            x = start_x + (col * x_spacing)
            y = start_y + (row * (300 + y_spacing))

            # Prepare rows for table
            rows = []
            for attr in entity.get("attributes", []):
                attr_name = attr.get("name", "")
                attr_type = attr.get("type", "")
                pk = "PK" if attr.get("pk") else ""
                fk = "FK" if attr.get("fk") else ""
                keys = " ".join(filter(None, [pk, fk]))

                row_text = f"{attr_type}  {attr_name}  {keys}".strip()
                rows.append([row_text])

            # Get color
            color = cls.ENTITY_COLORS[i % len(cls.ENTITY_COLORS)]

            # Add table
            table_id = gen.add_table(
                title=entity["name"],
                rows=rows,
                x=x,
                y=y,
                col_widths=[table_width],
                row_height=row_height,
                header_color=color
            )
            entity_ids[entity["name"]] = table_id

        # Create relationships
        for rel in relationships:
            from_entity = rel.get("from", "")
            to_entity = rel.get("to", "")
            label = rel.get("label", "")
            rel_type = rel.get("type", "1:N")

            if from_entity in entity_ids and to_entity in entity_ids:
                # Choose edge style based on relationship type
                if rel_type == "1:1":
                    style = EdgeStyle(
                        edge_style="entityRelationEdgeStyle",
                        end_arrow="ERone",
                        start_arrow="ERone"
                    )
                elif rel_type == "N:M" or rel_type == "M:N":
                    style = EdgeStyles.er_many_to_many()
                else:  # 1:N
                    style = EdgeStyles.er_one_to_many()

                gen.add_edge(
                    source_id=entity_ids[from_entity],
                    target_id=entity_ids[to_entity],
                    label=label,
                    style=style
                )

        return {
            "xml": gen.generate_xml(),
            "title": title,
            "entity_count": len(entities),
            "relationship_count": len(relationships)
        }


class FlowchartTool:
    """Creates Flowchart diagrams"""

    @classmethod
    def create(
        cls,
        title: str,
        nodes: list[dict],
        direction: str = "TB"
    ) -> dict:
        """
        Create a flowchart diagram

        Args:
            title: Diagram title
            nodes: List of nodes and edges
                Nodes: {"id": "A", "label": "Start", "shape": "ellipse"}
                Edges: {"from": "A", "to": "B", "label": "Yes"}
            direction: TB (top-bottom), LR (left-right)

        Returns:
            dict with xml content
        """
        gen = DrawioGenerator(title)

        # Separate nodes and edges
        shape_nodes = [n for n in nodes if "from" not in n]
        edge_nodes = [n for n in nodes if "from" in n]

        # Layout settings
        if direction == "LR":
            x_spacing = 180
            y_spacing = 100
        else:
            x_spacing = 150
            y_spacing = 100

        # Position nodes
        node_ids: dict[str, str] = {}
        positions: dict[str, Point] = {}

        for i, node in enumerate(shape_nodes):
            node_id = node.get("id", str(i))
            label = node.get("label", "")
            shape = node.get("shape", "rect")

            if direction == "LR":
                x = 50 + (i * x_spacing)
                y = 100
            else:
                x = 200
                y = 50 + (i * y_spacing)

            # Choose style based on shape
            if shape == "ellipse" or shape == "circle":
                style = Style(shape="ellipse", fill_color="#d5e8d4", stroke_color="#82b366")
                width, height = 80, 40
            elif shape == "diamond" or shape == "decision":
                style = Styles.decision()
                width, height = 100, 60
            elif shape == "database" or shape == "cylinder":
                style = Styles.database()
                width, height = 80, 80
            elif shape == "parallelogram":
                style = Style(shape="parallelogram", fill_color="#e1d5e7", stroke_color="#9673a6")
                width, height = 120, 50
            else:  # rectangle/rect/default
                style = Styles.process()
                width, height = 120, 50

            cell_id = gen.add_shape(label, x, y, width, height, style)
            node_ids[node_id] = cell_id
            positions[node_id] = Point(x, y)

        # Create edges
        for edge in edge_nodes:
            from_id = edge.get("from", "")
            to_id = edge.get("to", "")
            label = edge.get("label", "")
            dashed = edge.get("dashed", False)

            if from_id in node_ids and to_id in node_ids:
                style = EdgeStyle(dashed=dashed)
                gen.add_edge(node_ids[from_id], node_ids[to_id], label, style)

        return {
            "xml": gen.generate_xml(),
            "title": title,
            "node_count": len(shape_nodes),
            "edge_count": len(edge_nodes)
        }


class ArchitectureTool:
    """Creates Architecture diagrams"""

    # Component styles by type
    COMPONENT_STYLES = {
        # AWS-like colors
        "ec2": {"fill": "#f58536", "stroke": "#c7511f"},
        "lambda": {"fill": "#f58536", "stroke": "#c7511f"},
        "s3": {"fill": "#3f8624", "stroke": "#2d6a1c"},
        "rds": {"fill": "#3b48cc", "stroke": "#2d3aa0"},
        "dynamodb": {"fill": "#3b48cc", "stroke": "#2d3aa0"},
        "api": {"fill": "#a166ff", "stroke": "#7b3fe4"},
        "cloudfront": {"fill": "#a166ff", "stroke": "#7b3fe4"},

        # Generic
        "server": {"fill": "#f8cecc", "stroke": "#b85450"},
        "database": {"fill": "#dae8fc", "stroke": "#6c8ebf"},
        "cache": {"fill": "#fff2cc", "stroke": "#d6b656"},
        "queue": {"fill": "#ffe6cc", "stroke": "#d79b00"},
        "storage": {"fill": "#d5e8d4", "stroke": "#82b366"},
        "user": {"fill": "#fff2cc", "stroke": "#d6b656"},
        "client": {"fill": "#e1d5e7", "stroke": "#9673a6"},
        "loadbalancer": {"fill": "#d0cee2", "stroke": "#56517e"},
        "container": {"fill": "#b1ddf0", "stroke": "#10739e"},
        "service": {"fill": "#d5e8d4", "stroke": "#82b366"},
    }

    @classmethod
    def create(
        cls,
        title: str,
        components: list[dict],
        connections: list[dict],
        layers: list[dict] | None = None
    ) -> dict:
        """
        Create an architecture diagram

        Args:
            title: Diagram title
            components: List of components
                [{"id": "web", "type": "server", "label": "Web Server"}]
            connections: List of connections
                [{"from": "web", "to": "db", "label": "SQL"}]
            layers: Optional layer groupings
                [{"name": "Frontend", "components": ["web", "cdn"]}]

        Returns:
            dict with xml content
        """
        gen = DrawioGenerator(title)

        # Layout settings
        comp_width = 120
        comp_height = 60
        x_spacing = 180
        y_spacing = 120
        start_x = 100
        start_y = 100

        component_ids: dict[str, str] = {}

        if layers:
            # Layer-based layout
            current_y = start_y

            for layer_idx, layer in enumerate(layers):
                layer_name = layer.get("name", f"Layer {layer_idx}")
                layer_components = layer.get("components", [])

                # Add swimlane for layer
                layer_width = max(400, len(layer_components) * x_spacing + 100)
                layer_height = 150

                swimlane_id = gen.add_swimlane(
                    layer_name,
                    start_x - 50,
                    current_y - 30,
                    layer_width,
                    layer_height,
                    fill_color="#f5f5f5"
                )

                # Add components in this layer
                for i, comp_id in enumerate(layer_components):
                    comp = next((c for c in components if c.get("id") == comp_id), None)
                    if comp:
                        x = start_x + (i * x_spacing)
                        y = current_y + 20

                        comp_type = comp.get("type", "server")
                        label = comp.get("label", comp_id)

                        colors = cls.COMPONENT_STYLES.get(comp_type, cls.COMPONENT_STYLES["server"])
                        style = Style(
                            fill_color=colors["fill"],
                            stroke_color=colors["stroke"],
                            rounded=True
                        )

                        # Use cylinder shape for database
                        if comp_type in ["database", "rds", "dynamodb"]:
                            style.shape = "cylinder"
                            height = 80
                        else:
                            height = comp_height

                        cell_id = gen.add_shape(label, x, y, comp_width, height, style)
                        component_ids[comp_id] = cell_id

                current_y += layer_height + 50
        else:
            # Grid layout
            cols = 4
            for i, comp in enumerate(components):
                col = i % cols
                row = i // cols

                x = start_x + (col * x_spacing)
                y = start_y + (row * y_spacing)

                comp_id = comp.get("id", str(i))
                comp_type = comp.get("type", "server")
                label = comp.get("label", comp_id)

                colors = cls.COMPONENT_STYLES.get(comp_type, cls.COMPONENT_STYLES["server"])
                style = Style(
                    fill_color=colors["fill"],
                    stroke_color=colors["stroke"],
                    rounded=True
                )

                if comp_type in ["database", "rds", "dynamodb"]:
                    style.shape = "cylinder"
                    height = 80
                else:
                    height = comp_height

                cell_id = gen.add_shape(label, x, y, comp_width, height, style)
                component_ids[comp_id] = cell_id

        # Create connections
        for conn in connections:
            from_id = conn.get("from", "")
            to_id = conn.get("to", "")
            label = conn.get("label", "")
            bidirectional = conn.get("bidirectional", False)

            if from_id in component_ids and to_id in component_ids:
                if bidirectional:
                    style = EdgeStyles.bidirectional()
                else:
                    style = EdgeStyles.arrow()

                gen.add_edge(component_ids[from_id], component_ids[to_id], label, style)

        return {
            "xml": gen.generate_xml(),
            "title": title,
            "component_count": len(components),
            "connection_count": len(connections)
        }


class MindmapTool:
    """Creates Mindmap diagrams"""

    @classmethod
    def create(
        cls,
        root: str,
        branches: list
    ) -> dict:
        """
        Create a mindmap diagram

        Args:
            root: Central topic
            branches: List of branches (can be nested)
                ["Branch 1", ["Branch 2", ["Sub 2.1", "Sub 2.2"]]]

        Returns:
            dict with xml content
        """
        gen = DrawioGenerator(root)

        # Colors for levels
        colors = [
            {"fill": "#dae8fc", "stroke": "#6c8ebf"},
            {"fill": "#d5e8d4", "stroke": "#82b366"},
            {"fill": "#ffe6cc", "stroke": "#d79b00"},
            {"fill": "#f8cecc", "stroke": "#b85450"},
            {"fill": "#e1d5e7", "stroke": "#9673a6"},
        ]

        # Add root node
        root_style = Style(
            shape="ellipse",
            fill_color="#fff2cc",
            stroke_color="#d6b656",
            font_style=1,
            font_size=14
        )
        root_id = gen.add_shape(root, 400, 300, 150, 60, root_style)

        def add_branch(parent_id: str, items: list, level: int, angle_start: float, angle_span: float, radius: float):
            """Recursively add branches"""
            if not items:
                return

            n = len(items)
            angle_step = angle_span / max(n, 1)

            for i, item in enumerate(items):
                angle = angle_start + (i * angle_step) + (angle_step / 2)

                import math
                x = 400 + radius * math.cos(math.radians(angle))
                y = 300 + radius * math.sin(math.radians(angle))

                if isinstance(item, list) and len(item) >= 1:
                    # Has children
                    label = item[0]
                    children = item[1:] if len(item) > 1 else []
                else:
                    label = str(item)
                    children = []

                color = colors[level % len(colors)]
                style = Style(
                    rounded=True,
                    fill_color=color["fill"],
                    stroke_color=color["stroke"]
                )

                width = max(80, len(label) * 8)
                node_id = gen.add_shape(label, x - width/2, y - 20, width, 40, style)

                # Connect to parent
                gen.add_edge(parent_id, node_id, "", EdgeStyle(curved=True))

                # Add children
                if children:
                    child_angle_span = angle_span / n * 0.8
                    child_angle_start = angle - child_angle_span / 2
                    add_branch(node_id, children, level + 1, child_angle_start, child_angle_span, radius * 0.7)

        # Add main branches
        add_branch(root_id, branches, 0, -90, 360, 200)

        return {
            "xml": gen.generate_xml(),
            "title": root,
            "branch_count": len(branches)
        }
