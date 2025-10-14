#!/bin/bash
# SMCP Server Start Script

# Activate virtual environment
source ../venv/bin/activate

# Start SMCP server with auto-reload and log to file
python smcp.py --allow-external 2>&1 | tee server.log