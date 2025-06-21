#!/bin/bash
# JP2Forge Web Environment Reset Script
# This script performs a complete reset of the JP2Forge Web application environment:
# 1. Cleans up Python cache, virtual envs, and other temporary files
# 2. Sets up a fresh virtual environment with all dependencies
# 3. Prepares the database and static files

set -e  # Exit on any error

echo "==================================================================="
echo "JP2FORGE WEB ENVIRONMENT RESET"
echo "==================================================================="
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

# Make sure the script is executable
chmod +x ./cleanup.py

echo ""
echo "Step 1: Cleaning up environment..."
echo "==================================================================="
python ./cleanup.py
echo ""

echo "Step 2: Setting up fresh environment..."
echo "==================================================================="
# Make setup.sh executable
chmod +x ./setup.sh

# Run setup script
./setup.sh

echo ""
echo "==================================================================="
echo "RESET COMPLETED SUCCESSFULLY!"
echo "==================================================================="
echo ""
echo "Your JP2Forge Web environment has been completely reset."
echo ""
echo "To start the development server:"
echo "  ./start_dev.sh"
echo ""
echo "To start the Celery worker (in a separate terminal):"
echo "  ./start_celery.sh"
echo ""