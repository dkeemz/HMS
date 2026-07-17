from __future__ import annotations

import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import MrnSequence

logger = logging.getLogger(__name__)


class MRNService:
    """Generate unique MRNs using the MrnSequence table.

    Each facility has its own sequence (e.g., LAG-000001).
    MRN format: PREFIX-NNNNNN (6 digits, zero-padded) per D-01, D-02.
    """

    _MRN_FORMAT = re.compile(r"^[A-Z]{2,5}-\d{6}$")

    @staticmethod
    async def generate_mrn(
        db: AsyncSession,
        facility_prefix: str = "LAG",
    ) -> str:
        """Generate next MRN for the given facility.

        Uses MrnSequence table with SELECT FOR UPDATE for safe
        concurrent access. Sequence continues indefinitely (D-03).
        Never reused (D-05).
        """
        result = await db.execute(
            select(MrnSequence)
            .where(MrnSequence.facility_prefix == facility_prefix)
            .with_for_update()
        )
        seq = result.scalar_one_or_none()

        if seq is None:
            # First time — create the sequence row
            seq = MrnSequence(
                facility_prefix=facility_prefix,
                facility_name=facility_prefix,
                last_value=1,
            )
            db.add(seq)
            await db.flush()
            next_val = 1
        else:
            seq.last_value += 1
            next_val = seq.last_value
            await db.flush()

        mrn = f"{facility_prefix}-{next_val:06d}"
        logger.info("Generated MRN: %s", mrn)
        return mrn

    @staticmethod
    def validate_mrn_format(mrn: str) -> bool:
        """Validate MRN format: PREFIX-NNNNNN where PREFIX is 2-5 uppercase letters."""
        return bool(MRNService._MRN_FORMAT.match(mrn))
