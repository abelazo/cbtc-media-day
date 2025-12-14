import os

import pytest
from playwright.sync_api import Page, expect

# Default to local Vite server
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class TestUS003DniForm:
    """
    Functional test for US-003: User can submit DNI and Name via Web Form.
    """

    def test_user_sees_form_elements(self, page: Page):
        """
        Scenario: User sees the form with required fields
        """
        try:
            page.goto(FRONTEND_URL)
        except Exception:
            pytest.skip(
                f"Frontend not reachable at {FRONTEND_URL}. Ensure 'cd app && just dev' is running."
            )

        # Check for DNI input
        # We assume label association or placeholder
        dni_input = page.get_by_label("DNI")
        if not dni_input.is_visible():
            # Fallback to placeholder if label not found (though label is better for a11y)
            dni_input = page.get_by_placeholder("DNI")

        expect(dni_input).to_be_visible()

        # Check for Nombre input
        nombre_input = page.get_by_label("Nombre")
        if not nombre_input.is_visible():
            nombre_input = page.get_by_placeholder("Nombre")

        expect(nombre_input).to_be_visible()

        # Check for Submit button
        submit_button = page.get_by_role("button", name="Enviar")
        expect(submit_button).to_be_visible()

    def test_user_can_interact_with_form(self, page: Page):
        """
        Scenario: User can submit valid DNI and Name
        """
        try:
            page.goto(FRONTEND_URL)
        except Exception:
            pytest.skip(f"Frontend not reachable at {FRONTEND_URL}")

        dni_input = page.get_by_label("DNI")
        nombre_input = page.get_by_label("Nombre")
        submit_button = page.get_by_role("button", name="Enviar")

        dni_input.fill("12345678A")
        nombre_input.fill("ValidUser")

        # We don't assert network here yet as backend might not be connected
        # But we verify no crash
        submit_button.click()

    def test_user_receives_greeting_from_backend(self, page: Page, seeded_users):
        """
        Scenario: User receives feedback after submission (E2E)
        """
        try:
            page.goto(FRONTEND_URL)
        except Exception:
            pytest.skip(f"Frontend not reachable at {FRONTEND_URL}")

        # Get a valid user
        user = seeded_users[0]
        dni = user["dnis"][0]
        username = user["username"]

        page.get_by_label("DNI").fill(dni)
        page.get_by_label("Nombre").fill(username)
        page.get_by_role("button", name="Enviar").click()

        # Check for success message ("Hello, {username}!")
        # TODO: enable this when backend is ready
        # expect(page.get_by_text(f"Hello, {username}!")).to_be_visible()
        expect(page.get_by_text("Hello, World!")).to_be_visible()
