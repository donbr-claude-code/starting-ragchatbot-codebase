# Query Flow Mermaid Diagrams

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[index.html<br/>User Interface]
        JS[script.js<br/>API Client]
        CSS[style.css<br/>Styling]
    end

    subgraph "Backend API Layer"
        APP[app.py<br/>FastAPI Server]
        RAG[rag_system.py<br/>Query Orchestrator]
    end

    subgraph "Core Processing"
        AI[ai_generator.py<br/>Claude Integration]
        TOOLS[search_tools.py<br/>Search & Outline Tools]
        VECTOR[vector_store.py<br/>ChromaDB Interface]
        DOC[document_processor.py<br/>Text Processing]
        SESSION[session_manager.py<br/>Conversation History]
    end

    subgraph "Data Storage"
        DOCS[(docs/<br/>Course Files)]
        CHROMA[(ChromaDB<br/>Vector Store)]
        SESSIONS[(Session<br/>Memory)]
    end

    subgraph "External Services"
        CLAUDE[Claude API<br/>claude-3-sonnet]
        SBERT[Sentence Transformers<br/>all-MiniLM-L6-v2]
    end

    UI --> JS
    JS --> |HTTP POST /api/query| APP
    APP --> |process_query()| RAG
    RAG --> AI
    RAG --> TOOLS
    RAG --> SESSION
    AI --> |API calls| CLAUDE
    TOOLS --> VECTOR
    VECTOR --> |embeddings| SBERT
    VECTOR --> |search| CHROMA
    DOC --> |process files| DOCS
    DOC --> |store chunks| CHROMA
    SESSION --> SESSIONS
    APP --> |startup| DOC

    classDef frontend fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef backend fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef ragcore fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef tools fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef external fill:#f1f8e9,stroke:#689f38,stroke-width:2px

    class UI,JS,CSS frontend
    class APP,RAG backend
    class AI,SESSION ragcore
    class TOOLS,VECTOR,DOC tools
    class DOCS,CHROMA,SESSIONS storage
    class CLAUDE,SBERT external
```

## Query Processing Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend<br/>(script.js)
    participant A as API<br/>(app.py)
    participant R as RAG System<br/>(rag_system.py)
    participant AI as AI Generator<br/>(ai_generator.py)
    participant T as Search Tools<br/>(search_tools.py)
    participant V as Vector Store<br/>(vector_store.py)
    participant C as Claude API
    participant S as Session Manager<br/>(session_manager.py)

    U->>F: Enter query
    F->>F: Generate/retrieve session_id
    F->>A: POST /api/query<br/>{query, session_id}
    A->>R: process_query(query, session_id)

    R->>S: get_history(session_id)
    S-->>R: Return conversation history

    R->>AI: generate(prompt, tools, history)
    AI->>C: API call with tools schema

    alt Claude decides to search
        C-->>AI: Tool call: search_course_content
        AI->>T: execute_search(params)
        T->>V: search(query, filters)
        V->>V: Generate embeddings
        V->>V: ChromaDB similarity search
        V-->>T: Return chunks
        T-->>AI: Return results
        AI->>C: Continue with search results
    else Claude answers directly
        C-->>AI: Direct response
    end

    C-->>AI: Final response
    AI-->>R: Response with sources

    R->>S: add_to_history(query, response)
    R-->>A: QueryResponse
    A-->>F: JSON response
    F->>F: Render markdown
    F->>U: Display answer + sources
```

## Data Flow Diagram

```mermaid
flowchart LR
    subgraph "Input Sources"
        COURSE[Course Files<br/>docs/*.txt]
        USER[User Query]
    end

    subgraph "Processing Pipeline"
        PROC[document_processor.py]
        CHUNK[Text Chunker]
        EMBED[Embedding Generator]
        STORE[ChromaDB Storage]
    end

    subgraph "Query Pipeline"
        QUERY[Query Processor]
        SEARCH[Semantic Search]
        FILTER[Course/Lesson Filter]
        RANK[Result Ranking]
    end

    subgraph "Response Generation"
        CONTEXT[Context Builder]
        CLAUDE[Claude AI]
        FORMAT[Response Formatter]
    end

    COURSE --> |startup| PROC
    PROC --> |parse| CHUNK
    CHUNK --> |chunks| EMBED
    EMBED --> |vectors| STORE

    USER --> QUERY
    QUERY --> SEARCH
    SEARCH --> |similarity| STORE
    STORE --> FILTER
    FILTER --> RANK
    RANK --> CONTEXT

    CONTEXT --> CLAUDE
    CLAUDE --> FORMAT
    FORMAT --> |JSON| USER

    classDef input fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef process fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef query fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef response fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

    class COURSE,USER input
    class PROC,CHUNK,EMBED,STORE process
    class QUERY,SEARCH,FILTER,RANK query
    class CONTEXT,CLAUDE,FORMAT response
```

