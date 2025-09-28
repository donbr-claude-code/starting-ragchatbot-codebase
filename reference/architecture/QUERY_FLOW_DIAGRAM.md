# Query Flow ASCII Diagram

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            RAG Chatbot System Architecture                     │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐                  ┌──────────────────────────────────────────┐
│                 │                  │            Backend (FastAPI)              │
│    Frontend     │                  │                                          │
│   (HTML/JS)     │                  │  ┌────────────────────────────────────┐ │
│                 │     HTTP/REST    │  │         app.py                     │ │
│ ┌─────────────┐ │ ──────────────> │  │    - API Endpoints                │ │
│ │   index.    │ │                  │  │    - CORS Middleware              │ │
│ │    html     │ │                  │  │    - Static File Serving         │ │
│ └─────────────┘ │                  │  │    - Startup Document Loading    │ │
│                 │                  │  └────────────┬──────────────────────┘ │
│ ┌─────────────┐ │                  │               │                         │
│ │  script.js  │ │                  │               ▼                         │
│ │             │ │  <───────────    │  ┌────────────────────────────────────┐ │
│ └─────────────┘ │   JSON Response  │  │      rag_system.py                │ │
│                 │                  │  │   - Query Processing              │ │
│ ┌─────────────┐ │                  │  │   - Tool Registration             │ │
│ │  style.css  │ │                  │  │   - Response Synthesis            │ │
│ └─────────────┘ │                  │  └──────┬──────────────┬─────────────┘ │
│                 │                  │         │              │                │
└─────────────────┘                  │         ▼              ▼                │
                                     │  ┌──────────────┐ ┌──────────────────┐ │
                                     │  │ ai_generator │ │ search_tools.py  │ │
                                     │  │     .py      │ │                  │ │
                                     │  │              │ │ - SearchContent  │ │
                                     │  │   Claude     │ │   Tool           │ │
                                     │  │     API      │ │ - GetOutline     │ │
                                     │  │ Integration  │ │   Tool           │ │
                                     │  └──────────────┘ └────────┬──────────┘ │
                                     │                            │            │
                                     │         ┌──────────────────┴───────┐    │
                                     │         ▼                          ▼    │
                                     │  ┌──────────────┐          ┌────────────┐│
                                     │  │vector_store. │          │  session_  ││
                                     │  │     py       │          │  manager.  ││
                                     │  │              │          │     py     ││
                                     │  │  ChromaDB    │          │            ││
                                     │  │  Interface   │          │  History   ││
                                     │  └──────┬───────┘          │  Tracking  ││
                                     │         │                  └────────────┘│
                                     │         ▼                                │
                                     │  ┌──────────────────────────────────┐   │
                                     │  │        document_processor.py     │   │
                                     │  │                                  │   │
                                     │  │   - Course File Parsing         │   │
                                     │  │   - Text Chunking               │   │
                                     │  │   - Context Enhancement         │   │
                                     │  └──────────────┬───────────────────┘   │
                                     │                 │                       │
                                     └─────────────────┼───────────────────────┘
                                                       │
                                     ┌─────────────────▼───────────────────────┐
                                     │           External Services              │
                                     │                                          │
                                     │  ┌────────────────────────────────────┐ │
                                     │  │         ChromaDB (Local)           │ │
                                     │  │                                    │ │
                                     │  │  Collections:                     │ │
                                     │  │  - course_catalog (metadata)      │ │
                                     │  │  - course_content (chunks)        │ │
                                     │  └────────────────────────────────────┘ │
                                     │                                          │
                                     │  ┌────────────────────────────────────┐ │
                                     │  │       Anthropic Claude API         │ │
                                     │  │                                    │ │
                                     │  │  - claude-3-sonnet model          │ │
                                     │  │  - Tool calling capability         │ │
                                     │  └────────────────────────────────────┘ │
                                     │                                          │
                                     │  ┌────────────────────────────────────┐ │
                                     │  │    Sentence Transformers           │ │
                                     │  │                                    │ │
                                     │  │  - all-MiniLM-L6-v2 model        │ │
                                     │  │  - Embedding generation            │ │
                                     │  └────────────────────────────────────┘ │
                                     │                                          │
                                     └──────────────────────────────────────────┘
```

## Query Flow Sequence

```
User                Frontend            Backend API          RAG System         AI Generator
 │                     │                     │                    │                  │
 ├──Enter Query───────>│                     │                    │                  │
 │                     │                     │                    │                  │
 │                     ├──POST /api/query──->│                    │                  │
 │                     │                     │                    │                  │
 │                     │                     ├──process_query()──>│                  │
 │                     │                     │                    │                  │
 │                     │                     │                    ├──get_history()──>│
 │                     │                     │                    │                  │
 │                     │                     │                    ├──generate()─────>│
 │                     │                     │                    │                  ├──Claude API
 │                     │                     │                    │                  │
 │                     │                     │                    │                  ├──Tool Decision
 │                     │                     │                    │                  │
 │                     │                     │                    │<──tool_call──────┤
 │                     │                     │                    │                  │
 │                     │                     │                    ├──search()───────>│
 │                     │                     │                    │                  ├──ChromaDB
 │                     │                     │                    │<──results────────┤
 │                     │                     │                    │                  │
 │                     │                     │                    ├──generate()─────>│
 │                     │                     │                    │                  ├──Claude API
 │                     │                     │                    │<──response───────┤
 │                     │                     │                    │                  │
 │                     │                     │                    ├──save_history()─>│
 │                     │                     │                    │                  │
 │                     │                     │<──return_response──┤                  │
 │                     │                     │                    │                  │
 │                     │<──JSON Response─────┤                    │                  │
 │                     │                     │                    │                  │
 │<──Display Response──┤                     │                    │                  │
 │                     │                     │                    │                  │
