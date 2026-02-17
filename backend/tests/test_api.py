from fastapi.testclient import TestClient
from main import app
import os
from unittest.mock import patch

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": "Balance AI v1.0"}

def test_agent_health():
    response = client.get("/agent/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "components" in data

@patch.dict(os.environ, {"USE_MOCK_SHEETS": "true", "GEMINI_API_KEY": "test_key"})
def test_upload_mock_flow():
    # Test file upload with mock environment
    # Create a small dummy file
    files = {'file': ('test.jpg', b'fake_image_content', 'image/jpeg')}
    
    # We need to mock the tools since we don't want real calls in unit tests
    with patch('main.get_vision_model') as mock_vision:
        mock_vision.return_value.analyze_image.return_value = {
            "vendor": "Test Vendor",
            "amount": 10.00,
            "date": "2023-01-01",
            "category": "Test",
            "description": "Start of unit test"
        }
        
        response = client.post("/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["vendor"] == "Test Vendor"
