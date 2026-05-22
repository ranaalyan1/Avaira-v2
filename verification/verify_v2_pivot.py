import asyncio
from playwright.sync_api import sync_playwright, expect
import json
import os

def test_registration_and_api_key(page):
    # Mock the backend response to avoid needing a live DB
    page.route("**/api/auth/me", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"user_id": "user_123", "email": "admin@avaira.io", "is_admin": True})
    ))

    page.route("**/api/agents", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([])
    ))

    page.route("**/api/scores/all", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([])
    ))

    page.route("**/api/agents/register", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"agent_id": "agent_abc", "api_key": "avaira_live_test_key_123456789"})
    ))

    page.goto("http://localhost:3000/agents")

    # Click register
    page.get_by_test_id("register-agent-btn").click()

    # Fill form
    page.get_by_test_id("register-name").fill("VerificationBot")
    page.get_by_test_id("register-goal").fill("Verify the V2 pivot")

    # Submit
    page.get_by_test_id("submit-register-btn").click()

    # Expect modal with API Key
    expect(page.get_by_text("API KEY GENERATED")).to_be_visible()
    expect(page.get_by_text("avaira_live_test_key_123456789")).to_be_visible()

    # Take screenshot
    page.screenshot(path="verification/api_key_modal.png")

    # Close modal
    page.get_by_role("button", name="I HAVE SAVED THE KEY").click()
    expect(page.get_by_text("API KEY GENERATED")).not_to_be_visible()

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            test_registration_and_api_key(page)
        finally:
            browser.close()
