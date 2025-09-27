# RAG System Query Flow - Mermaid Diagrams

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[User Interface<br/>index.html]
        JS[JavaScript Logic<br/>script.js]
        CSS[Styling<br/>style.css]
    end

    subgraph "API Layer"
        API[FastAPI Endpoint<br/>/api/query]
        CORS[CORS Middleware]
        STATIC[Static File Server]
    end

    subgraph "RAG System Core"
        RAG[RAG Orchestrator<br/>rag_system.py]
        SESSION[Session Manager<br/>session_manager.py]
        AI[AI Generator<br/>ai_generator.py]
    end

    subgraph "Search & Tools"
        TOOLS[Tool Manager<br/>search_tools.py]
        SEARCH[Course Search Tool]
        VECTOR[Vector Store<br/>vector_store.py]
    end

    subgraph "Data Processing"
        PROC[Document Processor<br/>document_processor.py]
        MODELS[Data Models<br/>models.py]
        CONFIG[Configuration<br/>config.py]
    end

    subgraph "External Services"
        CLAUDE[Anthropic Claude API]
        CHROMA[(ChromaDB<br/>Vector Database)]
        EMBED[Sentence Transformers<br/>Embeddings]
    end

    UI --> JS
    JS --> API
    API --> RAG
    RAG --> SESSION
    RAG --> AI
    AI --> CLAUDE
    AI --> TOOLS
    TOOLS --> SEARCH
    SEARCH --> VECTOR
    VECTOR --> CHROMA
    VECTOR --> EMBED
    PROC --> MODELS
    PROC --> CHROMA

    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef search fill:#fff3e0
    classDef data fill:#fce4ec
    classDef external fill:#f1f8e9

    class UI,JS,CSS frontend
    class API,CORS,STATIC api
    class RAG,SESSION,AI core
    class TOOLS,SEARCH,VECTOR search
    class PROC,MODELS,CONFIG data
    class CLAUDE,CHROMA,EMBED external
```

## 2. Query Processing Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend<br/>(script.js)
    participant A as FastAPI<br/>(app.py)
    participant R as RAG System<br/>(rag_system.py)
    participant AI as AI Generator<br/>(ai_generator.py)
    participant C as Claude API
    participant T as Tool Manager<br/>(search_tools.py)
    participant V as Vector Store<br/>(vector_store.py)
    participant DB as ChromaDB

    U->>F: Types query & clicks send
    F->>F: Validate input & show loading
    F->>A: POST /api/query {query, session_id}

    A->>A: Create session if needed
    A->>R: rag_system.query(query, session_id)

    R->>R: Format prompt
    R->>R: Get conversation history
    R->>AI: generate_response(prompt, history, tools)

    AI->>C: Claude API call with tools
    C->>C: Analyze query & decide tool usage

    alt Claude decides to search
        C-->>AI: Tool use request
        AI->>T: execute_tool("search_course_content")
        T->>V: search(query, course_name, lesson_number)
        V->>V: Resolve course name (if provided)
        V->>V: Build search filters
        V->>DB: Semantic search query
        DB-->>V: Results with embeddings
        V-->>T: Formatted search results
        T-->>AI: Tool execution result
        AI->>C: Claude API call with tool results
        C-->>AI: Final synthesized response
    else Claude answers directly
        C-->>AI: Direct response (no search needed)
    end

    AI-->>R: Generated response
    R->>R: Extract sources from tool manager
    R->>R: Update conversation history
    R-->>A: (response, sources)

    A-->>F: JSON {answer, sources, session_id}
    F->>F: Remove loading animation
    F->>F: Display response with sources
    F->>F: Re-enable input field
```

## 3. Data Flow Architecture

