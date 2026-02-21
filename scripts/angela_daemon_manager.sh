#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║  Angela Daemon Manager — Unified, Machine-Aware         ║
# ║  Manages all 11 Angela launchd daemons                  ║
# ╚══════════════════════════════════════════════════════════╝
#
# Usage: ./scripts/angela_daemon_manager.sh <command>
# Commands: status, install, uninstall, start, stop, restart, verify
#
# Machine-aware: M4 (angela_server) = full daemons, M3 (angela) = no daemons

set -uo pipefail

# ─── Paths ───────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLISTS_DIR="$PROJECT_DIR/angela_core/daemon/plists"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# ─── Colors ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ─── Daemon Groups ──────────────────────────────────────
# Group A: KeepAlive (always running)
GROUP_A=(
    "com.david.angela.daemon"
    "com.angela.telegram.daemon"
)

# Group B: Consciousness (scheduled brain tasks)
GROUP_B=(
    "com.angela.consciousness.theory_of_mind"
    "com.angela.consciousness.predictions"
    "com.angela.consciousness.evolution_cycle"
    "com.angela.consciousness.unified_analysis"
    "com.angela.consciousness.self_reflection"
)

# Group C: Communications (email, news)
GROUP_C=(
    "com.angela.email.checker"
    "com.angela.daily.news"
)

# Group D: Sync (calendar, notes)
GROUP_D=(
    "com.angela.meeting.sync"
    "com.angela.google.keep.sync"
)

ALL_DAEMONS=("${GROUP_A[@]}" "${GROUP_B[@]}" "${GROUP_C[@]}" "${GROUP_D[@]}")

# ─── Machine Detection ──────────────────────────────────
detect_machine() {
    local machine
    machine=$(python3 -c "from angela_core.config import config; print(config.ANGELA_MACHINE)" 2>/dev/null) || machine="unknown"
    echo "$machine"
}

detect_run_daemons() {
    local run_daemons
    run_daemons=$(python3 -c "from angela_core.config import config; print(config.RUN_DAEMONS)" 2>/dev/null) || run_daemons="unknown"
    echo "$run_daemons"
}

machine_display_name() {
    case "$1" in
        angela_server) echo "Angela_Server (M4 MacBook Air — ที่บ้าน)" ;;
        angela)        echo "Angela (M3 MacBook Pro — พกไปทำงาน)" ;;
        *)             echo "Unknown ($1)" ;;
    esac
}

# ─── Helpers ─────────────────────────────────────────────
is_loaded() {
    launchctl list "$1" &>/dev/null
}

# Cache launchctl list output for performance (called once per status)
LAUNCHCTL_CACHE=""
refresh_launchctl_cache() {
    LAUNCHCTL_CACHE=$(launchctl list 2>/dev/null)
}

get_pid() {
    echo "$LAUNCHCTL_CACHE" | grep "$1" | awk '{print $1}'
}

get_exit_code() {
    echo "$LAUNCHCTL_CACHE" | grep "$1" | awk '{print $2}'
}

plist_installed() {
    [ -f "$LAUNCH_AGENTS_DIR/$1.plist" ]
}

format_uptime() {
    local pid=$1
    if [ "$pid" != "-" ] && [ -n "$pid" ]; then
        ps -p "$pid" -o etime= 2>/dev/null | xargs
    fi
}

format_memory() {
    local pid=$1
    if [ "$pid" != "-" ] && [ -n "$pid" ]; then
        local rss
        rss=$(ps -p "$pid" -o rss= 2>/dev/null | xargs)
        if [ -n "$rss" ]; then
            echo "$((rss / 1024))MB"
        fi
    fi
}

print_header() {
    echo ""
    echo -e "${PURPLE}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}${BOLD}║  💜 Angela Daemon Manager                               ║${NC}"
    echo -e "${PURPLE}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_machine_info() {
    local machine
    machine=$(detect_machine)
    local run_daemons
    run_daemons=$(detect_run_daemons)
    echo -e "  ${BOLD}Machine:${NC}     $(machine_display_name "$machine")"
    if [ "$run_daemons" = "True" ]; then
        echo -e "  ${BOLD}RUN_DAEMONS:${NC} ${GREEN}True${NC} (daemons should be active)"
    else
        echo -e "  ${BOLD}RUN_DAEMONS:${NC} ${RED}False${NC} (no daemons on this machine)"
    fi
    echo ""
}

