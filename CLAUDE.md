# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start

```bash
# Install dependencies
uv sync

# Set up environment variables (required)
cp .env.example .env
# Edit .env to add your ANTHROPIC_API_KEY

# Run the application
./run.sh
```

### Common Commands

```bash
# Manual start with debugging
cd backend && uv run uvicorn app:app --reload --port 8000 --log-level debug

# Check application health
curl http://localhost:8000/health

# Reset database (clears all indexed documents)
rm -rf backend/chroma_db
# Restart application to re-index documents from /docs

# Test query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this course about?", "session_id": "test123"}'
```

## Architecture Overview

This is a **Retrieval-Augmented Generation (RAG) chatbot** for course materials using a **tool-calling architecture** where Claude dynamically decides when to search the knowledge base.

### Core Pipeline Flow

1. **Document Ingestion** (`app.py:startup`): Loads all `.txt` files from `/docs` on startup
2. **Query Processing** (`rag_system.py:RAGSystem.query`): Main orchestrator that:
   - Builds conversation context from session history
   - Sends query to Claude with available search tools
   - Handles tool calls (search operations) when Claude requests them
   - Returns final response with source citations

3. **Tool Execution** (`search_tools.py`): Two tools available to Claude:
   - `search_course_content`: Semantic search with optional course/lesson filtering
   - `get_course_outline`: Returns structured course metadata and lesson lists

4. **Vector Search** (`vector_store.py:VectorStore`): Manages two ChromaDB collections:
   - `course_catalog`: Maps course names to IDs for fuzzy matching
   - `course_content`: Stores document chunks with embeddings for semantic search

### Key Architecture Decisions

**Tool-Based RAG**: Instead of searching for every query, Claude decides when to use search tools based on query context. This reduces unnecessary searches for general conversation.

**Course Name Resolution**: The system uses fuzzy matching to resolve course names (e.g., "course 1" → "Introduction to Machine Learning") via a separate catalog collection.

**Context-Enhanced Chunks**: Each text chunk is prefixed with course/lesson metadata during indexing to improve retrieval relevance: `"Course {title} Lesson {number} content: {chunk}"`

**Stateful Sessions**: Conversation history is maintained server-side with configurable window size (default: 2 exchanges) for context-aware responses.

### Document Format Requirements

Course documents in `/docs` must follow this structure:

```text
Course Title: [title]
Course Link: [url]
Course Instructor: [instructor]

Lesson 0: Introduction
Lesson Link: [lesson_url]
[content...]

Lesson 1: [title]
[content...]
```

The document processor (`document_processor.py`) expects:

- First 3 lines contain course metadata
- Lessons marked with pattern: `^Lesson\s+(\d+):\s*(.+)$`
- Lesson links (optional) on line immediately after lesson title

### Configuration Points

All configuration in `backend/config.py`:

- `ANTHROPIC_MODEL`: "claude-sonnet-4-20250514"
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2"
- `CHUNK_SIZE`: 800 chars
- `CHUNK_OVERLAP`: 100 chars
- `MAX_RESULTS`: 5 search results
- `MAX_HISTORY`: 2 conversation turns
- `CHROMA_PATH`: "./chroma_db"

### API Endpoints

- `GET /` - Web interface
- `POST /api/query` - Main query endpoint
  - Request: `{"query": string, "session_id": string?}`
  - Response: `{"response": string, "sources": [...], "session_id": string}`
- `POST /api/clear-session/{session_id}` - Clear conversation history
- `GET /health` - Health check

## Implementation Notes

**Dependencies**: Requires Python 3.13+, managed via `uv`. Key packages: chromadb==1.0.15, anthropic==0.58.2, fastapi==0.116.1, sentence-transformers==5.0.0

**Error Boundaries**: Each component has try-catch blocks with fallback behavior. Network failures, API errors, and search failures return user-friendly messages.

**Tool Registration**: New tools must inherit from `Tool` abstract class (`search_tools.py`) and be registered in `RAGSystem.__init__` (`rag_system.py:22-26`)

**Windows Users**: Use Git Bash to run shell scripts and commands

## Reference Documentation

The `/reference/` folder contains supplementary documentation:

### Architecture Documentation (`/reference/architecture/`)

- **QUERY_FLOW.md**: Detailed narrative walkthrough of the query processing pipeline with specific line references
- **QUERY_FLOW_DIAGRAM.md**: ASCII block diagrams showing system architecture and data flow
- **QUERY_FLOW_MERMAID.md**: Mermaid diagrams for system visualization (flowcharts, sequence diagrams, component diagrams)

These documents provide deep-dive explanations of how queries flow through the system, from user input through tool execution to response generation.

### Playwright MCP Integration (`/reference/playwright-mcp-wsl-quickstart.md`)

Quick setup guide for using Playwright MCP server with Claude Code on WSL for browser automation testing. Includes configuration for headless Chromium and troubleshooting tips.
