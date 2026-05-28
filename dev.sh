#!/bin/bash
#
# JP2Forge Web Service Manager
# Version 0.2.0
#
# Consolidates: start_dev.sh, start_celery.sh, monitor_redis.py, and manage_services.py
#
# Usage:
#   ./dev.sh          - Start Django server and Celery background worker
#   ./dev.sh start    - Start both services
#   ./dev.sh stop     - Stop Django and Celery processes
#   ./dev.sh status   - Check status of Django, Celery, and Redis
#   ./dev.sh restart  - Restart services
#   ./dev.sh clean    - Stop services and clean up temporary files

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Activate virtualenv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

check_redis() {
    echo -e "${YELLOW}Checking Redis status...${NC}"
    if ! command -v redis-cli &> /dev/null; then
        echo -e "${RED}Error: redis-cli is not installed or not in PATH.${NC}"
        return 1
    fi

    if ! redis-cli ping > /dev/null 2>&1; then
        echo -e "${YELLOW}Redis is not running. Attempting to start Redis...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start redis || true
        else
            sudo service redis-server start || sudo systemctl start redis-server || true
        fi
        sleep 2
        
        if ! redis-cli ping > /dev/null 2>&1; then
            echo -e "${RED}Error: Failed to start Redis. Redis is required for Celery broker.${NC}"
            return 1
        fi
    fi
    echo -e "${GREEN}✓ Redis is running${NC}"

    # Set stop-writes-on-bgsave-error to no
    python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    config = r.config_get('stop-writes-on-bgsave-error')
    if config.get('stop-writes-on-bgsave-error') == 'yes':
        r.config_set('stop-writes-on-bgsave-error', 'no')
        print('Disabled stop-writes-on-bgsave-error in Redis')
except Exception as e:
    print('Warning: could not configure Redis settings:', e)
" 2>/dev/null || true
    return 0
}

start_services() {
    check_redis || {
        echo -e "${RED}Cannot start services: Redis is unavailable.${NC}"
        exit 1
    }

    echo -e "${GREEN}Starting Django server and Celery worker...${NC}"
    echo -e "Press ${YELLOW}Ctrl+C${NC} to shut down both services."
    echo ""

    # Ensure logs folder exists
    mkdir -p logs

    # Trap Ctrl+C (SIGINT) and exit signals to terminate child processes
    trap 'echo -e "\n${YELLOW}Stopping background services...${NC}"; kill $(jobs -p) 2>/dev/null || true; exit 0' INT TERM EXIT

    # Start Celery worker in background
    celery -A jp2forge_web worker -l INFO > logs/celery.log 2>&1 &
    CELERY_PID=$!
    echo -e "${GREEN}✓ Celery worker started in background (PID: $CELERY_PID, logs at logs/celery.log)${NC}"

    # Start Django server in foreground
    python manage.py runserver
}

stop_services() {
    echo -e "${YELLOW}Stopping Django and Celery processes...${NC}"
    # Stop Django
    pkill -f "manage.py runserver" || true
    # Stop Celery
    pkill -f "celery -A jp2forge_web" || true
    echo -e "${GREEN}✓ Stopped all development processes${NC}"
}

check_status() {
    echo -e "${BLUE}=== JP2Forge Web Service Status ===${NC}"
    
    # Check Django
    if pgrep -f "manage.py runserver" > /dev/null; then
        echo -e "Django Server:  ${GREEN}RUNNING${NC}"
    else
        echo -e "Django Server:  ${RED}STOPPED${NC}"
    fi

    # Check Celery
    if pgrep -f "celery -A jp2forge_web" > /dev/null; then
        echo -e "Celery Worker:  ${GREEN}RUNNING${NC}"
    else
        echo -e "Celery Worker:  ${RED}STOPPED${NC}"
    fi

    # Check Redis
    if command -v redis-cli &> /dev/null && redis-cli ping > /dev/null 2>&1; then
        echo -e "Redis Server:   ${GREEN}RUNNING${NC}"
    else
        echo -e "Redis Server:   ${RED}STOPPED/UNAVAILABLE${NC}"
    fi
}

clean_env() {
    stop_services
    echo -e "${YELLOW}Cleaning temporary files...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf staticfiles 2>/dev/null || true
    rm -rf media/jobs/* 2>/dev/null || true
    rm -f *.log logs/*.log 2>/dev/null || true
    echo -e "${GREEN}✓ Clean complete${NC}"
}

# Main command router
case "$1" in
    stop)
        stop_services
        ;;
    status)
        check_status
        ;;
    clean)
        clean_env
        ;;
    restart)
        stop_services
        sleep 1
        start_services
        ;;
    start|"")
        start_services
        ;;
    *)
        echo "Usage: ./dev.sh [start|stop|restart|status|clean]"
        exit 1
        ;;
esac
