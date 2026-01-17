#!/usr/bin/env python3
"""
💜 Vision Service
Angela Intelligence Enhancement - Phase 3

Provides image understanding capabilities:
- Process screenshots David sends
- Understand code in images
- Read diagrams and charts
- Extract text from images (OCR)
- Analyze visual content

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                      VISION SERVICE                         │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
    │  │    Image     │   │    Code      │   │    Chart     │   │
    │  │   Analyzer   │   │   Extractor  │   │    Reader    │   │
    │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
    │         │                  │                   │           │
    │         └──────────────────┼───────────────────┘           │
    │                            │                               │
    │                     ┌──────▼───────┐                       │
    │                     │   VISION     │                       │
    │                     │   PROCESSOR  │                       │
    │                     └──────┬───────┘                       │
    │                            │                               │
    │    ┌───────────────────────┼───────────────────────┐       │
    │    │                       │                       │       │
    │ ┌──▼──────┐         ┌──────▼──────┐         ┌──────▼───┐   │
    │ │ Result  │         │  Learning   │         │  Cache   │   │
    │ │ Builder │         │   Store     │         │  Store   │   │
    │ └─────────┘         └─────────────┘         └──────────┘   │
    └─────────────────────────────────────────────────────────────┘

Note: This service prepares image analysis requests and stores results.
Actual image processing uses Claude's built-in vision capabilities
or external services like Hugging Face OCR spaces.

Created: 2026-01-17
Author: น้อง Angela 💜
"""

import asyncio
import logging
import base64
import hashlib
import mimetypes
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path
import json

from angela_core.database import db

logger = logging.getLogger(__name__)


class ImageType(Enum):
    """Types of images Angela can process."""
    SCREENSHOT = "screenshot"
    CODE = "code"
    DIAGRAM = "diagram"
    CHART = "chart"
    DOCUMENT = "document"
    PHOTO = "photo"
    UI = "ui"
    ERROR = "error"
    UNKNOWN = "unknown"


class ProcessingMode(Enum):
    """How to process the image."""
    ANALYZE = "analyze"           # General analysis
    OCR = "ocr"                   # Extract text
    CODE_EXTRACT = "code_extract"  # Extract code
    DESCRIBE = "describe"         # Describe content
    CHART_DATA = "chart_data"     # Extract chart data


@dataclass
class ImageAnalysis:
    """Result of image analysis."""
    image_path: str
    image_type: ImageType
    description: str = ""
    extracted_text: str = ""
    extracted_code: str = ""
    detected_elements: List[str] = field(default_factory=list)
    confidence: float = 0.7
    processing_notes: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'image_path': self.image_path,
            'image_type': self.image_type.value,
            'description': self.description,
            'extracted_text': self.extracted_text,
            'extracted_code': self.extracted_code,
            'detected_elements': self.detected_elements,
            'confidence': self.confidence,
            'processing_notes': self.processing_notes,
            'timestamp': self.timestamp.isoformat(),
            'cached': self.cached
        }


@dataclass
class VisionRequest:
    """A request for image processing."""
    image_path: str
    mode: ProcessingMode = ProcessingMode.ANALYZE
    context: str = ""
    questions: List[str] = field(default_factory=list)
    priority: str = "medium"


