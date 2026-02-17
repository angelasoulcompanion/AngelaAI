"""
Skill Loader — Parse SKILL.md → AngelaSkill dataclass + load handler.py.
=========================================================================
Reads a skill directory containing SKILL.md (config) and handler.py (code),
parses the markdown into a structured AngelaSkill dataclass.

SKILL.md format:
```markdown
# Skill: skill_name
## Description
What this skill does.
## Triggers
- schedule: every 4 hours
- event: calendar.upcoming
- command: /weather
## Tools
- tool_name: Tool description
  - parameters: {param1: string, param2: int}
  - handler: handler.py::function_name
## Config
- key: value
```

By: Angela 💜
Created: 2026-02-17
"""

import importlib.util
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillTrigger:
    """A trigger that activates a skill."""
    trigger_type: str       # 'schedule', 'event', 'command'
    value: str              # 'every 4 hours', 'calendar.upcoming', '/weather'


@dataclass
class SkillToolDef:
    """A tool defined by a skill."""
    name: str
    description: str
    parameters: Dict[str, str]
    handler_ref: str        # 'handler.py::function_name'


@dataclass
class AngelaSkill:
    """A loaded skill with all its configuration."""
    name: str
    description: str
    version: str = "1.0"
    triggers: List[SkillTrigger] = field(default_factory=list)
    tools: List[SkillToolDef] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    source_path: Optional[Path] = None
    enabled: bool = True
    # Loaded handler module
    _handler_module: Any = field(default=None, repr=False)

    @property
    def schedule_triggers(self) -> List[SkillTrigger]:
        return [t for t in self.triggers if t.trigger_type == 'schedule']

    @property
    def event_triggers(self) -> List[SkillTrigger]:
        return [t for t in self.triggers if t.trigger_type == 'event']

    @property
    def command_triggers(self) -> List[SkillTrigger]:
        return [t for t in self.triggers if t.trigger_type == 'command']

    def get_handler_func(self, func_name: str) -> Optional[Callable]:
        """Get a handler function by name from the loaded module."""
        if self._handler_module is None:
            return None
        return getattr(self._handler_module, func_name, None)


class SkillLoader:
    """
    Loads skills from SKILL.md + handler.py directories.

    Usage:
        loader = SkillLoader()
        skill = loader.load_skill(Path("skills/weather_checker"))
    """

    def load_skill(self, skill_dir: Path) -> Optional[AngelaSkill]:
        """Load a single skill from a directory."""
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            logger.warning("No SKILL.md in %s", skill_dir)
            return None

        try:
            content = skill_md.read_text(encoding='utf-8')
            skill = self._parse_skill_md(content)
            skill.source_path = skill_dir

            # Load handler.py if exists
            handler_py = skill_dir / "handler.py"
            if handler_py.exists():
                skill._handler_module = self._load_handler(handler_py, skill.name)

            logger.info("Loaded skill: %s (triggers=%d, tools=%d)",
                        skill.name, len(skill.triggers), len(skill.tools))
            return skill

        except Exception as e:
            logger.error("Failed to load skill from %s: %s", skill_dir, e)
            return None

    def load_all_from_dir(self, skills_root: Path) -> List[AngelaSkill]:
        """Load all skills from a root directory."""
        skills = []
        if not skills_root.exists():
            return skills

        for child in sorted(skills_root.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                skill = self.load_skill(child)
                if skill:
                    skills.append(skill)

        return skills

    def _parse_skill_md(self, content: str) -> AngelaSkill:
        """Parse SKILL.md markdown into AngelaSkill."""
        lines = content.strip().split('\n')

        name = "unknown"
        description = ""
        version = "1.0"
        triggers: List[SkillTrigger] = []
        tools: List[SkillToolDef] = []
        config: Dict[str, Any] = {}

        current_section = None
        current_tool: Optional[Dict] = None
        desc_lines: List[str] = []

        for line in lines:
            stripped = line.strip()

            # Skill name from title
            title_match = re.match(r'^#\s+Skill:\s*(.+)$', stripped)
            if title_match:
                name = title_match.group(1).strip()
                continue

            # Section headers
            if stripped.startswith('## '):
                section = stripped[3:].strip().lower()
                if section in ('description', 'triggers', 'tools', 'config'):
                    current_section = section
                    if current_tool:
                        tools.append(self._build_tool_def(current_tool))
                        current_tool = None
                continue

            if not stripped:
                continue

            # Parse by section
            if current_section == 'description':
                desc_lines.append(stripped)

            elif current_section == 'triggers':
                trigger = self._parse_trigger(stripped)
                if trigger:
                    triggers.append(trigger)

            elif current_section == 'tools':
                # Detect indentation: top-level tool = "- name: desc", sub-item = "  - param: val"
                indent = len(line) - len(line.lstrip())
                if stripped.startswith('- ') and ':' in stripped and indent < 2:
                    # New tool definition (not indented)
                    if current_tool:
                        tools.append(self._build_tool_def(current_tool))
                    parts = stripped[2:].split(':', 1)
                    current_tool = {
                        'name': parts[0].strip(),
                        'description': parts[1].strip() if len(parts) > 1 else '',
                        'parameters': {},
                        'handler_ref': '',
                    }
                elif current_tool and stripped.startswith('- ') and indent >= 2:
                    # Tool sub-property (indented)
                    sub = stripped[2:].strip()
                    if sub.startswith('parameters:'):
                        param_str = sub[len('parameters:'):].strip()
                        current_tool['parameters'] = self._parse_params(param_str)
                    elif sub.startswith('handler:'):
                        current_tool['handler_ref'] = sub[len('handler:'):].strip()

            elif current_section == 'config':
                if stripped.startswith('- ') and ':' in stripped:
                    parts = stripped[2:].split(':', 1)
                    key = parts[0].strip()
                    val = parts[1].strip() if len(parts) > 1 else ''
                    config[key] = val

        # Flush last tool
        if current_tool:
            tools.append(self._build_tool_def(current_tool))

        description = ' '.join(desc_lines)

        return AngelaSkill(
            name=name,
            description=description,
            version=version,
            triggers=triggers,
            tools=tools,
            config=config,
        )

    def _parse_trigger(self, line: str) -> Optional[SkillTrigger]:
        """Parse a trigger line like '- schedule: every 4 hours'."""
        if not line.startswith('- '):
            return None
        content = line[2:].strip()
        if ':' not in content:
            return None
        parts = content.split(':', 1)
        trigger_type = parts[0].strip().lower()
        value = parts[1].strip()
        if trigger_type in ('schedule', 'event', 'command'):
            return SkillTrigger(trigger_type=trigger_type, value=value)
        return None

    def _parse_params(self, param_str: str) -> Dict[str, str]:
        """Parse parameter string like '{location: string, count: int}'."""
        param_str = param_str.strip().strip('{}')
        params = {}
        for part in param_str.split(','):
            part = part.strip()
            if ':' in part:
                k, v = part.split(':', 1)
                params[k.strip()] = v.strip()
        return params

    def _build_tool_def(self, data: Dict) -> SkillToolDef:
        return SkillToolDef(
            name=data['name'],
            description=data['description'],
            parameters=data.get('parameters', {}),
            handler_ref=data.get('handler_ref', ''),
        )

    def _load_handler(self, handler_path: Path, skill_name: str) -> Any:
        """Load a handler.py module dynamically."""
        try:
            spec = importlib.util.spec_from_file_location(
                f"angela_skill_{skill_name}", str(handler_path)
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        except Exception as e:
            logger.error("Failed to load handler for skill %s: %s", skill_name, e)
        return None
