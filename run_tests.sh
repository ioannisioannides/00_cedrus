#!/bin/bash
# Script to run tests manually when VS Code discovery fails

# Activate virtual environment
source ./.venv/bin/activate

# Run pytest with verbose output
pytest --verbose
