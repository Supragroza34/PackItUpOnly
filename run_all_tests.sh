#!/usr/bin/env bash
set -e

# Root of the project
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Running backend (Django) tests ==="
cd "$ROOT_DIR"

# Activate virtualenv if it exists
if [ -d "venv" ]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

python3 manage.py test

echo
echo "=== Running frontend (React) tests ==="
cd "$ROOT_DIR/frontend"

# Run Jest tests once (no watch mode)
npm test -- --watch=false

echo
echo "All tests completed."

