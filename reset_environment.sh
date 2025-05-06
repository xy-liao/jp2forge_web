#!/bin/bash
# JP2Forge Web Environment Reset Script
# This script helps ensure a clean environment before and after tests

# Show usage if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  echo "JP2Forge Web Environment Reset Script"
  echo ""
  echo "Usage: ./reset_environment.sh [command]"
  echo ""
  echo "Commands:"
  echo "  clean    Stop all services and clean environment (default)"
  echo "  start    Start all services after cleaning"
  echo "  restart  Stop, clean, and restart all services"
  echo "  status   Check status of all services"
  echo ""
  echo "Examples:"
  echo "  ./reset_environment.sh           # Stop services and clean environment"
  echo "  ./reset_environment.sh clean     # Same as above"
  echo "  ./reset_environment.sh start     # Start all services"
  echo "  ./reset_environment.sh restart   # Full restart of all services"
  echo "  ./reset_environment.sh status    # Check what's running"
  exit 0
fi

# Set default command if not provided
COMMAND=${1:-clean}

# Check if pip and psutil are installed
check_dependencies() {
  echo "Checking dependencies..."
  
  # Check for psutil
  if ! python -c "import psutil" &>/dev/null; then
    echo "Installing required Python package: psutil"
    pip install psutil
  fi
}

# Main execution
echo "JP2Forge Web Environment Manager"
echo "================================"

# Ensure dependencies are installed
check_dependencies

# Execute the requested command
case "$COMMAND" in
  clean)
    echo "Stopping all services and cleaning environment..."
    python manage_services.py clean
    ;;
  start)
    echo "Starting all services..."
    python manage_services.py start
    ;;
  restart)
    echo "Restarting all services..."
    python manage_services.py restart
    ;;
  status)
    echo "Checking service status..."
    python manage_services.py status
    ;;
  *)
    echo "Unknown command: $COMMAND"
    echo "Use --help for usage information"
    exit 1
    ;;
esac

echo "Done!"
exit 0