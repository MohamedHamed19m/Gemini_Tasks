#!/usr/bin/env bash
# Template verification script for Ralph loops
# Copy this to your project's .gemini/verify.sh

set -e

echo "Running verification..." >&2

# Run tests
if [ -f "package.json" ]; then
  npm test
fi

# Run linting
if [ -f ".eslintrc" ]; then
  npm run lint
fi

# Check build
if [ -f "package.json" ] && grep -q "build" package.json; then
  npm run build
fi

echo "✓ All verification passed" >&2
exit 0
