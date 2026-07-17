"""Seed Nigerian insurance providers for HMS.

Usage:
    python -m app.seeds.insurance_providers
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.patient import InsuranceProvider


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    provider_type: str  # NHIS, HMO, Private, Corporate, Military, Tertiary
    short_code: str
    website: str | None = None


PROVIDER_SPECS: list[ProviderSpec] = [
    ProviderSpec("National Health Insurance Scheme", "NHIS", "NHIS", "https://nhis.gov.ng"),
    ProviderSpec("Hygeia HMO", "HMO", "HYG", "https://hygeiahmo.com"),
    ProviderSpec("Leadway Health", "HMO", "LDW", "https://leadway.com"),
    ProviderSpec("AIICO Insurance Health", "HMO", "AII", "https://aiicoplc.com"),
    ProviderSpec("Reliance HMO", "HMO", "RLH", "https://reliancehmo.com"),
    ProviderSpec("AXA Mansard Health", "HMO", "AXM", "https://mansard.com"),
    ProviderSpec("Cornerstone Insurance Health", "HMO", "COR", "https://cornerstone.com.ng"),
    ProviderSpec("Defence Health Insurance Scheme", "Military", "DHIS"),
    ProviderSpec("Police Health Insurance", "Military", "PHI"),
    ProviderSpec("Lagos State Health Management Agency", "Tertiary", "LASHMA"),
]


async def seed() -> None:
    """Run the seed: idempotent insert of providers."""
    async with async_session() as session:
        async with session.begin():
            existing = (
                await session.execute(select(InsuranceProvider))
            ).scalars().all()
            existing_names = {p.name for p in existing}

            added = 0
            for spec in PROVIDER_SPECS:
                if spec.name not in existing_names:
                    session.add(InsuranceProvider(
                        name=spec.name,
                        provider_type=spec.provider_type,
                        short_code=spec.short_code,
                        website=spec.website,
                    ))
                    added += 1

            await session.flush()

    print(f"Seeded {added} new insurance providers ({len(PROVIDER_SPECS)} total)")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
