#!/bin/sh
# Health check script for JP2Forge Web
curl -f http://localhost:8000/health/ || exit 1