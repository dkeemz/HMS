"""Shared test infrastructure for HMS integration tests.

Creates a separate FastAPI app using SQLite in-memory with:
- PostgreSQL UUID → VARCHAR(36) adaptation
- JSONB → JSON column adaptation
- FOR UPDATE → stripped queries (SQLite doesn't support row locking)
- Mocked KeycloakService (no external HTTP calls)
- Local JWT tokens via settings.SECRET_KEY
- Per-test database cleanup
"""

from __future__ import annotations

import os

os.environ.setdefault("DEBUG", "true")

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
import sqlalchemy as sa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.models import *  # noqa: F401,F403 — ensure all models are registered
from app.models.account_lockout import AccountLockout
from app.models.allergy import Allergy
from app.models.audit_log import AuditLog
from app.models.break_glass import BreakGlassAccess
from app.models.break_glass_audit import BreakGlassAudit
from app.models.condition import Condition
from app.models.family_history import FamilyHistory
from app.models.password_history import PasswordHistory
from app.models.password_reset import PasswordResetToken
from app.models.insurance_policy import InsurancePolicy
from app.models.patient import (
    Consent,
    EmergencyContact,
    InsuranceProvider,
    MrnSequence,
    NextOfKin,
    Patient,
)
from app.models.permission import Permission
from app.models.permission_override import PermissionOverride
from app.models.role import Role
from app.models.role_approval import RoleAssignmentApproval
from app.models.role_permission import RolePermission
from app.models.session import UserSession
from app.models.surgery import Surgery
from app.models.temporary_role import TemporaryRoleElevation
from app.models.user import User
from app.models.user_role import UserRole
from app.models.visit import Visit
from app.models.visit_summary import VisitSummary
from app.services.keycloak import KeycloakService
from app.services.notifications import NotificationService

# ── Table cleanup order (reverse FK dependency) ────────────────────────────

_TABLES_IN_DELETE_ORDER = [
    BreakGlassAudit,
    BreakGlassAccess,
    Allergy,
    Condition,
    FamilyHistory,
    Surgery,
    EmergencyContact,
    NextOfKin,
    Consent,
    VisitSummary,
    Patient,
    InsurancePolicy,
    InsuranceProvider,
    MrnSequence,
    RoleAssignmentApproval,
    TemporaryRoleElevation,
    PermissionOverride,
    RolePermission,
    UserRole,
    PasswordResetToken,
    PasswordHistory,
    AccountLockout,
    UserSession,
    AuditLog,
    Role,
    Permission,
    User,
]

# ── Engine & session factory (session-scoped) ─────────────────────────────

engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Strip FOR UPDATE from all SQL (SQLite doesn't support row-level locking)
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _strip_for_update(
    conn, cursor, statement, context, parameters, *args,
):  # type: ignore[no-untyped-def]
    if "FOR UPDATE" in statement:
        cursor.statement = re.sub(
            r"\s+FOR\s+UPDATE", "", statement, flags=re.IGNORECASE
        )


_test_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# ── PostgreSQL type adaptation ────────────────────────────────────────────
# SQLite doesn't support UUID or JSONB types. We replace column types with
# compatible Python types AND provide bind-level conversion so that Python
# uuid.UUID objects are serialized to strings before reaching SQLite.

class _StringUUID(sa.TypeDecorator):
    """Store UUIDs as VARCHAR(36) and round-trip uuid.UUID objects."""
    impl = sa.String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> uuid.UUID | None:
        if value is None:
            return None
        return uuid.UUID(value)


class _StringJSON(sa.TypeDecorator):
    """Accept JSONB-style dict/list and pass through as plain JSON."""
    impl = sa.JSON()
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        return value


class _AwareDateTime(sa.TypeDecorator):
    """Wrap DateTime(timezone=True) so naive datetimes from SQLite get UTC attached."""
    impl = sa.DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is not None and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return value


def _adapt_uuid_columns() -> None:
    """Replace PostgreSQL UUID/JSONB columns with SQLite-compatible types."""
    for table in Base.metadata.tables.values():
        for col in table.columns:
            cls_name = col.type.__class__.__name__
            if cls_name == "UUID":
                col.type = _StringUUID()
            elif cls_name == "JSONB":
                col.type = _StringJSON()
            elif cls_name == "DateTime" and getattr(col.type, "timezone", False):
                col.type = _AwareDateTime()


_adapt_uuid_columns()


# ── Mock KeycloakService ──────────────────────────────────────────────────

class MockKeycloakService:
    """Fake KeycloakService that never hits the network."""

    def __init__(self) -> None:
        self.admin = MagicMock()

    def get_token(self, username: str, password: str) -> dict[str, Any]:
        if password == "wrong":
            raise Exception("Invalid credentials")
        return {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_in": 900,
        }

    def get_user_info(self, token: str) -> dict[str, Any]:
        return {
            "sub": str(uuid.uuid4()),
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
        }

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        if refresh_token == "invalid":
            raise Exception("Invalid refresh token")
        return {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 900,
        }

    def logout(self, refresh_token: str) -> None:
        pass

    def validate_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

    def get_required_actions(self, keycloak_user_id: str) -> list[str]:
        return []

    def set_required_actions(self, keycloak_user_id: str, actions: list[str]) -> None:
        pass

    async def sync_roles_from_keycloak(self, db: Any, user_id: Any) -> None:
        pass


# ── Test app (no AuditMiddleware / SessionTimeoutMiddleware) ──────────────

def create_test_app() -> FastAPI:
    """Create a clean FastAPI app for testing without middleware that
    requires external infrastructure."""
    from fastapi import APIRouter
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    from app.api.v1.audit import router as audit_router
    from app.api.v1.auth import router as auth_router
    from app.api.v1.break_glass import router as break_glass_router
    from app.api.v1.insurance import providers_router, router as insurance_router
    from app.api.v1.medical_history import router as medical_history_router
    from app.api.v1.patient_search import router as patient_search_router
    from app.api.v1.password import router as password_router
    from app.api.v1.patients import router as patients_router
    from app.api.v1.rbac import router as rbac_router
    from app.api.v1.visits import router as visits_router
    from app.core.rate_limit import limiter

    app = FastAPI(title="HMS Test")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    v1 = APIRouter()
    v1.include_router(auth_router)
    v1.include_router(password_router)
    v1.include_router(rbac_router)
    v1.include_router(audit_router)
    v1.include_router(break_glass_router)
    v1.include_router(patient_search_router)
    v1.include_router(patients_router)
    v1.include_router(medical_history_router)
    v1.include_router(insurance_router)
    v1.include_router(providers_router)
    v1.include_router(visits_router)

    @v1.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/")
    async def root():
        return {"status": "ok"}

    app.include_router(v1, prefix="/api/v1")
    return app


test_app = create_test_app()


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
async def _setup_db():
    """Create all tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def _clear_tables():
    """Delete all rows after each test for isolation."""
    yield
    async with engine.begin() as conn:
        for model in _TABLES_IN_DELETE_ORDER:
            table = model.__table__
            try:
                await conn.execute(
                    text(f"DELETE FROM {table.name}"),  # noqa: S608
                )
            except Exception:  # noqa: BLE001
                pass  # table may not exist yet


@pytest.fixture()
async def db_session():
    """Provide an async DB session for direct model manipulation in tests."""
    async with _test_session_factory() as session:
        yield session


@pytest.fixture()
async def client():
    """HTTP client wired to the test FastAPI app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Token helpers ─────────────────────────────────────────────────────────

def create_access_token(
    sub: str | None = None,
    email: str | None = None,
    **extra: Any,
) -> str:
    """Create a HS256 JWT that decode_keycloak_token can verify."""
    payload: dict[str, Any] = {
        "sub": sub or str(uuid.uuid4()),
        "email": email or "user@example.com",
        "given_name": "Test",
        "family_name": "User",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
    }
    payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── User / Role / Permission factories ────────────────────────────────────

async def create_user(
    db: AsyncSession,
    email: str = "test@example.com",
    first_name: str = "Test",
    last_name: str = "User",
    password_hash: str | None = None,
    status: str = "active",
    **kwargs: Any,
) -> User:
    if password_hash is None:
        password_hash = f"keycloak:{uuid.uuid4()}"
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password_hash=password_hash,
        status=status,
        **kwargs,
    )
    db.add(user)
    await db.flush()
    return user


async def create_role(
    db: AsyncSession,
    name: str = "TestRole",
    description: str | None = None,
    is_system: bool = False,
) -> Role:
    role = Role(name=name, description=description, is_system=is_system)
    db.add(role)
    await db.flush()
    return role


async def create_permission(
    db: AsyncSession,
    resource: str = "patient",
    action: str = "read",
    description: str | None = None,
) -> Permission:
    perm = Permission(resource=resource, action=action, description=description)
    db.add(perm)
    await db.flush()
    return perm


async def assign_role_to_user(
    db: AsyncSession,
    user: User,
    role: Role,
    status: str = "approved",
    assigned_by: uuid.UUID | None = None,
) -> UserRole:
    ur = UserRole(
        user_id=user.id,
        role_id=role.id,
        assigned_by=assigned_by,
        status=status,
    )
    db.add(ur)
    await db.flush()
    return ur


async def assign_permission_to_role(
    db: AsyncSession,
    role: Role,
    permission: Permission,
) -> RolePermission:
    rp = RolePermission(role_id=role.id, permission_id=permission.id)
    db.add(rp)
    await db.flush()
    return rp


# ── Composite fixture helpers ─────────────────────────────────────────────

