# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Set up environment variables (required)
cp .env.example .env
# Edit .env to add your ANTHROPIC_API_KEY
```

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Access Points
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Architecture Overview

This is a **Retrieval-Augmented Generation (RAG) chatbot system** for querying course materials. The architecture follows a tool-based approach where Claude AI dynamically decides when to search course content.

### Core Components Architecture

**Frontend (`/frontend/`)**: Simple HTML/CSS/JavaScript web interface that communicates with the backend via REST API.

**Backend (`/backend/`)**: FastAPI application organized around the RAG pipeline:

- **`app.py`**: FastAPI router and startup logic that loads initial documents from `/docs` folder
- **`rag_system.py`**: **Main orchestrator** - coordinates all components and manages the query processing pipeline
- **`ai_generator.py`**: Claude API integration with tool calling capabilities
- **`search_tools.py`**: Tool system that enables Claude to search course content dynamically
- **`vector_store.py`**: ChromaDB interface with unified search and course resolution
- **`document_processor.py`**: Processes course documents into structured chunks with context
- **`session_manager.py`**: Maintains conversation context across queries
- **`models.py`**: Data models for Course, Lesson, and CourseChunk

### Query Processing Flow

1. **Frontend** sends JSON query to `/api/query` endpoint
2. **RAG System** creates prompt and retrieves conversation history
3. **AI Generator** calls Claude with available tools (search functionality)
4. **Claude decides** whether to search course content based on query type
5. **Search Tool** executes semantic search if needed, with optional course/lesson filtering
6. **Vector Store** performs ChromaDB search with course name resolution
7. **Response** synthesized by Claude and returned with source attribution

### Key Design Patterns

**Tool-Based Search**: Claude has access to a `search_course_content` tool with parameters for `query`, `course_name`, and `lesson_number`. This enables intelligent search decisions rather than searching for every query.

**Document Structure**: Course files follow this expected format:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [instructor]

Lesson 0: Introduction
Lesson Link: [lesson_url]
[content...]
```

**Context Enhancement**: Text chunks are prefixed with course and lesson context (e.g., "Course {title} Lesson {number} content: {chunk}") to improve retrieval accuracy.

**Dual ChromaDB Collections**:
- `course_catalog`: Course metadata for name resolution
- `course_content`: Actual text chunks with embeddings

### Configuration

All settings are centralized in `backend/config.py`:
- **Embedding Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Chunk Size**: 800 characters with 100 character overlap
- **Claude Model**: `claude-sonnet-4-20250514`
- **Database Path**: `./chroma_db` (created automatically)

### Document Processing Pipeline

Documents in `/docs/` are automatically loaded on startup. The processor:
1. Extracts course metadata from first 3 lines
2. Parses lessons using regex pattern `^Lesson\s+(\d+):\s*(.+)$`
3. Chunks text using sentence boundaries with smart overlap
4. Enhances chunks with course/lesson context
5. Stores in ChromaDB with embeddings

### Session Management

Each conversation gets a unique session ID that maintains:
- Conversation history (configurable window size)
- Context for multi-turn conversations
- Source attribution across queries

## Important Implementation Notes

**Environment Requirements**: Python 3.13+, requires ANTHROPIC_API_KEY in `.env` file.

**Dependencies**: Uses `uv` package manager. Core dependencies include ChromaDB 1.0.15, Anthropic 0.58.2, FastAPI 0.116.1, and sentence-transformers 5.0.0.

**Course Data**: Place course files (*.txt) in `/docs/` directory. They will be automatically processed on application startup.

**Error Handling**: Each layer handles failures gracefully - network errors, search failures, and API issues are caught and presented as user-friendly messages.
- always use uv to run the server.  do not use pip to run it directly
- make sure to use uv for all dependencies