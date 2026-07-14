from __future__ import annotations

import logging
from typing import Any

from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakError

from app.core.config import settings

logger = logging.getLogger(__name__)


class KeycloakService:
    """Thin wrapper around python-keycloak providing OIDC and admin helpers.

    Instances are lightweight and safe to create per-request.  The underlying
    library caches HTTP connections internally.
    """

    def __init__(self) -> None:
        self.openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
        )
        try:
            self.admin = KeycloakAdmin(
                server_url=settings.KEYCLOAK_SERVER_URL,
                username=settings.KEYCLOAK_ADMIN_USERNAME,
                password=settings.KEYCLOAK_ADMIN_PASSWORD,
                realm_name=settings.KEYCLOAK_REALM,
                verify=True,
            )
        except KeycloakError as exc:
            logger.warning(
                "Keycloak admin client init failed (admin ops unavailable): %s",
                exc,
            )
            self.admin = None  # type: ignore[assignment]

    # ---- OIDC helpers ----

    def validate_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a Keycloak access token.

        Returns the decoded payload dict on success.  Raises
        ``KeycloakError`` or ``jwt.JWTError`` on failure.
        """
        return self.openid.decode_token(
            token,
            key=settings.KEYCLOAK_CLIENT_SECRET,
            options={
                "verify_signature": True,
                "verify_aud": False,
                "verify_exp": True,
            },
        )

    def get_well_known(self) -> dict[str, Any]:
        """Fetch the ``.well-known/openid-configuration`` document."""
        return self.openid.well_know()

    def get_user_info(self, token: str) -> dict[str, Any]:
        """Return the OIDC userinfo for the given access token."""
        return self.openid.userinfo(token)

    def get_token(
        self, username: str, password: str
    ) -> dict[str, Any]:
        """Exchange username + password for tokens (resource-owner grant)."""
        return self.openid.token(username=username, password=password)

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Obtain a new access token using a refresh token."""
        return self.openid.refresh_token(refresh_token)

    def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token (server-side logout)."""
        self.openid.logout(refresh_token)

    # ---- Admin helpers ----

    def get_user(self, keycloak_user_id: str) -> dict[str, Any]:
        """Fetch a user by their Keycloak UUID."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        return self.admin.get_user(keycloak_user_id)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Look up a user by email. Returns None if not found."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        results = self.admin.get_users({"email": email})
        return results[0] if results else None

    def create_user(self, user_data: dict[str, Any]) -> str:
        """Create a user in Keycloak. Returns the new user's ID."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        return self.admin.create_user(user_data)

    def get_user_roles(self, keycloak_user_id: str) -> list[str]:
        """Return realm-level role names for a user."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        roles = self.admin.get_user_roles(keycloak_user_id)
        return [r["name"] for r in roles]

    def assign_role(
        self, keycloak_user_id: str, role_name: str
    ) -> None:
        """Assign a realm role to a user."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        role = self.admin.get_realm_role(role_name)
        self.admin.assign_realm_roles(keycloak_user_id, [role])

    def remove_role(
        self, keycloak_user_id: str, role_name: str
    ) -> None:
        """Remove a realm role from a user."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        role = self.admin.get_realm_role(role_name)
        self.admin.delete_realm_roles_of_user(keycloak_user_id, [role])

    def get_realm_roles(self) -> list[dict[str, Any]]:
        """List all realm roles."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        return self.admin.get_realm_roles()

    def create_realm_role(
        self, name: str, description: str = ""
    ) -> None:
        """Create a new realm role in Keycloak."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        self.admin.create_realm_role(
            {"name": name, "description": description}
        )

    # ---- MFA helpers ----

    def get_required_actions(self, keycloak_user_id: str) -> list[str]:
        """Return the list of required actions for a user."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        user = self.admin.get_user(keycloak_user_id)
        return user.get("requiredActions", [])

    def set_required_actions(
        self, keycloak_user_id: str, actions: list[str]
    ) -> None:
        """Set the required actions for a user."""
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")
        self.admin.update_user(
            keycloak_user_id, {"requiredActions": actions}
        )

    def configure_mfa_policy(
        self,
        *,
        push_notification: bool = True,
        totp: bool = True,
    ) -> None:
        """Update the realm's Required Action bindings for MFA.

        This registers the desired authenticators as required actions so
        that new devices will be prompted for MFA.
        """
        if self.admin is None:
            raise RuntimeError("Keycloak admin client not available")

        actions: list[str] = []
        if push_notification:
            actions.append("EXECUTE_ACTIONS")
        if totp:
            actions.append("CONFIGURE_TOTP")

        logger.info(
            "MFA policy update requested (push=%s, totp=%s)",
            push_notification,
            totp,
        )
