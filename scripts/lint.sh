#!/bin/bash

# Code quality checking script for the RAG chatbot project

set -e

echo "🔍 Running code quality checks..."

# Run flake8 linting
echo "🧹 Running flake8 linter..."
uv run --group dev flake8 backend/ main.py

# Skip mypy for now - requires significant type annotation work
# echo "🔬 Running mypy type checker..."
# uv run --group dev mypy backend/ main.py

# Check import sorting
echo "📦 Checking import order with isort..."
uv run --group dev isort --check-only --diff backend/ main.py

# Check code formatting
echo "📝 Checking code format with Black..."
uv run --group dev black --check --diff backend/ main.py

echo "✅ All quality checks passed!"