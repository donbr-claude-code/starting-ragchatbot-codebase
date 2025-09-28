import os
import shutil
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
from config import Config
from models import Course, CourseChunk, Lesson
from rag_system import RAGSystem


class TestRAGSystemIntegration:
    """Integration tests for the complete RAG system"""

    @pytest.fixture
    def test_rag_system(self):
        """Create a test RAG system with temporary storage"""
        config = Config()
        config.CHROMA_PATH = tempfile.mkdtemp()
        config.ANTHROPIC_API_KEY = "sk-test-key-for-testing"
        config.MAX_RESULTS = 3
        config.CHUNK_SIZE = 500
        config.CHUNK_OVERLAP = 50

        rag_system = RAGSystem(config)

        yield rag_system

        # Cleanup
        if os.path.exists(config.CHROMA_PATH):
            shutil.rmtree(config.CHROMA_PATH)

    @pytest.fixture
    def populated_rag_system(self, test_rag_system):
        """RAG system populated with test data"""
        # Create test course
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

        # Create test chunks
        chunks = [
            CourseChunk(
                content="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                course_title=course.title,
                lesson_number=0,
                chunk_index=0,
            ),
            CourseChunk(
                content="Supervised learning uses labeled data to train models for prediction tasks.",
                course_title=course.title,
                lesson_number=1,
                chunk_index=1,
            ),
            CourseChunk(
                content="Neural networks are inspired by biological neural networks and can learn complex patterns.",
                course_title=course.title,
                lesson_number=2,
                chunk_index=2,
            ),
        ]

        # Add data to RAG system
        test_rag_system.vector_store.add_course_metadata(course)
        test_rag_system.vector_store.add_course_content(chunks)

        return test_rag_system

    def test_rag_system_initialization(self, test_rag_system):
        """Test RAG system components are properly initialized"""
        assert test_rag_system.document_processor is not None
        assert test_rag_system.vector_store is not None
        assert test_rag_system.ai_generator is not None
        assert test_rag_system.session_manager is not None
        assert test_rag_system.tool_manager is not None

        # Check tools are registered
        tool_definitions = test_rag_system.tool_manager.get_tool_definitions()
        tool_names = [tool["name"] for tool in tool_definitions]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    def test_add_course_document_success(self, test_rag_system):
        """Test adding a course document successfully"""
        # Create a temporary course file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Course Title: Test Course\n")
            f.write("Course Link: http://example.com/course\n")
            f.write("Course Instructor: Test Instructor\n")
            f.write("\n")
            f.write("Lesson 0: Introduction\n")
            f.write("Lesson Link: http://example.com/lesson0\n")
            f.write("This is the introduction to the course.\n")
            f.write("\n")
            f.write("Lesson 1: Main Content\n")
            f.write(
                "This is the main content of the course with lots of detailed information.\n"
            )
            temp_file = f.name

        try:
            course, chunk_count = test_rag_system.add_course_document(temp_file)

            assert course is not None
            assert course.title == "Test Course"
            assert course.instructor == "Test Instructor"
            assert len(course.lessons) == 2
            assert chunk_count > 0

            # Verify data was added to vector store
            assert test_rag_system.get_course_analytics()["total_courses"] == 1

        finally:
            os.unlink(temp_file)

    def test_add_course_document_error(self, test_rag_system):
        """Test handling of document processing errors"""
        # Try to add a non-existent file
        course, chunk_count = test_rag_system.add_course_document(
            "/nonexistent/file.txt"
        )

        assert course is None
        assert chunk_count == 0

    @patch("rag_system.anthropic.Anthropic")
    def test_query_without_tool_use(self, mock_anthropic, populated_rag_system):
        """Test query that doesn't trigger tool use"""
        # Mock Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="This is a general knowledge response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response

        # Patch the ai_generator client
        populated_rag_system.ai_generator.client = mock_client

        response, sources, source_links = populated_rag_system.query("What is 2+2?")

        assert response == "This is a general knowledge response"
        assert sources == []
        assert source_links == {}

        # Verify AI generator was called with tools
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        assert "tools" in call_args
        assert (
            len(call_args["tools"]) == 2
        )  # search_course_content and get_course_outline

    @patch("rag_system.anthropic.Anthropic")
    def test_query_with_tool_use(self, mock_anthropic, populated_rag_system):
        """Test query that triggers tool use"""
        # Mock Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        # Mock tool use response
        tool_use_response = Mock()
        tool_use_response.stop_reason = "tool_use"

        tool_content = Mock()
        tool_content.type = "tool_use"
        tool_content.name = "search_course_content"
        tool_content.id = "tool_use_123"
        tool_content.input = {"query": "machine learning"}

        tool_use_response.content = [tool_content]

        # Mock final response
        final_response = Mock()
        final_response.content = [
            Mock(text="Machine learning is a subset of AI based on the search results")
        ]

        mock_client.messages.create.side_effect = [tool_use_response, final_response]

        # Patch the ai_generator client
        populated_rag_system.ai_generator.client = mock_client

        response, sources, source_links = populated_rag_system.query(
            "What is machine learning?"
        )

        assert (
            response == "Machine learning is a subset of AI based on the search results"
        )
        assert len(sources) > 0  # Should have sources from the search
        assert isinstance(source_links, dict)

        # Verify two API calls were made (initial + final)
        assert mock_client.messages.create.call_count == 2

    @patch("rag_system.anthropic.Anthropic")
    def test_query_with_session_management(self, mock_anthropic, populated_rag_system):
        """Test query with session management"""
        # Mock Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response with session")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response

        populated_rag_system.ai_generator.client = mock_client

        session_id = "test_session_123"

        # First query
        response1, _, _ = populated_rag_system.query("What is AI?", session_id)
        assert response1 == "Response with session"

        # Second query - should include conversation history
        response2, _, _ = populated_rag_system.query("Tell me more", session_id)

        # Verify that conversation history was included in the second call
        assert mock_client.messages.create.call_count == 2
        second_call_args = mock_client.messages.create.call_args_list[1][1]
        assert (
            "What is AI?" in second_call_args["system"]
        )  # History should be in system prompt

    def test_query_error_handling(self, populated_rag_system):
        """Test error handling in query processing"""
        # Mock an error in AI generator
        with patch.object(
            populated_rag_system.ai_generator,
            "generate_response",
            side_effect=Exception("API Error"),
        ):
            with pytest.raises(Exception, match="API Error"):
                populated_rag_system.query("test query")

    def test_get_course_analytics(self, populated_rag_system):
        """Test course analytics functionality"""
        analytics = populated_rag_system.get_course_analytics()

        assert "total_courses" in analytics
        assert "course_titles" in analytics
        assert analytics["total_courses"] == 1
        assert "Introduction to Machine Learning" in analytics["course_titles"]

    def test_add_course_folder_with_existing_data(self, test_rag_system):
        """Test adding course folder when data already exists"""
        # Create temporary directory with course files
        temp_dir = tempfile.mkdtemp()

        try:
            # Create first course file
            course1_path = os.path.join(temp_dir, "course1.txt")
            with open(course1_path, "w") as f:
                f.write("Course Title: Course 1\n")
                f.write("Course Link: http://example.com/course1\n")
                f.write("Course Instructor: Instructor 1\n")
                f.write("\nLesson 0: Introduction\nContent for course 1.\n")

            # Add courses first time
            courses1, chunks1 = test_rag_system.add_course_folder(temp_dir)
            assert courses1 == 1
            assert chunks1 > 0

            # Create second course file
            course2_path = os.path.join(temp_dir, "course2.txt")
            with open(course2_path, "w") as f:
                f.write("Course Title: Course 2\n")
                f.write("Course Link: http://example.com/course2\n")
                f.write("Course Instructor: Instructor 2\n")
                f.write("\nLesson 0: Introduction\nContent for course 2.\n")

            # Add courses second time - should only add new course
            courses2, chunks2 = test_rag_system.add_course_folder(temp_dir)
            assert courses2 == 1  # Only one new course
            assert chunks2 > 0

            # Total should be 2 courses
            analytics = test_rag_system.get_course_analytics()
            assert analytics["total_courses"] == 2

        finally:
            shutil.rmtree(temp_dir)

    def test_add_course_folder_clear_existing(self, test_rag_system):
        """Test adding course folder with clear_existing=True"""
        # Add some initial data
        course = Course(title="Initial Course", lessons=[])
        test_rag_system.vector_store.add_course_metadata(course)

        # Verify initial data exists
        assert test_rag_system.get_course_analytics()["total_courses"] == 1

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()

        try:
            course_path = os.path.join(temp_dir, "new_course.txt")
            with open(course_path, "w") as f:
                f.write("Course Title: New Course\n")
                f.write("Course Link: http://example.com/new\n")
                f.write("Course Instructor: New Instructor\n")
                f.write("\nLesson 0: Introduction\nNew content.\n")

            # Add with clear_existing=True
            courses, chunks = test_rag_system.add_course_folder(
                temp_dir, clear_existing=True
            )

            assert courses == 1
            assert chunks > 0

            # Should only have the new course
            analytics = test_rag_system.get_course_analytics()
            assert analytics["total_courses"] == 1
            assert "New Course" in analytics["course_titles"]
            assert "Initial Course" not in analytics["course_titles"]

        finally:
            shutil.rmtree(temp_dir)

    def test_add_course_folder_nonexistent_folder(self, test_rag_system):
        """Test adding course folder that doesn't exist"""
        courses, chunks = test_rag_system.add_course_folder("/nonexistent/folder")

        assert courses == 0
        assert chunks == 0

    @patch("rag_system.anthropic.Anthropic")
    def test_full_workflow_with_real_search(self, mock_anthropic, populated_rag_system):
        """Test complete workflow: query triggers search, returns real results"""
        # Mock Anthropic client to simulate tool use
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        # Mock tool use response
        tool_use_response = Mock()
        tool_use_response.stop_reason = "tool_use"

        tool_content = Mock()
        tool_content.type = "tool_use"
        tool_content.name = "search_course_content"
        tool_content.id = "tool_use_123"
        tool_content.input = {"query": "machine learning"}

        tool_use_response.content = [tool_content]

        # Mock final response
        final_response = Mock()
        final_response.content = [
            Mock(text="Based on the course content, machine learning is defined as...")
        ]

        mock_client.messages.create.side_effect = [tool_use_response, final_response]

        # Patch the ai_generator client
        populated_rag_system.ai_generator.client = mock_client

        # Execute query
        response, sources, source_links = populated_rag_system.query(
            "What is machine learning?"
        )

        # Verify response
        assert (
            response == "Based on the course content, machine learning is defined as..."
        )

        # Verify that real search was performed and returned results
        assert len(sources) > 0
        assert "Introduction to Machine Learning - Lesson 0" in sources

        # Verify source links
        assert len(source_links) > 0
        for source, link in source_links.items():
            assert link.startswith("http://example.com/lesson")

        # Verify that the search tool was actually called with real vector store
        # (This is tested implicitly by the fact that we get real sources back)

    def test_tool_manager_integration(self, populated_rag_system):
        """Test that tool manager properly integrates with search tools"""
        # Test direct tool execution
        result = populated_rag_system.tool_manager.execute_tool(
            "search_course_content", query="machine learning"
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert "machine learning" in result.lower() or "Machine learning" in result

        # Check that sources were tracked
        sources = populated_rag_system.tool_manager.get_last_sources()
        assert len(sources) > 0

        source_links = populated_rag_system.tool_manager.get_last_source_links()
        assert len(source_links) > 0

        # Test source reset
        populated_rag_system.tool_manager.reset_sources()
        assert populated_rag_system.tool_manager.get_last_sources() == []
        assert populated_rag_system.tool_manager.get_last_source_links() == {}

    def test_outline_tool_integration(self, populated_rag_system):
        """Test course outline tool integration"""
        result = populated_rag_system.tool_manager.execute_tool(
            "get_course_outline", course_name="Machine Learning"
        )

        assert isinstance(result, str)
        assert "Introduction to Machine Learning" in result
        assert "Dr. Test" in result
        assert "Lesson 0: Introduction" in result
        assert "Lesson 1: Basic Concepts" in result
        assert "Lesson 2: Advanced Topics" in result
