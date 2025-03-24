#!/bin/bash

# Navigate to the working directory
cd ~/form-automation-worker || exit

# Activate the virtual environment
source venv/bin/activate

# Run the Python scripts with xvfb
xvfb-run -a --server-args='-screen 0 1920x1080x24' python3 tests/playwright_form_checks.py
xvfb-run -a --server-args='-screen 0 1920x1080x24' python3 tests/playwright_url_checks.py
