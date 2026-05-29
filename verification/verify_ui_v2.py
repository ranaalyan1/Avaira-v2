import asyncio
import json
from playwright.async_api import async_playwright

async def verify_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Set auth cookie
        await context.add_cookies([{
            'name': 'session_token',
            'value': 'mock-session-token',
            'domain': 'localhost',
            'path': '/'
        }])

        # Mock /auth/me
        await page.route("**/api/auth/me", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "user_id": "user-1",
                "email": "admin@avaira.xyz",
                "name": "Admin User",
                "picture": "",
                "is_admin": True
            })
        ))

        # Mock API responses
        await page.route("**/api/dashboard/stats", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "total_agents": 12,
                "active_agents": 8,
                "frozen_agents": 2,
                "total_executions": 156,
                "completed_executions": 142,
                "failed_executions": 14,
                "pending_executions": 0,
                "total_fees_collected": 1240.50,
                "trust_pool_balance": 930.37,
                "protocol_revenue": 310.13,
                "total_collateral_staked": 5000.0
            })
        ))

        await page.route("**/api/dashboard/activity", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([
                {
                    "id": "1",
                    "type": "execution",
                    "description": "Agent 'Alpha' - search (completed)",
                    "status": "completed",
                    "timestamp": "2024-05-20T10:00:00Z"
                },
                {
                    "id": "2",
                    "type": "freeze",
                    "description": "Agent 'Omega' - FREEZE: High Risk Deviation",
                    "status": "freeze",
                    "reason": "High Risk Deviation",
                    "timestamp": "2024-05-20T10:05:00Z"
                }
            ])
        ))

        await page.route("**/api/agents", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([
                {
                    "id": "agent-1",
                    "name": "Alpha-Shield",
                    "status": "active",
                    "reputation": 95,
                    "total_executions": 45,
                    "successful_executions": 44,
                    "goal": "Optimize yields",
                    "registered_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "agent-2",
                    "name": "Omega-Risk",
                    "status": "frozen",
                    "reputation": 32,
                    "total_executions": 12,
                    "successful_executions": 8,
                    "goal": "Aggressive trading",
                    "registered_at": "2024-02-01T00:00:00Z"
                }
            ])
        ))

        await page.route("**/api/scores/all", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([
                {"agent_id": "agent-1", "grade": "AA", "composite_score": 92},
                {"agent_id": "agent-2", "grade": "D", "composite_score": 35}
            ])
        ))

        # Navigate to Dashboard
        try:
            await page.goto("http://localhost:3000/dashboard", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for animations
            await page.screenshot(path="verification/dashboard_v2.png")
            print("Dashboard screenshot saved.")
        except Exception as e:
            print(f"Dashboard failed: {e}")

        # Navigate to Agent Registry
        try:
            await page.goto("http://localhost:3000/agents", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for animations
            await page.screenshot(path="verification/registry_v2.png")
            print("Registry screenshot saved.")
        except Exception as e:
            print(f"Registry failed: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_ui())
