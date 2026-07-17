from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeResponse,
    DepartmentUpdate,
)
from app.services.department import DepartmentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/departments", tags=["departments"])

_jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=True,
)


def _render(template_name: str, context: dict | None = None) -> str:
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(context or {})


# ── JSON API endpoints ──────────────────────────────────────────────────────


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department(
    body: DepartmentCreate,
    current_user=Depends(require_permission("department", "create")),
    db: AsyncSession = Depends(get_db),
):
    try:
        dept = await DepartmentService.create_department(
            db,
            name=body.name,
            code=body.code,
            created_by=current_user.id,
            description=body.description,
            parent_id=body.parent_id,
            head_id=body.head_id,
            display_order=body.display_order,
        )
        await db.commit()
        return DepartmentResponse.model_validate(dept)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=list[DepartmentResponse])
async def list_departments(
    current_user=Depends(require_permission("department", "read")),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 50,
    include_inactive: bool = False,
):
    departments, _total = await DepartmentService.list_departments(
        db, include_inactive=include_inactive, page=page, page_size=page_size
    )
    return [
        DepartmentResponse.model_validate(d)
        for d in departments
    ]


@router.get("/tree", response_model=list[DepartmentTreeResponse])
async def get_department_tree(
    current_user=Depends(require_permission("department", "read")),
    db: AsyncSession = Depends(get_db),
):
    tree = await DepartmentService.get_department_tree(db)
    return tree


@router.get("/list-rows", response_class=HTMLResponse)
async def list_department_rows_html(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(require_permission("department", "read")),
    db: AsyncSession = Depends(get_db),
):
    departments, total = await DepartmentService.list_departments(
        db, page=page, page_size=page_size
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    html = _render("components/department_list_rows.html", {
        "departments": departments,
        "page": page,
        "total": total,
        "total_pages": total_pages,
    })
    return HTMLResponse(html)


@router.get("/select-options", response_class=HTMLResponse)
async def department_select_options_html(
    current_user=Depends(require_permission("department", "read")),
    db: AsyncSession = Depends(get_db),
):
    departments, _total = await DepartmentService.list_departments(
        db, page=1, page_size=200
    )
    html = ""
    for dept in departments:
        html += f'<option value="{dept.id}">{dept.name} ({dept.code})</option>\n'
    return HTMLResponse(html)


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: str,
    current_user=Depends(require_permission("department", "read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        did = uuid.UUID(dept_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Department not found")

    dept = await DepartmentService.get_department(db, did)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")

    resp = DepartmentResponse.model_validate(dept)
    resp.children_count = len(dept.children) if dept.children else 0
    return resp


@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: str,
    body: DepartmentUpdate,
    current_user=Depends(require_permission("department", "update")),
    db: AsyncSession = Depends(get_db),
):
    try:
        did = uuid.UUID(dept_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Department not found")

    try:
        update_data = body.model_dump(exclude_unset=True)
        dept = await DepartmentService.update_department(
            db, did, current_user.id, **update_data
        )
        await db.commit()
        return DepartmentResponse.model_validate(dept)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{dept_id}", response_model=DepartmentResponse)
async def delete_department(
    dept_id: str,
    current_user=Depends(require_permission("department", "delete")),
    db: AsyncSession = Depends(get_db),
):
    try:
        did = uuid.UUID(dept_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Department not found")

    try:
        dept = await DepartmentService.deactivate_department(db, did, current_user.id)
        await db.commit()
        return DepartmentResponse.model_validate(dept)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
