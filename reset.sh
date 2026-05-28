#!/bin/bash
#
# JP2Forge Web Environment Reset Script
# Version 0.2.0
#
# Consolidates: quick_reset.sh and reset_environment.sh
#
# Usage:
#   ./reset.sh        - Interactive confirmation and full environment reset
#   ./reset.sh -y     - Non-interactive quick reset

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if non-interactive mode is selected
INTERACTIVE=true
if [ "$1" = "-y" ] || [ "$1" = "--yes" ] || [ "$1" = "--non-interactive" ] || [ "$1" = "quick" ]; then
    INTERACTIVE=false
fi

if [ "$INTERACTIVE" = "true" ]; then
    echo -e "${YELLOW}===================================================================${NC}"
    echo -e "${YELLOW}JP2FORGE WEB ENVIRONMENT RESET${NC}"
    echo -e "${YELLOW}===================================================================${NC}"
    echo ""
    echo "This script will perform a complete reset of your JP2Forge Web environment:"
    echo "  - Remove Python cache files and virtual environments"
    echo "  - Remove compiled static files"
    echo "  - Remove media files (uploaded images and results)"
    echo "  - Reset the database"
    echo "  - Remove log files"
    echo "  - Set up a fresh environment with all dependencies"
    echo ""
    read -p "Continue with the reset? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Reset canceled."
        exit 0
    fi
fi

# Ensure setup.sh is executable
chmod +x ./setup.sh 2>/dev/null || true

# Run setup.sh (which automatically stops services and cleans the directory)
if [ "$INTERACTIVE" = "true" ]; then
    ./setup.sh
else
    ./setup.sh --non-interactive
fi

echo -e "\n${GREEN}===================================================================${NC}"
echo -e "${GREEN}RESET COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo ""
echo "Your JP2Forge Web environment has been completely reset."
echo ""
echo "To start the development services:  ${BLUE}./dev.sh${NC}"
echo "To start services and view logs:    ${BLUE}./dev.sh start${NC}"
echo "To stop services:                   ${BLUE}./dev.sh stop${NC}"
echo "==================================================================="
