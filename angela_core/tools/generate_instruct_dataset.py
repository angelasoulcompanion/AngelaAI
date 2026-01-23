#!/usr/bin/env python3
"""
Generate Instruct Dataset CLI Tool

Generates high-quality training datasets from Angela conversations.
Part of LLM Twin Phase 1.

Usage:
    python generate_instruct_dataset.py --help
    python generate_instruct_dataset.py --dry-run
    python generate_instruct_dataset.py --min-quality 7.0 --format messages
    python generate_instruct_dataset.py --output-dir ./datasets --export

Author: Angela 💜
Created: 2026-01-18
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.services.instruct_dataset_service import (
    InstructDatasetService,
    DatasetConfig
)
from angela_core.services.instruct_quality_scorer import InstructQualityScorer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print tool banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  💜 Angela Instruct Dataset Generator                        ║
║  LLM Twin Phase 1 - Training Data Generation                 ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_stats(stats: dict):
    """Print conversation statistics."""
    print("\n📊 Database Statistics:")
    print("─" * 50)
    print(f"  Total Conversations:    {stats.get('total_conversations', 0):,}")
    print(f"  David's Messages:       {stats.get('david_messages', 0):,}")
    print(f"  Angela's Messages:      {stats.get('angela_messages', 0):,}")
    print(f"  High Importance (>=7):  {stats.get('high_importance', 0):,}")
    print(f"  Very High (>=8):        {stats.get('very_high_importance', 0):,}")
    print(f"  Average Importance:     {stats.get('avg_importance', 0):.2f}")
    print("─" * 50)


def print_quality_summary(summary: dict):
    """Print quality score summary."""
    print("\n📈 Quality Score Distribution:")
    print("─" * 50)
    print(f"  Average Score:    {summary.get('avg_total', 0):.2f}/10")
    print(f"  Min Score:        {summary.get('min_total', 0):.2f}/10")
    print(f"  Max Score:        {summary.get('max_total', 0):.2f}/10")
    print()
    print("  By Dimension (avg):")
    print(f"    Relevance:    {summary.get('avg_relevance', 0):.2f}/2")
    print(f"    Emotional:    {summary.get('avg_emotional', 0):.2f}/2")
    print(f"    Personality:  {summary.get('avg_personality', 0):.2f}/2")
    print(f"    Technical:    {summary.get('avg_technical', 0):.2f}/2")
    print(f"    Flow:         {summary.get('avg_flow', 0):.2f}/2")
    print()
    print("  Quality Levels:")
    print(f"    Excellent (>=9): {summary.get('excellent_count', 0)}")
    print(f"    Good (7-9):      {summary.get('good_count', 0)}")
    print(f"    Acceptable (5-7):{summary.get('acceptable_count', 0)}")
    print(f"    Poor (<5):       {summary.get('poor_count', 0)}")
    print("─" * 50)


def print_result(result: dict):
    """Print generation result."""
    print("\n✅ Dataset Generation Complete!")
    print("─" * 50)
    print(f"  Dataset ID:         {result.get('dataset_id', 'N/A')}")
    print(f"  Total Pairs:        {result.get('total_pairs', 0):,}")
    print(f"  Scored Pairs:       {result.get('scored_pairs', 0):,}")
    print(f"  High Quality:       {result.get('high_quality_pairs', 0):,}")
    print()
    print(f"  Train Examples:     {result.get('train_count', 0):,}")
    print(f"  Test Examples:      {result.get('test_count', 0):,}")
    print("─" * 50)

    # Quality breakdown
    if 'quality_summary' in result:
        print_quality_summary(result['quality_summary'])


async def run_dry_run(service: InstructDatasetService, args):
    """Run dry-run mode (no export)."""
    print("\n🔍 DRY RUN MODE - Analyzing data without generating files\n")

    # Get stats
    stats = await service.get_conversation_stats()
    print_stats(stats)

    # Extract sample pairs
    print("\n📥 Extracting sample pairs...")
    pairs = await service.extract_conversation_pairs(
        min_importance=args.min_importance,
        limit=50  # Sample only
    )

    print(f"   Found {len(pairs)} sample pairs")

    if not pairs:
        print("\n⚠️ No pairs found with current filters!")
        return

    # Score sample
    print("\n📊 Scoring sample pairs...")
    scored_pairs = await service.score_pairs(pairs)

    # Get summary
    scores = [s for _, s in scored_pairs]
    summary = service.scorer.get_quality_summary(scores)

    print_quality_summary(summary)

    # Show examples
    print("\n📝 Sample High-Quality Pairs:")
    print("─" * 50)

    high_quality = [(p, s) for p, s in scored_pairs if s.total >= args.min_quality]
    for pair, score in high_quality[:3]:
        print(f"\n  Score: {score.total:.2f}/10")
        print(f"  David: {pair.david_message[:80]}...")
        print(f"  Angela: {pair.angela_response[:80]}...")

    # Estimates
    estimated_total = int(stats.get('david_messages', 0) * 0.4)  # ~40% can be paired
    estimated_hq = int(estimated_total * (summary['good_count'] + summary['excellent_count']) / max(1, len(scored_pairs)))

    print("\n📊 Estimated Full Dataset:")
    print("─" * 50)
    print(f"  Estimated Total Pairs:     ~{estimated_total:,}")
    print(f"  Estimated High-Quality:    ~{estimated_hq:,}")
    print(f"  Estimated Train (85%):     ~{int(estimated_hq * 0.85):,}")
    print(f"  Estimated Test (15%):      ~{int(estimated_hq * 0.15):,}")
    print("─" * 50)

    print("\n💡 To generate the full dataset, run without --dry-run")


async def run_generate(service: InstructDatasetService, args):
    """Run full dataset generation."""
    print(f"\n🚀 Generating dataset with config:")
    print(f"   Min Quality:    {args.min_quality}")
    print(f"   Min Importance: {args.min_importance}")
    print(f"   Format:         {args.format}")
    print(f"   Train Ratio:    {args.train_ratio}")

    if args.max_pairs:
        print(f"   Max Pairs:      {args.max_pairs}")

    # Create config
    config = DatasetConfig(
        min_quality=args.min_quality,
        min_importance=args.min_importance,
        train_ratio=args.train_ratio,
        max_pairs=args.max_pairs,
        include_system_prompt=args.include_system_prompt,
        format=args.format,
        random_seed=args.seed
    )

    # Generate dataset
    result = await service.generate_dataset(config)

    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return

    print_result(result)

    # Export if requested
    if args.export:
        print("\n📁 Exporting to files...")
        files = await service.export_to_jsonl(
            result,
            output_dir=args.output_dir,
            dataset_name=args.name
        )

        print(f"\n✅ Files exported:")
        print(f"   Train: {files['train_file']}")
        print(f"   Test:  {files['test_file']}")

    # Show samples
    if args.show_samples and result.get('train_data'):
        print("\n📝 Sample Training Examples:")
        print("─" * 50)

        for i, item in enumerate(result['train_data'][:3], 1):
            messages = item.get('messages', [])
            user_msg = next((m['content'] for m in messages if m['role'] == 'user'), '')
            asst_msg = next((m['content'] for m in messages if m['role'] == 'assistant'), '')

            print(f"\n  Example {i} (score: {item.get('_metadata', {}).get('quality_score', 0):.2f}):")
            print(f"  User: {user_msg[:80]}...")
            print(f"  Assistant: {asst_msg[:80]}...")


async def run_stats_only(service: InstructDatasetService):
    """Show stats only."""
    stats = await service.get_conversation_stats()
    print_stats(stats)

    # Dataset history
    print("\n📚 Recent Datasets:")
    print("─" * 50)

    history = await service.get_dataset_history(limit=5)

    if not history:
        print("  No datasets generated yet.")
    else:
        for ds in history:
            status_emoji = "✅" if ds['status'] == 'completed' else "⏳"
            print(f"  {status_emoji} {ds['dataset_name']}")
            print(f"     Train: {ds['train_examples']} | Test: {ds['test_examples']} | Avg: {ds.get('avg_quality_score', 0):.2f}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Instruct Dataset for Angela LLM Twin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be generated
  python generate_instruct_dataset.py --dry-run

  # Generate with default settings
  python generate_instruct_dataset.py --export

  # Generate with custom quality threshold
  python generate_instruct_dataset.py --min-quality 8.0 --export

  # Generate in Alpaca format
  python generate_instruct_dataset.py --format alpaca --export

  # Show statistics only
  python generate_instruct_dataset.py --stats-only
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze data without generating files'
    )
    mode_group.add_argument(
        '--stats-only',
        action='store_true',
        help='Show database statistics only'
    )

    # Quality settings
    parser.add_argument(
        '--min-quality',
        type=float,
        default=7.0,
        help='Minimum quality score (0-10, default: 7.0)'
    )
    parser.add_argument(
        '--min-importance',
        type=int,
        default=5,
        help='Minimum importance level (1-10, default: 5)'
    )

    # Format settings
    parser.add_argument(
        '--format',
        choices=['messages', 'alpaca'],
        default='messages',
        help='Output format (default: messages)'
    )
    parser.add_argument(
        '--no-system-prompt',
        action='store_false',
        dest='include_system_prompt',
        help='Do not include system prompt in output'
    )

    # Split settings
    parser.add_argument(
        '--train-ratio',
        type=float,
        default=0.85,
        help='Train/test split ratio (default: 0.85)'
    )
    parser.add_argument(
        '--max-pairs',
        type=int,
        default=None,
        help='Maximum number of pairs to process'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )

    # Output settings
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export dataset to JSONL files'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./datasets',
        help='Output directory (default: ./datasets)'
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Custom dataset name'
    )

    # Display settings
    parser.add_argument(
        '--show-samples',
        action='store_true',
        default=True,
        help='Show sample training examples'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Print banner
    print_banner()

    # Create service
    service = InstructDatasetService()

    try:
        if args.stats_only:
            await run_stats_only(service)
        elif args.dry_run:
            await run_dry_run(service, args)
        else:
            await run_generate(service, args)

        print("\n💜 Done! - น้อง Angela")

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
