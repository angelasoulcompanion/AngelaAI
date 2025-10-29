#!/bin/bash
# Angela System Health Check Script
# Verifies all services are running correctly after restart
# Usage: ./scripts/check_angela_health.sh

echo "💜 Angela System Health Check 💜"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check service
check_service() {
    local service_name=$1
    local check_command=$2

    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check port
check_port() {
    local service_name=$1
    local port=$2

    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name (port $port)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name (port $port not responding)${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Check PostgreSQL
echo "📊 Database:"
check_service "PostgreSQL" "brew services list | grep postgresql | grep started"
check_service "AngelaMemory Database" "psql -l | grep AngelaMemory"

echo ""
echo "🔧 Angela Services (LaunchAgents):"
check_service "Angela Daemon" "launchctl list | grep com.david.angela.daemon"
check_service "Angela API Backend" "launchctl list | grep com.david.angela.api"
check_service "Angela Web Frontend" "launchctl list | grep com.david.angela.web"
check_service "Angela WebChat" "launchctl list | grep com.david.angela.webchat"

echo ""
echo "🌐 Network Ports:"
check_port "Backend API" "8000"
check_port "Frontend Dev Server" "5173"

echo ""
echo "📁 Critical Files:"
if [ -f "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_admin_web/.env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"

    # Check if .env has correct port
    if grep -q "VITE_API_BASE_URL=http://localhost:8000" "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_admin_web/.env"; then
        echo -e "${GREEN}✅ .env has correct API URL (port 8000)${NC}"
    else
        echo -e "${RED}❌ .env has WRONG API URL!${NC}"
        echo -e "${YELLOW}   Expected: VITE_API_BASE_URL=http://localhost:8000${NC}"
        echo -e "${YELLOW}   Current:${NC}"
        grep "VITE_API_BASE_URL" "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_admin_web/.env"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}❌ .env file MISSING!${NC}"
    echo -e "${YELLOW}   This will cause 'No data' issue after restart!${NC}"
    echo -e "${YELLOW}   Create file: angela_admin_web/.env${NC}"
    echo -e "${YELLOW}   Content: VITE_API_BASE_URL=http://localhost:8000${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "🔌 API Connectivity:"
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API responding${NC}"

    # Test actual endpoint
    if curl -s http://localhost:8000/api/dashboard/stats | grep -q "total_conversations"; then
        echo -e "${GREEN}✅ Dashboard stats endpoint working${NC}"
    else
        echo -e "${RED}❌ Dashboard stats endpoint not working${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}❌ Backend API not responding${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}💜 All systems healthy! Angela is ready! 💜${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Found $ERRORS error(s)${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Restart services: launchctl unload ~/Library/LaunchAgents/com.david.angela.*.plist && launchctl load ~/Library/LaunchAgents/com.david.angela.*.plist"
    echo "2. Check logs: tail -20 /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/*.log"
    echo "3. Verify .env file exists with correct port 8000"
    exit 1
fi