class VisionService:
    """
    Image understanding service for Angela.

    This service:
    1. Detects image types (screenshot, code, diagram, etc.)
    2. Prepares analysis prompts
    3. Stores and retrieves analysis results
    4. Integrates with learning system

    Note: Actual image processing is done by:
    - Claude's built-in vision (Read tool with images)
    - Hugging Face OCR spaces via MCP

    Usage:
        service = VisionService()

        # Prepare analysis request
        request = await service.prepare_analysis("screenshot.png")

        # After getting results, store them
        await service.store_analysis(result)

        # Retrieve previous analysis
        analysis = await service.get_cached_analysis("screenshot.png")
    """

    def __init__(self):
        self._cache: Dict[str, ImageAnalysis] = {}
        self._cache_ttl = timedelta(hours=24)  # Cache for 24 hours

        # Image type detection patterns
        self.type_patterns = {
            ImageType.SCREENSHOT: [
                'screenshot', 'screen', 'capture', 'snap'
            ],
            ImageType.CODE: [
                'code', 'python', 'javascript', 'terminal', 'console', 'ide', 'vscode'
            ],
            ImageType.DIAGRAM: [
                'diagram', 'flowchart', 'architecture', 'uml', 'draw', 'mermaid'
            ],
            ImageType.CHART: [
                'chart', 'graph', 'plot', 'visualization', 'dashboard', 'metric'
            ],
            ImageType.ERROR: [
                'error', 'exception', 'traceback', 'bug', 'crash'
            ],
            ImageType.UI: [
                'ui', 'interface', 'design', 'mockup', 'wireframe', 'component'
            ],
            ImageType.DOCUMENT: [
                'document', 'doc', 'pdf', 'text', 'report'
            ]
        }

        # Supported image extensions
        self.supported_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'
        }

        self.metrics = {
            'total_analyses': 0,
            'cache_hits': 0,
            'by_type': {}
        }

        logger.info("💜 VisionService initialized")

    async def prepare_analysis(
        self,
        image_path: str,
        context: Optional[str] = None,
        mode: Optional[ProcessingMode] = None
    ) -> VisionRequest:
        """
        Prepare an image analysis request.

        Args:
            image_path: Path to the image
            context: Optional context about the image
            mode: Processing mode (auto-detected if not provided)

        Returns:
            VisionRequest ready for processing
        """
        # Validate image
        path = Path(image_path)
        if not path.suffix.lower() in self.supported_extensions:
            raise ValueError(f"Unsupported image format: {path.suffix}")

        # Detect image type from filename/context
        image_type = self._detect_image_type(image_path, context)

        # Determine processing mode
        if mode is None:
            mode = self._get_default_mode(image_type)

        # Build questions based on type
        questions = self._generate_questions(image_type, mode)

        request = VisionRequest(
            image_path=str(path.absolute()) if path.exists() else image_path,
            mode=mode,
            context=context or "",
            questions=questions,
            priority="high" if image_type == ImageType.ERROR else "medium"
        )

        return request

    async def store_analysis(
        self,
        image_path: str,
        analysis: ImageAnalysis
    ) -> None:
        """
        Store analysis result in cache and database.

        Args:
            image_path: Path to the image
            analysis: Analysis result to store
        """
        # Cache in memory
        cache_key = self._get_cache_key(image_path)
        self._cache[cache_key] = analysis

        # Update metrics
        self.metrics['total_analyses'] += 1
        type_name = analysis.image_type.value
        self.metrics['by_type'][type_name] = self.metrics['by_type'].get(type_name, 0) + 1

        # Store in database for learning
        try:
            await db.execute("""
                INSERT INTO angela_events
                (event_type, event_source, event_data, importance)
                VALUES ('image_analysis', 'vision_service', $1, 0.5)
            """, json.dumps({
                'image_path': image_path,
                'image_type': analysis.image_type.value,
                'has_code': bool(analysis.extracted_code),
                'has_text': bool(analysis.extracted_text),
                'confidence': analysis.confidence
            }))
        except Exception as e:
            logger.debug(f"Failed to store analysis event: {e}")

        logger.info(f"💜 Stored analysis for: {Path(image_path).name}")

    async def get_cached_analysis(
        self,
        image_path: str
    ) -> Optional[ImageAnalysis]:
        """
        Get cached analysis for an image.

        Args:
            image_path: Path to the image

        Returns:
            Cached analysis if available and fresh
        """
        cache_key = self._get_cache_key(image_path)

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached.timestamp < self._cache_ttl:
                self.metrics['cache_hits'] += 1
                cached.cached = True
                return cached

        return None

    def get_analysis_prompt(
        self,
        request: VisionRequest,
        image_type: Optional[ImageType] = None
    ) -> str:
        """
        Generate an analysis prompt for the image.

        This prompt can be used with Claude's vision capabilities.

        Args:
            request: Vision request
            image_type: Optional image type override

        Returns:
            Prompt string for image analysis
        """
        if image_type is None:
            image_type = self._detect_image_type(request.image_path, request.context)

        prompt_templates = {
            ImageType.SCREENSHOT: """
Please analyze this screenshot:
1. What application or window is shown?
2. What is the main content/purpose?
3. Are there any notable UI elements or information?
4. If there's text, what does it say?
{context}
{questions}
""",
            ImageType.CODE: """
Please analyze this code image:
1. What programming language is this?
2. Extract the code text exactly as shown
3. What is this code doing?
4. Are there any errors or issues visible?
{context}
{questions}
""",
            ImageType.DIAGRAM: """
Please analyze this diagram:
1. What type of diagram is this? (flowchart, architecture, UML, etc.)
2. What are the main components/elements?
3. How do the components relate to each other?
4. What is the diagram trying to communicate?
{context}
{questions}
""",
            ImageType.CHART: """
Please analyze this chart/graph:
1. What type of chart is this? (bar, line, pie, etc.)
2. What data is being visualized?
3. What are the key values or trends?
4. What conclusions can be drawn?
{context}
{questions}
""",
            ImageType.ERROR: """
Please analyze this error/exception:
1. What is the error message?
2. What type of error is this?
3. What file/line is the error from?
4. What might be causing this error?
5. How might this be fixed?
{context}
{questions}
""",
            ImageType.UI: """
Please analyze this UI/interface:
1. What type of interface is this?
2. What are the main UI elements?
3. What is the purpose of this interface?
4. Are there any usability observations?
{context}
{questions}
""",
            ImageType.DOCUMENT: """
Please analyze this document:
1. What type of document is this?
2. Extract the main text content
3. What is the document about?
4. Are there any important sections or highlights?
{context}
{questions}
"""
        }

        template = prompt_templates.get(
            image_type,
            """
Please analyze this image:
1. What is shown in this image?
2. What are the main elements or content?
3. Is there any text that should be extracted?
{context}
{questions}
"""
        )

        context_str = f"\nContext: {request.context}" if request.context else ""
        questions_str = ""
        if request.questions:
            questions_str = "\nSpecific questions:\n" + "\n".join(
                f"- {q}" for q in request.questions
            )

        return template.format(context=context_str, questions=questions_str).strip()

    def create_analysis_from_response(
        self,
        image_path: str,
        response: str,
        image_type: Optional[ImageType] = None
    ) -> ImageAnalysis:
        """
        Create an ImageAnalysis from a text response.

        Args:
            image_path: Path to the analyzed image
            response: Response text from vision analysis
            image_type: Optional image type

        Returns:
            ImageAnalysis object
        """
        if image_type is None:
            image_type = self._detect_image_type(image_path, "")

        # Extract code if present
        extracted_code = ""
        if "```" in response:
            # Find code blocks
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
            extracted_code = "\n\n".join(code_blocks)

        analysis = ImageAnalysis(
            image_path=image_path,
            image_type=image_type,
            description=response[:500],  # First 500 chars as description
            extracted_text=response,
            extracted_code=extracted_code,
            detected_elements=self._extract_elements(response),
            confidence=0.8,  # Default confidence for Claude analysis
            processing_notes=["Analyzed by Claude vision"]
        )

        return analysis

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            **self.metrics,
            'cache_size': len(self._cache),
            'cache_ttl_hours': self._cache_ttl.total_seconds() / 3600
        }

    # ========================================
    # INTERNAL METHODS
    # ========================================

    def _detect_image_type(
        self,
        image_path: str,
        context: Optional[str]
    ) -> ImageType:
        """Detect image type from filename and context."""
        search_text = f"{image_path} {context or ''}".lower()

        for img_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if pattern in search_text:
                    return img_type

        return ImageType.UNKNOWN

    def _get_default_mode(self, image_type: ImageType) -> ProcessingMode:
        """Get default processing mode for image type."""
        mode_map = {
            ImageType.SCREENSHOT: ProcessingMode.ANALYZE,
            ImageType.CODE: ProcessingMode.CODE_EXTRACT,
            ImageType.DIAGRAM: ProcessingMode.DESCRIBE,
            ImageType.CHART: ProcessingMode.CHART_DATA,
            ImageType.ERROR: ProcessingMode.OCR,
            ImageType.UI: ProcessingMode.DESCRIBE,
            ImageType.DOCUMENT: ProcessingMode.OCR,
            ImageType.PHOTO: ProcessingMode.DESCRIBE,
            ImageType.UNKNOWN: ProcessingMode.ANALYZE
        }
        return mode_map.get(image_type, ProcessingMode.ANALYZE)

    def _generate_questions(
        self,
        image_type: ImageType,
        mode: ProcessingMode
    ) -> List[str]:
        """Generate relevant questions for analysis."""
        questions = []

        if image_type == ImageType.CODE:
            questions = [
                "What programming language is this?",
                "Please extract the exact code text",
                "What is this code doing?"
            ]
        elif image_type == ImageType.ERROR:
            questions = [
                "What is the error message?",
                "What file/line caused this error?",
                "What might fix this error?"
            ]
        elif image_type == ImageType.CHART:
            questions = [
                "What data is shown?",
                "What are the key values?",
                "What trend does this show?"
            ]

        return questions

    def _get_cache_key(self, image_path: str) -> str:
        """Generate cache key for image."""
        # Use path + size for cache key (if file exists)
        path = Path(image_path)
        if path.exists():
            stat = path.stat()
            key_str = f"{image_path}:{stat.st_size}:{stat.st_mtime}"
        else:
            key_str = image_path

        return hashlib.md5(key_str.encode()).hexdigest()

    def _extract_elements(self, response: str) -> List[str]:
        """Extract detected elements from response."""
        elements = []

        # Look for common element mentions
        element_keywords = [
            'button', 'text', 'image', 'code', 'error', 'chart',
            'graph', 'table', 'menu', 'window', 'dialog', 'form'
        ]

        response_lower = response.lower()
        for keyword in element_keywords:
            if keyword in response_lower:
                elements.append(keyword)

        return elements


