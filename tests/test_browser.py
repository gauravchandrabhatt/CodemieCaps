"""Optional real-browser smoke test. Install the test extra and run playwright install chromium first."""
import os
import socket
import subprocess
import sys
import time

import pytest


def wait_for_server(process, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Uvicorn exited before the browser test could connect")
        try:
            with socket.create_connection(("127.0.0.1", 8765), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError("Timed out waiting for the local demo server")


@pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Set RUN_BROWSER_TESTS=1 after installing Chromium")
def test_browser_approves_phase_and_adds_backlog_item(tmp_path):
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    env = os.environ.copy()
    env["CODIEMIE_DATABASE_URL"] = f"sqlite:///{tmp_path / 'browser-test.db'}"
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "codemie_caps.main:app", "--app-dir", "src",
        "--host", "127.0.0.1", "--port", "8765",
    ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for_server(process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto("http://127.0.0.1:8765", wait_until="networkidle")
            assert page.get_by_role("heading", name="SDLC Cockpit").is_visible()
            page.locator("#review-note").fill("Approved in browser smoke test.")
            page.get_by_role("button", name="Approve phase").click()
            page.get_by_text("Stories & plan").wait_for()
            page.get_by_role("button", name="Add item").click()
            page.get_by_placeholder("What should improve?").fill("Browser-created enhancement")
            page.get_by_role("button", name="Create item").click()
            page.get_by_text("Browser-created enhancement").wait_for()
            browser.close()
    finally:
        process.terminate()
        process.wait(timeout=10)
