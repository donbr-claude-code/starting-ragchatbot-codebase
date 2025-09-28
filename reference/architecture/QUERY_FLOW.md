# Query Flow Narrative Walkthrough

## Overview
This document provides a detailed narrative walkthrough of how queries flow through the RAG chatbot system from user input to final response. The system uses a tool-based architecture where Claude AI dynamically decides when to search course content versus providing direct answers.

## System Initialization

### 1. Application Startup (`backend/app.py:78-82`)
When the FastAPI application starts, it automatically loads course documents:
- Reads all `.txt` files from the `/docs/` folder
- Processes each file through `document_processor.py`
- Stores course metadata in ChromaDB's `course_catalog` collection
- Stores text chunks with embeddings in `course_content` collection
- Reports loaded courses and chunk counts to console

### 2. Frontend Initialization (`frontend/index.html` + `frontend/script.js`)
The web interface initializes with:
- Session ID generation for conversation tracking
- WebSocket-style UI for real-time interaction
- Markdown rendering capability for formatted responses
- Source attribution display system

## Query Processing Pipeline

### Step 1: User Input Capture (`frontend/script.js:35-45`)
1. User types question in the chat interface
2. JavaScript captures the input and validates non-empty
3. Generates or retrieves existing session ID
4. Displays user message in chat interface immediately

### Step 2: API Request (`frontend/script.js:47-55`)
1. Frontend sends POST request to `/api/query` endpoint
2. Request payload includes:
   - `query`: User's question text
   - `session_id`: Unique conversation identifier
3. Shows loading indicator while waiting for response

### Step 3: Request Reception (`backend/app.py:57-66`)
1. FastAPI endpoint receives `QueryRequest` model
2. Validates query string is not empty
3. Passes to RAG system with session context
4. Handles any exceptions with proper HTTP error codes

### Step 4: RAG System Orchestration (`backend/rag_system.py:43-85`)
The RAG system coordinates the entire query processing:

1. **Session History Retrieval** (`session_manager.py:16-20`)
   - Fetches previous conversation history for context
   - Maintains configurable conversation window (default: 5 exchanges)

2. **Prompt Construction** (`rag_system.py:60-70`)
   - Combines system prompt with conversation history
   - Includes current query
   - Prepares for Claude API call

3. **Tool Registration** (`rag_system.py:36-42`)
   - Registers `search_course_content` tool for semantic search
   - Registers `get_course_outline` tool for structural queries
   - Provides tool schemas to Claude

### Step 5: AI Decision Making (`backend/ai_generator.py:24-95`)
Claude analyzes the query and decides:

1. **Direct Answer Path**
   - For general questions, greetings, or clarifications
   - No tool calls executed
   - Response generated from Claude's knowledge

2. **Content Search Path**
   - Detects course-related questions
   - Calls `search_course_content` tool with:
     - Query text for semantic search
     - Optional course name filter
     - Optional lesson number filter

3. **Course Structure Path**
   - Detects requests for course outlines or available courses
   - Calls `get_course_outline` tool
   - Returns structured course information

### Step 6: Tool Execution (`backend/search_tools.py:25-65`)
When Claude calls a search tool:

1. **Query Processing**
   - Extracts search parameters from tool call
   - Resolves fuzzy course names to exact matches
   - Prepares ChromaDB query

2. **Vector Search** (`backend/vector_store.py:84-130`)
   - Converts query to embedding using Sentence Transformers
   - Performs semantic similarity search in ChromaDB
   - Applies course/lesson filters if specified
   - Returns top K results (default: 5)

3. **Result Enhancement**
   - Includes course title and lesson info with each chunk
   - Provides source links when available
   - Formats results for Claude's consumption

### Step 7: Response Generation (`backend/ai_generator.py:96-120`)
Claude synthesizes the final response:

1. **With Search Results**
   - Analyzes retrieved course content
   - Synthesizes coherent answer from multiple sources
   - Maintains context from conversation history
   - Cites sources appropriately

2. **Without Search Results**
   - Provides direct answer
   - May suggest related topics
   - Maintains conversational flow

### Step 8: Response Processing (`backend/rag_system.py:86-95`)
The RAG system processes Claude's response:

1. **Source Extraction**
   - Parses response for source citations
   - Maps sources to course links
   - Maintains source attribution

2. **Session Update** (`session_manager.py:22-30`)
   - Adds query and response to conversation history
   - Maintains sliding window of conversations
   - Preserves context for follow-up questions

### Step 9: API Response (`backend/app.py:67-75`)
FastAPI returns `QueryResponse` model containing:
- `answer`: Claude's generated response
- `sources`: List of cited course materials
- `source_links`: Mapping of sources to URLs
- `session_id`: Conversation identifier

### Step 10: Frontend Display (`frontend/script.js:56-85`)
The web interface receives and displays:

1. **Message Rendering**
   - Parses markdown formatting
   - Highlights code blocks
   - Renders lists and formatting

2. **Source Attribution**
   - Displays cited sources below answer
   - Makes source titles clickable links
   - Shows course and lesson context

3. **UI Updates**
   - Removes loading indicator
   - Scrolls to show new message
   - Re-enables input field for next query

## Error Handling Paths

### Frontend Errors (`frontend/script.js:86-95`)
- Network failures show user-friendly error messages
- Timeout handling for long-running queries
- Graceful degradation on API failures

### Backend Errors
1. **API Level** (`backend/app.py:76-77`)
   - Returns appropriate HTTP status codes
   - Provides detailed error messages
   - Logs exceptions for debugging

2. **RAG System Level** (`backend/rag_system.py:96-105`)
   - Catches and logs search failures
   - Falls back to direct answers on tool failures
   - Maintains conversation continuity

3. **Vector Store Level** (`backend/vector_store.py:131-140`)
   - Handles ChromaDB connection issues
   - Manages embedding failures gracefully
   - Returns empty results on search errors

## Performance Optimizations

### Caching and Persistence
- ChromaDB persists embeddings to disk (`./chroma_db`)
- Course metadata cached in memory after initial load
- Session history maintained across queries

### Concurrent Processing
- Asynchronous FastAPI endpoints
- Parallel chunk processing during document loading
- Efficient batch embedding generation

### Resource Management
- Configurable chunk sizes (800 chars default)
- Limited context windows for Claude API
- Automatic conversation history pruning

## Key Design Decisions

### Tool-Based Architecture
The system uses Claude's tool-calling capability rather than always searching:
- Reduces unnecessary searches for simple questions
- Improves response time for non-course queries
- Allows intelligent decision-making about when to search

### Dual Collection Strategy
ChromaDB uses two collections:
- `course_catalog`: Fast course name resolution
- `course_content`: Semantic search on actual content
This separation optimizes both exact matching and semantic search.

### Context Enhancement
Text chunks include course and lesson context:
- Improves retrieval accuracy
- Enables filtering by course or lesson
- Provides better source attribution

### Session Management
Conversation history tracking enables:
- Multi-turn conversations with context
- Follow-up questions
- Clarifications and refinements

## File References

- Entry point: `backend/app.py:57` - `/api/query` endpoint
- Orchestration: `backend/rag_system.py:43` - `process_query()` method
- AI interaction: `backend/ai_generator.py:24` - `generate()` method
- Tool system: `backend/search_tools.py:25` - Tool class implementations
- Vector search: `backend/vector_store.py:84` - `search()` method
- Document processing: `backend/document_processor.py:17` - `process_course_file()`
- Session tracking: `backend/session_manager.py:16` - Session management
- Frontend handler: `frontend/script.js:35` - `sendMessage()` function