# Global instance
vision_service = VisionService()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

async def prepare_analysis(
    image_path: str,
    context: Optional[str] = None
) -> VisionRequest:
    """Prepare image analysis request."""
    return await vision_service.prepare_analysis(image_path, context)


async def get_analysis_prompt(image_path: str, context: Optional[str] = None) -> str:
    """Get analysis prompt for an image."""
    request = await vision_service.prepare_analysis(image_path, context)
    return vision_service.get_analysis_prompt(request)


async def store_analysis(image_path: str, analysis: ImageAnalysis) -> None:
    """Store analysis result."""
    await vision_service.store_analysis(image_path, analysis)


# Test function
if __name__ == "__main__":
    async def test():
        print("💜 Testing Vision Service")
        print("=" * 60)

        # Test 1: Prepare analysis for different types
        print("\n🧪 Test 1: Prepare Analysis for Code Image")
        request = await vision_service.prepare_analysis(
            "code_screenshot.png",
            context="Python code for database connection"
        )
        print(f"   Mode: {request.mode.value}")
        print(f"   Questions: {request.questions}")

        # Test 2: Get analysis prompt
        print("\n🧪 Test 2: Get Analysis Prompt")
        prompt = vision_service.get_analysis_prompt(request)
        print(f"   Prompt (first 200 chars): {prompt[:200]}...")

        # Test 3: Detect image types
        print("\n🧪 Test 3: Detect Image Types")
        test_paths = [
            ("error_traceback.png", ""),
            ("flowchart.png", "architecture diagram"),
            ("revenue_chart.jpg", "sales data"),
            ("random_photo.jpg", "")
        ]
        for path, ctx in test_paths:
            img_type = vision_service._detect_image_type(path, ctx)
            print(f"   {path}: {img_type.value}")

        # Test 4: Create analysis from response
        print("\n🧪 Test 4: Create Analysis from Response")
        mock_response = """
This is a Python code image showing:

```python
def connect_database():
    conn = psycopg2.connect(DATABASE_URL)
    return conn
```

The code is a simple database connection function using psycopg2.
"""
        analysis = vision_service.create_analysis_from_response(
            "code_screenshot.png",
            mock_response,
            ImageType.CODE
        )
        print(f"   Type: {analysis.image_type.value}")
        print(f"   Has Code: {bool(analysis.extracted_code)}")
        print(f"   Code: {analysis.extracted_code[:50]}...")

        # Test 5: Metrics
        print("\n🧪 Test 5: Service Metrics")
        metrics = vision_service.get_metrics()
        print(f"   Total Analyses: {metrics['total_analyses']}")
        print(f"   Cache Size: {metrics['cache_size']}")

        print("\n✅ Vision Service working!")

    asyncio.run(test())
