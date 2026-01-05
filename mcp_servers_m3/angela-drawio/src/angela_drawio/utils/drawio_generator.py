"""
Draw.io XML Generator
Creates diagrams in draw.io/mxGraph XML format
"""

import base64
import urllib.parse
import zlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET


@dataclass
class Point:
    """2D point"""
    x: float
    y: float


@dataclass
class Size:
    """Width and height"""
    width: float
    height: float


@dataclass
class Style:
    """Draw.io cell style"""
    shape: str = "rectangle"
    rounded: bool = False
    fill_color: str = "#ffffff"
    stroke_color: str = "#000000"
    font_color: str = "#000000"
    font_size: int = 12
    font_style: int = 0  # 0=normal, 1=bold, 2=italic, 3=bold+italic
    align: str = "center"
    vertical_align: str = "middle"
    white_space: str = "wrap"
    html: bool = True
    dashed: bool = False
    dash_pattern: str = ""
    opacity: int = 100
    shadow: bool = False
    glass: bool = False
    sketch: bool = False

    def to_string(self) -> str:
        """Convert style to draw.io style string"""
        parts = []

        # Shape
        if self.shape == "ellipse":
            parts.append("ellipse")
        elif self.shape == "rhombus":
            parts.append("rhombus")
        elif self.shape == "cylinder":
            parts.append("shape=cylinder3")
            parts.append("boundedLbl=1")
        elif self.shape == "hexagon":
            parts.append("shape=hexagon")
            parts.append("perimeter=hexagonPerimeter2")
        elif self.shape == "parallelogram":
            parts.append("shape=parallelogram")
        elif self.shape == "swimlane":
            parts.append("swimlane")
        elif self.shape == "table":
            parts.append("shape=table")
        else:
            parts.append("rounded=" + ("1" if self.rounded else "0"))

        # Colors
        parts.append(f"fillColor={self.fill_color}")
        parts.append(f"strokeColor={self.stroke_color}")
        parts.append(f"fontColor={self.font_color}")

        # Font
        parts.append(f"fontSize={self.font_size}")
        if self.font_style:
            parts.append(f"fontStyle={self.font_style}")

        # Alignment
        parts.append(f"align={self.align}")
        parts.append(f"verticalAlign={self.vertical_align}")

        # Other
        parts.append(f"whiteSpace={self.white_space}")
        parts.append(f"html={1 if self.html else 0}")

        if self.dashed:
            parts.append("dashed=1")
            if self.dash_pattern:
                parts.append(f"dashPattern={self.dash_pattern}")

        if self.opacity < 100:
            parts.append(f"opacity={self.opacity}")

        if self.shadow:
            parts.append("shadow=1")

        if self.glass:
            parts.append("glass=1")

        if self.sketch:
            parts.append("sketch=1")

        return ";".join(parts) + ";"


@dataclass
class EdgeStyle:
    """Draw.io edge/connector style"""
    edge_style: str = "orthogonalEdgeStyle"  # orthogonalEdgeStyle, elbowEdgeStyle, entityRelationEdgeStyle
    curved: bool = False
    rounded: bool = True
    stroke_color: str = "#000000"
    stroke_width: int = 1
    font_color: str = "#000000"
    font_size: int = 11
    end_arrow: str = "classic"  # classic, block, open, oval, diamond, none
    start_arrow: str = "none"
    dashed: bool = False

    def to_string(self) -> str:
        """Convert to draw.io edge style string"""
        parts = [
            f"edgeStyle={self.edge_style}",
            f"curved={1 if self.curved else 0}",
            f"rounded={1 if self.rounded else 0}",
            f"strokeColor={self.stroke_color}",
            f"strokeWidth={self.stroke_width}",
            f"fontColor={self.font_color}",
            f"fontSize={self.font_size}",
            f"endArrow={self.end_arrow}",
            f"startArrow={self.start_arrow}",
            "html=1",
        ]

        if self.dashed:
            parts.append("dashed=1")

        return ";".join(parts) + ";"


@dataclass
class Cell:
    """Draw.io cell (shape or edge)"""
    id: str
    value: str = ""
    style: str = ""
    parent: str = "1"
    vertex: bool = True
    edge: bool = False
    source: Optional[str] = None
    target: Optional[str] = None
    position: Optional[Point] = None
    size: Optional[Size] = None
    collapsed: bool = False