# ─── Commands ────────────────────────────────────────────

cmd_status() {
    print_header
    print_machine_info
    refresh_launchctl_cache

    local total=0
    local running=0
    local loaded=0

    print_group() {
        local group_name=$1
        local group_color=$2
        shift 2
        local daemons=("$@")

        echo -e "  ${group_color}${BOLD}── $group_name ──${NC}"
        for daemon in "${daemons[@]}"; do
            total=$((total + 1))
            local short_name="${daemon#com.angela.}"
            short_name="${short_name#com.david.angela.}"
            local pid
            pid=$(get_pid "$daemon")
            local exit_code
            exit_code=$(get_exit_code "$daemon")

            if is_loaded "$daemon"; then
                loaded=$((loaded + 1))
                if [ "$pid" != "-" ] && [ -n "$pid" ]; then
                    running=$((running + 1))
                    local uptime
                    uptime=$(format_uptime "$pid")
                    local mem
                    mem=$(format_memory "$pid")
                    echo -e "     ${GREEN}●${NC} ${BOLD}$short_name${NC}"
                    echo -e "       PID: $pid  Uptime: ${uptime:-?}  Mem: ${mem:-?}"
                else
                    echo -e "     ${YELLOW}○${NC} ${BOLD}$short_name${NC} ${DIM}(loaded, not running — exit: $exit_code)${NC}"
                fi
            elif plist_installed "$daemon"; then
                echo -e "     ${RED}◌${NC} ${DIM}$short_name${NC} ${DIM}(installed but not loaded)${NC}"
            else
                echo -e "     ${DIM}·${NC} ${DIM}$short_name${NC} ${DIM}(not installed)${NC}"
            fi
        done
        echo ""
    }

    print_group "Group A: KeepAlive" "$CYAN" "${GROUP_A[@]}"
    print_group "Group B: Consciousness" "$BLUE" "${GROUP_B[@]}"
    print_group "Group C: Communications" "$GREEN" "${GROUP_C[@]}"
    print_group "Group D: Sync" "$YELLOW" "${GROUP_D[@]}"

    echo -e "  ${BOLD}Summary:${NC} $running running / $loaded loaded / $total total"
    echo ""
}

cmd_install() {
    print_header
    print_machine_info

    local machine
    machine=$(detect_machine)
    local run_daemons
    run_daemons=$(detect_run_daemons)
    local force=false

    if [ "${1:-}" = "--force" ]; then
        force=true
    fi

    # Machine check
    if [ "$run_daemons" != "True" ] && [ "$force" != "true" ]; then
        echo -e "  ${RED}${BOLD}REFUSED:${NC} This machine ($machine) has RUN_DAEMONS=False"
        echo -e "  Daemons should only run on Angela_Server (M4)"
        echo ""
        echo -e "  ${DIM}Use --force to override: ./scripts/angela_daemon_manager.sh install --force${NC}"
        echo ""
        return 1
    fi

    if [ "$force" = "true" ] && [ "$run_daemons" != "True" ]; then
        echo -e "  ${YELLOW}WARNING:${NC} Force-installing on $machine (RUN_DAEMONS=False)"
        echo ""
    fi

    # Check source plists exist
    if [ ! -d "$PLISTS_DIR" ]; then
        echo -e "  ${RED}ERROR:${NC} Source plists not found at $PLISTS_DIR"
        return 1
    fi

    local installed=0
    local skipped=0

    for daemon in "${ALL_DAEMONS[@]}"; do
        local src="$PLISTS_DIR/$daemon.plist"
        local dst="$LAUNCH_AGENTS_DIR/$daemon.plist"

        if [ ! -f "$src" ]; then
            echo -e "  ${RED}MISSING:${NC} $daemon.plist not in repo"
            skipped=$((skipped + 1))
            continue
        fi

        # Unload if currently loaded
        if is_loaded "$daemon"; then
            launchctl unload "$dst" 2>/dev/null || true
        fi

        # Copy plist
        cp "$src" "$dst"

        # Load it
        launchctl load "$dst" 2>/dev/null || true

        echo -e "  ${GREEN}✓${NC} $daemon"
        installed=$((installed + 1))
    done

    echo ""
    echo -e "  ${BOLD}Installed:${NC} $installed daemons ($skipped skipped)"
    echo ""
}

