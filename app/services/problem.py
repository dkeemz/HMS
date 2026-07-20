from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.problem import Problem
from app.schemas.problem import ProblemCreate, ProblemUpdate


class ProblemService:
    @staticmethod
    async def create(db: AsyncSession, data: ProblemCreate) -> Problem:
        problem = Problem(**data.model_dump())
        db.add(problem)
        await db.flush()
        await db.refresh(problem)
        return problem

    @staticmethod
    async def get(db: AsyncSession, problem_id: uuid.UUID) -> Problem | None:
        result = await db.execute(select(Problem).where(Problem.id == problem_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_patient(db: AsyncSession, patient_id: uuid.UUID, active_only: bool = False) -> list[Problem]:
        stmt = select(Problem).where(Problem.patient_id == patient_id).order_by(Problem.created_at.desc())
        if active_only:
            stmt = stmt.where(Problem.status == "active")
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, problem_id: uuid.UUID, data: ProblemUpdate) -> Problem | None:
        problem = await ProblemService.get(db, problem_id)
        if not problem:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(problem, k, v)
        await db.flush()
        await db.refresh(problem)
        return problem

    @staticmethod
    async def resolve(db: AsyncSession, problem_id: uuid.UUID, resolved_date: date | None = None) -> Problem | None:
        problem = await ProblemService.get(db, problem_id)
        if not problem:
            return None
        problem.status = "resolved"
        problem.resolved_date = resolved_date or date.today()
        await db.flush()
        await db.refresh(problem)
        return problem

    @staticmethod
    async def delete(db: AsyncSession, problem_id: uuid.UUID) -> bool:
        problem = await ProblemService.get(db, problem_id)
        if not problem:
            return False
        await db.delete(problem)
        await db.flush()
        return True
