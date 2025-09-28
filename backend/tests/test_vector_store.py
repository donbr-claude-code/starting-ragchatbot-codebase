import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch
from vector_store import VectorStore, SearchResults
from models import Course, Lesson, CourseChunk


class TestSearchResults:
    """Test SearchResults functionality"""

    def test_from_chroma_with_results(self):
        """Test creating SearchResults from ChromaDB results"""
        chroma_results = {
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{'key1': 'value1'}, {'key2': 'value2'}]],
            'distances': [[0.1, 0.2]]
        }

        results = SearchResults.from_chroma(chroma_results)

        assert results.documents == ['doc1', 'doc2']
        assert results.metadata == [{'key1': 'value1'}, {'key2': 'value2'}]
        assert results.distances == [0.1, 0.2]
        assert results.error is None

    def test_from_chroma_empty_results(self):
        """Test creating SearchResults from empty ChromaDB results"""
        chroma_results = {
            'documents': [],
            'metadatas': [],
            'distances': []
        }

        results = SearchResults.from_chroma(chroma_results)

        assert results.documents == []
        assert results.metadata == []
        assert results.distances == []
        assert results.error is None

    def test_empty_with_error(self):
        """Test creating empty SearchResults with error"""
        error_msg = "Database connection failed"
        results = SearchResults.empty(error_msg)

        assert results.documents == []
        assert results.metadata == []
        assert results.distances == []
        assert results.error == error_msg

    def test_is_empty(self):
        """Test is_empty method"""
        # Empty results
        empty_results = SearchResults([], [], [])
        assert empty_results.is_empty() is True

        # Non-empty results
        non_empty_results = SearchResults(['doc'], [{}], [0.1])
        assert non_empty_results.is_empty() is False


