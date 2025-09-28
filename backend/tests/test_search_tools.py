from unittest.mock import Mock, patch

import pytest
from search_tools import CourseOutlineTool, CourseSearchTool, Tool, ToolManager
from vector_store import SearchResults


class TestCourseSearchTool:
    """Test CourseSearchTool functionality"""

    def test_tool_definition(self, mock_vector_store):
        """Test that tool definition is properly formatted"""
        tool = CourseSearchTool(mock_vector_store)
        definition = tool.get_tool_definition()

        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition

        schema = definition["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "course_name" in schema["properties"]
        assert "lesson_number" in schema["properties"]
        assert schema["required"] == ["query"]

    def test_execute_successful_search(self, mock_vector_store):
        """Test successful search execution"""
        # Setup mock vector store response
        mock_result = Mock()
        mock_result.error = None
        mock_result.is_empty.return_value = False
        mock_result.documents = ["Test content about machine learning"]
        mock_result.metadata = [
            {
                "course_title": "ML Course",
                "lesson_number": 1,
                "lesson_link": "http://example.com/lesson1",
            }
        ]

        mock_vector_store.search.return_value = mock_result

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="machine learning")

        # Verify search was called with correct parameters
        mock_vector_store.search.assert_called_once_with(
            query="machine learning", course_name=None, lesson_number=None
        )

        # Verify result formatting
        assert isinstance(result, str)
        assert "ML Course" in result
        assert "Lesson 1" in result
        assert "Test content about machine learning" in result

    def test_execute_with_course_filter(self, mock_vector_store):
        """Test search with course name filter"""
        mock_result = Mock()
        mock_result.error = None
        mock_result.is_empty.return_value = False
        mock_result.documents = ["Filtered content"]
        mock_result.metadata = [{"course_title": "Specific Course", "lesson_number": 2}]

        mock_vector_store.search.return_value = mock_result

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="test", course_name="Specific Course")

        mock_vector_store.search.assert_called_once_with(
            query="test", course_name="Specific Course", lesson_number=None
        )

    def test_execute_with_lesson_filter(self, mock_vector_store):
        """Test search with lesson number filter"""
        mock_result = Mock()
        mock_result.error = None
        mock_result.is_empty.return_value = False
        mock_result.documents = ["Lesson specific content"]
        mock_result.metadata = [{"course_title": "Test Course", "lesson_number": 3}]

        mock_vector_store.search.return_value = mock_result

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="test", lesson_number=3)

        mock_vector_store.search.assert_called_once_with(
            query="test", course_name=None, lesson_number=3
        )

    def test_execute_with_error(self, mock_vector_store):
        """Test handling of search errors"""
        mock_result = Mock()
        mock_result.error = "Vector store connection failed"

        mock_vector_store.search.return_value = mock_result

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="test")

        assert result == "Vector store connection failed"

    def test_execute_empty_results(self, mock_vector_store):
        """Test handling of empty search results"""
        mock_result = Mock()
        mock_result.error = None
        mock_result.is_empty.return_value = True

        mock_vector_store.search.return_value = mock_result

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="nonexistent")

        assert "No relevant content found" in result

    def test_execute_empty_results_with_filters(self, mock_vector_store):
        """Test empty results with course and lesson filters"""
        mock_result = Mock()
        mock_result.error = None
        mock_result.is_empty.return_value = True

        mock_vector_store.search.return_value = mock_result

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="test", course_name="ML Course", lesson_number=1)

        assert "No relevant content found" in result
        assert "in course 'ML Course'" in result
        assert "in lesson 1" in result

    def test_format_results_tracks_sources(self, mock_vector_store):
        """Test that sources and links are properly tracked"""
        mock_result = Mock()
        mock_result.error = None
        mock_result.is_empty.return_value = False
        mock_result.documents = ["Content 1", "Content 2"]
        mock_result.metadata = [
            {
                "course_title": "Course A",
                "lesson_number": 1,
                "lesson_link": "http://a.com/1",
            },
            {
                "course_title": "Course B",
                "lesson_number": 2,
                "lesson_link": "http://b.com/2",
            },
        ]

        mock_vector_store.search.return_value = mock_result

        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="test")

        # Check that sources were tracked
        assert len(tool.last_sources) == 2
        assert "Course A - Lesson 1" in tool.last_sources
        assert "Course B - Lesson 2" in tool.last_sources

        # Check that source links were tracked
        assert len(tool.last_source_links) == 2
        assert tool.last_source_links["Course A - Lesson 1"] == "http://a.com/1"
        assert tool.last_source_links["Course B - Lesson 2"] == "http://b.com/2"


