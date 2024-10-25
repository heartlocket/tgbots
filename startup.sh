#!/bin/bash

echo "Starting startup script at $(date)" | tee -a /home/LogFiles/startup.log

# Create and activate virtual environment
python -m venv /home/site/wwwroot/antenv
source /home/site/wwwroot/antenv/bin/activate

# Install required packages from requirements.txt
echo "Installing required packages..." | tee -a /home/LogFiles/startup.log
pip install -r requirements.txt | tee -a /home/LogFiles/startup.log

# Ensure log directory exists
mkdir -p /home/LogFiles

# Run the application with unbuffered output and logging
echo "Starting application..." | tee -a /home/LogFiles/startup.log
exec python -u app.py 2>&1 | tee -a /home/LogFiles/stdout.log