class TestVectorStore:
    """Test VectorStore functionality"""

    def test_initialization(self, test_config):
        """Test VectorStore initialization"""
        store = VectorStore(
            chroma_path=test_config.CHROMA_PATH,
            embedding_model=test_config.EMBEDDING_MODEL,
            max_results=test_config.MAX_RESULTS
        )

        assert store.max_results == test_config.MAX_RESULTS
        assert store.client is not None
        assert store.embedding_function is not None
        assert store.course_catalog is not None
        assert store.course_content is not None

        # Cleanup
        if os.path.exists(test_config.CHROMA_PATH):
            shutil.rmtree(test_config.CHROMA_PATH)

    def test_add_course_metadata(self, real_vector_store, sample_course):
        """Test adding course metadata"""
        real_vector_store.add_course_metadata(sample_course)

        # Verify course was added
        results = real_vector_store.course_catalog.get(ids=[sample_course.title])
        assert len(results['ids']) == 1
        assert results['ids'][0] == sample_course.title

        metadata = results['metadatas'][0]
        assert metadata['title'] == sample_course.title
        assert metadata['instructor'] == sample_course.instructor
        assert metadata['course_link'] == sample_course.course_link
        assert metadata['lesson_count'] == len(sample_course.lessons)

        # Check lessons JSON
        import json
        lessons = json.loads(metadata['lessons_json'])
        assert len(lessons) == 3
        assert lessons[0]['lesson_number'] == 0
        assert lessons[0]['lesson_title'] == "Introduction"

    def test_add_course_content(self, real_vector_store, sample_course_chunks):
        """Test adding course content chunks"""
        real_vector_store.add_course_content(sample_course_chunks)

        # Verify chunks were added
        results = real_vector_store.course_content.get()
        assert len(results['ids']) == 3

        # Check that IDs are properly formatted
        expected_ids = [
            "Introduction_to_Machine_Learning_0",
            "Introduction_to_Machine_Learning_1",
            "Introduction_to_Machine_Learning_2"
        ]
        assert set(results['ids']) == set(expected_ids)

        # Check metadata
        for i, metadata in enumerate(results['metadatas']):
            chunk = sample_course_chunks[i]
            assert metadata['course_title'] == chunk.course_title
            assert metadata['lesson_number'] == chunk.lesson_number
            assert metadata['chunk_index'] == chunk.chunk_index

    def test_search_without_filters(self, populated_vector_store):
        """Test basic search without filters"""
        results = populated_vector_store.search("machine learning")

        assert not results.is_empty()
        assert results.error is None
        assert len(results.documents) > 0

        # Check that all results contain relevant content
        for doc in results.documents:
            assert isinstance(doc, str)
            assert len(doc) > 0

    def test_search_with_course_filter(self, populated_vector_store):
        """Test search with course name filter"""
        # Use partial course name
        results = populated_vector_store.search(
            "concepts",
            course_name="Machine Learning"
        )

        assert not results.is_empty()
        assert results.error is None

        # All results should be from the correct course
        for metadata in results.metadata:
            assert metadata['course_title'] == "Introduction to Machine Learning"

    def test_search_with_lesson_filter(self, populated_vector_store):
        """Test search with lesson number filter"""
        results = populated_vector_store.search(
            "concepts",
            lesson_number=1
        )

        assert not results.is_empty()
        assert results.error is None

        # All results should be from lesson 1
        for metadata in results.metadata:
            assert metadata['lesson_number'] == 1

    def test_search_with_both_filters(self, populated_vector_store):
        """Test search with both course and lesson filters"""
        results = populated_vector_store.search(
            "advanced",
            course_name="Machine Learning",
            lesson_number=2
        )

        assert not results.is_empty()
        assert results.error is None

        # All results should match both filters
        for metadata in results.metadata:
            assert metadata['course_title'] == "Introduction to Machine Learning"
            assert metadata['lesson_number'] == 2

    def test_search_nonexistent_course(self, populated_vector_store):
        """Test search with nonexistent course name"""
        results = populated_vector_store.search(
            "test",
            course_name="Nonexistent Course"
        )

        assert results.error is not None
        assert "No course found matching" in results.error

    def test_search_empty_query(self, populated_vector_store):
        """Test search with empty query"""
        results = populated_vector_store.search("")

        # Should still work, might return results based on embeddings
        assert results.error is None

    def test_resolve_course_name_exact_match(self, populated_vector_store):
        """Test course name resolution with exact match"""
        resolved = populated_vector_store._resolve_course_name("Introduction to Machine Learning")
        assert resolved == "Introduction to Machine Learning"

    def test_resolve_course_name_partial_match(self, populated_vector_store):
        """Test course name resolution with partial match"""
        resolved = populated_vector_store._resolve_course_name("Machine Learning")
        assert resolved == "Introduction to Machine Learning"

    def test_resolve_course_name_no_match(self, populated_vector_store):
        """Test course name resolution with no match"""
        resolved = populated_vector_store._resolve_course_name("Nonexistent Course")
        assert resolved is None

    def test_build_filter_no_filters(self, real_vector_store):
        """Test filter building with no filters"""
        filter_dict = real_vector_store._build_filter(None, None)
        assert filter_dict is None

    def test_build_filter_course_only(self, real_vector_store):
        """Test filter building with course only"""
        filter_dict = real_vector_store._build_filter("Test Course", None)
        assert filter_dict == {"course_title": "Test Course"}

    def test_build_filter_lesson_only(self, real_vector_store):
        """Test filter building with lesson only"""
        filter_dict = real_vector_store._build_filter(None, 2)
        assert filter_dict == {"lesson_number": 2}

    def test_build_filter_both(self, real_vector_store):
        """Test filter building with both course and lesson"""
        filter_dict = real_vector_store._build_filter("Test Course", 1)
        expected = {
            "$and": [
                {"course_title": "Test Course"},
                {"lesson_number": 1}
            ]
        }
        assert filter_dict == expected

    def test_enrich_metadata_with_lesson_links(self, populated_vector_store):
        """Test enriching metadata with lesson links"""
        # Create mock search results
        search_results = SearchResults(
            documents=["test doc"],
            metadata=[{
                "course_title": "Introduction to Machine Learning",
                "lesson_number": 1
            }],
            distances=[0.1]
        )

        populated_vector_store._enrich_metadata_with_lesson_links(search_results)

        # Check that lesson link was added
        assert 'lesson_link' in search_results.metadata[0]
        assert search_results.metadata[0]['lesson_link'] == "http://example.com/lesson1"

    def test_get_existing_course_titles(self, populated_vector_store):
        """Test getting existing course titles"""
        titles = populated_vector_store.get_existing_course_titles()
        assert "Introduction to Machine Learning" in titles

    def test_get_course_count(self, populated_vector_store):
        """Test getting course count"""
        count = populated_vector_store.get_course_count()
        assert count == 1

    def test_get_course_link(self, populated_vector_store):
        """Test getting course link"""
        link = populated_vector_store.get_course_link("Introduction to Machine Learning")
        assert link == "http://example.com/course"

    def test_get_lesson_link(self, populated_vector_store):
        """Test getting lesson link"""
        # Test existing lesson
        link = populated_vector_store.get_lesson_link("Introduction to Machine Learning", 1)
        assert link == "http://example.com/lesson1"

        # Test non-existent lesson
        link = populated_vector_store.get_lesson_link("Introduction to Machine Learning", 99)
        assert link is None

        # Test non-existent course
        link = populated_vector_store.get_lesson_link("Nonexistent Course", 1)
        assert link is None

    def test_clear_all_data(self, real_vector_store, sample_course, sample_course_chunks):
        """Test clearing all data"""
        # Add some data first
        real_vector_store.add_course_metadata(sample_course)
        real_vector_store.add_course_content(sample_course_chunks)

        # Verify data exists
        assert real_vector_store.get_course_count() > 0

        # Clear data
        real_vector_store.clear_all_data()

        # Verify data is cleared
        assert real_vector_store.get_course_count() == 0

    def test_get_all_courses_metadata(self, populated_vector_store):
        """Test getting all courses metadata"""
        metadata_list = populated_vector_store.get_all_courses_metadata()

        assert len(metadata_list) == 1
        metadata = metadata_list[0]

        assert metadata['title'] == "Introduction to Machine Learning"
        assert metadata['instructor'] == "Dr. Test"
        assert 'lessons' in metadata
        assert len(metadata['lessons']) == 3
        assert 'lessons_json' not in metadata  # Should be removed

    def test_search_with_limit(self, populated_vector_store):
        """Test search with custom limit"""
        results = populated_vector_store.search("machine learning", limit=1)

        assert not results.is_empty()
        assert len(results.documents) <= 1

    def test_error_handling_in_search(self, real_vector_store):
        """Test error handling in search method"""
        # Mock the collection to raise an exception
        with patch.object(real_vector_store.course_content, 'query', side_effect=Exception("Database error")):
            results = real_vector_store.search("test query")

            assert results.error is not None
            assert "Search error: Database error" in results.error
            assert results.is_empty()


