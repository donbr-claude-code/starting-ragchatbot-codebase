#!/bin/bash

# Code formatting script for the RAG chatbot project

set -e

echo "🔧 Running code formatting tools..."

# Run Black formatter
echo "📝 Formatting code with Black..."
uv run --group dev black backend/ main.py

# Run isort for import sorting
echo "📦 Sorting imports with isort..."
uv run --group dev isort backend/ main.py

echo "✅ Code formatting complete!"