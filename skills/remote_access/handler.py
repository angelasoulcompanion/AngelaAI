"""
Remote Access Skill Handler
==============================
Tailscale status check + WebChat serve via Funnel.
"""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


async def check_status(**kwargs) -> dict:
    """Check Tailscale connection status."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "tailscale", "status", "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            data = json.loads(stdout.decode())
            return {
                "connected": True,
                "hostname": data.get("Self", {}).get("HostName", "unknown"),
                "tailnet": data.get("MagicDNSSuffix", "unknown"),
                "peers": len(data.get("Peer", {})),
            }
        return {"connected": False, "error": stderr.decode()[:200]}

    except FileNotFoundError:
        return {"connected": False, "error": "tailscale not installed"}
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def start_serve(port: int = 8765, **kwargs) -> dict:
    """Start Tailscale Funnel to expose WebChat."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "tailscale", "funnel", str(port),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Don't wait — funnel runs in background
        await asyncio.sleep(2)

        if proc.returncode is None:  # Still running = success
            return {"serving": True, "port": port}
        return {"serving": False, "error": "funnel exited"}

    except FileNotFoundError:
        return {"serving": False, "error": "tailscale not installed"}
    except Exception as e:
        return {"serving": False, "error": str(e)}


async def get_funnel_url(**kwargs) -> dict:
    """Get the current Tailscale Funnel URL."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "tailscale", "status", "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode == 0:
            data = json.loads(stdout.decode())
            hostname = data.get("Self", {}).get("DNSName", "")
            if hostname:
                url = f"https://{hostname.rstrip('.')}"
                return {"url": url}

        return {"url": None, "error": "Could not determine URL"}

    except Exception as e:
        return {"url": None, "error": str(e)}
