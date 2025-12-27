"""
Diagram Renderer Utilities
Handles rendering of various diagram types to images
"""

import asyncio
import base64
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional


def find_mmdc() -> Optional[str]:
    """Find mmdc executable with common npm paths"""
    # Try shutil.which first
    mmdc = shutil.which("mmdc")
    if mmdc:
        return mmdc

    # Common npm global paths
    common_paths = [
        Path.home() / ".npm-global" / "bin" / "mmdc",
        Path.home() / ".nvm" / "versions" / "node" / "*/bin/mmdc",
        Path("/usr/local/bin/mmdc"),
        Path("/opt/homebrew/bin/mmdc"),
    ]

    for path in common_paths:
        if "*" in str(path):
            # Handle glob patterns
            import glob
            matches = glob.glob(str(path))
            if matches:
                return matches[0]
        elif path.exists():
            return str(path)

    return None

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "output"


class DiagramRenderer:
    """Renders diagrams to various formats"""

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, prefix: str, extension: str) -> Path:
        """Generate unique filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{prefix}_{timestamp}.{extension}"

    async def render_mermaid(
        self,
        code: str,
        output_format: str = "svg",
        theme: str = "default"
    ) -> dict:
        """
        Render Mermaid diagram using mmdc CLI

        Args:
            code: Mermaid diagram code
            output_format: svg, png, or pdf
            theme: default, dark, forest, neutral

        Returns:
            dict with file_path and base64 content
        """
        output_file = self._generate_filename("mermaid", output_format)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False
        ) as f:
            f.write(code)
            input_file = f.name

        try:
            # Find mmdc executable
            mmdc_path = find_mmdc()

            if not mmdc_path:
                # Fallback: return the mermaid code for browser rendering
                return {
                    "success": False,
                    "error": "mmdc not installed. Install with: npm install -g @mermaid-js/mermaid-cli",
                    "mermaid_code": code,
                    "render_url": f"https://mermaid.live/edit#base64:{base64.b64encode(code.encode()).decode()}"
                }

            # Use mmdc (mermaid-cli)
            cmd = [
                mmdc_path,
                "-i", input_file,
                "-o", str(output_file),
                "-t", theme,
                "-b", "white"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # Render failed
                return {
                    "success": False,
                    "error": f"mmdc render failed: {stderr.decode()}",
                    "mermaid_code": code,
                    "render_url": f"https://mermaid.live/edit#base64:{base64.b64encode(code.encode()).decode()}"
                }

            # Read and encode the output
            with open(output_file, "rb") as f:
                content = f.read()
                content_base64 = base64.b64encode(content).decode()

            return {
                "success": True,
                "file_path": str(output_file),
                "format": output_format,
                "base64": content_base64,
                "mermaid_code": code
            }

        finally:
            os.unlink(input_file)

    async def render_graphviz(
        self,
        code: str,
        output_format: str = "svg",
        engine: str = "dot"
    ) -> dict:
        """
        Render Graphviz diagram

        Args:
            code: DOT language code
            output_format: svg, png, pdf
            engine: dot, neato, fdp, sfdp, circo, twopi
        """
        output_file = self._generate_filename("graphviz", output_format)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".dot", delete=False
        ) as f:
            f.write(code)
            input_file = f.name

        try:
            cmd = [
                engine,
                f"-T{output_format}",
                "-o", str(output_file),
                input_file
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Graphviz error: {stderr.decode()}",
                    "dot_code": code
                }

            with open(output_file, "rb") as f:
                content = f.read()
                content_base64 = base64.b64encode(content).decode()

            return {
                "success": True,
                "file_path": str(output_file),
                "format": output_format,
                "base64": content_base64,
                "dot_code": code
            }

        finally:
            os.unlink(input_file)

    def get_mermaid_live_url(self, code: str) -> str:
        """Generate Mermaid Live Editor URL"""
        encoded = base64.b64encode(code.encode()).decode()
        return f"https://mermaid.live/edit#base64:{encoded}"
