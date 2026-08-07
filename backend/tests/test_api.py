import pytest
from fastapi.testclient import TestClient
from app.api import routes
from main import app

client = TestClient(app)


class StubRAGService:
    async def retrieve_context(self, query, k=3):
        return (
            "Admissions questions are handled by Enrolment Services.",
            [{"title": "Departments", "excerpt": "Admissions / Enrolment Services handles applications."}],
        )

    async def query(self, query, context=None, k=3):
        return (
            "Admissions questions are handled by Enrolment Services.",
            [{"title": "Departments", "excerpt": "Admissions / Enrolment Services handles applications."}],
            0.91,
        )

    async def chat(self, message, chat_history=None, k=3):
        return (
            "Admissions questions are handled by Enrolment Services.",
            [{"title": "Departments", "excerpt": "Admissions / Enrolment Services handles applications."}],
            0.91,
        )


@pytest.fixture(autouse=True)
def stub_rag_service(monkeypatch):
    monkeypatch.setattr(routes, "rag_service", StubRAGService())
    routes.chat_service.conversations.clear()


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestChatEndpoint:
    """Test chat endpoint"""

    def test_chat_valid_request(self):
        """Test chat endpoint with valid request"""
        payload = {
            "message": "What are the admissions requirements?"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "response" in data["data"]
        assert "conversation_id" in data["data"]

    def test_chat_with_conversation_id(self):
        """Test chat with conversation ID for multi-turn"""
        payload = {
            "message": "Hello",
            "conversation_id": "test_conv_123"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["conversation_id"] == "test_conv_123"

    def test_chat_invalid_request(self):
        """Test chat with invalid request"""
        payload = {"message": ""}  # Empty message
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422  # Validation error


class TestQueryEndpoint:
    """Test query endpoint"""

    def test_query_valid_request(self):
        """Test query endpoint with valid request"""
        payload = {
            "query": "Tell me about engineering programs"
        }
        response = client.post("/api/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "answer" in data["data"]
        assert "confidence" in data["data"]

    def test_query_with_context(self):
        """Test query with additional context"""
        payload = {
            "query": "What programs do you offer?",
            "context": "I'm interested in technology"
        }
        response = client.post("/api/query", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_query_invalid_request(self):
        """Test query with invalid request"""
        payload = {"query": ""}  # Empty query
        response = client.post("/api/query", json=payload)
        assert response.status_code == 422


class TestFeedbackEndpoint:
    """Test feedback endpoint"""

    def test_feedback_valid_request(self):
        """Test feedback endpoint with valid request"""
        payload = {
            "response_id": "resp_123",
            "rating": 5,
            "comment": "Very helpful!"
        }
        response = client.post("/api/feedback", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_feedback_without_comment(self):
        """Test feedback without optional comment"""
        payload = {
            "response_id": "resp_456",
            "rating": 4
        }
        response = client.post("/api/feedback", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_feedback_invalid_rating(self):
        """Test feedback with invalid rating"""
        payload = {
            "response_id": "resp_789",
            "rating": 10  # Rating must be 1-5
        }
        response = client.post("/api/feedback", json=payload)
        assert response.status_code == 422


class TestConversationHistory:
    """Test conversation history endpoint"""

    def test_get_conversation_history(self):
        """Test retrieving conversation history"""
        # Create a conversation first
        chat_payload = {
            "message": "Test message",
            "conversation_id": "test_conv_history"
        }
        client.post("/api/chat", json=chat_payload)

        # Retrieve history
        response = client.get("/api/conversations/test_conv_history")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["conversation_id"] == "test_conv_history"

    def test_get_nonexistent_conversation(self):
        """Test retrieving non-existent conversation"""
        response = client.get("/api/conversations/nonexistent_conv")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["messages"]) == 0


class TestErrorHandling:
    """Test error handling"""

    def test_missing_required_field(self):
        """Test request with missing required field"""
        payload = {"conversation_id": "test"}  # Missing 'message'
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_invalid_content_type(self):
        """Test request with invalid content type"""
        response = client.post("/api/chat", data="invalid data")
        assert response.status_code in [400, 422, 415]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
