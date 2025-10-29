#!/bin/bash

###############################################################################
# Start Angela Backend
# Starts the FastAPI backend server for Angela Native macOS App
###############################################################################

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/Users/davidsamanyaporn/PycharmProjects/AngelaAI"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🚀 Starting Angela Backend Server${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if PostgreSQL is running
echo -e "\n${YELLOW}📊 Checking PostgreSQL...${NC}"
if pg_isready -q; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo -e "${YELLOW}   Starting PostgreSQL...${NC}"
    brew services start postgresql@14
    sleep 2
fi

# Check if Ollama is running
echo -e "\n${YELLOW}🤖 Checking Ollama...${NC}"
if curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${RED}❌ Ollama is not running${NC}"
    echo -e "${YELLOW}   Please start Ollama manually${NC}"
    exit 1
fi

# Check if database exists
echo -e "\n${YELLOW}💾 Checking AngelaMemory database...${NC}"
if psql -lqt | cut -d \| -f 1 | grep -qw AngelaMemory; then
    echo -e "${GREEN}✅ AngelaMemory database exists${NC}"
else
    echo -e "${RED}❌ AngelaMemory database not found${NC}"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR" || exit

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Start the backend server
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🌟 Starting Angela Backend API Server...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📍 Server will be available at: http://localhost:8000${NC}"
echo -e "${YELLOW}📖 API docs at: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}🔌 WebSocket at: ws://localhost:8000/ws/chat${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Run uvicorn
python3 -m uvicorn angela_backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
