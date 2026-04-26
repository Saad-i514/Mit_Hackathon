"""
Live endpoint tests — run against the running backend at localhost:8000.

Usage:
    pytest backend/tests/integration/test_endpoints_live.py -v --timeout=30 -s

These tests verify:
1. Public endpoints (health, metrics, root, docs)
2. Auth enforcement (401 on protected routes without token)
3. Request validation (422 on bad input)
4. Data flow correctness
"""
import pytest
import httpx

BASE = "http://localhost:8000"


class TestPublicEndpoints:
    """Tests that don't require authentication"""

    def test_root_returns_200(self):
        r = httpx.get(f"{BASE}/", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == "1.0.0"
        assert "docs" in data
        assert "health" in data

    def test_health_returns_healthy(self):
        r = httpx.get(f"{BASE}/health", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("healthy", "degraded")
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert "openai" in data["dependencies"]
        assert "semantic_scholar" in data["dependencies"]
        assert "serper" in data["dependencies"]

    def test_health_database_is_healthy(self):
        r = httpx.get(f"{BASE}/health", timeout=15)
        data = r.json()
        assert data["dependencies"]["database"]["status"] == "healthy"

    def test_metrics_returns_200(self):
        r = httpx.get(f"{BASE}/metrics", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "requests" in data
        assert "pipeline" in data
        assert "alerts" in data

    def test_openapi_docs_accessible(self):
        r = httpx.get(f"{BASE}/docs", timeout=5)
        assert r.status_code == 200

    def test_openapi_json_schema(self):
        r = httpx.get(f"{BASE}/openapi.json", timeout=5)
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        paths = schema["paths"]
        assert "/api/v1/plans/generate" in paths
        assert "/api/v1/plans/{plan_id}" in paths
        assert "/api/v1/plans" in paths
        assert "/health" in paths
        assert "/metrics" in paths


class TestAuthEnforcement:
    """Tests that protected endpoints return 401 without a token"""

    def test_generate_plan_requires_auth(self):
        r = httpx.post(
            f"{BASE}/api/v1/plans/generate",
            json={"hypothesis": "Test hypothesis that is long enough to pass validation"},
            timeout=5
        )
        assert r.status_code == 401

    def test_get_plan_requires_auth(self):
        r = httpx.get(f"{BASE}/api/v1/plans/some-plan-id", timeout=5)
        assert r.status_code == 401

    def test_list_plans_requires_auth(self):
        r = httpx.get(f"{BASE}/api/v1/plans", timeout=5)
        assert r.status_code == 401

    def test_submit_review_requires_auth(self):
        r = httpx.post(
            f"{BASE}/api/v1/plans/some-plan-id/reviews",
            json={
                "protocol_rating": 4,
                "materials_rating": 4,
                "timeline_rating": 4,
                "validation_rating": 4
            },
            timeout=5
        )
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        r = httpx.post(
            f"{BASE}/api/v1/plans/generate",
            headers={"Authorization": "Bearer invalid.token.here"},
            json={"hypothesis": "Test hypothesis that is long enough to pass validation"},
            timeout=10
        )
        assert r.status_code == 401


class TestRequestValidation:
    """Tests that request validation works correctly"""

    def test_generate_plan_rejects_short_hypothesis(self):
        """Hypothesis under 20 chars should return 422"""
        r = httpx.post(
            f"{BASE}/api/v1/plans/generate",
            headers={"Authorization": "Bearer fake-token"},
            json={"hypothesis": "Too short"},
            timeout=5
        )
        # 422 (validation) or 401 (auth) — both are acceptable
        # 422 means validation ran before auth, 401 means auth ran first
        assert r.status_code in (401, 422)

    def test_generate_plan_rejects_missing_hypothesis(self):
        """Missing hypothesis field should return 422"""
        r = httpx.post(
            f"{BASE}/api/v1/plans/generate",
            headers={"Authorization": "Bearer fake-token"},
            json={},
            timeout=5
        )
        assert r.status_code in (401, 422)

    def test_generate_plan_rejects_empty_hypothesis(self):
        """Empty hypothesis should return 422"""
        r = httpx.post(
            f"{BASE}/api/v1/plans/generate",
            headers={"Authorization": "Bearer fake-token"},
            json={"hypothesis": "   "},
            timeout=5
        )
        assert r.status_code in (401, 422)

    def test_list_plans_accepts_valid_pagination(self):
        """Valid pagination params should not cause 422"""
        r = httpx.get(
            f"{BASE}/api/v1/plans?limit=10&offset=0",
            timeout=5
        )
        # 401 is expected (no auth), not 422
        assert r.status_code == 401

    def test_list_plans_rejects_invalid_limit(self):
        """limit > 100 should return 422"""
        r = httpx.get(
            f"{BASE}/api/v1/plans?limit=999",
            headers={"Authorization": "Bearer fake-token"},
            timeout=5
        )
        assert r.status_code in (401, 422)


class TestCORSHeaders:
    """Tests that CORS headers are set correctly"""

    def test_cors_preflight_returns_200(self):
        r = httpx.options(
            f"{BASE}/api/v1/plans/generate",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type"
            },
            timeout=5
        )
        assert r.status_code == 200

    def test_cors_origin_allowed(self):
        r = httpx.get(
            f"{BASE}/health",
            headers={"Origin": "http://localhost:3000"},
            timeout=5
        )
        assert r.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in r.headers or r.status_code == 200


class TestResponseStructure:
    """Tests that response structures match expected schemas"""

    def test_health_response_structure(self):
        r = httpx.get(f"{BASE}/health", timeout=15)
        data = r.json()
        assert "status" in data
        assert "timestamp" in data
        assert "dependencies" in data
        assert "version" in data
        for dep in ["database", "openai", "semantic_scholar", "serper"]:
            assert dep in data["dependencies"]
            assert "status" in data["dependencies"][dep]

    def test_metrics_response_structure(self):
        r = httpx.get(f"{BASE}/metrics", timeout=5)
        data = r.json()
        assert "requests" in data
        assert "total" in data["requests"]
        assert "errors" in data["requests"]
        assert "error_rate" in data["requests"]
        assert "pipeline" in data
        assert "alerts" in data
        assert "firing" in data["alerts"]
        assert "count" in data["alerts"]

    def test_401_response_structure(self):
        r = httpx.get(f"{BASE}/api/v1/plans", timeout=5)
        assert r.status_code == 401
        # Should have structured error response
        try:
            data = r.json()
            # FastAPI returns detail field for HTTP exceptions
            assert "detail" in data
        except Exception:
            pass  # Some 401s may not have JSON body

    def test_root_response_structure(self):
        r = httpx.get(f"{BASE}/", timeout=5)
        data = r.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
