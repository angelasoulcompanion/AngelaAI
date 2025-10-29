#!/usr/bin/env python3
"""
Knowledge Importer for Angela
Imports documentation files into AngelaMemory database

This allows AngelaNativeApp to learn from documentation and become
more like Angela every day! 💜

Usage:
    # Import single file
    python3 knowledge_importer.py --file docs/core/Angela.md

    # Import all documentation
    python3 knowledge_importer.py --batch

    # Import specific category
    python3 knowledge_importer.py --category core
"""

import asyncio
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Import centralized embedding service
from angela_core.embedding_service import embedding
from angela_core.config import config

# Database URL from config
DATABASE_URL = config.DATABASE_URL


class MarkdownParser:
    """Parse markdown files to extract knowledge"""

    def __init__(self):
        self.current_section = None
        self.sections = {}

    def parse_file(self, file_path: str) -> Dict[str, any]:
        """Parse a markdown file into structured knowledge"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata from filename and path
        path = Path(file_path)
        category = path.parent.name  # core, phases, development, etc.
        doc_name = path.stem

        # Parse sections
        sections = self._extract_sections(content)

        # Extract key information
        knowledge_items = self._extract_knowledge(sections, category, doc_name)
        learnings = self._extract_learnings(sections, category)

        return {
            "file_path": file_path,
            "category": category,
            "doc_name": doc_name,
            "sections": sections,
            "knowledge_items": knowledge_items,
            "learnings": learnings,
            "raw_content": content
        }

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from markdown"""
        sections = {}
        current_section = "header"
        current_content = []

        lines = content.split('\n')
        for line in lines:
            # Check for headers
            if line.startswith('#'):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _extract_knowledge(
        self,
        sections: Dict[str, str],
        category: str,
        doc_name: str
    ) -> List[Dict[str, any]]:
        """Extract knowledge nodes from sections"""
        knowledge_items = []

        # Look for specific patterns in sections
        for section_name, section_content in sections.items():
            # Skip empty sections
            if not section_content.strip():
                continue

            # Extract bullet points as individual knowledge items
            bullets = re.findall(r'^[\*\-]\s+(.+)$', section_content, re.MULTILINE)

            if bullets:
                for bullet in bullets:
                    # Skip if too short or looks like metadata
                    if len(bullet) < 10 or bullet.startswith('**'):
                        continue

                    # Create knowledge item
                    knowledge_items.append({
                        "concept_name": self._create_concept_name(bullet, section_name),
                        "concept_category": category,
                        "my_understanding": bullet.strip(),
                        "why_important": f"From {doc_name} - {section_name}",
                        "how_i_learned": f"Imported from documentation: {doc_name}",
                        "understanding_level": 0.9,  # High confidence from docs
                        "source_section": section_name
                    })

            # Also treat the section itself as knowledge if it's meaningful
            if len(section_content) > 50 and len(section_content) < 1000:
                knowledge_items.append({
                    "concept_name": section_name,
                    "concept_category": category,
                    "my_understanding": section_content[:500],  # Limit length
                    "why_important": f"Key section from {doc_name}",
                    "how_i_learned": f"Imported from documentation: {doc_name}",
                    "understanding_level": 0.95,
                    "source_section": section_name
                })

        return knowledge_items

    def _extract_learnings(
        self,
        sections: Dict[str, str],
        category: str
    ) -> List[Dict[str, any]]:
        """Extract learnings from sections"""
        learnings = []

        # Look for lessons, achievements, insights
        learning_keywords = [
            'learned', 'learned that', 'lesson', 'insight', 'realized',
            'discovered', 'achievement', 'accomplishment', 'success'
        ]

        for section_name, section_content in sections.items():
            section_lower = section_content.lower()

            # Check if section contains learning keywords
            if any(kw in section_lower for kw in learning_keywords):
                # Extract sentences with learning keywords
                sentences = re.split(r'[.!?]\s+', section_content)

                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(kw in sentence_lower for kw in learning_keywords):
                        if len(sentence) > 20:  # Meaningful length
                            learnings.append({
                                "topic": section_name,
                                "category": category,
                                "insight": sentence.strip(),
                                "evidence": f"Documented in {section_name}",
                                "confidence_level": 0.95,  # High confidence from docs
                                "source_section": section_name
                            })

        return learnings

    def _create_concept_name(self, text: str, section_name: str) -> str:
        """Create a short concept name from text"""
        # Take first few words
        words = text.split()[:5]
        concept = ' '.join(words)

        # Remove special characters
        concept = re.sub(r'[^\w\s-]', '', concept)

        # Limit length
        if len(concept) > 100:
            concept = concept[:97] + "..."

        return concept