```mermaid
flowchart LR
    subgraph Input["📥 Input Processing"]
        USER[User Query]
        VALIDATE[Input Validation]
        SESSION[Session Management]
    end

    subgraph Processing["⚙️ Query Processing"]
        PROMPT[Prompt Creation]
        HISTORY[History Retrieval]
        AI_CALL[Claude API Call]
    end

    subgraph Decision["🤔 AI Decision Making"]
        ANALYZE[Query Analysis]
        DECIDE{Search Needed?}
        DIRECT[Direct Response]
        SEARCH[Tool Search]
    end

    subgraph Search["🔍 Search Execution"]
        RESOLVE[Course Resolution]
        FILTER[Filter Building]
        VECTOR_SEARCH[Vector Search]
        FORMAT[Result Formatting]
    end

    subgraph Storage["💾 Data Storage"]
        CHROMA[(ChromaDB)]
        CATALOG[Course Catalog]
        CONTENT[Course Content]
    end

    subgraph Output["📤 Output Generation"]
        SYNTHESIS[Response Synthesis]
        SOURCES[Source Collection]
        DISPLAY[UI Display]
    end

    USER --> VALIDATE
    VALIDATE --> SESSION
    SESSION --> PROMPT
    PROMPT --> HISTORY
    HISTORY --> AI_CALL
    AI_CALL --> ANALYZE
    ANALYZE --> DECIDE

    DECIDE -->|No| DIRECT
    DECIDE -->|Yes| SEARCH

    SEARCH --> RESOLVE
    RESOLVE --> FILTER
    FILTER --> VECTOR_SEARCH
    VECTOR_SEARCH --> CHROMA
    CHROMA --> CATALOG
    CHROMA --> CONTENT
    CONTENT --> FORMAT

    DIRECT --> SYNTHESIS
    FORMAT --> SYNTHESIS
    SYNTHESIS --> SOURCES
    SOURCES --> DISPLAY

    classDef inputStyle fill:#e3f2fd
    classDef processStyle fill:#f3e5f5
    classDef decisionStyle fill:#fff3e0
    classDef searchStyle fill:#e8f5e8
    classDef storageStyle fill:#fce4ec
    classDef outputStyle fill:#f1f8e9

    class USER,VALIDATE,SESSION inputStyle
    class PROMPT,HISTORY,AI_CALL processStyle
    class ANALYZE,DECIDE,DIRECT,SEARCH decisionStyle
    class RESOLVE,FILTER,VECTOR_SEARCH,FORMAT searchStyle
    class CHROMA,CATALOG,CONTENT storageStyle
    class SYNTHESIS,SOURCES,DISPLAY outputStyle
```

## 4. Component Interaction Network

```mermaid
graph TB
    subgraph "User Interface"
        UI[Web Interface]
    end

    subgraph "Application Layer"
        API[FastAPI Router]
        RAG[RAG Orchestrator]
    end

    subgraph "AI Processing"
        GEN[AI Generator]
        TOOLS[Tool Manager]
        SEARCH[Search Tool]
    end

    subgraph "Data Layer"
        VS[Vector Store]
        SM[Session Manager]
        DP[Document Processor]
    end

    subgraph "External APIs"
        CLAUDE[Claude API]
    end

    subgraph "Databases"
        VDB[(Vector DB)]
        FS[(File System)]
    end

    UI <==> API
    API <==> RAG
    RAG <==> GEN
    RAG <==> SM
    GEN <==> CLAUDE
    GEN <==> TOOLS
    TOOLS <==> SEARCH
    SEARCH <==> VS
    VS <==> VDB
    DP <==> FS
    DP <==> VDB

    %% Connection labels
    UI -.->|"HTTP Requests"| API
    API -.->|"Query Processing"| RAG
    RAG -.->|"Response Generation"| GEN
    GEN -.->|"Tool Execution"| TOOLS
    VS -.->|"Semantic Search"| VDB
```

## 5. Error Handling Flow