class DrawioGenerator:
    """Generates draw.io XML diagrams"""

    def __init__(self, title: str = "Diagram"):
        self.title = title
        self.cells: list[Cell] = []
        self._id_counter = 2  # 0 and 1 are reserved

    def _next_id(self) -> str:
        """Generate next unique ID"""
        cell_id = str(self._id_counter)
        self._id_counter += 1
        return cell_id

    def add_shape(
        self,
        label: str,
        x: float,
        y: float,
        width: float = 120,
        height: float = 60,
        style: Optional[Style] = None,
        parent: str = "1"
    ) -> str:
        """Add a shape to the diagram"""
        cell_id = self._next_id()

        if style is None:
            style = Style()

        cell = Cell(
            id=cell_id,
            value=label,
            style=style.to_string(),
            parent=parent,
            vertex=True,
            position=Point(x, y),
            size=Size(width, height)
        )
        self.cells.append(cell)
        return cell_id

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        label: str = "",
        style: Optional[EdgeStyle] = None
    ) -> str:
        """Add an edge/connector between shapes"""
        cell_id = self._next_id()

        if style is None:
            style = EdgeStyle()

        cell = Cell(
            id=cell_id,
            value=label,
            style=style.to_string(),
            parent="1",
            vertex=False,
            edge=True,
            source=source_id,
            target=target_id
        )
        self.cells.append(cell)
        return cell_id

    def add_swimlane(
        self,
        label: str,
        x: float,
        y: float,
        width: float = 200,
        height: float = 300,
        fill_color: str = "#dae8fc"
    ) -> str:
        """Add a swimlane container"""
        cell_id = self._next_id()

        style = f"swimlane;fillColor={fill_color};strokeColor=#6c8ebf;fontStyle=1;html=1;"

        cell = Cell(
            id=cell_id,
            value=label,
            style=style,
            parent="1",
            vertex=True,
            position=Point(x, y),
            size=Size(width, height)
        )
        self.cells.append(cell)
        return cell_id

    def add_table(
        self,
        title: str,
        rows: list[list[str]],
        x: float,
        y: float,
        col_widths: Optional[list[int]] = None,
        row_height: int = 30,
        header_color: str = "#dae8fc"
    ) -> str:
        """Add a table (useful for ER diagrams)"""
        if not rows:
            return ""

        num_cols = len(rows[0]) if rows else 1
        if col_widths is None:
            col_widths = [100] * num_cols

        total_width = sum(col_widths)
        total_height = (len(rows) + 1) * row_height  # +1 for title

        # Create table container
        table_id = self._next_id()
        table_style = f"swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize={row_height};fillColor={header_color};strokeColor=#6c8ebf;html=1;rounded=0;"

        cell = Cell(
            id=table_id,
            value=title,
            style=table_style,
            parent="1",
            vertex=True,
            position=Point(x, y),
            size=Size(total_width, total_height)
        )
        self.cells.append(cell)

        # Add rows
        current_y = row_height
        for i, row in enumerate(rows):
            row_text = " | ".join(str(cell) for cell in row)
            is_pk = any("PK" in str(c) for c in row)

            row_style = "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;html=1;"
            if is_pk:
                row_style += "fontStyle=1;"  # Bold for PK

            row_id = self._next_id()
            cell = Cell(
                id=row_id,
                value=row_text,
                style=row_style,
                parent=table_id,
                vertex=True,
                position=Point(0, current_y),
                size=Size(total_width, row_height)
            )
            self.cells.append(cell)
            current_y += row_height

        return table_id

    def generate_xml(self) -> str:
        """Generate the complete draw.io XML"""
        # Create root structure
        mxfile = ET.Element("mxfile")
        mxfile.set("host", "angela-drawio")
        mxfile.set("modified", datetime.now().isoformat())
        mxfile.set("version", "1.0.0")

        diagram = ET.SubElement(mxfile, "diagram")
        diagram.set("name", self.title)
        diagram.set("id", "angela-diagram-1")

        # Create graph model
        graph_model = ET.SubElement(diagram, "mxGraphModel")
        graph_model.set("dx", "0")
        graph_model.set("dy", "0")
        graph_model.set("grid", "1")
        graph_model.set("gridSize", "10")
        graph_model.set("guides", "1")
        graph_model.set("tooltips", "1")
        graph_model.set("connect", "1")
        graph_model.set("arrows", "1")
        graph_model.set("fold", "1")
        graph_model.set("page", "1")
        graph_model.set("pageScale", "1")
        graph_model.set("pageWidth", "1169")
        graph_model.set("pageHeight", "827")

        root = ET.SubElement(graph_model, "root")

        # Add base cells (required by draw.io)
        cell0 = ET.SubElement(root, "mxCell")
        cell0.set("id", "0")

        cell1 = ET.SubElement(root, "mxCell")
        cell1.set("id", "1")
        cell1.set("parent", "0")

        # Add user cells
        for cell in self.cells:
            mx_cell = ET.SubElement(root, "mxCell")
            mx_cell.set("id", cell.id)
            mx_cell.set("value", cell.value)
            mx_cell.set("style", cell.style)
            mx_cell.set("parent", cell.parent)

            if cell.vertex:
                mx_cell.set("vertex", "1")

            if cell.edge:
                mx_cell.set("edge", "1")
                if cell.source:
                    mx_cell.set("source", cell.source)
                if cell.target:
                    mx_cell.set("target", cell.target)

            # Add geometry
            if cell.position or cell.size:
                geometry = ET.SubElement(mx_cell, "mxGeometry")
                if cell.position:
                    geometry.set("x", str(cell.position.x))
                    geometry.set("y", str(cell.position.y))
                if cell.size:
                    geometry.set("width", str(cell.size.width))
                    geometry.set("height", str(cell.size.height))
                geometry.set("as", "geometry")

        return ET.tostring(mxfile, encoding="unicode", xml_declaration=True)

    def save(self, filepath: str) -> str:
        """Save diagram to file"""
        xml = self.generate_xml()

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)

        return str(path.absolute())