class TestCourseOutlineTool:
    """Test CourseOutlineTool functionality"""

    def test_tool_definition(self, mock_vector_store):
        """Test that tool definition is properly formatted"""
        tool = CourseOutlineTool(mock_vector_store)
        definition = tool.get_tool_definition()

        assert definition["name"] == "get_course_outline"
        assert "description" in definition
        assert "input_schema" in definition

        schema = definition["input_schema"]
        assert schema["required"] == ["course_name"]

    def test_execute_successful_outline(self, mock_vector_store):
        """Test successful course outline retrieval"""
        # Mock course name resolution
        mock_vector_store._resolve_course_name.return_value = "Test Course"

        # Mock course catalog get
        mock_vector_store.course_catalog.get.return_value = {
            "metadatas": [
                {
                    "course_link": "http://example.com/course",
                    "lessons_json": '[{"lesson_number": 1, "lesson_title": "Introduction"}, {"lesson_number": 2, "lesson_title": "Advanced"}]',
                }
            ]
        }

        tool = CourseOutlineTool(mock_vector_store)
        result = tool.execute(course_name="Test")

        # Verify course name resolution was called
        mock_vector_store._resolve_course_name.assert_called_once_with("Test")

        # Verify course catalog was queried
        mock_vector_store.course_catalog.get.assert_called_once_with(
            ids=["Test Course"]
        )

        # Verify result formatting
        assert "**Course:** Test Course" in result
        assert "**Course Link:** http://example.com/course" in result
        assert "**Lessons (2 total):**" in result
        assert "Lesson 1: Introduction" in result
        assert "Lesson 2: Advanced" in result

    def test_execute_course_not_found(self, mock_vector_store):
        """Test handling when course is not found"""
        mock_vector_store._resolve_course_name.return_value = None

        tool = CourseOutlineTool(mock_vector_store)
        result = tool.execute(course_name="Nonexistent Course")

        assert "No course found matching 'Nonexistent Course'" in result

    def test_execute_metadata_not_found(self, mock_vector_store):
        """Test handling when course metadata is not found"""
        mock_vector_store._resolve_course_name.return_value = "Test Course"
        mock_vector_store.course_catalog.get.return_value = {"metadatas": []}

        tool = CourseOutlineTool(mock_vector_store)
        result = tool.execute(course_name="Test")

        assert "Course metadata not found for 'Test Course'" in result


class TestToolManager:
    """Test ToolManager functionality"""

    def test_register_tool(self):
        """Test tool registration"""
        manager = ToolManager()
        mock_tool = Mock(spec=Tool)
        mock_tool.get_tool_definition.return_value = {"name": "test_tool"}

        manager.register_tool(mock_tool)

        assert "test_tool" in manager.tools
        assert manager.tools["test_tool"] == mock_tool

    def test_register_tool_without_name(self):
        """Test tool registration fails without name"""
        manager = ToolManager()
        mock_tool = Mock(spec=Tool)
        mock_tool.get_tool_definition.return_value = {}

        with pytest.raises(
            ValueError, match="Tool must have a 'name' in its definition"
        ):
            manager.register_tool(mock_tool)

    def test_get_tool_definitions(self, mock_vector_store):
        """Test getting all tool definitions"""
        manager = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        outline_tool = CourseOutlineTool(mock_vector_store)

        manager.register_tool(search_tool)
        manager.register_tool(outline_tool)

        definitions = manager.get_tool_definitions()

        assert len(definitions) == 2
        tool_names = [defn["name"] for defn in definitions]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    def test_execute_tool(self, mock_vector_store):
        """Test tool execution"""
        manager = ToolManager()
        mock_tool = Mock(spec=Tool)
        mock_tool.get_tool_definition.return_value = {"name": "test_tool"}
        mock_tool.execute.return_value = "test result"

        manager.register_tool(mock_tool)

        result = manager.execute_tool("test_tool", param1="value1")

        mock_tool.execute.assert_called_once_with(param1="value1")
        assert result == "test result"

    def test_execute_nonexistent_tool(self):
        """Test execution of nonexistent tool"""
        manager = ToolManager()

        result = manager.execute_tool("nonexistent_tool")

        assert "Tool 'nonexistent_tool' not found" in result

    def test_get_last_sources(self, mock_vector_store):
        """Test getting sources from tools"""
        manager = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        search_tool.last_sources = ["Source 1", "Source 2"]

        manager.register_tool(search_tool)

        sources = manager.get_last_sources()

        assert sources == ["Source 1", "Source 2"]

    def test_get_last_source_links(self, mock_vector_store):
        """Test getting source links from tools"""
        manager = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        search_tool.last_source_links = {"Source 1": "http://link1.com"}

        manager.register_tool(search_tool)

        links = manager.get_last_source_links()

        assert links == {"Source 1": "http://link1.com"}

    def test_reset_sources(self, mock_vector_store):
        """Test resetting sources in tools"""
        manager = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        search_tool.last_sources = ["Source 1"]
        search_tool.last_source_links = {"Source 1": "http://link1.com"}

        manager.register_tool(search_tool)
        manager.reset_sources()

        assert search_tool.last_sources == []
        assert search_tool.last_source_links == {}