```mermaid
flowchart TD
    START[User Query] --> VALIDATE{Input Valid?}

    VALIDATE -->|No| UI_ERROR[Show Input Error]
    VALIDATE -->|Yes| SEND[Send to Backend]

    SEND --> API_CHECK{API Available?}
    API_CHECK -->|No| NETWORK_ERROR[Network Error Display]
    API_CHECK -->|Yes| PROCESS[Process Query]

    PROCESS --> RAG_CHECK{RAG Processing OK?}
    RAG_CHECK -->|No| SERVER_ERROR[Server Error Display]
    RAG_CHECK -->|Yes| AI_CALL[Call Claude API]

    AI_CALL --> AI_CHECK{AI Response OK?}
    AI_CHECK -->|No| AI_ERROR[AI Error Handling]
    AI_CHECK -->|Yes| SEARCH_DECISION{Search Needed?}

    SEARCH_DECISION -->|No| DIRECT_RESPONSE[Direct Response]
    SEARCH_DECISION -->|Yes| VECTOR_SEARCH[Vector Search]

    VECTOR_SEARCH --> SEARCH_CHECK{Search Results?}
    SEARCH_CHECK -->|No| NO_RESULTS[No Results Message]
    SEARCH_CHECK -->|Yes| FORMAT_RESULTS[Format Results]

    DIRECT_RESPONSE --> SUCCESS[Display Response]
    FORMAT_RESULTS --> SUCCESS
    NO_RESULTS --> SUCCESS

    UI_ERROR --> RETRY[Allow Retry]
    NETWORK_ERROR --> RETRY
    SERVER_ERROR --> RETRY
    AI_ERROR --> RETRY

    RETRY --> START

    classDef errorStyle fill:#ffebee,stroke:#f44336
    classDef successStyle fill:#e8f5e8,stroke:#4caf50
    classDef processStyle fill:#e3f2fd,stroke:#2196f3

    class UI_ERROR,NETWORK_ERROR,SERVER_ERROR,AI_ERROR,NO_RESULTS errorStyle
    class SUCCESS successStyle
    class VALIDATE,SEND,PROCESS,AI_CALL,VECTOR_SEARCH processStyle
```

## 6. Session Management Flow

```mermaid
stateDiagram-v2
    [*] --> NewUser

    NewUser --> CreateSession : First Query
    CreateSession --> ActiveSession : Session ID Generated

    ActiveSession --> ProcessQuery : User Query
    ProcessQuery --> UpdateHistory : Response Generated
    UpdateHistory --> ActiveSession : History Stored

    ActiveSession --> SessionTimeout : Inactivity
    SessionTimeout --> [*]

    ActiveSession --> UserLeaves : Browser Close
    UserLeaves --> [*]

    note right of CreateSession
        Generate unique session ID
        Initialize conversation history
    end note

    note right of UpdateHistory
        Store query-response pair
        Maintain context window
    end note
```

## 7. Document Processing Pipeline

```mermaid
flowchart LR
    subgraph Input["📄 Input Sources"]
        FILES[Course Files<br/>*.txt]
        METADATA[Course Metadata<br/>Title, Instructor, Links]
    end

    subgraph Processing["⚙️ Processing Pipeline"]
        READ[File Reading<br/>UTF-8 Encoding]
        PARSE[Structure Parsing<br/>Lessons & Content]
        CHUNK[Text Chunking<br/>Sentence-based]
        CONTEXT[Context Enhancement<br/>Course/Lesson Labels]
    end

    subgraph Storage["💾 Vector Storage"]
        EMBED[Generate Embeddings<br/>Sentence Transformers]
        CATALOG[Store in Catalog<br/>Course Metadata]
        CONTENT[Store in Content<br/>Text Chunks]
    end

    subgraph Database["🗄️ ChromaDB Collections"]
        CATALOG_DB[(Course Catalog<br/>Collection)]
        CONTENT_DB[(Course Content<br/>Collection)]
    end

    FILES --> READ
    METADATA --> PARSE
    READ --> PARSE
    PARSE --> CHUNK
    CHUNK --> CONTEXT
    CONTEXT --> EMBED
    EMBED --> CATALOG
    EMBED --> CONTENT
    CATALOG --> CATALOG_DB
    CONTENT --> CONTENT_DB

    classDef inputStyle fill:#e3f2fd
    classDef processStyle fill:#f3e5f5
    classDef storageStyle fill:#e8f5e8
    classDef dbStyle fill:#fff3e0

    class FILES,METADATA inputStyle
    class READ,PARSE,CHUNK,CONTEXT processStyle
    class EMBED,CATALOG,CONTENT storageStyle
    class CATALOG_DB,CONTENT_DB dbStyle
```

These Mermaid diagrams provide a comprehensive visual representation of your RAG system that will render natively in GitHub, GitLab, and most modern documentation platforms.