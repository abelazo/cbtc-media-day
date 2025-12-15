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
            pytest.skip(f"Frontend not reachable at {FRONTEND_URL}. Ensure 'cd app && just dev' is running.")

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
        # Use a non-existent user to ensure 404
        dni = "00000000X"
        username = "NonExistentUser"

        page.get_by_label("DNI").fill(dni)
        page.get_by_label("Nombre").fill(username)
        page.get_by_role("button", name="Enviar").click()

        # Check for error message ("No hay fotos asociadas a este jugador")
        # Since US-004, if not in DB, it returns 404 and frontend should show it.
        # But wait, frontend logic is OLD (expects JSON).
        # The user asked to update the *test*.
        # If I run this test now, it might check for "No hay fotos..." but frontend might display "Error: 404".
        # But the user request implies checking that the backend returns error (or frontend displays it).
        # "return an error as the DNI/Name is not present in the DB".
        # So I will assert the text: "No hay fotos asociadas a este jugador" OR "Error" if frontend handles it
        # generically.
        # In `DniForm.jsx`, `setMessage('Error: ' + response.status)` is the fallback.
        # So it will likely show "Error: 404".
        # UNLESS the backend returns JSON body with "message" and frontend displays it?
        # Backend returns `{"message": "No hay fotos..."}` on 404.
        # Frontend: `const data = await response.json(); setMessage(data.message || 'Success');` is only inside
        # `if (response.ok)`.
        # Else: `setMessage('Error: ' + response.status);`

        # So it will show "Error: 404".
        # I should expect that.
        expect(page.get_by_text("Error: 404")).to_be_visible()
