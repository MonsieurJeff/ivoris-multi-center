#!/bin/bash
#
# show-architecture.sh - Display architecture diagram for presentation
#
# Usage: ./scripts/show-architecture.sh
#

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear

echo -e "${BOLD}${BLUE}"
cat << 'EOF'
  ╔═══════════════════════════════════════════════════════════════════════════╗
  ║                                                                           ║
  ║   ██╗██╗   ██╗ ██████╗ ██████╗ ██╗███████╗    ██████╗ ██╗██████╗ ███████╗ ║
  ║   ██║██║   ██║██╔═══██╗██╔══██╗██║██╔════╝    ██╔══██╗██║██╔══██╗██╔════╝ ║
  ║   ██║██║   ██║██║   ██║██████╔╝██║███████╗    ██████╔╝██║██████╔╝█████╗   ║
  ║   ██║╚██╗ ██╔╝██║   ██║██╔══██╗██║╚════██║    ██╔═══╝ ██║██╔═══╝ ██╔══╝   ║
  ║   ██║ ╚████╔╝ ╚██████╔╝██║  ██║██║███████║    ██║     ██║██║     ███████╗ ║
  ║   ╚═╝  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝    ╚═╝     ╚═╝╚═╝     ╚══════╝ ║
  ║                                                                           ║
  ║              Multi-Center Extraction Pipeline                             ║
  ║                                                                           ║
  ╚═══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

sleep 1

echo -e "${BOLD}${YELLOW}THE PROBLEM:${NC}"
echo ""
echo -e "  ${RED}30 dental centers${NC}, each with ${RED}randomly generated${NC} table/column names:"
echo ""
echo -e "  ${CYAN}Center 1:${NC}  KARTEI_${RED}MN${NC}    → PATNR_${RED}NAN6${NC}, DATUM_${RED}3A4${NC}"
echo -e "  ${CYAN}Center 2:${NC}  KARTEI_${RED}8Y${NC}    → PATNR_${RED}DZ${NC},   DATUM_${RED}QW2${NC}"
echo -e "  ${CYAN}Center 3:${NC}  KARTEI_${RED}XQ4${NC}   → PATNR_${RED}R2Z5${NC}, DATUM_${RED}7M${NC}"
echo -e "  ${CYAN}...${NC}"
echo -e "  ${CYAN}Center 30:${NC} KARTEI_${RED}???${NC}   → PATNR_${RED}????${NC}, DATUM_${RED}???${NC}"
echo ""

sleep 2

echo -e "${BOLD}${GREEN}THE SOLUTION:${NC}"
echo ""
echo -e "${CYAN}"
cat << 'EOF'
  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │   30 Databases  │     │    Discovery    │     │    Extraction   │
  │   Random Names  │ ──► │ Pattern Matching│ ──► │    Parallel     │
  │                 │     │  Mapping Files  │     │   ThreadPool    │
  └─────────────────┘     └─────────────────┘     └─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  Human Review   │
                          │ reviewed: false │
                          │    ──────►      │
                          │ reviewed: true  │
                          └─────────────────┘
EOF
echo -e "${NC}"

sleep 2

echo -e "${BOLD}${YELLOW}KEY INSIGHT:${NC}"
echo ""
echo -e "  ${GREEN}KARTEI_MN${NC}    →  Strip suffix  →  ${BOLD}KARTEI${NC}     (canonical)"
echo -e "  ${GREEN}PATNR_NAN6${NC}   →  Strip suffix  →  ${BOLD}PATNR${NC}      (canonical)"
echo -e "  ${GREEN}DATUM_3A4${NC}    →  Strip suffix  →  ${BOLD}DATUM${NC}      (canonical)"
echo ""

sleep 2

echo -e "${BOLD}${BLUE}RESULTS:${NC}"
echo ""
echo -e "  ┌────────────────────────────────────────────┐"
echo -e "  │  ${GREEN}✓${NC} 30 centers extracted                    │"
echo -e "  │  ${GREEN}✓${NC} 466ms total time (target: 5000ms)       │"
echo -e "  │  ${GREEN}✓${NC} 10x faster than required                │"
echo -e "  │  ${GREEN}✓${NC} Zero code changes to add new center     │"
echo -e "  └────────────────────────────────────────────┘"
echo ""

echo -e "${BOLD}Commands:${NC}"
echo -e "  ${CYAN}python -m src.cli list${NC}              # See all centers"
echo -e "  ${CYAN}python -m src.cli discover-raw${NC}      # See the chaos"
echo -e "  ${CYAN}python -m src.cli show-mapping${NC}      # See the order"
echo -e "  ${CYAN}python -m src.cli benchmark${NC}         # See the speed"
echo ""