class TestVectorStoreIntegration:
    """Integration tests for VectorStore with real data"""

    def test_full_workflow(self, real_vector_store):
        """Test complete workflow: add data, search, get metadata"""
        # Create test course
        lessons = [
            Lesson(lesson_number=1, title="Introduction", lesson_link="http://test.com/1"),
            Lesson(lesson_number=2, title="Advanced", lesson_link="http://test.com/2")
        ]
        course = Course(
            title="Test Course",
            course_link="http://test.com/course",
            instructor="Test Instructor",
            lessons=lessons
        )

        # Create test chunks
        chunks = [
            CourseChunk(
                content="This course covers fundamental concepts of testing",
                course_title="Test Course",
                lesson_number=1,
                chunk_index=0
            ),
            CourseChunk(
                content="Advanced testing techniques and methodologies",
                course_title="Test Course",
                lesson_number=2,
                chunk_index=1
            )
        ]

        # Add data
        real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(chunks)

        # Test search
        results = real_vector_store.search("testing concepts")
        assert not results.is_empty()
        assert len(results.documents) > 0

        # Test course name resolution
        resolved = real_vector_store._resolve_course_name("Test")
        assert resolved == "Test Course"

        # Test metadata retrieval
        metadata = real_vector_store.get_all_courses_metadata()
        assert len(metadata) == 1
        assert metadata[0]['title'] == "Test Course"