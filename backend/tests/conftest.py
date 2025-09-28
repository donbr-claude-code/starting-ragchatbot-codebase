import pytest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config
from vector_store import VectorStore
from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from ai_generator import AIGenerator
from rag_system import RAGSystem
from models import Course, Lesson, CourseChunk


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
        is_empty=Mock(return_value=False)
    )

    mock_store._resolve_course_name.return_value = "Test Course"
    mock_store.get_existing_course_titles.return_value = ["Test Course"]

    return mock_store


@pytest.fixture
def sample_course():
    """Sample course data for testing"""
    lessons = [
        Lesson(lesson_number=0, title="Introduction", lesson_link="http://example.com/lesson0"),
        Lesson(lesson_number=1, title="Basic Concepts", lesson_link="http://example.com/lesson1"),
        Lesson(lesson_number=2, title="Advanced Topics", lesson_link="http://example.com/lesson2")
    ]

    course = Course(
        title="Introduction to Machine Learning",
        course_link="http://example.com/course",
        instructor="Dr. Test",
        lessons=lessons
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
            chunk_index=0
        ),
        CourseChunk(
            content="We will cover basic concepts and terminology.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=1
        ),
        CourseChunk(
            content="Advanced topics include neural networks and deep learning.",
            course_title=sample_course.title,
            lesson_number=2,
            chunk_index=2
        )
    ]

    return chunks


@pytest.fixture
def real_vector_store(test_config):
    """Real vector store instance for integration testing"""
    store = VectorStore(
        chroma_path=test_config.CHROMA_PATH,
        embedding_model=test_config.EMBEDDING_MODEL,
        max_results=test_config.MAX_RESULTS
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
def cleanup_test_files():
    """Cleanup any test files created during testing"""
    yield
    # Cleanup code can be added here if needed