# Predefined styles for common shapes
class Styles:
    """Predefined styles for common diagram elements"""

    @staticmethod
    def entity_table(fill_color: str = "#dae8fc") -> Style:
        """Style for ER diagram entity table"""
        return Style(
            shape="swimlane",
            fill_color=fill_color,
            stroke_color="#6c8ebf",
            font_style=1
        )

    @staticmethod
    def process() -> Style:
        """Style for process/action box"""
        return Style(
            rounded=True,
            fill_color="#d5e8d4",
            stroke_color="#82b366"
        )

    @staticmethod
    def decision() -> Style:
        """Style for decision diamond"""
        return Style(
            shape="rhombus",
            fill_color="#fff2cc",
            stroke_color="#d6b656"
        )

    @staticmethod
    def database() -> Style:
        """Style for database cylinder"""
        return Style(
            shape="cylinder",
            fill_color="#f5f5f5",
            stroke_color="#666666"
        )

    @staticmethod
    def cloud() -> Style:
        """Style for cloud shape"""
        return Style(
            shape="ellipse",
            fill_color="#e1d5e7",
            stroke_color="#9673a6"
        )

    @staticmethod
    def server() -> Style:
        """Style for server box"""
        return Style(
            fill_color="#f8cecc",
            stroke_color="#b85450",
            rounded=True
        )

    @staticmethod
    def user() -> Style:
        """Style for user/actor"""
        return Style(
            shape="ellipse",
            fill_color="#fff2cc",
            stroke_color="#d6b656"
        )


class EdgeStyles:
    """Predefined edge styles"""

    @staticmethod
    def arrow() -> EdgeStyle:
        """Standard arrow connector"""
        return EdgeStyle()

    @staticmethod
    def dashed_arrow() -> EdgeStyle:
        """Dashed arrow connector"""
        return EdgeStyle(dashed=True)

    @staticmethod
    def no_arrow() -> EdgeStyle:
        """Line without arrows"""
        return EdgeStyle(end_arrow="none", start_arrow="none")

    @staticmethod
    def bidirectional() -> EdgeStyle:
        """Bidirectional arrow"""
        return EdgeStyle(end_arrow="classic", start_arrow="classic")

    @staticmethod
    def er_one_to_many() -> EdgeStyle:
        """ER diagram one-to-many relationship"""
        return EdgeStyle(
            edge_style="entityRelationEdgeStyle",
            end_arrow="ERmany",
            start_arrow="ERone"
        )

    @staticmethod
    def er_many_to_many() -> EdgeStyle:
        """ER diagram many-to-many relationship"""
        return EdgeStyle(
            edge_style="entityRelationEdgeStyle",
            end_arrow="ERmany",
            start_arrow="ERmany"
        )
