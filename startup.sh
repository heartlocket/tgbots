#!/bin/bash

echo "Starting startup script at $(date)" | tee -a /home/LogFiles/startup.log

# Create virtual environment if it doesn't exist
if [ ! -d "/home/site/wwwroot/antenv" ]; then
    echo "Creating virtual environment..." | tee -a /home/LogFiles/startup.log
    python -m venv /home/site/wwwroot/antenv
    source /home/site/wwwroot/antenv/bin/activate
    pip install -r requirements.txt
else
    source /home/site/wwwroot/antenv/bin/activate
fi

# Run the application with unbuffered output and logging
exec python -u app.py 2>&1 | tee -a /home/LogFiles/stdout.log