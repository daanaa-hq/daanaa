"""
Routing Safety Tests — Prevent SPA fallback from shadowing API routes

These tests ensure that:
1. API routes are always matched before SPA fallback
2. Non-API requests fall through to SPA correctly
3. Routing order is deterministic and testable

This test suite guards against the Flask pitfall where a catch-all route
added early in the file accidentally shadows more specific routes.
"""

import pytest
import json
from droplet_api import app


@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPIRoutes:
    """Verify API routes are matched correctly."""

    def test_health_endpoint(self, client):
        """GET /health should return JSON, not SPA."""
        resp = client.get('/health')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'
        data = json.loads(resp.data)
        assert 'status' in data

    def test_api_organizations_recall(self, client):
        """GET /api/organizations/{ein}/recall should return JSON, not SPA."""
        resp = client.get('/api/organizations/832672211/recall')
        # May return 404 if org not found, but should NOT return SPA HTML
        assert resp.status_code in (200, 404)
        assert resp.content_type == 'application/json'

    def test_api_health_json_not_html(self, client):
        """Ensure /api/health returns JSON, not HTML fallback."""
        resp = client.get('/api/health')
        assert 'text/html' not in resp.content_type
        assert 'application/json' in resp.content_type

    def test_api_search_json(self, client):
        """GET /api/search should return JSON, not SPA."""
        resp = client.get('/api/search?q=health')
        assert 'text/html' not in resp.content_type
        assert resp.content_type in ('application/json', 'application/json; charset=utf-8')

    def test_api_stats_json(self, client):
        """GET /api/stats should return JSON, not SPA."""
        resp = client.get('/api/stats')
        assert 'text/html' not in resp.content_type
        assert 'application/json' in resp.content_type


class TestSPAFallback:
    """Verify SPA fallback works for non-API routes."""

    def test_spa_fallback_for_unknown_routes(self, client):
        """GET /unknown-page should return SPA (index.html), not 404."""
        resp = client.get('/unknown-page')
        assert resp.status_code == 200
        assert resp.content_type == 'text/html; charset=utf-8'
        assert b'<!doctype html>' in resp.data.lower()

    def test_spa_root_route(self, client):
        """GET / should return SPA (index.html)."""
        resp = client.get('/')
        assert resp.status_code == 200
        assert resp.content_type == 'text/html; charset=utf-8'

    def test_spa_for_frontend_routes(self, client):
        """GET /directory (frontend route) should return SPA."""
        resp = client.get('/directory')
        assert resp.status_code == 200
        assert 'text/html' in resp.content_type


class TestAPIRoutePatterns:
    """Verify all API route patterns work correctly."""

    @pytest.mark.parametrize("api_path", [
        '/health',
        '/api/stats',
        '/api/search',
        '/api/organizations/832672211',
        '/api/organizations/832672211/similar',
        '/api/organizations/832672211/financials',
    ])
    def test_api_returns_json_not_html(self, client, api_path):
        """All /api/* routes should return JSON, never HTML fallback."""
        resp = client.get(api_path)
        # Status may vary (200, 404, 400) but should NEVER return HTML
        assert 'text/html' not in resp.content_type, \
            f"{api_path} returned HTML instead of JSON"


class TestRoutingOrder:
    """Verify routing order is deterministic."""

    def test_api_routes_before_spa(self, client):
        """API routes must be registered before SPA fallback."""
        # If this fails, it means routing order is wrong

        # Specific API route should be matched exactly
        resp_api = client.get('/api/organizations/832672211/recall')
        assert resp_api.content_type == 'application/json'

        # Similar-looking non-API route should hit SPA
        resp_spa = client.get('/api-docs')  # Doesn't match /api/*, hits SPA
        assert 'text/html' in resp_spa.content_type

    def test_recall_endpoint_specificity(self, client):
        """The recall endpoint pattern should match before SPA fallback."""
        # /api/organizations/{ein}/recall should match, not fall through to SPA
        resp = client.get('/api/organizations/832672211/recall')

        # Should return JSON API response (not HTML from SPA)
        assert resp.content_type == 'application/json', \
            "Recall endpoint pattern not matched before SPA fallback"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
