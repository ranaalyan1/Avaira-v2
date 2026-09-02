import os
from playwright.sync_api import sync_playwright

os.makedirs("/home/jules/verification/screenshots", exist_ok=True)

def run_cuj(page):
    page.route("**/*auth/me", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"user_id": "u1", "name": "Jules Dev", "email": "jules@avaira.io"}'
    ))
    page.route("**/api/**", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[]'
    ))

    page.goto("http://localhost:3000/hardening-report")
    page.wait_for_timeout(2000)
    print("Page URL:", page.url)
    page.screenshot(path="/home/jules/verification/screenshots/verification.png", full_page=True)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
