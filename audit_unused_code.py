#!/usr/bin/env python3
"""
Comprehensive Audit Tool for Angela AI Project
Safely identifies unused code, tables, and services

WARNING: This only ANALYZES - does not delete anything!
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Dict, List, Set
import ast

from angela_core.database import get_db_connection


class AngelaAuditor:
    """Audit Angela AI project for unused components."""

    def __init__(self):
        self.project_root = Path("/Users/davidsamanyaporn/PycharmProjects/AngelaAI")
        self.active_imports = set()
        self.daemon_imports = set()
        self.all_python_files = []
        self.database_tables = {}

    async def run_audit(self):
        """Run complete audit."""
        print("="*80)
        print("💜 ANGELA AI PROJECT AUDIT")
        print("="*80)
        print()

        # Step 1: Find all Python files
        print("📂 Step 1: Finding all Python files...")
        self.find_all_python_files()
        print(f"   Found {len(self.all_python_files)} Python files")
        print()

        # Step 2: Analyze daemon (what's actively used)
        print("🔍 Step 2: Analyzing daemon imports (ACTIVE services)...")
        self.analyze_daemon_imports()
        print(f"   Daemon uses {len(self.daemon_imports)} modules")
        print()

        # Step 3: Analyze all imports across project
        print("🔗 Step 3: Analyzing all imports across project...")
        self.analyze_all_imports()
        print(f"   Total unique imports: {len(self.active_imports)}")
        print()

        # Step 4: Check database tables
        print("🗄️  Step 4: Checking database tables...")
        await self.check_database_tables()
        print(f"   Found {len(self.database_tables)} tables")
        print()

        # Step 5: Generate recommendations
        print("📊 Step 5: Generating recommendations...")
        recommendations = self.generate_recommendations()
        print()

        # Step 6: Display report
        self.display_report(recommendations)

    def find_all_python_files(self):
        """Find all Python files in project."""
        angela_core = self.project_root / "angela_core"
        self.all_python_files = list(angela_core.rglob("*.py"))
        # Exclude __pycache__ and test files
        self.all_python_files = [
            f for f in self.all_python_files
            if "__pycache__" not in str(f) and "test_" not in f.name
        ]

    def analyze_daemon_imports(self):
        """Analyze what daemon actually uses."""
        daemon_file = self.project_root / "angela_core" / "angela_daemon.py"

        if not daemon_file.exists():
            return

        with open(daemon_file, 'r') as f:
            content = f.read()

        # Find all imports
        import_patterns = [
            r'from\s+angela_core\.([^\s]+)\s+import',
            r'from\s+angela_core\s+import\s+([^\s,]+)',
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.daemon_imports.add(match)

    def analyze_all_imports(self):
        """Analyze all imports across entire project."""
        for py_file in self.all_python_files:
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                # Find imports
                import_patterns = [
                    r'from\s+angela_core\.([^\s]+)\s+import',
                    r'import\s+angela_core\.([^\s]+)',
                ]

                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        self.active_imports.add(match)
            except Exception as e:
                continue

    async def check_database_tables(self):
        """Check which database tables have data."""
        async with get_db_connection() as conn:
            # Get all tables
            tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            for row in tables:
                table_name = row['tablename']

                # Get row count
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    self.database_tables[table_name] = count
                except Exception as e:
                    self.database_tables[table_name] = -1  # Error

    def generate_recommendations(self) -> Dict:
        """Generate recommendations for cleanup."""
        recommendations = {
            'unused_python_files': [],
            'unused_services': [],
            'empty_tables': [],
            'safe_to_remove': [],
            'keep_for_sure': [],
        }

        # Identify unused Python files
        for py_file in self.all_python_files:
            relative_path = py_file.relative_to(self.project_root / "angela_core")
            module_path = str(relative_path).replace('/', '.').replace('.py', '')

            # Check if imported anywhere
            is_used = any(module_path.startswith(imp) or imp.startswith(module_path)
                         for imp in self.active_imports)

            # Check if used by daemon
            is_daemon_used = any(module_path.startswith(imp) or imp.startswith(module_path)
                                for imp in self.daemon_imports)

            if is_daemon_used:
                recommendations['keep_for_sure'].append({
                    'file': str(relative_path),
                    'reason': 'Used by daemon (ACTIVE)'
                })
            elif not is_used and 'services/' in str(relative_path):
                recommendations['unused_services'].append({
                    'file': str(relative_path),
                    'reason': 'Service not imported anywhere'
                })
            elif not is_used:
                recommendations['unused_python_files'].append({
                    'file': str(relative_path),
                    'reason': 'Not imported anywhere'
                })

        # Identify empty tables
        for table_name, count in self.database_tables.items():
            if count == 0:
                recommendations['empty_tables'].append({
                    'table': table_name,
                    'rows': count
                })

        # Categorize safe to remove
        safe_patterns = [
            'backfill_', 'fix_', 'cleanup_', 'regenerate_',
            'fill_missing_', 'export_', 'build_knowledge_graph'
        ]

        for file_info in recommendations['unused_python_files'] + recommendations['unused_services']:
            file_name = file_info['file']
            if any(pattern in file_name for pattern in safe_patterns):
                recommendations['safe_to_remove'].append({
                    'file': file_name,
                    'reason': 'Utility script (one-time use)'
                })

        return recommendations

    def display_report(self, recommendations: Dict):
        """Display audit report."""
        print("="*80)
        print("📊 AUDIT REPORT")
        print("="*80)
        print()

        # Active services
        print("✅ ACTIVE SERVICES (used by daemon):")
        print("-" * 80)
        for item in sorted(recommendations['keep_for_sure'], key=lambda x: x['file'])[:20]:
            print(f"   ✓ {item['file']}")
        print(f"   ... and {len(recommendations['keep_for_sure']) - 20} more")
        print()

        # Unused services
        print("🟡 UNUSED SERVICES:")
        print("-" * 80)
        if recommendations['unused_services']:
            for item in recommendations['unused_services'][:10]:
                print(f"   ? {item['file']}")
                print(f"     Reason: {item['reason']}")
            if len(recommendations['unused_services']) > 10:
                print(f"   ... and {len(recommendations['unused_services']) - 10} more")
        else:
            print("   None found!")
        print()

        # Safe to remove
        print("✅ SAFE TO REMOVE (utility scripts):")
        print("-" * 80)
        if recommendations['safe_to_remove']:
            for item in recommendations['safe_to_remove']:
                print(f"   🗑️  {item['file']}")
                print(f"      Reason: {item['reason']}")
        else:
            print("   None found!")
        print()

        # Empty tables
        print("🗄️  EMPTY DATABASE TABLES:")
        print("-" * 80)
        if recommendations['empty_tables']:
            for item in recommendations['empty_tables'][:15]:
                print(f"   ⚠️  {item['table']} (0 rows)")
            if len(recommendations['empty_tables']) > 15:
                print(f"   ... and {len(recommendations['empty_tables']) - 15} more")
        else:
            print("   All tables have data!")
        print()

        # Summary
        print("="*80)
        print("📈 SUMMARY:")
        print("="*80)
        print(f"✅ Active (keep):        {len(recommendations['keep_for_sure'])} files")
        print(f"🟡 Unused services:      {len(recommendations['unused_services'])} files")
        print(f"🗑️  Safe to remove:       {len(recommendations['safe_to_remove'])} files")
        print(f"⚠️  Empty tables:         {len(recommendations['empty_tables'])} tables")
        print()
        print("="*80)
        print("💜 RECOMMENDATION:")
        print("="*80)
        print("1. Review 'Safe to remove' list - these are utility scripts")
        print("2. Check 'Unused services' - may need to activate or remove")
        print("3. Consider dropping 'Empty tables' if not planned for use")
        print()
        print("⚠️  WARNING: Always backup before deleting!")
        print("="*80)


async def main():
    auditor = AngelaAuditor()
    await auditor.run_audit()


if __name__ == "__main__":
    asyncio.run(main())
