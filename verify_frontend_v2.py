import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Dashboard
        await page.goto("http://localhost:3000/dashboard")
        await asyncio.sleep(2)
        await page.screenshot(path="verification/dashboard_v2.png")
        print("Captured dashboard_v2.png")

        # Registry
        await page.goto("http://localhost:3000/agents")
        await asyncio.sleep(2)
        await page.screenshot(path="verification/registry_v2.png")
        print("Captured registry_v2.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