```

## Data Storage Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           File System Layout                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  /project_root/                                                        │
│      │                                                                 │
│      ├── /docs/                    [Course Content - DATA]            │
│      │    ├── course1.txt          Automatically loaded on startup    │
│      │    ├── course2.txt          Processed into ChromaDB           │
│      │    └── course3.txt          User-queryable content            │
│      │                                                                 │
│      ├── /backend/                 [Application Code]                 │
│      │    ├── app.py                                                  │
│      │    ├── rag_system.py                                          │
│      │    ├── ai_generator.py                                        │
│      │    ├── search_tools.py                                        │
│      │    ├── vector_store.py                                        │
│      │    ├── document_processor.py                                  │
│      │    ├── session_manager.py                                     │
│      │    ├── config.py                                             │
│      │    └── models.py                                             │
│      │                                                                 │
│      ├── /frontend/                [Web Interface]                    │
│      │    ├── index.html                                             │
│      │    ├── script.js                                              │
│      │    └── style.css                                              │
│      │                                                                 │
│      ├── /reference/               [Documentation - META]             │
│      │    └── /architecture/       System documentation              │
│      │         ├── QUERY_FLOW.md                                     │
│      │         ├── QUERY_FLOW_DIAGRAM.md                            │
│      │         └── QUERY_FLOW_MERMAID.md                           │
│      │                                                                 │
│      ├── /chroma_db/               [Vector Database]                  │
│      │    ├── /course_catalog/     Course metadata collection        │
│      │    └── /course_content/     Text chunks with embeddings       │
│      │                                                                 │
│      └── CLAUDE.md                 [Project Instructions]             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Interactions

```
┌──────────────────────────────────────────────────────────────┐
│                    Component Dependencies                     │
└──────────────────────────────────────────────────────────────┘

                           app.py
                             │
                             ▼
                       rag_system.py
                        /    │    \
                       /     │     \
                      /      │      \
                     ▼       ▼       ▼
            ai_generator  search   session
                .py       tools    manager
                │           │         │
                │           ▼         │
                │      vector_store   │
                │           │         │
                │           ▼         │
                │      document       │
                │      processor      │
                │           │         │
                └───────────┴─────────┘
                            │
                            ▼
                    External Services
                  (Claude, ChromaDB,
                   SentenceTransformers)
```

## Tool-Based Decision Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Claude's Tool Decision Logic               │
└─────────────────────────────────────────────────────────────┘

                    User Query
                        │
                        ▼
                ┌───────────────┐
                │  Claude AI    │
                │  Analyzes     │
                │  Query        │
                └───────┬───────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
   Query about                    General question
   course content?                or greeting?
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│ Call search_     │          │ Direct response  │
│ course_content   │          │ (no tool call)   │
│ tool             │          └──────────────────┘
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ChromaDB Search  │
│ - Semantic       │
│ - Course filter  │
│ - Lesson filter  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Synthesize       │
│ Response with    │
│ Sources          │
└──────────────────┘
```

## Session Management Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Tracking                         │
└─────────────────────────────────────────────────────────────┘

    New User ──────> Generate Session ID
                            │
                            ▼
                    ┌───────────────┐
                    │  First Query  │
                    └───────┬───────┘
                            │
                            ▼
                    Store in Session:
                    - Query
                    - Response
                    - Sources
                            │
                            ▼
                    ┌───────────────┐
                    │ Follow-up     │
                    │ Query         │
                    └───────┬───────┘
                            │
                            ▼
                    Retrieve History
                    (last 5 exchanges)
                            │
                            ▼
                    Include in Context
                    for Claude
                            │
                            ▼
                    Generate Contextual
                    Response
                            │
                            ▼
                    Update Session
                    (sliding window)
```

## Error Handling Paths

```
┌─────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                      │
└─────────────────────────────────────────────────────────────┘

                      API Request
                          │
                          ▼
                  ┌───────────────┐
                  │  Validation   │
                  │  Error?       │
                  └───────┬───────┘
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
            HTTP 422            Continue
            Validation             │
            Error                  ▼
                          ┌───────────────┐
                          │  ChromaDB     │
                          │  Error?       │
                          └───────┬───────┘
                                  │
                        ┌─────────┴─────────┐
                        │                   │
                        ▼                   ▼
                    Log Error          Continue
                    Return Empty           │
                    Results                ▼
                          ┌───────────────┐
                          │  Claude API   │
                          │  Error?       │
                          └───────┬───────┘
                                  │
                        ┌─────────┴─────────┐
                        │                   │
                        ▼                   ▼
                    HTTP 503          Success
                    Service              │
                    Unavailable          ▼
                                    Return
                                    Response
```