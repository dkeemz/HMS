from __future__ import annotations

import logging
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_lockout import AccountLockout
from app.models.password_history import PasswordHistory
from app.models.password_reset import PasswordResetToken

logger = logging.getLogger(__name__)


class PasswordPolicyService:
    """HMS-side password policy enforcement.

    Keycloak handles actual password validation during login, but this
    service enforces HIPAA-aligned policies for:
    - Password complexity validation (pre-change)
    - Password history (no reuse of last N)
    - Account lockout after failed attempts
    - Password reset tokens
    - Session invalidation on password change
    """

    MIN_LENGTH = 12
    MAX_AGE_DAYS = 90
    HISTORY_COUNT = 12
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 30
    RESET_TOKEN_EXPIRY_MINUTES = 15

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password meets HIPAA-aligned policy.

        Returns (is_valid, error_message).
        """
        errors: list[str] = []

        if len(password) < PasswordPolicyService.MIN_LENGTH:
            errors.append(
                f"Password must be at least {PasswordPolicyService.MIN_LENGTH} "
                "characters long"
            )

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", password):
            errors.append("Password must contain at least one special character")

        if errors:
            return False, "; ".join(errors)

        return True, ""

    @staticmethod
    async def check_password_history(
        db: AsyncSession, user_id: uuid.UUID, new_password_hash: str
    ) -> bool:
        """Check if the new password was used in the last N passwords.

        Returns True if the password is allowed (not reused).
        """
        result = await db.execute(
            select(PasswordHistory.password_hash)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(PasswordPolicyService.HISTORY_COUNT)
        )
        recent_hashes = [row[0] for row in result.all()]

        # Compare using constant-time comparison to prevent timing attacks
        for old_hash in recent_hashes:
            if secrets.compare_digest(new_password_hash, old_hash):
                return False

        return True

    @staticmethod
    async def record_password_usage(
        db: AsyncSession, user_id: uuid.UUID, password_hash: str
    ) -> None:
        """Record password usage in history."""
        record = PasswordHistory(user_id=user_id, password_hash=password_hash)
        db.add(record)

        # Prune entries beyond the history limit
        subquery = (
            select(PasswordHistory.id)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .offset(PasswordPolicyService.HISTORY_COUNT)
            .limit(100)
        )
        old_entries = await db.execute(
            select(PasswordHistory).where(PasswordHistory.id.in_(subquery))
        )
        for entry in old_entries.scalars().all():
            await db.delete(entry)

        await db.flush()

    @staticmethod
    async def check_account_lockout(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, datetime | None]:
        """Check if account is locked.

        Returns (is_locked, locked_until).
        """
        result = await db.execute(
            select(AccountLockout).where(AccountLockout.user_id == user_id)
        )
        lockout = result.scalar_one_or_none()

        if lockout is None:
            return False, None

        if lockout.locked_until is None:
            return False, None

        now = datetime.now(UTC)
        if now < lockout.locked_until:
            return True, lockout.locked_until

        # Lockout expired — reset the record
        lockout.failed_attempts = 0
        lockout.locked_until = None
        await db.flush()
        return False, None

    @staticmethod
    async def record_failed_attempt(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, datetime | None]:
        """Record a failed login attempt. Locks the account if threshold is reached.

        Returns (is_now_locked, locked_until).
        """
        result = await db.execute(
            select(AccountLockout).where(AccountLockout.user_id == user_id)
        )
        lockout = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if lockout is None:
            lockout = AccountLockout(user_id=user_id, failed_attempts=0)
            db.add(lockout)

        lockout.failed_attempts = (lockout.failed_attempts or 0) + 1
        lockout.last_failed_at = now

        if lockout.failed_attempts >= PasswordPolicyService.MAX_FAILED_ATTEMPTS:
            lockout.locked_until = now + timedelta(
                minutes=PasswordPolicyService.LOCKOUT_MINUTES
            )
            logger.warning(
                "Account locked for user %s after %d failed attempts",
                user_id,
                lockout.failed_attempts,
            )
            await db.flush()
            return True, lockout.locked_until

        await db.flush()
        return False, None

    @staticmethod
    async def clear_failed_attempts(db: AsyncSession, user_id: uuid.UUID) -> None:
        """Clear failed attempts on successful login."""
        result = await db.execute(
            select(AccountLockout).where(AccountLockout.user_id == user_id)
        )
        lockout = result.scalar_one_or_none()

        if lockout is not None:
            lockout.failed_attempts = 0
            lockout.locked_until = None
            await db.flush()

    @staticmethod
    async def generate_reset_token(
        db: AsyncSession, user_id: uuid.UUID
    ) -> str:
        """Generate a password reset token with 15-minute expiry.

        Invalidates any previous unused tokens for this user.
        """
        # Invalidate old tokens
        await db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used.is_(False),
            )
            .values(used=True)
        )

        token = secrets.token_urlsafe(48)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=PasswordPolicyService.RESET_TOKEN_EXPIRY_MINUTES
        )

        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        db.add(reset_token)
        await db.flush()

        return token

    @staticmethod
    async def validate_reset_token(
        db: AsyncSession, token: str
    ) -> uuid.UUID | None:
        """Validate a reset token and return the user_id.

        Returns None if the token is invalid or expired.
        """
        result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == token,
                PasswordResetToken.used.is_(False),
            )
        )
        reset_token = result.scalar_one_or_none()

        if reset_token is None:
            return None

        if datetime.now(UTC) > reset_token.expires_at:
            reset_token.used = True
            await db.flush()
            return None

        return reset_token.user_id

    @staticmethod
    async def mark_token_used(db: AsyncSession, token: str) -> None:
        """Mark a reset token as used."""
        await db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.token == token)
            .values(used=True)
        )
        await db.flush()

    @staticmethod
    async def check_password_age(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, datetime | None]:
        """Check if the user's password has exceeded the max age.

        Returns (is_expired, password_changed_at).
        """
        from app.models.user import User

        result = await db.execute(
            select(User.password_last_changed_at).where(User.id == user_id)
        )
        password_changed_at = result.scalar_one_or_none()

        if password_changed_at is None:
            return False, None

        age = datetime.now(UTC) - password_changed_at
        is_expired = age > timedelta(days=PasswordPolicyService.MAX_AGE_DAYS)
        return is_expired, password_changed_at
