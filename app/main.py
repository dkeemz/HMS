from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.deps import get_current_user_from_cookie
from app.core.rate_limit import limiter
from app.middleware.audit import AuditMiddleware
from app.middleware.session import SessionTimeoutMiddleware
from app.models.user import User

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(HTTPException)
async def redirect_on_auth_failure(request: Request, exc: HTTPException):
    """Return actual redirects for 307s (cookie auth failures on page routes)."""
    if exc.status_code == 307 and exc.headers and "Location" in exc.headers:
        return RedirectResponse(url=exc.headers["Location"], status_code=307)
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)
app.add_middleware(SessionTimeoutMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(v1_router, prefix=settings.API_V1_PREFIX, tags=["v1"])


@app.get("/")
async def root(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "index.html")


@app.get("/auth/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@app.get("/auth/mfa")
async def mfa_page(request: Request, session_id: str = ""):
    ctx = {"session_id": session_id}
    return templates.TemplateResponse(request, "auth/mfa.html", ctx)


@app.get("/auth/password-reset")
async def password_reset_page(request: Request):
    return templates.TemplateResponse(request, "auth/password_reset.html")


@app.get("/auth/password-reset/confirm")
async def password_reset_confirm_page(request: Request):
    return templates.TemplateResponse(request, "auth/password_reset_confirm.html")


@app.get("/admin/users")
async def admin_users(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "admin/users.html")


@app.get("/admin/roles")
async def admin_roles(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "admin/roles.html")


@app.get("/admin/permissions")
async def admin_permissions(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "admin/permissions.html")


@app.get("/admin/audit")
async def admin_audit(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "admin/audit.html")


@app.get("/admin/audit/integrity")
async def admin_audit_integrity(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "admin/audit-integrity.html")


@app.get("/admin/break-glass")
async def admin_break_glass(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "admin/break_glass.html")


@app.get("/patients")
async def patients_list(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "patients/list.html")


@app.get("/patients/register")
async def patients_register(request: Request, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "patients/register.html")


@app.get("/patients/{patient_id}")
async def patient_profile(request: Request, patient_id: str, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "patients/profile.html", {"patient_id": patient_id})


@app.get("/patients/{patient_id}/medical-history")
async def patient_medical_history(request: Request, patient_id: str, user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request, "patients/medical_history.html", {"patient_id": patient_id})