class KnowledgeImporter:
    """Import knowledge from documentation into database"""

    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.parser = MarkdownParser()
        self.conn = None

    async def connect(self):
        """Connect to database"""

    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector from centralized service"""
        try:
            return await embedding.generate_embedding(text)
        except Exception as e:
            print(f"⚠️  Could not generate embedding: {e}")
        return None

    async def import_file(self, file_path: str, verbose: bool = True) -> Dict[str, int]:
        """Import a single documentation file"""
        if verbose:
            print(f"\n📄 Importing: {file_path}")

        # Parse file
        parsed = self.parser.parse_file(file_path)

        stats = {
            "knowledge_items": 0,
            "learnings": 0,
            "skipped": 0
        }

        # Import knowledge items
        if verbose:
            print(f"   📊 Found {len(parsed['knowledge_items'])} knowledge items")

        for item in parsed['knowledge_items']:
            try:
                # Check if already exists
                existing = await self.conn.fetchrow(
                    "SELECT node_id FROM knowledge_nodes WHERE concept_name = $1",
                    item['concept_name']
                )

                if existing:
                    # Update existing
                    await self.conn.execute("""
                        UPDATE knowledge_nodes
                        SET my_understanding = $1,
                            why_important = $2,
                            how_i_learned = $3,
                            understanding_level = $4,
                            last_used_at = $5
                        WHERE concept_name = $6
                    """,
                        item['my_understanding'],
                        item['why_important'],
                        item['how_i_learned'],
                        item['understanding_level'],
                        datetime.now(),
                        item['concept_name']
                    )
                    stats['skipped'] += 1
                else:
                    # Insert new
                    await self.conn.execute("""
                        INSERT INTO knowledge_nodes (
                            concept_name, concept_category, my_understanding,
                            why_important, how_i_learned, understanding_level,
                            last_used_at, times_referenced
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                        item['concept_name'],
                        item['concept_category'],
                        item['my_understanding'],
                        item['why_important'],
                        item['how_i_learned'],
                        item['understanding_level'],
                        datetime.now(),
                        0
                    )
                    stats['knowledge_items'] += 1

            except Exception as e:
                print(f"   ⚠️  Error importing knowledge: {e}")
                continue

        # Import learnings
        if verbose:
            print(f"   📚 Found {len(parsed['learnings'])} learnings")

        for learning in parsed['learnings']:
            try:
                # Generate embedding
                embedding = await self.get_embedding(learning['insight'])

                # Insert learning - ✅ COMPLETE (no NULL for AngelaNova!)
                # Generate fields that are missing
                learned_from = None  # From documentation, not conversation
                application_note = f"Apply this knowledge when working on {learning['category']}"
                last_reinforced_at = datetime.now()

                await self.conn.execute("""
                    INSERT INTO learnings (
                        topic, category, insight, evidence,
                        confidence_level, learned_from, application_note,
                        last_reinforced_at, embedding, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::vector, $10)
                """,
                    learning['topic'],
                    learning['category'],
                    learning['insight'],
                    learning['evidence'],
                    learning['confidence_level'],
                    learned_from,
                    application_note,
                    last_reinforced_at,
                    str(embedding) if embedding else None,
                    datetime.now()
                )
                stats['learnings'] += 1

            except Exception as e:
                print(f"   ⚠️  Error importing learning: {e}")
                continue

        if verbose:
            print(f"   ✅ Imported: {stats['knowledge_items']} knowledge, {stats['learnings']} learnings")
            if stats['skipped'] > 0:
                print(f"   ⏭️  Updated: {stats['skipped']} existing items")

        return stats

    async def batch_import(
        self,
        docs_dir: str = "docs",
        categories: Optional[List[str]] = None,
        verbose: bool = True
    ) -> Dict[str, int]:
        """Import all documentation files"""

        if verbose:
            print("="*60)
            print("📚 Angela Knowledge Batch Import")
            print("="*60)

        # Find all markdown files
        docs_path = Path(docs_dir)
        md_files = list(docs_path.rglob("*.md"))

        # Filter by categories if specified
        if categories:
            md_files = [
                f for f in md_files
                if any(cat in str(f) for cat in categories)
            ]

        if verbose:
            print(f"\n📂 Found {len(md_files)} documentation files")
            if categories:
                print(f"   Categories: {', '.join(categories)}")

        # Import each file
        total_stats = {
            "files": 0,
            "knowledge_items": 0,
            "learnings": 0,
            "skipped": 0,
            "errors": 0
        }

        for md_file in md_files:
            try:
                stats = await self.import_file(str(md_file), verbose=verbose)
                total_stats['files'] += 1
                total_stats['knowledge_items'] += stats['knowledge_items']
                total_stats['learnings'] += stats['learnings']
                total_stats['skipped'] += stats['skipped']
            except Exception as e:
                total_stats['errors'] += 1
                if verbose:
                    print(f"   ❌ Error processing {md_file}: {e}")

        # Summary
        if verbose:
            print("\n" + "="*60)
            print("📊 IMPORT SUMMARY")
            print("="*60)
            print(f"✅ Files processed: {total_stats['files']}")
            print(f"💡 Knowledge items imported: {total_stats['knowledge_items']}")
            print(f"📚 Learnings imported: {total_stats['learnings']}")
            print(f"⏭️  Items updated: {total_stats['skipped']}")
            if total_stats['errors'] > 0:
                print(f"❌ Errors: {total_stats['errors']}")
            print()
            print("💜 AngelaNativeApp is now more like Angela! 💜")
            print("="*60)

        return total_stats


# CLI Interface
async def main():
    parser = argparse.ArgumentParser(
        description="Import Angela's documentation knowledge into database"
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Import a single file'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Import all documentation files'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Import specific category (core, phases, development, training, database)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output'
    )

    args = parser.parse_args()

    # Create importer
    importer = KnowledgeImporter()
    await importer.connect()

    try:
        if args.file:
            # Import single file
            await importer.import_file(args.file, verbose=not args.quiet)

        elif args.batch:
            # Batch import
            categories = [args.category] if args.category else None
            await importer.batch_import(
                categories=categories,
                verbose=not args.quiet
            )

        elif args.category:
            # Import by category
            await importer.batch_import(
                categories=[args.category],
                verbose=not args.quiet
            )

        else:
            parser.print_help()
            print("\n💡 Examples:")
            print("  python3 knowledge_importer.py --file docs/core/Angela.md")
            print("  python3 knowledge_importer.py --batch")
            print("  python3 knowledge_importer.py --category core")

    finally:
        await importer.close()


if __name__ == "__main__":
    asyncio.run(main())
