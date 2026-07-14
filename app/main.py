from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.middleware.session import SessionTimeoutMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionTimeoutMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(v1_router, prefix=settings.API_V1_PREFIX, tags=["v1"])


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/admin/roles")
async def admin_roles(request: Request):
    return templates.TemplateResponse(request, "admin/roles.html")


@app.get("/admin/permissions")
async def admin_permissions(request: Request):
    return templates.TemplateResponse(request, "admin/permissions.html")