@pytest.fixture()
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user with the Admin role."""
    user = await create_user(
        db_session, email="admin@hms.local",
        first_name="Admin", last_name="User",
    )
    role = await create_role(db_session, name="Admin", is_system=True)
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    return user


@pytest.fixture()
async def doctor_user(db_session: AsyncSession) -> User:
    """Create a doctor user with the Doctor role."""
    user = await create_user(
        db_session, email="doctor@hms.local",
        first_name="Doc", last_name="Tor",
    )
    role = await create_role(db_session, name="Doctor", is_system=True)
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    return user


@pytest.fixture()
async def compliance_user(db_session: AsyncSession) -> User:
    """Create a compliance officer user."""
    user = await create_user(
        db_session, email="compliance@hms.local",
        first_name="Comp", last_name="Officer",
    )
    role = await create_role(db_session, name="Compliance Officer", is_system=True)
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    return user


@pytest.fixture()
async def auditor_user(db_session: AsyncSession) -> User:
    """Create a system auditor user."""
    user = await create_user(
        db_session, email="auditor@hms.local",
        first_name="Sys", last_name="Auditor",
    )
    role = await create_role(db_session, name="System Auditor", is_system=True)
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    return user


@pytest.fixture()
async def nurse_user(db_session: AsyncSession) -> User:
    """Create a nurse user."""
    user = await create_user(
        db_session, email="nurse@hms.local",
        first_name="Nurse", last_name="User",
    )
    role = await create_role(db_session, name="Nurse", is_system=True)
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    return user


@pytest.fixture()
async def sample_permission(db_session: AsyncSession) -> Permission:
    """Create a sample patient:read permission."""
    perm = await create_permission(db_session, resource="patient", action="read")
    await db_session.commit()
    return perm


# ── Patient factory ──────────────────────────────────────────────────────

async def create_patient(
    db: AsyncSession,
    first_name: str = "Test",
    last_name: str = "Patient",
    mrn: str = "LAG-000001",
    date_of_birth: Any | None = None,
    gender: str = "Male",
    phone: str = "08012345678",
    status: str = "active",
    **kwargs: Any,
) -> Patient:
    from datetime import date as _date

    if date_of_birth is None:
        date_of_birth = _date(1990, 1, 1)
    patient = Patient(
        mrn=mrn,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        phone=phone,
        status=status,
        address_street="123 Test St",
        address_city="Lagos",
        address_state="Lagos",
        **kwargs,
    )
    db.add(patient)
    await db.flush()
    return patient


@pytest.fixture()
async def sample_patient(db_session: AsyncSession) -> Patient:
    """Create a sample patient for tests."""
    patient = await create_patient(db_session)
    await db_session.commit()
    return patient


# ── Override dependencies on test_app ─────────────────────────────────────

async def _override_get_db():
    """Yield a session wired to the test engine."""
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


test_app.dependency_overrides[get_db] = _override_get_db


def _mock_keycloak_service() -> MockKeycloakService:
    return MockKeycloakService()


# Override the _keycloak_service factory function used in auth.py
from app.api.v1 import auth as auth_module  # noqa: E402

_original_keycloak_factory = auth_module._keycloak_service
auth_module._keycloak_service = _mock_keycloak_service  # type: ignore[attr-defined]
test_app.dependency_overrides[_original_keycloak_factory] = (
    _mock_keycloak_service
)

# Override KeycloakService class used as Depends in password.py
test_app.dependency_overrides[KeycloakService] = _mock_keycloak_service


# ── Monkey-patch decode_keycloak_token & sync_user_from_keycloak ──────────
# Replace the module-level functions so they use local JWT decode
# and skip Keycloak API calls during testing.

import app.core.security as _security_mod  # noqa: E402


def _test_decode_keycloak_token(token: str) -> dict:
    """Decode a HS256 JWT (same as the fallback in production)."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        from fastapi import HTTPException
        from fastapi import status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc


async def _test_sync_user_from_keycloak(
    db: AsyncSession, payload: dict
) -> User:
    """Find or create user by email — no Keycloak API calls."""
    from sqlalchemy import select as sa_select

    email = payload.get("email", "")
    result = await db.execute(
        sa_select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            first_name=payload.get("given_name", ""),
            last_name=payload.get("family_name", ""),
            password_hash=f"keycloak:{payload.get('sub', '')}",
            status="active",
        )
        db.add(user)
        await db.flush()
    return user


_security_mod.decode_keycloak_token = _test_decode_keycloak_token  # type: ignore[assignment]
_security_mod.sync_user_from_keycloak = _test_sync_user_from_keycloak  # type: ignore[assignment]

# Also patch in deps.py module since it imported the originals


# ── Notification mocking (prevent email side effects) ─────────────────────

@pytest.fixture(autouse=True)
def _mock_notifications(monkeypatch: pytest.MonkeyPatch) -> None:
    """Silence all NotificationService calls in tests."""
    for method_name in dir(NotificationService):
        if method_name.startswith("send_"):
            monkeypatch.setattr(
                NotificationService,
                method_name,
                AsyncMock(return_value=True),
            )
