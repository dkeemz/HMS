from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class DepartmentService:
    """Hierarchical department CRUD."""

    @staticmethod
    async def create_department(
        db: AsyncSession,
        name: str,
        code: str,
        created_by: uuid.UUID,
        description: str | None = None,
        parent_id: uuid.UUID | None = None,
        head_id: uuid.UUID | None = None,
        display_order: int = 0,
    ) -> Department:
        existing = await db.execute(
            select(Department).where(
                (Department.name == name) | (Department.code == code)
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(
                f"Department with name '{name}' or code '{code}' already exists"
            )

        if parent_id:
            parent = await db.get(Department, parent_id)
            if not parent:
                raise ValueError("Parent department not found")

        dept = Department(
            name=name,
            code=code.upper(),
            description=description,
            parent_id=parent_id,
            head_id=head_id,
            display_order=display_order,
        )
        db.add(dept)
        await db.flush()
        await db.refresh(dept)

        await AuditService.log_event(
            db,
            user_id=created_by,
            action="create",
            resource="department",
            resource_id=str(dept.id),
            details=f"Created department: {dept.name} ({dept.code})",
        )
        logger.info("Created department %s (%s)", dept.name, dept.code)
        return dept

    @staticmethod
    async def list_departments(
        db: AsyncSession,
        include_inactive: bool = False,
        parent_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Department], int]:
        query = select(Department)
        if not include_inactive:
            query = query.where(Department.is_active == True)
        if parent_id is not None:
            query = query.where(Department.parent_id == parent_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.options(selectinload(Department.head))
        query = query.order_by(Department.display_order, Department.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        departments = list(result.scalars().all())
        return departments, total

    @staticmethod
    async def get_department_tree(db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(Department)
            .where(Department.is_active == True)
            .options(selectinload(Department.head))
            .order_by(Department.display_order, Department.name)
        )
        all_depts = list(result.scalars().all())

        dept_map: dict[uuid.UUID, dict] = {}
        for d in all_depts:
            dept_map[d.id] = {
                "id": d.id,
                "name": d.name,
                "code": d.code,
                "description": d.description,
                "parent_id": d.parent_id,
                "head_id": d.head_id,
                "display_order": d.display_order,
                "is_active": d.is_active,
                "children": [],
            }
        roots: list[dict] = []
        for d in all_depts:
            dept_dict = dept_map[d.id]
            if d.parent_id and d.parent_id in dept_map:
                dept_map[d.parent_id]["children"].append(dept_dict)
            else:
                roots.append(dept_dict)
        return roots

    @staticmethod
    async def get_department(
        db: AsyncSession, dept_id: uuid.UUID
    ) -> Department | None:
        result = await db.execute(
            select(Department)
            .where(Department.id == dept_id)
            .options(
                selectinload(Department.head),
                selectinload(Department.children),
                selectinload(Department.parent),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_department(
        db: AsyncSession,
        dept_id: uuid.UUID,
        updated_by: uuid.UUID,
        **kwargs,
    ) -> Department:
        dept = await DepartmentService.get_department(db, dept_id)
        if not dept:
            raise ValueError("Department not found")

        if kwargs.get("parent_id") == dept_id:
            raise ValueError("Department cannot be its own parent")

        for key, value in kwargs.items():
            if value is not None and hasattr(dept, key):
                setattr(dept, key, value)

        await db.flush()
        await db.refresh(dept)

        await AuditService.log_event(
            db,
            user_id=updated_by,
            action="update",
            resource="department",
            resource_id=str(dept.id),
            details=f"Updated department: {dept.name}",
        )
        return dept

    @staticmethod
    async def deactivate_department(
        db: AsyncSession,
        dept_id: uuid.UUID,
        deactivated_by: uuid.UUID,
    ) -> Department:
        dept = await DepartmentService.get_department(db, dept_id)
        if not dept:
            raise ValueError("Department not found")

        dept.is_active = False
        await db.flush()
        await db.refresh(dept)

        await AuditService.log_event(
            db,
            user_id=deactivated_by,
            action="delete",
            resource="department",
            resource_id=str(dept.id),
            details=f"Deactivated department: {dept.name}",
        )
        return dept