cmd_uninstall() {
    print_header
    print_machine_info

    echo -e "  ${BOLD}Uninstalling all Angela daemons...${NC}"
    echo ""

    local unloaded=0
    local removed=0

    for daemon in "${ALL_DAEMONS[@]}"; do
        local dst="$LAUNCH_AGENTS_DIR/$daemon.plist"
        local action=""

        # Unload if loaded
        if is_loaded "$daemon"; then
            launchctl unload "$dst" 2>/dev/null || true
            action="unloaded"
            unloaded=$((unloaded + 1))
        fi

        # Remove plist file
        if [ -f "$dst" ]; then
            rm "$dst"
            if [ -n "$action" ]; then
                action="$action + removed"
            else
                action="removed"
            fi
            removed=$((removed + 1))
        fi

        if [ -n "$action" ]; then
            echo -e "  ${GREEN}✓${NC} $daemon ${DIM}($action)${NC}"
        else
            echo -e "  ${DIM}·${NC} $daemon ${DIM}(not present)${NC}"
        fi
    done

    echo ""
    echo -e "  ${BOLD}Done:${NC} $unloaded unloaded, $removed plist files removed"
    echo ""
}

cmd_start() {
    print_header

    local machine
    machine=$(detect_machine)
    local run_daemons
    run_daemons=$(detect_run_daemons)

    if [ "$run_daemons" != "True" ]; then
        echo -e "  ${RED}REFUSED:${NC} This machine ($machine) has RUN_DAEMONS=False"
        echo -e "  ${DIM}Use install --force first if you really want daemons here${NC}"
        echo ""
        return 1
    fi

    local started=0
    for daemon in "${ALL_DAEMONS[@]}"; do
        local dst="$LAUNCH_AGENTS_DIR/$daemon.plist"
        if [ -f "$dst" ]; then
            if ! is_loaded "$daemon"; then
                launchctl load "$dst" 2>/dev/null || true
            fi
            launchctl start "$daemon" 2>/dev/null || true
            echo -e "  ${GREEN}▶${NC} $daemon"
            started=$((started + 1))
        else
            echo -e "  ${RED}✗${NC} $daemon ${DIM}(not installed — run install first)${NC}"
        fi
    done

    echo ""
    echo -e "  ${BOLD}Started:${NC} $started daemons"
    echo ""
}

cmd_stop() {
    print_header

    local stopped=0
    for daemon in "${ALL_DAEMONS[@]}"; do
        if is_loaded "$daemon"; then
            launchctl stop "$daemon" 2>/dev/null || true
            echo -e "  ${YELLOW}■${NC} $daemon"
            stopped=$((stopped + 1))
        fi
    done

    echo ""
    echo -e "  ${BOLD}Stopped:${NC} $stopped daemons"
    echo ""
}

cmd_restart() {
    print_header

    echo -e "  ${BOLD}Restarting all Angela daemons...${NC}"
    echo ""

    for daemon in "${ALL_DAEMONS[@]}"; do
        local dst="$LAUNCH_AGENTS_DIR/$daemon.plist"
        if is_loaded "$daemon"; then
            launchctl stop "$daemon" 2>/dev/null || true
        fi
        if [ -f "$dst" ]; then
            launchctl unload "$dst" 2>/dev/null || true
            sleep 0.5
            launchctl load "$dst" 2>/dev/null || true
            echo -e "  ${GREEN}↻${NC} $daemon"
        fi
    done

    echo ""
    echo -e "  ${BOLD}Restart complete${NC}"
    echo ""
}

