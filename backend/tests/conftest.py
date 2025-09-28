import os
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai_generator import AIGenerator
from config import Config
from models import Course, CourseChunk, Lesson
from rag_system import RAGSystem
from search_tools import CourseOutlineTool, CourseSearchTool, ToolManager
from vector_store import VectorStore


@pytest.fixture
def test_config():
    """Test configuration with temporary paths"""
    config = Config()
    config.CHROMA_PATH = tempfile.mkdtemp()
    config.ANTHROPIC_API_KEY = "sk-test-key-for-testing"
    config.MAX_RESULTS = 3
    config.CHUNK_SIZE = 500
    config.CHUNK_OVERLAP = 50
    return config


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    mock_store = Mock(spec=VectorStore)

    # Setup default return values
    mock_store.search.return_value = Mock(
        documents=["Test document content"],
        metadata=[{"course_title": "Test Course", "lesson_number": 1}],
        distances=[0.1],
        error=None,
        is_empty=Mock(return_value=False),
    )

    mock_store._resolve_course_name.return_value = "Test Course"
    mock_store.get_existing_course_titles.return_value = ["Test Course"]

    return mock_store


@pytest.fixture
def sample_course():
    """Sample course data for testing"""
    lessons = [
        Lesson(
            lesson_number=0,
            title="Introduction",
            lesson_link="http://example.com/lesson0",
        ),
        Lesson(
            lesson_number=1,
            title="Basic Concepts",
            lesson_link="http://example.com/lesson1",
        ),
        Lesson(
            lesson_number=2,
            title="Advanced Topics",
            lesson_link="http://example.com/lesson2",
        ),
    ]

    course = Course(
        title="Introduction to Machine Learning",
        course_link="http://example.com/course",
        instructor="Dr. Test",
        lessons=lessons,
    )

    return course


@pytest.fixture
def sample_course_chunks(sample_course):
    """Sample course chunks for testing"""
    chunks = [
        CourseChunk(
            content="This is an introduction to machine learning concepts.",
            course_title=sample_course.title,
            lesson_number=0,
            chunk_index=0,
        ),
        CourseChunk(
            content="We will cover basic concepts and terminology.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=1,
        ),
        CourseChunk(
            content="Advanced topics include neural networks and deep learning.",
            course_title=sample_course.title,
            lesson_number=2,
            chunk_index=2,
        ),
    ]

    return chunks


@pytest.fixture
def real_vector_store(test_config):
    """Real vector store instance for integration testing"""
    store = VectorStore(
        chroma_path=test_config.CHROMA_PATH,
        embedding_model=test_config.EMBEDDING_MODEL,
        max_results=test_config.MAX_RESULTS,
    )

    yield store

    # Cleanup
    if os.path.exists(test_config.CHROMA_PATH):
        shutil.rmtree(test_config.CHROMA_PATH)


@pytest.fixture
def populated_vector_store(real_vector_store, sample_course, sample_course_chunks):
    """Vector store populated with test data"""
    real_vector_store.add_course_metadata(sample_course)
    real_vector_store.add_course_content(sample_course_chunks)
    return real_vector_store


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing AI generator"""
    mock_client = Mock()

    # Mock successful response without tools
    mock_response = Mock()
    mock_response.content = [Mock(text="This is a test response")]
    mock_response.stop_reason = "end_turn"

    mock_client.messages.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_anthropic_client_with_tools():
    """Mock Anthropic client that uses tools"""
    mock_client = Mock()

    # Mock tool use response
    tool_use_response = Mock()
    tool_use_response.stop_reason = "tool_use"

    # Mock tool use content block
    tool_content = Mock()
    tool_content.type = "tool_use"
    tool_content.name = "search_course_content"
    tool_content.id = "test_tool_id"
    tool_content.input = {"query": "test query"}

    tool_use_response.content = [tool_content]

    # Mock final response after tool execution
    final_response = Mock()
    final_response.content = [Mock(text="Response based on tool results")]

    # Setup sequence of responses
    mock_client.messages.create.side_effect = [tool_use_response, final_response]

    return mock_client


@pytest.fixture
def test_app():
    """Create a test FastAPI app without static file mounting issues"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from pydantic import BaseModel
    from typing import List, Optional, Dict

    # Create test app without static file mounting
    app = FastAPI(title="Course Materials RAG System", root_path="")

    # Add middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Pydantic models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        source_links: Dict[str, str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    # Mock RAG system for testing
    mock_rag = Mock()
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Test Course 1", "Test Course 2"]
    }
    mock_rag.query.return_value = (
        "This is a test response",
        ["Test source 1", "Test source 2"],
        {"Test source 1": "http://example.com/1", "Test source 2": "http://example.com/2"}
    )
    mock_rag.session_manager.create_session.return_value = "test_session_123"
    mock_rag.session_manager.clear_session.return_value = None

    # API Routes
    @app.get("/health")
    async def health_check():
        try:
            analytics = mock_rag.get_course_analytics()
            return {
                "status": "healthy",
                "total_courses": analytics["total_courses"],
                "components": {
                    "vector_store": "ok",
                    "rag_system": "ok"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "components": {
                    "vector_store": "error",
                    "rag_system": "error"
                }
            }

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag.session_manager.create_session()

            answer, sources, source_links = mock_rag.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                source_links=source_links,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/sessions/{session_id}/clear")
    async def clear_session(session_id: str):
        try:
            mock_rag.session_manager.clear_session(session_id)
            return {"message": "Session cleared successfully", "session_id": session_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Store mock for access in tests
    app.state.mock_rag = mock_rag

    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI app"""
    return TestClient(test_app)


@pytest.fixture
def mock_rag_system(test_config):
    """Mock RAG system for testing"""
    mock_rag = Mock(spec=RAGSystem)

    # Setup default responses
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Introduction to Machine Learning", "Advanced Deep Learning"]
    }

    mock_rag.query.return_value = (
        "This is a test response about machine learning.",
        ["Course: Introduction to Machine Learning, Lesson 1"],
        {"Course: Introduction to Machine Learning, Lesson 1": "http://example.com/course1/lesson1"}
    )

    # Mock session manager
    mock_session_manager = Mock()
    mock_session_manager.create_session.return_value = "test_session_123"
    mock_session_manager.clear_session.return_value = None
    mock_rag.session_manager = mock_session_manager

    return mock_rag


@pytest.fixture
def sample_api_requests():
    """Sample API request data for testing"""
    return {
        "valid_query": {
            "query": "What is machine learning?",
            "session_id": "test_session_123"
        },
        "query_without_session": {
            "query": "Explain neural networks"
        },
        "empty_query": {
            "query": "",
            "session_id": "test_session_123"
        },
        "invalid_json": '{"query": "test", "invalid": }'
    }


@pytest.fixture
def cleanup_test_files():
    """Cleanup any test files created during testing"""
    yield
    # Cleanup code can be added here if needed
