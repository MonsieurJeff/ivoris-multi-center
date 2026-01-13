#!/bin/bash
# Restart script for Ivoris Multi-Center application
# Usage: ./scripts/restart.sh [--web-only]

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "  Ivoris Multi-Center - Full Restart"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. Kill existing web server
echo -e "\n${YELLOW}[1/3] Stopping existing web server...${NC}"
pkill -f "uvicorn.*src.web.app" 2>/dev/null || true
pkill -f "python.*src.cli.*web" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1
echo -e "${GREEN}Done${NC}"

# 2. Check Docker SQL Server
echo -e "\n${YELLOW}[2/3] Checking Docker SQL Server...${NC}"
if [[ "$1" == "--web-only" ]]; then
    echo -e "${CYAN}Skipping Docker (--web-only flag)${NC}"
elif docker ps &>/dev/null; then
    # Docker CLI works
    if docker ps | grep -q "ivoris-multi-sqlserver"; then
        echo -e "${GREEN}SQL Server container is running${NC}"
    else
        echo "Starting SQL Server container..."
        docker-compose up -d
        echo "Waiting for SQL Server to be ready..."
        sleep 15
    fi
else
    echo -e "${YELLOW}Docker CLI not accessible.${NC}"
    echo -e "${CYAN}If SQL Server is running in Docker Desktop, Data view will work.${NC}"
    echo -e "${CYAN}Otherwise, start Docker Desktop and run: docker-compose up -d${NC}"
fi

# 3. Start web server
echo -e "\n${YELLOW}[3/3] Starting web server...${NC}"
echo -e "${GREEN}=========================================="
echo -e "  Web UI: http://localhost:8000"
echo -e "==========================================${NC}\n"

python -m src.cli web
