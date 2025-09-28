#!/bin/bash

# Complete quality assurance script for the RAG chatbot project

set -e

echo "🚀 Running complete quality assurance pipeline..."

# Install dev dependencies if not already installed
echo "📥 Ensuring dev dependencies are installed..."
uv sync --group dev

# Format code first
echo "🔧 Step 1: Auto-formatting code..."
./scripts/format.sh

# Run quality checks
echo "🔍 Step 2: Running quality checks..."
./scripts/lint.sh

# Run tests
echo "🧪 Step 3: Running tests..."
uv run pytest backend/tests/ -v

echo "🎉 Complete quality assurance pipeline finished successfully!"