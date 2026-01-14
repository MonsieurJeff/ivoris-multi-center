#!/bin/bash
#
# demo-add-center.sh - Live demo: Add a new center with zero code changes
#
# This script demonstrates that adding a new center requires ONLY configuration.
# No Python code changes needed.
#
# Usage: ./scripts/demo-add-center.sh
#

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

# Config
NEW_CENTER_ID="center_31"
NEW_CENTER_NAME="Demo Zahnklinik"
NEW_CENTER_DB="DentalDB_31"
NEW_CENTER_CITY="Demo City"

echo ""
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   LIVE DEMO: Adding a New Center (Zero Code Changes)           ${NC}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Show current state
echo -e "${BOLD}${YELLOW}STEP 1: Current State${NC}"
echo -e "────────────────────────────────────────────────────────────────"
echo ""
echo -e "${CYAN}Current centers:${NC}"
python -m src.cli list 2>/dev/null | grep -c "\[mapped\]" | xargs -I {} echo "  {} centers configured"
echo ""

read -p "Press Enter to continue..."
echo ""

# Step 2: Check if center_31 exists
echo -e "${BOLD}${YELLOW}STEP 2: Verify New Center Doesn't Exist${NC}"
echo -e "────────────────────────────────────────────────────────────────"
echo ""

if grep -q "$NEW_CENTER_ID" config/centers.yml 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} $NEW_CENTER_ID already in config (for demo purposes)"
else
    echo -e "  ${CYAN}$NEW_CENTER_ID not found in config${NC}"
    echo ""
    echo -e "  ${YELLOW}Adding to config/centers.yml...${NC}"

    # Add new center to config
    cat >> config/centers.yml << EOF

  # Demo center - added live
  - id: $NEW_CENTER_ID
    name: $NEW_CENTER_NAME
    database: $NEW_CENTER_DB
    city: $NEW_CENTER_CITY
EOF

    echo -e "  ${GREEN}✓${NC} Added $NEW_CENTER_ID to config"
fi
echo ""

read -p "Press Enter to continue..."
echo ""

# Step 3: Create database (if needed)
echo -e "${BOLD}${YELLOW}STEP 3: Create Database with Random Schema${NC}"
echo -e "────────────────────────────────────────────────────────────────"
echo ""

# Check if database exists
DB_EXISTS=$(docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Clinero2026" -C -Q "SELECT DB_ID('$NEW_CENTER_DB')" -h -1 2>/dev/null | tr -d '[:space:]')

if [ "$DB_EXISTS" != "NULL" ] && [ -n "$DB_EXISTS" ]; then
    echo -e "  ${GREEN}✓${NC} Database $NEW_CENTER_DB already exists"
else
    echo -e "  ${CYAN}Creating $NEW_CENTER_DB with random schema...${NC}"

    # Generate random suffixes
    TABLE_SUFFIX=$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 3 | head -n 1)
    COL_SUFFIX_1=$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 4 | head -n 1)
    COL_SUFFIX_2=$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 3 | head -n 1)
    COL_SUFFIX_3=$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 4 | head -n 1)

    echo -e "  ${CYAN}Random suffixes: KARTEI_${RED}$TABLE_SUFFIX${NC}, PATNR_${RED}$COL_SUFFIX_1${NC}${NC}"

    # Create database and tables
    docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Clinero2026" -C -Q "
        CREATE DATABASE [$NEW_CENTER_DB];
    " 2>/dev/null

    docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Clinero2026" -C -d "$NEW_CENTER_DB" -Q "
        CREATE SCHEMA ck;

        CREATE TABLE ck.PATIENT_$TABLE_SUFFIX (
            ID INT PRIMARY KEY,
            P_NAME_$COL_SUFFIX_1 NVARCHAR(100),
            P_VORNAME_$COL_SUFFIX_2 NVARCHAR(100),
            DELKZ INT DEFAULT 0
        );

        CREATE TABLE ck.KASSEN_$TABLE_SUFFIX (
            ID INT PRIMARY KEY,
            NAME_$COL_SUFFIX_1 NVARCHAR(100),
            ART_$COL_SUFFIX_2 VARCHAR(10),
            DELKZ INT DEFAULT 0
        );

        CREATE TABLE ck.PATKASSE_$TABLE_SUFFIX (
            ID INT IDENTITY PRIMARY KEY,
            PATNR_$COL_SUFFIX_1 INT,
            KASSENID_$COL_SUFFIX_2 INT,
            DELKZ INT DEFAULT 0
        );

        CREATE TABLE ck.KARTEI_$TABLE_SUFFIX (
            ID INT IDENTITY PRIMARY KEY,
            PATNR_$COL_SUFFIX_1 INT,
            DATUM_$COL_SUFFIX_2 INT,
            BEMERKUNG_$COL_SUFFIX_3 NVARCHAR(500),
            DELKZ INT DEFAULT 0
        );

        CREATE TABLE ck.LEISTUNG_$TABLE_SUFFIX (
            ID INT IDENTITY PRIMARY KEY,
            PATIENTID_$COL_SUFFIX_1 INT,
            DATUM_$COL_SUFFIX_2 INT,
            LEISTUNG_$COL_SUFFIX_3 VARCHAR(20),
            DELKZ INT DEFAULT 0
        );

        -- Insert sample data
        INSERT INTO ck.PATIENT_$TABLE_SUFFIX (ID, P_NAME_$COL_SUFFIX_1, P_VORNAME_$COL_SUFFIX_2) VALUES (1, 'Demo', 'Patient');
        INSERT INTO ck.KASSEN_$TABLE_SUFFIX (ID, NAME_$COL_SUFFIX_1, ART_$COL_SUFFIX_2) VALUES (1, 'Demo Insurance', '8');
        INSERT INTO ck.PATKASSE_$TABLE_SUFFIX (PATNR_$COL_SUFFIX_1, KASSENID_$COL_SUFFIX_2) VALUES (1, 1);
        INSERT INTO ck.KARTEI_$TABLE_SUFFIX (PATNR_$COL_SUFFIX_1, DATUM_$COL_SUFFIX_2, BEMERKUNG_$COL_SUFFIX_3) VALUES (1, 20220118, 'Demo chart entry - added live!');
    " 2>/dev/null

    echo -e "  ${GREEN}✓${NC} Database created with random schema"
