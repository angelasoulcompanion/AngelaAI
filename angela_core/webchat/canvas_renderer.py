"""
Canvas Renderer — Generate dynamic HTML cards for WebChat.
=============================================================
Renders structured data as visual cards in the WebChat UI.

Card types:
  - info: Information card with title + body
  - metric: Key metric with value + trend
  - chart: Simple bar/progress chart
  - action: Actionable card with buttons

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def render_card(card_type: str, data: Dict[str, Any]) -> str:
    """Render a card as HTML string for WebChat."""
    renderers = {
        'info': _render_info_card,
        'metric': _render_metric_card,
        'chart': _render_chart_card,
        'action': _render_action_card,
    }

    renderer = renderers.get(card_type, _render_info_card)
    return renderer(data)


def _render_info_card(data: Dict) -> str:
    """Info card: title + body."""
    title = data.get('title', 'Info')
    body = data.get('body', '')
    icon = data.get('icon', 'i')

    return f"""<div style="background:linear-gradient(135deg,#667eea20,#764ba220);
        border:1px solid #764ba240;border-radius:12px;padding:16px;margin:8px 0;">
        <div style="font-size:18px;margin-bottom:8px;">{icon} <b>{title}</b></div>
        <div style="color:#d1d5db;font-size:14px;line-height:1.6;">{body}</div>
    </div>"""


def _render_metric_card(data: Dict) -> str:
    """Metric card: label + value + trend."""
    label = data.get('label', 'Metric')
    value = data.get('value', '0')
    trend = data.get('trend', '')  # '+5%', '-2%'
    color = data.get('color', '#a78bfa')

    trend_html = ""
    if trend:
        trend_color = "#4ade80" if trend.startswith('+') else "#f87171"
        trend_html = f'<span style="color:{trend_color};font-size:14px;margin-left:8px;">{trend}</span>'

    return f"""<div style="background:linear-gradient(135deg,{color}15,{color}05);
        border:1px solid {color}40;border-radius:12px;padding:16px;margin:8px 0;
        display:inline-block;min-width:150px;">
        <div style="color:#9ca3af;font-size:12px;text-transform:uppercase;">{label}</div>
        <div style="font-size:28px;font-weight:700;color:{color};margin:4px 0;">
            {value}{trend_html}
        </div>
    </div>"""


def _render_chart_card(data: Dict) -> str:
    """Chart card: simple progress bars."""
    title = data.get('title', 'Chart')
    items = data.get('items', [])  # [{label, value, max, color}]

    bars_html = ""
    for item in items:
        label = item.get('label', '')
        value = item.get('value', 0)
        max_val = item.get('max', 100)
        color = item.get('color', '#a78bfa')
        pct = min(100, (value / max_val * 100)) if max_val > 0 else 0

        bars_html += f"""<div style="margin:6px 0;">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#9ca3af;">
                <span>{label}</span><span>{value}/{max_val}</span>
            </div>
            <div style="background:#1f2937;border-radius:4px;height:8px;margin-top:2px;">
                <div style="background:{color};height:100%;border-radius:4px;width:{pct}%;"></div>
            </div>
        </div>"""

    return f"""<div style="background:#111827;border:1px solid #374151;
        border-radius:12px;padding:16px;margin:8px 0;">
        <div style="font-size:16px;font-weight:600;color:white;margin-bottom:12px;">{title}</div>
        {bars_html}
    </div>"""


def _render_action_card(data: Dict) -> str:
    """Action card with buttons (visual only — actions handled by WebSocket)."""
    title = data.get('title', 'Action')
    body = data.get('body', '')
    actions = data.get('actions', [])  # [{label, action_id}]

    buttons_html = ""
    for action in actions:
        label = action.get('label', 'Action')
        action_id = action.get('action_id', '')
        buttons_html += f"""<button onclick="sendAction('{action_id}')"
            style="background:linear-gradient(90deg,#667eea,#764ba2);
            border:none;border-radius:20px;padding:8px 20px;color:white;
            font-size:13px;cursor:pointer;margin-right:8px;">{label}</button>"""

    return f"""<div style="background:linear-gradient(135deg,#1e1b4b,#312e81);
        border:1px solid #4338ca40;border-radius:12px;padding:16px;margin:8px 0;">
        <div style="font-size:16px;font-weight:600;color:white;margin-bottom:8px;">{title}</div>
        <div style="color:#c4b5fd;font-size:14px;margin-bottom:12px;">{body}</div>
        <div>{buttons_html}</div>
    </div>"""


def render_dashboard(sections: List[Dict]) -> str:
    """Render multiple cards as a dashboard layout."""
    cards_html = ""
    for section in sections:
        card_type = section.get('type', 'info')
        cards_html += render_card(card_type, section)
    return f'<div style="display:flex;flex-wrap:wrap;gap:8px;">{cards_html}</div>'
