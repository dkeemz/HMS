"""Shared fixtures for Playwright E2E tests.

Starts a real uvicorn server against the full FastAPI app and provides
browser, page, and login-helper fixtures for every test.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import pytest
from playwright.sync_api import Page, Playwright, sync_playwright

os.environ.setdefault("DEBUG", "true")


# ---------------------------------------------------------------------------
# Disable seleniumbase plugin to avoid --browser conflict
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Unregister seleniumbase plugin if loaded (conflicts with
    pytest-playwright's --browser flag)."""
    for plugin_name in list(config.pluginmanager.get_plugins()):
        if "seleniumbase" in str(plugin_name):
            config.pluginmanager.unregister(plugin=plugin_name)

BASE_URL = "http://localhost:8765"


# ---------------------------------------------------------------------------
# Server fixture — starts uvicorn once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _server():
    """Start the FastAPI app in a subprocess and yield the base URL."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8765"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32"
            else 0
        ),
    )
    # Wait for the server to become healthy
    import httpx  # noqa: E402

    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE_URL}/api/v1/health", timeout=2)
            if r.status_code == 200:
                break
        except httpx.ConnectError:
            pass
        time.sleep(0.4)
    else:
        proc.kill()
        pytest.fail("Server did not start within 15 s")

    yield BASE_URL

    # Tear down
    try:
        if sys.platform == "win32":
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        proc.kill()


# ---------------------------------------------------------------------------
# Playwright browser / page fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _pw() -> Playwright:
    pw = sync_playwright().start()
    yield pw
    pw.stop()


@pytest.fixture(scope="session")
def _browser(_pw: Playwright):
    browser = _pw.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture()
def page(_browser, _server: str) -> Page:
    """Provide a fresh browser context + page for each test."""
    ctx = _browser.new_context(
        viewport={"width": 1280, "height": 720},
        base_url=_server,
    )
    pg = ctx.new_page()
    yield pg
    pg.close()
    ctx.close()


# ---------------------------------------------------------------------------
# Login helper
# ---------------------------------------------------------------------------

def login(
    page: Page,
    email: str = "admin@hms.local",
    password: str = "Admin123!",
) -> None:
    """Navigate to the login page and submit valid credentials."""
    page.goto("/auth/login")
    page.wait_for_selector("#login-email")
    page.fill("#login-email", email)
    page.fill("#login-password", password)
    page.click("#login-submit")
