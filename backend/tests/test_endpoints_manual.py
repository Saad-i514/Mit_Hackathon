"""
Manual endpoint testing script for all advanced feature endpoints.
Run with: python tests/test_endpoints_manual.py
"""
import asyncio
import json
import sys
import os
import httpx

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8001"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kdzzyxihfxxcsnifcnpi.supabase.co")
SUPABASE_ANON_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtkenp5eGloZnh4Y3NuaWZjbnBpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMzY2MTYsImV4cCI6MjA5MjcxMjYxNn0.N-gS5ir59OcMqO1pYqobKuEgm8YgxYLd30AsMGbk86Y"
)

# Test credentials — update if needed
TEST_EMAIL = "testuser@gmail.com"
TEST_PASSWORD = "TestPass123!"

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭  SKIP"

results = []

def log(status: str, name: str, detail: str = ""):
    line = f"{status}  {name}"
    if detail:
        line += f"\n       {detail}"
    print(line)
    results.append((status, name, detail))


# ── Auth helper ───────────────────────────────────────────────────────────────
async def get_auth_token(client: httpx.AsyncClient) -> str | None:
    """Sign in via Supabase and return JWT access token."""
    resp = await client.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        },
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.json().get("access_token")
    # Try sign-up if sign-in fails (first run)
    resp2 = await client.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        },
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    if resp2.status_code in (200, 201):
        token = resp2.json().get("access_token")
        if token:
            return token
    print(f"  Auth failed: sign-in {resp.status_code}, sign-up {resp2.status_code}")
    print(f"  sign-in body: {resp.text[:300]}")
    return None


