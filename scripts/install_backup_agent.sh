#!/bin/bash
#
# Install Angela Backup LaunchAgent
# =================================
#
# This script installs the LaunchAgent for automatic daily backups.
# Run once after setting up the backup system.
#
# Usage: ./scripts/install_backup_agent.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_SOURCE="$PROJECT_DIR/angela_core/backup/com.david.angela.backup.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.david.angela.backup.plist"

echo "=================================="
echo " Angela Backup Agent Installation"
echo "=================================="

# Check if source plist exists
if [ ! -f "$PLIST_SOURCE" ]; then
    echo "ERROR: Source plist not found at $PLIST_SOURCE"
    exit 1
fi

# Unload existing agent if loaded
if launchctl list | grep -q "com.david.angela.backup"; then
    echo "Unloading existing agent..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Create LaunchAgents directory if needed
mkdir -p "$HOME/Library/LaunchAgents"

# Copy plist
echo "Copying plist to $PLIST_DEST..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Set permissions
chmod 644 "$PLIST_DEST"

# Load the agent
echo "Loading agent..."
launchctl load "$PLIST_DEST"

# Verify
if launchctl list | grep -q "com.david.angela.backup"; then
    echo ""
    echo " Agent installed successfully!"
    echo ""
    echo "Status:"
    launchctl list | grep angela.backup
    echo ""
    echo "Backup will run daily at 3:00 AM"
    echo ""
    echo "Manual commands:"
    echo "  Run backup now:  launchctl start com.david.angela.backup"
    echo "  Check status:    python3 angela_core/backup/run_backup.py --status"
    echo "  Verify chain:    python3 angela_core/backup/run_backup.py --verify"
    echo ""
else
    echo "ERROR: Agent failed to load"
    exit 1
fi