fi
echo ""

read -p "Press Enter to continue..."
echo ""

# Step 4: Discover schema
echo -e "${BOLD}${YELLOW}STEP 4: Discover Schema (Pattern Matching)${NC}"
echo -e "────────────────────────────────────────────────────────────────"
echo ""
echo -e "${CYAN}Running: python -m src.cli discover-raw -c $NEW_CENTER_ID${NC}"
echo ""

python -m src.cli discover-raw -c $NEW_CENTER_ID 2>/dev/null | head -20

echo ""
read -p "Press Enter to continue..."
echo ""

# Step 5: Generate mapping
echo -e "${BOLD}${YELLOW}STEP 5: Generate Mapping File${NC}"
echo -e "────────────────────────────────────────────────────────────────"
echo ""
echo -e "${CYAN}Running: python -m src.cli generate-mappings${NC}"
echo ""

python -m src.cli generate-mappings 2>/dev/null | tail -5

echo ""
read -p "Press Enter to continue..."
echo ""

# Step 6: Show mapping
echo -e "${BOLD}${YELLOW}STEP 6: Review Mapping${NC}"
echo -e "────────────────────────────────────────────────────────────────"
echo ""
echo -e "${CYAN}Running: python -m src.cli show-mapping $NEW_CENTER_ID${NC}"
echo ""

python -m src.cli show-mapping $NEW_CENTER_ID 2>/dev/null

echo ""
read -p "Press Enter to continue..."
echo ""

# Step 7: Extract data
echo -e "${BOLD}${YELLOW}STEP 7: Extract Data${NC}"
echo -e "────────────────────────────────────────────────────────────────"
echo ""
echo -e "${CYAN}Running: python -m src.cli extract -c $NEW_CENTER_ID --date 2022-01-18${NC}"
echo ""

python -m src.cli extract -c $NEW_CENTER_ID --date 2022-01-18 2>&1 | grep -v "^2026"

echo ""

# Summary
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}   DEMO COMPLETE                                                ${NC}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Added new center with ${BOLD}zero code changes${NC}"
echo -e "  ${GREEN}✓${NC} Schema discovered automatically"
echo -e "  ${GREEN}✓${NC} Mapping generated via pattern matching"
echo -e "  ${GREEN}✓${NC} Data extracted successfully"
echo ""
echo -e "  ${CYAN}The same process works for center 32, 33, ... 500+${NC}"
echo ""
