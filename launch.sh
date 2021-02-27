#!/bin/bash

# Move to installation dir
cd /opt/pr-panel

# Make sure we are always up-to-date
git pull

# Launch the app
python3 app.py

