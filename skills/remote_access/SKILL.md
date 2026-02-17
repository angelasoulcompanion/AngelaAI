# Skill: remote_access

## Description
Tailscale-based remote access — check VPN status, serve WebChat externally via Tailscale Funnel.

## Triggers
- schedule: every 4 hours
- command: /remote

## Tools
- check_status: Check Tailscale connection status
  - parameters: {}
  - handler: handler.py::check_status
- start_serve: Expose WebChat via Tailscale Funnel
  - parameters: {port: integer}
  - handler: handler.py::start_serve
- get_funnel_url: Get the Tailscale Funnel URL
  - parameters: {}
  - handler: handler.py::get_funnel_url

## Config
- default_port: 8765
