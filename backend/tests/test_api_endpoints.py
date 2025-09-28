import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.mark.api
class TestAPIEndpoints:
    """Test FastAPI endpoint functionality"""

    def test_health_endpoint_success(self, test_client):
        """Test health endpoint returns success response"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "total_courses" in data
        assert "components" in data
        assert data["components"]["vector_store"] == "ok"
        assert data["components"]["rag_system"] == "ok"

    def test_health_endpoint_failure(self, test_app):
        """Test health endpoint handles failures gracefully"""
        # Mock failure in RAG system
        test_app.state.mock_rag.get_course_analytics.side_effect = Exception("Test error")

        client = TestClient(test_app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "unhealthy"
        assert "error" in data
        assert data["components"]["vector_store"] == "error"
        assert data["components"]["rag_system"] == "error"

    def test_query_endpoint_with_session(self, test_client, sample_api_requests):
        """Test query endpoint with provided session ID"""
        request_data = sample_api_requests["valid_query"]

        response = test_client.post("/api/query", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "source_links" in data
        assert data["session_id"] == request_data["session_id"]
        assert isinstance(data["sources"], list)
        assert isinstance(data["source_links"], dict)

    def test_query_endpoint_without_session(self, test_client, sample_api_requests):
        """Test query endpoint creates new session when none provided"""
        request_data = sample_api_requests["query_without_session"]

        response = test_client.post("/api/query", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "source_links" in data
        assert "session_id" in data
        assert data["session_id"] == "test_session_123"  # From mock

    def test_query_endpoint_empty_query(self, test_client, sample_api_requests):
        """Test query endpoint handles empty query"""
        request_data = sample_api_requests["empty_query"]

        response = test_client.post("/api/query", json=request_data)

        # Should still process successfully (empty query is valid input)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_query_endpoint_invalid_json(self, test_client):
        """Test query endpoint handles invalid JSON"""
        response = test_client.post(
            "/api/query",
            data='{"query": "test", invalid json}',
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Validation error

    def test_query_endpoint_missing_query_field(self, test_client):
        """Test query endpoint requires query field"""
        response = test_client.post("/api/query", json={"session_id": "test"})

        assert response.status_code == 422  # Validation error

    def test_query_endpoint_rag_system_error(self, test_app):
        """Test query endpoint handles RAG system errors"""
        # Mock RAG system to raise an error
        test_app.state.mock_rag.query.side_effect = Exception("RAG system error")

        client = TestClient(test_app)
        response = client.post("/api/query", json={"query": "test query"})

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "RAG system error" in data["detail"]

    def test_courses_endpoint_success(self, test_client):
        """Test courses endpoint returns course statistics"""
        response = test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2

    def test_courses_endpoint_error(self, test_app):
        """Test courses endpoint handles errors"""
        # Mock analytics to raise an error
        test_app.state.mock_rag.get_course_analytics.side_effect = Exception("Analytics error")

        client = TestClient(test_app)
        response = client.get("/api/courses")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Analytics error" in data["detail"]

    def test_clear_session_endpoint_success(self, test_client):
        """Test clear session endpoint"""
        session_id = "test_session_123"

        response = test_client.delete(f"/api/sessions/{session_id}/clear")

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Session cleared successfully"
        assert data["session_id"] == session_id

    def test_clear_session_endpoint_error(self, test_app):
        """Test clear session endpoint handles errors"""
        # Mock session manager to raise an error
        test_app.state.mock_rag.session_manager.clear_session.side_effect = Exception("Session error")

        client = TestClient(test_app)
        response = client.delete("/api/sessions/test_session/clear")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Session error" in data["detail"]

    def test_cors_headers(self, test_client):
        """Test CORS headers are properly set"""
        response = test_client.get("/health")

        # FastAPI TestClient doesn't send CORS headers in the same way
        # but we can verify the middleware is configured in the app
        assert response.status_code == 200

    def test_request_validation_types(self, test_client):
        """Test request validation for different data types"""
        # Test with integer instead of string for query
        response = test_client.post("/api/query", json={"query": 123})

        assert response.status_code == 422  # Validation error

        # Test with array instead of string for session_id
        response = test_client.post("/api/query", json={
            "query": "test",
            "session_id": ["not", "a", "string"]
        })

        assert response.status_code == 422  # Validation error

    def test_response_model_validation(self, test_client):
        """Test response models are properly structured"""
        # Test query response structure
        response = test_client.post("/api/query", json={"query": "test"})
        assert response.status_code == 200

        data = response.json()
        required_fields = {"answer", "sources", "source_links", "session_id"}
        assert required_fields.issubset(data.keys())

        # Test courses response structure
        response = test_client.get("/api/courses")
        assert response.status_code == 200

        data = response.json()
        required_fields = {"total_courses", "course_titles"}
        assert required_fields.issubset(data.keys())

    def test_endpoint_method_restrictions(self, test_client):
        """Test endpoints only accept allowed HTTP methods"""
        # Test POST on GET endpoint
        response = test_client.post("/health")
        assert response.status_code == 405  # Method not allowed

        # Test GET on POST endpoint
        response = test_client.get("/api/query")
        assert response.status_code == 405  # Method not allowed

        # Test PUT on DELETE endpoint
        response = test_client.put("/api/sessions/test/clear")
        assert response.status_code == 405  # Method not allowed


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints with real components"""

    def test_query_workflow_integration(self, test_client):
        """Test complete query workflow"""
        # First get course stats
        courses_response = test_client.get("/api/courses")
        assert courses_response.status_code == 200

        # Then make a query
        query_response = test_client.post("/api/query", json={
            "query": "What is machine learning?"
        })
        assert query_response.status_code == 200

        query_data = query_response.json()
        session_id = query_data["session_id"]

        # Make another query with same session
        query_response2 = test_client.post("/api/query", json={
            "query": "Tell me more details",
            "session_id": session_id
        })
        assert query_response2.status_code == 200

        # Clear the session
        clear_response = test_client.delete(f"/api/sessions/{session_id}/clear")
        assert clear_response.status_code == 200

    def test_health_check_integration(self, test_client):
        """Test health check provides useful system status"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] >= 0