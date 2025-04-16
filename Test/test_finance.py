import pytest
from unittest.mock import Mock, patch

def test_link_account(client):
    with patch('app.services.financial_service.FinancialService') as MockFinancialService:
        mock_service = Mock()
        mock_service.create_link_token.return_value = {"link_token": "test_token"}
        MockFinancialService.return_value = mock_service
        
        response = client.post("/api/v1/finance/link/token")
        assert response.status_code == 200
        assert "link_token" in response.json()

def test_sync_transactions(client):
    with patch('app.services.financial_service.FinancialService') as MockFinancialService:
        mock_service = Mock()
        mock_service.sync_transactions.return_value = {
            "added": 2,
            "modified": 0,
            "removed": 0
        }
        MockFinancialService.return_value = mock_service
        
        response = client.post("/api/v1/finance/sync")
        assert response.status_code == 200
        assert response.json()["added"] == 2