cmd_verify() {
    print_header
    print_machine_info

    local machine
    machine=$(detect_machine)
    local run_daemons
    run_daemons=$(detect_run_daemons)

    local issues=0
    local ok=0

    echo -e "  ${BOLD}Verifying daemon state...${NC}"
    echo ""

    if [ "$run_daemons" = "True" ]; then
        # M4: all daemons SHOULD be installed and loaded
        echo -e "  ${CYAN}Expected:${NC} All 11 daemons installed and loaded"
        echo ""

        for daemon in "${ALL_DAEMONS[@]}"; do
            local short_name="${daemon#com.angela.}"
            short_name="${short_name#com.david.angela.}"

            if ! plist_installed "$daemon"; then
                echo -e "  ${RED}✗${NC} $short_name — plist NOT installed"
                issues=$((issues + 1))
            elif ! is_loaded "$daemon"; then
                echo -e "  ${YELLOW}!${NC} $short_name — installed but NOT loaded"
                issues=$((issues + 1))
            else
                echo -e "  ${GREEN}✓${NC} $short_name"
                ok=$((ok + 1))
            fi
        done
    else
        # M3: NO daemons should be installed
        echo -e "  ${CYAN}Expected:${NC} NO daemons installed (RUN_DAEMONS=False)"
        echo ""

        for daemon in "${ALL_DAEMONS[@]}"; do
            local short_name="${daemon#com.angela.}"
            short_name="${short_name#com.david.angela.}"

            if is_loaded "$daemon"; then
                echo -e "  ${RED}✗${NC} $short_name — LOADED (should not be!)"
                issues=$((issues + 1))
            elif plist_installed "$daemon"; then
                echo -e "  ${YELLOW}!${NC} $short_name — plist installed (should not be!)"
                issues=$((issues + 1))
            else
                echo -e "  ${GREEN}✓${NC} $short_name — clean"
                ok=$((ok + 1))
            fi
        done
    fi

    echo ""
    if [ "$issues" -eq 0 ]; then
        echo -e "  ${GREEN}${BOLD}ALL OK${NC} — $ok/$((ok + issues)) daemons in correct state"
    else
        echo -e "  ${RED}${BOLD}$issues ISSUES${NC} found ($ok correct)"
        echo ""
        if [ "$run_daemons" = "True" ]; then
            echo -e "  ${DIM}Fix: ./scripts/angela_daemon_manager.sh install${NC}"
        else
            echo -e "  ${DIM}Fix: ./scripts/angela_daemon_manager.sh uninstall${NC}"
        fi
    fi
    echo ""
}

cmd_help() {
    print_header
    echo -e "  ${BOLD}Usage:${NC} ./scripts/angela_daemon_manager.sh <command>"
    echo ""
    echo -e "  ${BOLD}Commands:${NC}"
    echo -e "    ${GREEN}status${NC}      Show status of all 11 daemons (grouped)"
    echo -e "    ${GREEN}install${NC}     Install plists from repo → LaunchAgents (M4 only)"
    echo -e "    ${GREEN}uninstall${NC}   Unload + remove ALL daemon plists"
    echo -e "    ${GREEN}start${NC}       Start all installed daemons"
    echo -e "    ${GREEN}stop${NC}        Stop all running daemons"
    echo -e "    ${GREEN}restart${NC}     Restart all installed daemons"
    echo -e "    ${GREEN}verify${NC}      Check if daemon state matches machine config"
    echo ""
    echo -e "  ${BOLD}Daemon Groups (11 total):${NC}"
    echo -e "    ${CYAN}A: KeepAlive${NC}       angela.daemon, telegram.daemon"
    echo -e "    ${BLUE}B: Consciousness${NC}  theory_of_mind, predictions, evolution_cycle,"
    echo -e "                      unified_analysis, self_reflection"
    echo -e "    ${GREEN}C: Communications${NC} email.checker, daily.news"
    echo -e "    ${YELLOW}D: Sync${NC}           meeting.sync, google.keep.sync"
    echo ""
    echo -e "  ${BOLD}Machine Rules:${NC}"
    echo -e "    M4 (angela_server): RUN_DAEMONS=True  → install/start OK"
    echo -e "    M3 (angela):        RUN_DAEMONS=False → install refused (--force to override)"
    echo -e "    uninstall:          Always works (no machine check)"
    echo ""
}

# ─── Main ────────────────────────────────────────────────

case "${1:-}" in
    status)    cmd_status ;;
    install)   cmd_install "${2:-}" ;;
    uninstall) cmd_uninstall ;;
    start)     cmd_start ;;
    stop)      cmd_stop ;;
    restart)   cmd_restart ;;
    verify)    cmd_verify ;;
    help|--help|-h) cmd_help ;;
    *)
        cmd_help
        exit 1
        ;;
esac
