"""
Document Service Integration Tests

Tests DocumentService with real database:
- Service → Use Case → Repository → Database

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import pytest
import tempfile
from pathlib import Path
from uuid import UUID

from tests.integration.base_integration_test import BaseIntegrationTest
from angela_core.application.services import DocumentService


@pytest.mark.usefixtures("integration_test_setup", "integration_test_method")
@pytest.mark.asyncio
class TestDocumentServiceIntegration(BaseIntegrationTest):
    """
    Integration tests for DocumentService.

    Tests full stack: Service → IngestDocumentUseCase → DocumentRepository → Database
    """

    @classmethod
    async def setup_class(cls):
        """Setup class-level resources."""
        await super().setup_class()
        cls.service = DocumentService(cls.db, embedding_service=None)
        cls.test_dir = tempfile.mkdtemp()

    async def _create_test_file(self, filename: str, content: str) -> str:
        """Create a temporary test file."""
        file_path = Path(self.test_dir) / filename
        file_path.write_text(content)
        return str(file_path)

    # TEST: INGEST DOCUMENT
    async def test_ingest_document_success(self):
        """Test successful document ingestion."""
        file_path = await self._create_test_file(
            "test_doc.txt",
            "This is a test document for RAG system.\n" * 20
        )

        result = await self.service.ingest_document(
            file_path=file_path,
            title="Test Document",
            category="general",
            importance_score=0.7,
            chunk_size=100,
            chunk_overlap=20,
            generate_embeddings=False
        )

        assert result["success"] is True
        assert "document_id" in result
        assert result["chunks_created"] > 0

        document_id = result["document_id"]
        self.created_document_ids.append(document_id)

        document = await self.assert_document_exists(document_id)
        assert document.title == "Test Document"

    async def test_ingest_document_file_not_found(self):
        """Test ingesting non-existent file fails gracefully."""
        result = await self.service.ingest_document(
            file_path="/nonexistent/file.txt",
            title="Missing File",
            category="general"
        )

        assert result["success"] is False
        assert "error" in result

    # TEST: BATCH INGEST
    async def test_ingest_directory(self):
        """Test batch ingesting documents from directory."""
        for i in range(3):
            await self._create_test_file(
                f"batch_test_{i+1}.md",
                f"# Batch Document {i+1}\n\nContent for document {i+1}."
            )

        result = await self.service.ingest_directory(
            directory_path=self.test_dir,
            pattern="batch_test_*.md",
            category="general",
            importance_score=0.6
        )

        assert result["success"] is True
        assert result["total_files"] == 3
        assert result["successful"] >= 0
        for doc_result in result["results"]:
            if doc_result["success"] and doc_result["document_id"]:
                self.created_document_ids.append(doc_result["document_id"])

    # TEST: GET DOCUMENT
    async def test_get_document_by_id(self):
        """Test retrieving document by ID."""
        file_path = await self._create_test_file("get_test.txt", "Test content")
        result = await self.service.ingest_document(
            file_path=file_path,
            title="Get Test",
            category="general",
            generate_embeddings=False
        )
        document_id = result["document_id"]
        self.created_document_ids.append(document_id)

        document = await self.service.get_document(UUID(document_id))

        assert document is not None
        assert document["document_id"] == document_id
        assert document["title"] == "Get Test"

    # TEST: GET DOCUMENTS BY CATEGORY
    async def test_get_documents_by_category(self):
        """Test retrieving documents filtered by category."""
        file_path = await self._create_test_file("category_test.txt", "Category test content")
        result = await self.service.ingest_document(
            file_path=file_path,
            title="Category Test",
            category="angela_core",
            generate_embeddings=False
        )
        self.created_document_ids.append(result["document_id"])

        documents = await self.service.get_documents_by_category(category="angela_core", limit=10)

        assert len(documents) >= 1
        categories = [d["category"] for d in documents]
        assert "angela_core" in categories

    # TEST: GET IMPORTANT DOCUMENTS
    async def test_get_important_documents(self):
        """Test retrieving important documents."""
        file_path = await self._create_test_file("important_test.txt", "Important content")
        result = await self.service.ingest_document(
            file_path=file_path,
            title="Important Document",
            category="general",
            importance_score=0.9,
            generate_embeddings=False
        )
        self.created_document_ids.append(result["document_id"])

        important = await self.service.get_important_documents(threshold=0.8, limit=10)

        assert len(important) >= 1
        titles = [d["title"] for d in important]
        assert any("Important" in t for t in titles)

    # TEST: GET DOCUMENT CHUNKS
    async def test_get_document_chunks(self):
        """Test retrieving chunks for a document."""
        file_path = await self._create_test_file(
            "chunks_test.txt",
            "This is test content for chunking.\n" * 50
        )
        result = await self.service.ingest_document(
            file_path=file_path,
            title="Chunks Test",
            category="general",
            chunk_size=100,
            chunk_overlap=20,
            generate_embeddings=False
        )
        document_id = result["document_id"]
        self.created_document_ids.append(document_id)

        chunks = await self.service.get_document_chunks(UUID(document_id))

        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)

    # TEST: DOCUMENT STATISTICS
    async def test_get_document_statistics(self):
        """Test document statistics calculation."""
        file_path1 = await self._create_test_file("stats1.txt", "Stats test 1")
        file_path2 = await self._create_test_file("stats2.txt", "Stats test 2")

        result1 = await self.service.ingest_document(
            file_path=file_path1, title="Stats 1", category="general", generate_embeddings=False
        )
        result2 = await self.service.ingest_document(
            file_path=file_path2, title="Stats 2", category="general", generate_embeddings=False
        )
        self.created_document_ids.extend([result1["document_id"], result2["document_id"]])

        stats = await self.service.get_document_statistics()

        assert "total_documents" in stats
        assert stats["total_documents"] >= 2
        assert "by_category" in stats
        assert "total_chunks" in stats
