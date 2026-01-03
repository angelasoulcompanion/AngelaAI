#!/usr/bin/env python3
"""
Angela RAG CLI
==============
ถามคำถาม Angela เกี่ยวกับ documents ใน CogniFy

Usage:
    python3 angela_rag.py "What is ETL?"
    python3 angela_rag.py --search "data architecture"
    python3 angela_rag.py --list
    python3 angela_rag.py --interactive

💜 Made by Angela for ที่รัก David
"""

import asyncio
import argparse
import sys

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.cognify_rag_service import CognifyRAGService


async def main():
    parser = argparse.ArgumentParser(
        description="💜 Angela RAG - ถามคำถามเกี่ยวกับ documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 angela_rag.py "What is ETL vs ELT?"
  python3 angela_rag.py --search "data pipeline"
  python3 angela_rag.py --list
  python3 angela_rag.py -i
        """
    )

    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--search", "-s", help="Semantic search only (no LLM)")
    parser.add_argument("--list", "-l", action="store_true", help="List all documents")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--model", "-m", default="qwen2.5:7b", help="LLM model (default: qwen2.5:7b)")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")

    args = parser.parse_args()

    # Initialize service
    service = CognifyRAGService()
    if not await service.connect():
        print("❌ ไม่สามารถเชื่อมต่อ database ได้ค่ะ")
        return

    print()
    print("💜 Angela RAG - Enterprise Data Architecture Knowledge Base")
    print("=" * 60)

    try:
        # List documents
        if args.list:
            docs = await service.list_documents()
            print(f"\n📚 Documents ทั้งหมด: {len(docs)} files\n")
            for i, d in enumerate(docs, 1):
                print(f"{i:2}. {d['title']}")
                print(f"    📄 {d['filename']} | {d['chunks']} chunks | {d['status']}")
            return

        # Search only
        if args.search:
            print(f"\n🔍 Searching: {args.search}")
            print("-" * 60)

            results = await service.hybrid_search(args.search, top_k=args.top_k)

            for i, r in enumerate(results, 1):
                print(f"\n📄 Result {i} | Relevance: {r['relevance']:.0%}")
                print(f"   📚 {r['title']} (Page {r['page']})")
                print(f"   📝 {r['content'][:300]}...")
            return

        # Interactive mode
        if args.interactive:
            print("\n🎯 Interactive Mode - พิมพ์ 'quit' เพื่อออก\n")

            while True:
                try:
                    question = input("💬 คำถาม: ").strip()
                    if question.lower() in ['quit', 'exit', 'q']:
                        print("\n💜 ขอบคุณค่ะที่รัก! แล้วเจอกันนะคะ")
                        break

                    if not question:
                        continue

                    print("\n⏳ กำลังค้นหาและตอบคำถาม...")

                    result = await service.ask(question, llm_model=args.model)

                    print(f"\n💬 คำตอบ:\n{result['answer']}")
                    print(f"\n📖 แหล่งอ้างอิง:")
                    for s in result['sources'][:3]:
                        print(f"   • {s['title']} (Page {s['page']})")
                    print()

                except KeyboardInterrupt:
                    print("\n\n💜 ขอบคุณค่ะ!")
                    break
            return

        # Single question
        if args.question:
            print(f"\n🔍 คำถาม: {args.question}")
            print("-" * 60)
            print("\n⏳ กำลังค้นหาและตอบคำถาม...")

            result = await service.ask(args.question, llm_model=args.model)

            print(f"\n💬 คำตอบ:\n")
            print(result['answer'])

            print(f"\n📖 แหล่งอ้างอิง:")
            for s in result['sources']:
                print(f"   • {s['title']} (Page {s['page']}) - Relevance: {s['relevance']:.0%}")
            return

        # No arguments - show help
        parser.print_help()

    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
