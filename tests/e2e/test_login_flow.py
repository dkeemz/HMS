"""E2E tests for the login flow."""

from __future__ import annotations

from playwright.sync_api import Page, expect


def test_login_page_loads(page: Page) -> None:
    """Login page renders with all expected form elements."""
    page.goto("/auth/login")

    expect(page).to_have_title("Sign In — HMS")
    expect(page.locator("#login-email")).to_be_visible()
    expect(page.locator("#login-password")).to_be_visible()
    expect(page.locator("#login-submit")).to_be_visible()
    expect(page.locator("#login-submit")).to_have_text("Sign in")


def test_login_with_valid_credentials(page: Page) -> None:
    """Submitting valid credentials shows the MFA challenge or redirects."""
    page.goto("/auth/login")
    page.fill("#login-email", "admin@hms.local")
    page.fill("#login-password", "Admin123!")
    page.click("#login-submit")

    # After successful login the page should change — either redirect to
    # dashboard or show the MFA challenge.  Wait briefly for HTMX swap.
    page.wait_for_timeout(2000)

    # The form container should no longer be showing the original login form
    # (it will have been replaced by HTMX response)
    url = page.url
    logged_in = (
        not url.endswith("/auth/login")
        or "mfa" in url
        or url.rstrip("/").endswith("/")
    )
    assert logged_in, f"Expected redirect after login, still at {url}"


def test_login_with_invalid_password_shows_error(page: Page) -> None:
    """Invalid credentials display an error message."""
    page.goto("/auth/login")
    page.fill("#login-email", "admin@hms.local")
    page.fill("#login-password", "wrongpassword")
    page.click("#login-submit")

    # The HTMX response should swap in an error message
    page.wait_for_timeout(2000)
    error_area = page.locator("#login-error")
    expect(error_area).to_be_visible()


def test_login_with_empty_fields_validation(page: Page) -> None:
    """Browser prevents submission with empty required fields."""
    page.goto("/auth/login")
    # Click submit without filling anything
    page.click("#login-submit")
    page.wait_for_timeout(500)
    # The email input should have the browser's validation state
    email_input = page.locator("#login-email")
    expect(email_input).to_have_attribute("required", "")


def test_password_reset_link_navigates(page: Page) -> None:
    """Clicking 'Forgot password?' navigates to the password-reset page."""
    page.goto("/auth/login")
    page.click("text=Forgot password?")
    page.wait_for_url("**/auth/password-reset")
    expect(page).to_have_title("Reset Password — HMS")


def test_password_reset_flow(page: Page) -> None:
    """Submitting the password-reset form shows confirmation UI."""
    page.goto("/auth/password-reset")
    page.fill("#reset-email", "admin@hms.local")
    page.click("#reset-form button[type='submit']")
    page.wait_for_timeout(2000)

    # After submission the success state or confirmation should appear
    page.wait_for_selector("#reset-success:not(.hidden)", timeout=5000)


def test_mfa_challenge_displayed_on_new_device(page: Page) -> None:
    """Navigating to the MFA page renders the TOTP input form."""
    page.goto("/auth/mfa?session_id=test-session")
    expect(page).to_have_title("MFA Verification — HMS")
    expect(page.locator("#mfa-code")).to_be_visible()
    expect(page.locator("#mfa-form button[type='submit']")).to_be_visible()
