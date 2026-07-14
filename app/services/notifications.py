from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles HMS-side notifications for security events.

    In production, integrate with an email provider (SendGrid, SES, etc.).
    For now, all methods log the notification and return success, allowing
    the application to function without email infrastructure.
    """

    @staticmethod
    async def send_password_reset_email(email: str, token: str) -> bool:
        """Send a password reset email with the given token."""
        logger.info(
            "PASSWORD RESET EMAIL → %s | token=%s (expires in 15 min)",
            email,
            token[:8] + "...",
        )
        # TODO: Integrate with email provider (SendGrid / SES / SMTP)
        # Example payload:
        #   subject: "HMS — Reset Your Password"
        #   body: f"Click to reset: https://hms.example.com/reset?token={token}"
        return True

    @staticmethod
    async def send_login_notification(
        email: str, device_info: dict, is_new_device: bool
    ) -> bool:
        """Send login notification for new device or suspicious activity."""
        if is_new_device:
            logger.info(
                "LOGIN NOTIFICATION (new device) → %s | device=%s",
                email,
                device_info,
            )
        else:
            logger.debug(
                "Login notification skipped (known device) → %s", email
            )
        return True

    @staticmethod
    async def send_account_locked_notification(email: str) -> bool:
        """Notify user that their account has been locked."""
        logger.info("ACCOUNT LOCKED NOTIFICATION → %s", email)
        # TODO: Integrate with email provider
        return True

    @staticmethod
    async def send_password_changed_notification(email: str) -> bool:
        """Notify user that their password was changed."""
        logger.info("PASSWORD CHANGED NOTIFICATION → %s", email)
        # TODO: Integrate with email provider
        return True

    @staticmethod
    async def send_admin_password_reset_notification(
        admin_email: str, target_email: str
    ) -> bool:
        """Notify the admin and target user of an admin-initiated reset."""
        logger.info(
            "ADMIN PASSWORD RESET → target=%s initiated_by=%s",
            target_email,
            admin_email,
        )
        # TODO: Integrate with email provider
        return True