## Tool Decision Flow

```mermaid
flowchart TD
    START[User Query Received]
    ANALYZE[Claude Analyzes Query]

    COURSE_Q{Is it about<br/>course content?}
    OUTLINE_Q{Is it about<br/>course structure?}

    SEARCH_TOOL[Call search_course_content]
    OUTLINE_TOOL[Call get_course_outline]
    DIRECT[Generate Direct Response]

    EXEC_SEARCH[Execute ChromaDB Search]
    GET_OUTLINE[Retrieve Course Outlines]

    SYNTH[Synthesize Response<br/>with Sources]
    RETURN[Return to User]

    START --> ANALYZE
    ANALYZE --> COURSE_Q

    COURSE_Q -->|Yes| SEARCH_TOOL
    COURSE_Q -->|No| OUTLINE_Q

    OUTLINE_Q -->|Yes| OUTLINE_TOOL
    OUTLINE_Q -->|No| DIRECT

    SEARCH_TOOL --> EXEC_SEARCH
    OUTLINE_TOOL --> GET_OUTLINE

    EXEC_SEARCH --> SYNTH
    GET_OUTLINE --> SYNTH
    DIRECT --> RETURN
    SYNTH --> RETURN

    classDef decision fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef tool fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef action fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef terminal fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class COURSE_Q,OUTLINE_Q decision
    class SEARCH_TOOL,OUTLINE_TOOL,EXEC_SEARCH,GET_OUTLINE tool
    class ANALYZE,DIRECT,SYNTH action
    class START,RETURN terminal
```

## Error Handling Flow

```mermaid
flowchart TD
    REQ[API Request]

    VAL{Valid<br/>Request?}
    VAL_ERR[HTTP 422<br/>Validation Error]

    PROC[Process Query]

    CHROME_CHK{ChromaDB<br/>Available?}
    CHROME_ERR[Log Error<br/>Return Empty Results]

    CLAUDE_CHK{Claude API<br/>Available?}
    CLAUDE_ERR[HTTP 503<br/>Service Unavailable]

    SEARCH_CHK{Search<br/>Successful?}
    SEARCH_FALLBACK[Use Direct Response]

    SUCCESS[Return Response]

    REQ --> VAL
    VAL -->|No| VAL_ERR
    VAL -->|Yes| PROC

    PROC --> CHROME_CHK
    CHROME_CHK -->|No| CHROME_ERR
    CHROME_CHK -->|Yes| CLAUDE_CHK

    CHROME_ERR --> CLAUDE_CHK

    CLAUDE_CHK -->|No| CLAUDE_ERR
    CLAUDE_CHK -->|Yes| SEARCH_CHK

    SEARCH_CHK -->|No| SEARCH_FALLBACK
    SEARCH_CHK -->|Yes| SUCCESS

    SEARCH_FALLBACK --> SUCCESS

    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef check fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef fallback fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef success fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class VAL_ERR,CHROME_ERR,CLAUDE_ERR error
    class VAL,CHROME_CHK,CLAUDE_CHK,SEARCH_CHK check
    class SEARCH_FALLBACK fallback
    class SUCCESS success
```

## Session Management State Diagram

```mermaid
stateDiagram-v2
    [*] --> NewUser: First Visit

    NewUser --> GenerateID: Create Session
    GenerateID --> EmptyHistory: Initialize

    EmptyHistory --> FirstQuery: User Query
    FirstQuery --> StoreFirst: Save Q&A

    StoreFirst --> HasHistory: Session Active

    HasHistory --> NextQuery: Follow-up Query
    NextQuery --> LoadHistory: Retrieve Context
    LoadHistory --> ProcessWithContext: Include History
    ProcessWithContext --> UpdateHistory: Save New Q&A

    UpdateHistory --> CheckWindow: Check Size
    CheckWindow --> PruneOld: If > 5 exchanges
    CheckWindow --> HasHistory: If <= 5 exchanges
    PruneOld --> HasHistory: Maintain Window

    HasHistory --> ClearSession: User Clears
    ClearSession --> EmptyHistory: Reset

    HasHistory --> [*]: Session Ends
```

## Document Processing Pipeline

