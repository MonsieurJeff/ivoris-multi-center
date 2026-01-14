#!/bin/bash
#
# reset-demo.sh - Quick reset for coding session demo
#
# Usage: ./scripts/reset-demo.sh
#
# This script:
# 1. Stops and removes Docker containers
# 2. Clears output files
# 3. Restarts fresh
# 4. Waits for SQL Server to be ready
# 5. Verifies everything works
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Ivoris Demo Reset ===${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Step 1: Stop containers
echo -e "${YELLOW}[1/5] Stopping containers...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Containers stopped${NC}"

# Step 2: Clear output files
echo -e "${YELLOW}[2/5] Clearing output files...${NC}"
rm -f data/output/*.json data/output/*.csv 2>/dev/null || true
echo -e "${GREEN}✓ Output files cleared${NC}"

# Step 3: Start fresh containers
echo -e "${YELLOW}[3/5] Starting fresh containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"

# Step 4: Wait for SQL Server
echo -e "${YELLOW}[4/5] Waiting for SQL Server to be ready...${NC}"
echo -n "    "
for i in {1..20}; do
    if docker exec ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
        -S localhost -U sa -P 'YourStrong@Passw0rd' \
        -Q "SELECT 1" -h -1 > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓ SQL Server is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Step 5: Verify database
echo -e "${YELLOW}[5/5] Verifying database...${NC}"

# Check database exists
DB_EXISTS=$(docker exec ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
    -S localhost -U sa -P 'YourStrong@Passw0rd' \
    -Q "SELECT COUNT(*) FROM sys.databases WHERE name = 'DentalDB'" -h -1 2>/dev/null | tr -d ' ')

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ DentalDB exists${NC}"
else
    echo -e "${RED}✗ DentalDB not found - may need to run init script${NC}"
fi

# Check tables
TABLE_COUNT=$(docker exec ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
    -S localhost -U sa -P 'YourStrong@Passw0rd' -d DentalDB \
    -Q "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'" -h -1 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -ge "4" ]; then
    echo -e "${GREEN}✓ Tables present ($TABLE_COUNT tables)${NC}"
else
    echo -e "${RED}✗ Expected 4+ tables, found $TABLE_COUNT${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}=== Reset Complete ===${NC}"
echo ""
echo "Ready for demo! Try:"
echo "  docker ps | grep ivoris"
echo "  python src/main.py --test-connection"
echo ""
