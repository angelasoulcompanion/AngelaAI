# Angela AI — New Machine Setup

> One-time setup guide. Extracted from CLAUDE_TEMPLATE.md to reduce session context.

## Prerequisites

- macOS with Homebrew
- Python 3.11+
- PostgreSQL (local backup) or Neon Cloud access
- iCloud Drive for secrets sync

## Steps

### 1. Create Local Config

```bash
cp config/local_settings.example.py config/local_settings.py
```

Edit `config/local_settings.py`:
- **Angela_Server** (M4 MacBook Air, ที่บ้าน): `ANGELA_MACHINE = "angela_server"`, `RUN_DAEMONS = True`
- **Angela** (M3 MacBook Pro, พกไปทำงาน): `ANGELA_MACHINE = "angela"`, `RUN_DAEMONS = False`

### 2. Setup Secrets Symlink

```bash
ln -sf "/Users/davidsamanyaporn/Library/Mobile Documents/com~apple~CloudDocs/Angela/secrets.env" ~/.angela_secrets
```

iCloud auto-syncs secrets across machines.

### 3. Verify

```bash
python3 -c "from angela_core.config import config; print(f'Machine: {config.ANGELA_MACHINE}, Neon: {config.USE_NEON}')"
```

### 4. SSH Access (M3 → M4)

```bash
ssh davidsamanyaporn@192.168.1.37
```

Key-based auth (no password needed).