```mermaid
flowchart TD
    subgraph "Document Input"
        FILE[Course File<br/>docs/*.txt]
        META[Extract Metadata<br/>Lines 1-3]
        LESSONS[Parse Lessons<br/>Regex Pattern]
    end

    subgraph "Text Processing"
        SPLIT[Split by Sentences]
        CHUNK[Create Chunks<br/>800 chars]
        OVERLAP[Add Overlap<br/>100 chars]
        ENHANCE[Add Context<br/>Course + Lesson]
    end

    subgraph "Storage"
        CATALOG[(course_catalog<br/>Metadata)]
        CONTENT[(course_content<br/>Chunks)]
        EMBED[Generate<br/>Embeddings]
    end

    FILE --> META
    FILE --> LESSONS

    LESSONS --> SPLIT
    SPLIT --> CHUNK
    CHUNK --> OVERLAP
    OVERLAP --> ENHANCE

    META --> CATALOG
    ENHANCE --> EMBED
    EMBED --> CONTENT

    classDef input fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef process fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class FILE,META,LESSONS input
    class SPLIT,CHUNK,OVERLAP,ENHANCE,EMBED process
    class CATALOG,CONTENT storage
```

## Component Dependency Graph

```mermaid
graph TD
    APP[app.py]
    RAG[rag_system.py]
    AI[ai_generator.py]
    TOOLS[search_tools.py]
    VECTOR[vector_store.py]
    DOC[document_processor.py]
    SESSION[session_manager.py]
    CONFIG[config.py]
    MODELS[models.py]

    APP --> RAG
    APP --> CONFIG

    RAG --> AI
    RAG --> TOOLS
    RAG --> SESSION
    RAG --> CONFIG

    AI --> CONFIG

    TOOLS --> VECTOR
    TOOLS --> ABC[ABC Abstract Base]

    VECTOR --> DOC
    VECTOR --> CONFIG
    VECTOR --> MODELS

    DOC --> MODELS
    DOC --> CONFIG

    SESSION --> CONFIG

    classDef entry fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef core fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef support fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef config fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class APP entry
    class RAG,AI,SESSION core
    class TOOLS,VECTOR,DOC support
    class CONFIG,MODELS config
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Local Development Environment"
        DEV_TERM[Terminal<br/>./run.sh]
        DEV_APP[FastAPI Server<br/>localhost:8000]
        DEV_CHROME[ChromaDB<br/>./chroma_db]
        DEV_DOCS[Course Docs<br/>./docs]
    end

    subgraph "User Access"
        BROWSER[Web Browser]
        API_CLIENT[API Client<br/>curl/Postman]
    end

    subgraph "External Dependencies"
        CLAUDE_API[Anthropic API<br/>claude.ai]
        PYPI[Python Packages<br/>via uv]
    end

    DEV_TERM --> |starts| DEV_APP
    DEV_APP --> |loads| DEV_DOCS
    DEV_APP --> |initializes| DEV_CHROME

    BROWSER --> |HTTP| DEV_APP
    API_CLIENT --> |REST| DEV_APP

    DEV_APP --> |API calls| CLAUDE_API
    DEV_TERM --> |installs| PYPI

    classDef local fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef access fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef external fill:#f1f8e9,stroke:#689f38,stroke-width:2px

    class DEV_TERM,DEV_APP,DEV_CHROME,DEV_DOCS local
    class BROWSER,API_CLIENT access
    class CLAUDE_API,PYPI external
```

## Legend

### Color Coding
- 🔵 **Blue** (frontend): User interface components
- 🟣 **Purple** (backend): API and server components
- 🟢 **Green** (ragcore): Core RAG system logic
- 🟠 **Orange** (tools): Search and processing tools
- 🩷 **Pink** (storage): Data storage components
- 🟢 **Pale Green** (external): External services

### Diagram Types
1. **System Architecture**: High-level component overview
2. **Sequence Diagram**: Step-by-step query processing
3. **Data Flow**: How data moves through the system
4. **Tool Decision**: Claude's decision-making logic
5. **Error Handling**: Failure recovery paths
6. **Session State**: Conversation management states
7. **Document Pipeline**: Course file processing
8. **Dependencies**: Component relationships
9. **Deployment**: Runtime architecture

## Validation
These diagrams can be validated using:
- **GitHub**: Renders in markdown preview
- **Mermaid Live Editor**: https://mermaid.live/
- **VS Code**: With Mermaid preview extension
- **Command Line**: `npx @mermaid-js/mermaid-cli -i QUERY_FLOW_MERMAID.md -o output.svg`