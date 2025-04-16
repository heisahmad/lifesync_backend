import pytest
from unittest.mock import Mock, patch

def test_get_emails(client):
    with patch('app.services.gmail_service.GmailService') as MockGmailService:
        mock_service = Mock()
        mock_service.get_emails.return_value = [{"id": "123", "subject": "Test"}]
        MockGmailService.return_value = mock_service
        
        response = client.get("/api/v1/email/messages")
        assert response.status_code == 200
        assert len(response.json()) > 0

def test_create_label(client):
    with patch('app.services.gmail_service.GmailService') as MockGmailService:
        mock_service = Mock()
        mock_service.create_label.return_value = {"id": "Label_1", "name": "Important"}
        MockGmailService.return_value = mock_service
        
        response = client.post("/api/v1/email/labels", json={"name": "Important"})
        assert response.status_code == 200
        assert response.json()["name"] == "Important"
