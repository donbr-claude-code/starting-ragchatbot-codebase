# Complete Query Flow: Frontend to Backend

This document traces the end-to-end process of how a user query is handled from the frontend interface through the backend RAG system.

## Overview

The system processes user queries through an 8-step pipeline that combines FastAPI, Claude AI, semantic search, and dynamic tool execution to provide intelligent responses about course materials.

## 1. Frontend: User Input
**File**: `frontend/script.js:45-96`

- User types query and clicks send or presses Enter
- **Input validation**: Checks if query is not empty
- **UI updates**: Disables input, adds user message to chat, shows loading animation
- **HTTP request**: POST to `/api/query` with JSON payload:
  ```json
  {
    "query": "user's question",
    "session_id": "current_session_id_or_null"
  }
  ```

## 2. Backend: API Endpoint
**File**: `backend/app.py:56-74`

- FastAPI receives POST request at `/api/query`
- **Session handling**: Creates new session if none provided
- **RAG processing**: Calls `rag_system.query(request.query, session_id)`
- **Response formatting**: Returns `QueryResponse` with answer, sources, and session_id

## 3. RAG System Orchestration
**File**: `backend/rag_system.py:102-140`

- **Prompt creation**: Formats user query as `"Answer this question about course materials: {query}"`
- **History retrieval**: Gets conversation history from session if exists
- **AI generation**: Calls `ai_generator.generate_response()` with:
  - Query prompt
  - Conversation history
  - Available tools (search functionality)
  - Tool manager for execution

## 4. AI Generation with Tools
**File**: `backend/ai_generator.py:43-87`

- **Claude API call**: Sends request to Anthropic with:
  - System prompt (specialized for course assistance)
  - User query
  - Available tools definition
  - Conversation history
- **Tool execution**: If Claude decides to search, executes tool calls
- **Follow-up response**: Gets final answer after tool results

## 5. Tool Execution
**File**: `backend/search_tools.py:52-86`

- **CourseSearchTool**: Executes semantic search with parameters:
  - `query`: What to search for
  - `course_name`: Optional course filter
  - `lesson_number`: Optional lesson filter
- **Vector search**: Calls `vector_store.search()` method
- **Result formatting**: Formats results with course/lesson context
- **Source tracking**: Stores sources for UI display

## 6. Vector Search
**File**: `backend/vector_store.py:61-100`

- **Course resolution**: If course name provided, resolves to exact title using semantic matching
- **Filter building**: Creates ChromaDB filter for course/lesson constraints
- **Semantic search**: Queries ChromaDB with:
  - Embedded query vector
  - Content filters
  - Result limit (default 5)
- **Result packaging**: Returns `SearchResults` with documents, metadata, distances

## 7. Response Assembly

- **AI synthesis**: Claude processes search results into natural language answer
- **Source extraction**: Tool manager collects sources from search
- **Session update**: Adds query/response to conversation history
- **Return**: RAG system returns `(answer, sources)` tuple

## 8. Frontend: Response Display
**File**: `frontend/script.js:76-96`

- **JSON parsing**: Extracts answer, sources, session_id from response
- **UI updates**:
  - Removes loading animation
  - Displays AI response (with markdown rendering)
  - Shows collapsible sources section if sources exist
  - Updates session_id for future queries
- **Re-enable input**: User can ask next question

## Key Data Flow Points

- **ChromaDB**: Stores course chunks with embeddings for semantic search
- **Session Manager**: Maintains conversation context across queries
- **Tool System**: Enables Claude to search course content dynamically
- **Markdown**: Frontend renders AI responses with formatting
- **Error Handling**: Each layer handles failures gracefully with user feedback

## Architecture Highlights

The system uses a sophisticated RAG pipeline where Claude dynamically decides whether to search course content based on the user's question, enabling both general knowledge responses and specific course content queries.

### Tool-Based Search
Claude has access to a `search_course_content` tool that it can invoke when questions require specific course information. This allows for:
- Intelligent search decisions (not every query triggers a search)
- Parametric filtering by course name and lesson number
- Source attribution for transparency

### Session Management
Each conversation maintains context through session IDs, allowing for:
- Multi-turn conversations
- Contextual follow-up questions
- Conversation history for better responses

### Error Resilience
Each component handles errors gracefully:
- Network failures show user-friendly messages
- Search failures don't break the conversation
- Malformed responses are caught and handled