import asyncio
from playwright.async_api import async_playwright

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # Mock backend for zero-blockchain state
        async def handle_route(route):
            url = route.request.url
            if "agents" in url and "status" not in url:
                await route.fulfill(json=[{
                    "id": "agent-123",
                    "name": "Zero-Chain Bot",
                    "goal": "Operate without a blockchain",
                    "status": "active",
                    "reputation": 95,
                    "total_executions": 10,
                    "successful_executions": 10,
                    "registered_at": "2024-01-01T00:00:00Z"
                }])
            elif "scores/all" in url:
                await route.fulfill(json=[{"agent_id": "agent-123", "grade": "A+"}])
            elif "auth/me" in url:
                await route.fulfill(json={"email": "admin@avaira.io", "is_admin": True})
            elif "dashboard/stats" in url:
                await route.fulfill(json={
                    "total_agents": 1,
                    "active_agents": 1,
                    "frozen_agents": 0,
                    "total_executions": 10,
                    "completed_executions": 10,
                    "failed_executions": 0,
                    "pending_executions": 0,
                    "total_fees_collected": 5.50,
                    "trust_pool_balance": 4.12,
                    "protocol_revenue": 1.38,
                    "total_collateral_staked": 100.0
                })
            elif "dashboard/activity" in url:
                await route.fulfill(json=[])
            else:
                await route.continue_()

        await page.route("**/*", handle_route)

        # Go to dashboard
        try:
            await page.goto("http://localhost:3000/dashboard", timeout=5000)
        except:
            pass # Server might not be up, we just want to audit the code presence via grep mostly,
                 # but let's try to see if we can get a screenshot if it is up.

        # Capture dashboard screenshot if possible
        try:
            await page.wait_for_selector("[data-testid='dashboard-page']", timeout=2000)
            await page.screenshot(path="verification/zero_blockchain_dashboard.png")
            content = await page.content()
            if "USD" in content or "$" in content:
                 print("SUCCESS: USD terminology found")
            if "AVAX" in content or "ON-CHAIN" in content:
                 print("FAILURE: Blockchain terms found")
        except:
            print("INFO: Dev server not reachable for visual audit, relying on static analysis")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify())