async def get_first_plan_id(client: httpx.AsyncClient, token: str) -> str | None:
    """Return the first plan ID owned by the test user — prefer seeded plan if available."""
    # Check for seeded plan ID first
    seed_file = os.path.join(os.path.dirname(__file__), ".test_plan_id")
    if os.path.exists(seed_file):
        with open(seed_file) as f:
            pid = f.read().strip()
            if pid:
                return pid
    # Fall back to API
    resp = await client.get(
        f"{BASE_URL}/api/v1/plans",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        items = resp.json().get("items", [])
        if items:
            return items[0]["id"]
    return None


# ── Individual tests ──────────────────────────────────────────────────────────

async def test_health(client: httpx.AsyncClient):
    """GET /health"""
    try:
        resp = await client.get(f"{BASE_URL}/health", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            log(PASS, "GET /health", f"status={data.get('status','?')} db={data.get('dependencies',{}).get('database',{}).get('status','?')}")
        else:
            log(FAIL, "GET /health", f"status={resp.status_code} body={resp.text[:200]}")
    except Exception as e:
        log(FAIL, "GET /health", str(e))


async def test_list_plans(client: httpx.AsyncClient, token: str):
    """GET /api/v1/plans"""
    try:
        resp = await client.get(
            f"{BASE_URL}/api/v1/plans",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            log(PASS, "GET /api/v1/plans", f"total={data.get('total', '?')} items={len(data.get('items', []))}")
        else:
            log(FAIL, "GET /api/v1/plans", f"status={resp.status_code} body={resp.text[:200]}")
    except Exception as e:
        log(FAIL, "GET /api/v1/plans", str(e))


async def test_get_plan(client: httpx.AsyncClient, token: str, plan_id: str):
    """GET /api/v1/plans/{plan_id}"""
    try:
        resp = await client.get(
            f"{BASE_URL}/api/v1/plans/{plan_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            log(PASS, f"GET /api/v1/plans/{{plan_id}}", f"domain={data.get('domain','?')}")
        else:
            log(FAIL, f"GET /api/v1/plans/{{plan_id}}", f"status={resp.status_code} body={resp.text[:200]}")
    except Exception as e:
        log(FAIL, f"GET /api/v1/plans/{{plan_id}}", str(e))


async def test_get_versions(client: httpx.AsyncClient, token: str, plan_id: str):
    """GET /api/v1/plans/{plan_id}/versions"""
    try:
        resp = await client.get(
            f"{BASE_URL}/api/v1/plans/{plan_id}/versions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            log(PASS, "GET /api/v1/plans/{plan_id}/versions", f"versions={len(data.get('versions', []))}")
        else:
            log(FAIL, "GET /api/v1/plans/{plan_id}/versions", f"status={resp.status_code} body={resp.text[:200]}")
    except Exception as e:
        log(FAIL, "GET /api/v1/plans/{plan_id}/versions", str(e))


async def test_grant_methods(client: httpx.AsyncClient, token: str, plan_id: str):
    """POST /api/v1/plans/{plan_id}/grant-methods"""
    for grant_body in ["NIH", "NSF", "ERC"]:
        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/plans/{plan_id}/grant-methods?grant_body={grant_body}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                preview = data.get("methods_section", "")[:80].replace("\n", " ")
                log(PASS, f"POST /api/v1/plans/{{plan_id}}/grant-methods [{grant_body}]", f"preview: {preview}…")
            else:
                log(FAIL, f"POST /api/v1/plans/{{plan_id}}/grant-methods [{grant_body}]",
                    f"status={resp.status_code} body={resp.text[:300]}")
        except Exception as e:
            log(FAIL, f"POST /api/v1/plans/{{plan_id}}/grant-methods [{grant_body}]", str(e))


async def test_notebook(client: httpx.AsyncClient, token: str, plan_id: str):
    """POST /api/v1/plans/{plan_id}/notebook"""
    try:
        resp = await client.post(
            f"{BASE_URL}/api/v1/plans/{plan_id}/notebook",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            nb = data.get("notebook", {})
            log(PASS, "POST /api/v1/plans/{plan_id}/notebook",
                f"title={nb.get('title','?')} sections={len(nb.get('sections', []))}")
        else:
            log(FAIL, "POST /api/v1/plans/{plan_id}/notebook",
                f"status={resp.status_code} body={resp.text[:300]}")
    except Exception as e:
        log(FAIL, "POST /api/v1/plans/{plan_id}/notebook", str(e))


async def test_restore_version(client: httpx.AsyncClient, token: str, plan_id: str):
    """POST /api/v1/plans/{plan_id}/restore/{version_number} — only if versions exist"""
    try:
        # First check if any versions exist
        resp = await client.get(
            f"{BASE_URL}/api/v1/plans/{plan_id}/versions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code != 200:
            log(SKIP, "POST /api/v1/plans/{plan_id}/restore/{version}", "could not fetch versions")
            return

        versions = resp.json().get("versions", [])
        if not versions:
            log(SKIP, "POST /api/v1/plans/{plan_id}/restore/{version}", "no versions available to restore")
            return

        version_number = versions[0]["version_number"]
        resp2 = await client.post(
            f"{BASE_URL}/api/v1/plans/{plan_id}/restore/{version_number}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if resp2.status_code == 200:
            data = resp2.json()
            log(PASS, "POST /api/v1/plans/{plan_id}/restore/{version}",
                f"restored_from={data.get('restored_from')} new_version={data.get('version_number')}")
        else:
            log(FAIL, "POST /api/v1/plans/{plan_id}/restore/{version}",
                f"status={resp2.status_code} body={resp2.text[:300]}")
    except Exception as e:
        log(FAIL, "POST /api/v1/plans/{plan_id}/restore/{version}", str(e))


async def test_equipment(client: httpx.AsyncClient, token: str):
    """PUT /api/v1/plans/equipment/{equipment_name}"""
    test_cases = [
        ("Centrifuge_5424R", True, "Eppendorf, available in lab"),
        ("Confocal_Microscope", False, "Need to book core facility"),
        ("PCR_Thermocycler", True, None),
    ]
    for name, has_item, notes in test_cases:
        try:
            url = f"{BASE_URL}/api/v1/plans/equipment/{name}?has_item={str(has_item).lower()}"
            if notes:
                url += f"&notes={notes.replace(' ', '%20')}"
            resp = await client.put(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                log(PASS, f"PUT /api/v1/plans/equipment/{{{name}}}",
                    f"has_item={data.get('has_item')} saved_at={data.get('saved_at','?')[:19]}")
            else:
                log(FAIL, f"PUT /api/v1/plans/equipment/{{{name}}}",
                    f"status={resp.status_code} body={resp.text[:300]}")
        except Exception as e:
            log(FAIL, f"PUT /api/v1/plans/equipment/{{{name}}}", str(e))


async def test_404_plan(client: httpx.AsyncClient, token: str):
    """Verify 404 for non-existent plan"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    try:
        resp = await client.get(
            f"{BASE_URL}/api/v1/plans/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 404:
            log(PASS, "404 for non-existent plan", f"error_code={resp.json().get('detail', {}).get('error_code','?')}")
        else:
            log(FAIL, "404 for non-existent plan", f"expected 404, got {resp.status_code}")
    except Exception as e:
        log(FAIL, "404 for non-existent plan", str(e))


async def test_401_no_token(client: httpx.AsyncClient):
    """Verify 401/403 when no auth token provided"""
    try:
        resp = await client.get(f"{BASE_URL}/api/v1/plans", timeout=5)
        if resp.status_code in (401, 403):
            log(PASS, "401/403 without auth token", f"status={resp.status_code}")
        else:
            log(FAIL, "401/403 without auth token", f"expected 401/403, got {resp.status_code}")
    except Exception as e:
        log(FAIL, "401/403 without auth token", str(e))


# ── Main runner ───────────────────────────────────────────────────────────────

async def main():
    print("\n" + "="*60)
    print("  AI Scientist Platform — Endpoint Test Suite")
    print("="*60 + "\n")

    async with httpx.AsyncClient() as client:

        # 1. Health check (no auth needed)
        await test_health(client)

        # 2. Auth
        print("\n── Authentication ──────────────────────────────────────")
        token = await get_auth_token(client)
        if not token:
            log(FAIL, "Authentication", "Could not obtain JWT token — remaining tests skipped")
            _print_summary()
            return
        log(PASS, "Authentication", f"token obtained (…{token[-12:]})")

        # 3. Security checks
        print("\n── Security ─────────────────────────────────────────────")
        await test_401_no_token(client)
        await test_404_plan(client, token)

        # 4. Core plan endpoints
        print("\n── Core Plan Endpoints ──────────────────────────────────")
        await test_list_plans(client, token)

        plan_id = await get_first_plan_id(client, token)
        if not plan_id:
            log(SKIP, "Plan-specific tests", "No plans found in DB — skipping plan-specific tests")
            _print_summary()
            return

        print(f"  Using plan_id: {plan_id}\n")
        await test_get_plan(client, token, plan_id)

        # 5. Advanced feature endpoints
        print("\n── Advanced Feature Endpoints ───────────────────────────")
        await test_get_versions(client, token, plan_id)
        await test_restore_version(client, token, plan_id)
        await test_equipment(client, token)

        # 6. AI-powered endpoints (may take 10-60s each)
        print("\n── AI-Powered Endpoints (may take ~30s each) ────────────")
        await test_grant_methods(client, token, plan_id)
        await test_notebook(client, token, plan_id)

    _print_summary()


def _print_summary():
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = sum(1 for s, _, _ in results if s == FAIL)
    skipped = sum(1 for s, _, _ in results if s == SKIP)
    total = len(results)
    print(f"  Total : {total}")
    print(f"  {PASS} : {passed}")
    print(f"  {FAIL} : {failed}")
    print(f"  {SKIP} : {skipped}")
    print("="*60 + "\n")
    if failed > 0:
        print("Failed tests:")
        for s, name, detail in results:
            if s == FAIL:
                print(f"  • {name}")
                if detail:
                    print(f"    {detail}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
