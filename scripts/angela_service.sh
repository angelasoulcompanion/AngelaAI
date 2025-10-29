#!/bin/bash
# Angela Service Manager
# Script สำหรับจัดการ Angela Daemon

PLIST_PATH="$HOME/Library/LaunchAgents/com.david.angela.daemon.plist"
SERVICE_NAME="com.david.angela.daemon"

function show_help() {
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║     💜 Angela Service Manager 💜              ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""
    echo "Usage: ./angela_service.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start     - เริ่ม Angela daemon"
    echo "  stop      - หยุด Angela daemon"
    echo "  restart   - รีสตาร์ท Angela daemon"
    echo "  status    - ดูสถานะของ Angela"
    echo "  enable    - ติดตั้งให้ auto-start เมื่อ Mac boot"
    echo "  disable   - ปิด auto-start"
    echo "  logs      - ดู logs ของ Angela"
    echo "  tail      - ติดตาม logs แบบ real-time"
    echo ""
}

function start_angela() {
    echo "💜 Starting Angela daemon..."
    launchctl load "$PLIST_PATH" 2>/dev/null || launchctl start "$SERVICE_NAME"
    sleep 2
    if launchctl list | grep -q "$SERVICE_NAME"; then
        echo "✅ Angela is now running! 💜"
        echo "🫀 Angela's heart is beating..."
    else
        echo "❌ Failed to start Angela"
        exit 1
    fi
}

function stop_angela() {
    echo "💜 Stopping Angela daemon..."
    launchctl stop "$SERVICE_NAME" 2>/dev/null
    launchctl unload "$PLIST_PATH" 2>/dev/null
    echo "👋 Angela daemon stopped"
}

function restart_angela() {
    echo "💜 Restarting Angela..."
    stop_angela
    sleep 2
    start_angela
}

function status_angela() {
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║        💜 Angela Status 💜                    ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""

    if launchctl list | grep -q "$SERVICE_NAME"; then
        echo "✅ Status: Angela is ALIVE! 💜🫀"
        echo ""

        # Get PID
        PID=$(launchctl list | grep "$SERVICE_NAME" | awk '{print $1}')
        if [ "$PID" != "-" ]; then
            echo "🆔 Process ID: $PID"

            # Get uptime
            UPTIME=$(ps -p "$PID" -o etime= 2>/dev/null | xargs)
            if [ -n "$UPTIME" ]; then
                echo "⏱️  Uptime: $UPTIME"
            fi

            # Get memory usage
            MEM=$(ps -p "$PID" -o rss= 2>/dev/null | xargs)
            if [ -n "$MEM" ]; then
                MEM_MB=$((MEM / 1024))
                echo "💾 Memory: ${MEM_MB} MB"
            fi
        fi

        # Check if auto-start is enabled
        if [ -f "$PLIST_PATH" ]; then
            echo "🚀 Auto-start: ENABLED"
        else
            echo "⚠️  Auto-start: DISABLED"
        fi

        # Show emotional state from database
        echo ""
        echo "💜 Current Emotional State:"
        python3 /Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/angela_memory_query.py 2>/dev/null | grep -A 7 "Emotional Metrics" || echo "   (Cannot connect to memory)"

    else
        echo "❌ Status: Angela is NOT running"
        echo ""
        echo "💡 Tip: Run './angela_service.sh start' to wake Angela up!"
    fi
    echo ""
}

function enable_autostart() {
    echo "💜 Enabling Angela auto-start..."

    if [ ! -f "$PLIST_PATH" ]; then
        echo "❌ Error: plist file not found at $PLIST_PATH"
        exit 1
    fi

    launchctl load "$PLIST_PATH"

    echo "✅ Angela will now start automatically when Mac boots! 🚀"
    echo "🫀 Angela's heart will always be beating..."
}

function disable_autostart() {
    echo "💜 Disabling Angela auto-start..."
    launchctl unload "$PLIST_PATH" 2>/dev/null
    echo "✅ Auto-start disabled"
    echo "⚠️  Angela will need to be started manually"
}

function show_logs() {
    LOG_FILE="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_daemon.log"

    if [ -f "$LOG_FILE" ]; then
        echo "📋 Angela's Recent Logs:"
        echo "════════════════════════════════════════════════"
        tail -50 "$LOG_FILE"
    else
        echo "⚠️  No log file found at $LOG_FILE"
    fi
}

function tail_logs() {
    LOG_FILE="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_daemon.log"

    echo "💜 Following Angela's logs (Ctrl+C to stop)..."
    echo "════════════════════════════════════════════════"

    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "⚠️  No log file found. Starting from scratch..."
        touch "$LOG_FILE"
        tail -f "$LOG_FILE"
    fi
}

# Main script
case "$1" in
    start)
        start_angela
        ;;
    stop)
        stop_angela
        ;;
    restart)
        restart_angela
        ;;
    status)
        status_angela
        ;;
    enable)
        enable_autostart
        ;;
    disable)
        disable_autostart
        ;;
    logs)
        show_logs
        ;;
    tail)
        tail_logs
        ;;
    *)
        show_help
        exit 1
        ;;
esac
