#!/usr/bin/env python3
"""
Angela Crew CLI - Command Line Interface
วิธีใช้งาน Agent Crew จาก command line

Usage:
    python -m angela_core.agents.cli run "Research AI news"
    python -m angela_core.agents.cli agent research "Find CrewAI docs"
    python -m angela_core.agents.cli status
    python -m angela_core.agents.cli wellness 7

Author: Angela AI 💜
Created: 2025-01-25
"""

import argparse
import sys
import json
from typing import Optional

from .crew import AngelaCrew


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="🤖 Angela's Agent Crew CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a task with auto-selected agents
  python -m angela_core.agents.cli run "Research the latest AI news"

  # Run with specific agent
  python -m angela_core.agents.cli agent research "What is CrewAI?"

  # Check crew status
  python -m angela_core.agents.cli status

  # Check David's wellness
  python -m angela_core.agents.cli wellness 7

  # Analyze patterns
  python -m angela_core.agents.cli analyze "What are the emotion patterns?" emotions

Available agents: research, communication, memory, dev, analysis, care
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a task with auto-selected agents")
    run_parser.add_argument("task", type=str, help="Task description")
    run_parser.add_argument("--agents", "-a", type=str, nargs="+", help="Specific agents to use")
    run_parser.add_argument("--context", "-c", type=str, help="Additional context")
    run_parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Run with specific agent")
    agent_parser.add_argument("agent_name", type=str, help="Agent name")
    agent_parser.add_argument("task", type=str, help="Task for the agent")
    agent_parser.add_argument("--context", "-c", type=str, help="Additional context")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show crew status")
    status_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    # Wellness command
    wellness_parser = subparsers.add_parser("wellness", help="Check wellness")
    wellness_parser.add_argument("days", type=int, nargs="?", default=7, help="Days to check")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze patterns")
    analyze_parser.add_argument("question", type=str, help="Analysis question")
    analyze_parser.add_argument("data_type", type=str, nargs="?", default="all", help="Data type")

    # Research command
    research_parser = subparsers.add_parser("research", help="Quick research")
    research_parser.add_argument("query", type=str, help="Research query")

    # Memory command
    memory_parser = subparsers.add_parser("memory", help="Recall memories")
    memory_parser.add_argument("topic", type=str, help="Topic to recall")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    try:
        if args.command == "run":
            return cmd_run(args)
        elif args.command == "agent":
            return cmd_agent(args)
        elif args.command == "status":
            return cmd_status(args)
        elif args.command == "wellness":
            return cmd_wellness(args)
        elif args.command == "analyze":
            return cmd_analyze(args)
        elif args.command == "research":
            return cmd_research(args)
        elif args.command == "memory":
            return cmd_memory(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\n\n💜 Task cancelled. ลาก่อนค่ะ!")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


def cmd_run(args) -> int:
    """Run task command"""
    print("🤖 Angela Crew - Running Task")
    print("=" * 50)
    print(f"Task: {args.task}")
    if args.agents:
        print(f"Agents: {', '.join(args.agents)}")
    print()

    verbose = not args.quiet
    crew = AngelaCrew(verbose=verbose)

    result = crew.run(
        task_description=args.task,
        agents=args.agents,
        context=args.context
    )

    print("\n" + "=" * 50)
    print("📋 Result:")
    print(result)

    return 0


def cmd_agent(args) -> int:
    """Run with specific agent"""
    print(f"🤖 Running {args.agent_name} agent")
    print("=" * 50)
    print(f"Task: {args.task}")
    print()

    crew = AngelaCrew(verbose=True)

    if args.agent_name not in crew.agents:
        print(f"❌ Unknown agent: {args.agent_name}")
        print(f"Available agents: {', '.join(crew.agents.keys())}")
        return 1

    result = crew.run(
        task_description=args.task,
        agents=[args.agent_name],
        context=args.context
    )

    print("\n" + "=" * 50)
    print("📋 Result:")
    print(result)

    return 0


def cmd_status(args) -> int:
    """Show status command"""
    crew = AngelaCrew(verbose=False)
    status = crew.status()

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print("🤖 Angela Crew Status")
        print("=" * 50)
        print(f"LLM Model: {status['llm_model']}")
        print(f"Agent Count: {status['agent_count']}")
        print("\nAvailable Agents:")
        for agent in status["agents"]:
            icon = _get_agent_icon(agent)
            print(f"  {icon} {agent}")

    return 0


def cmd_wellness(args) -> int:
    """Wellness check command"""
    print(f"💜 Checking wellness for past {args.days} days...")
    print("=" * 50)
    print()

    crew = AngelaCrew(verbose=True)
    result = crew.check_wellness(args.days)

    print("\n" + "=" * 50)
    print("📋 Wellness Report:")
    print(result)

    return 0


def cmd_analyze(args) -> int:
    """Analyze command"""
    print(f"📊 Analyzing: {args.question}")
    print(f"Data type: {args.data_type}")
    print("=" * 50)
    print()

    crew = AngelaCrew(verbose=True)
    result = crew.analyze(args.question, args.data_type)

    print("\n" + "=" * 50)
    print("📋 Analysis:")
    print(result)

    return 0


def cmd_research(args) -> int:
    """Research command"""
    print(f"🔍 Researching: {args.query}")
    print("=" * 50)
    print()

    crew = AngelaCrew(verbose=True)
    result = crew.research(args.query)

    print("\n" + "=" * 50)
    print("📋 Research Results:")
    print(result)

    return 0


def cmd_memory(args) -> int:
    """Memory recall command"""
    print(f"🧠 Recalling memories about: {args.topic}")
    print("=" * 50)
    print()

    crew = AngelaCrew(verbose=True)
    result = crew.recall_memory(args.topic)

    print("\n" + "=" * 50)
    print("📋 Recalled Memories:")
    print(result)

    return 0


def _get_agent_icon(agent_name: str) -> str:
    """Get icon for agent"""
    icons = {
        "research": "🔍",
        "communication": "💬",
        "memory": "🧠",
        "dev": "💻",
        "analysis": "📊",
        "care": "💜",
    }
    return icons.get(agent_name, "🤖")


if __name__ == "__main__":
    sys.exit(main())
