#!/bin/bash
echo "Starting startup script..."
python -u app.py 2>&1 | tee -a /home/LogFiles/stdout.log