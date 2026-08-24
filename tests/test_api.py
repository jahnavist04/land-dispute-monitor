import pytest
import json

class TestDisputesAPI:
    def test_list_disputes_requires_auth(self, client):
        """Request without API key should return 401."""
        response = client.get('/api/v1/disputes')
        assert response.status_code == 401
    
    def test_list_disputes_empty(self, api_client):
        response = api_client.get('/api/v1/disputes',
            headers={'X-API-Key': api_client.api_key})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['items'] == []
    
    def test_get_dispute_not_found(self, api_client):
        response = api_client.get('/api/v1/disputes/99999',
            headers={'X-API-Key': api_client.api_key})
        assert response.status_code == 404

class TestSubscriptionsAPI:
    def test_create_subscription(self, api_client):
        response = api_client.post('/api/v1/subscribe',
            headers={'X-API-Key': api_client.api_key, 'Content-Type': 'application/json'},
            data=json.dumps({
                'tracked_regions': ['Bangalore', 'Chennai'],
                'min_severity': 'high',
                'notification_method': 'webhook',
                'webhook_url': 'https://example.com/hook'
            }))
        assert response.status_code == 201
    
    def test_create_subscription_missing_regions(self, api_client):
        response = api_client.post('/api/v1/subscribe',
            headers={'X-API-Key': api_client.api_key, 'Content-Type': 'application/json'},
            data=json.dumps({}))
        assert response.status_code == 400

class TestSourcesAPI:
    def test_list_sources(self, api_client):
        response = api_client.get('/api/v1/sources',
            headers={'X-API-Key': api_client.api_key})
        assert response.status_code == 200
    
    def test_create_source(self, api_client):
        response = api_client.post('/api/v1/sources',
            headers={'X-API-Key': api_client.api_key, 'Content-Type': 'application/json'},
            data=json.dumps({
                'name': 'Test Paper',
                'base_url': 'https://test.com/notices',
                'source_type': 'html',
                'selectors_config': {'article_links': 'a.link'}
            }))
        assert response.status_code == 201

class TestClientsAPI:
    def test_get_alerts_requires_auth(self, client):
        response = client.get('/api/v1/clients/1/alerts')
        assert response.status_code == 401
