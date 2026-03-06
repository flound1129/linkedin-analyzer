#!/usr/bin/env bash
# Run all tests for the HiredScore optimizer
set -euo pipefail
cd "$(dirname "$0")/.."
source venv/bin/activate
echo "Running unit tests..."
python -m pytest tests/ -v --ignore=tests/test_integration.py
echo ""
echo "Running integration tests (requires ANTHROPIC_API_KEY)..."
python -m pytest tests/test_integration.py -v
