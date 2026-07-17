"""Notifications API — stub for now."""
from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications():
    """Return placeholder notifications HTML for HTMX polling."""
    return """
    <div class="p-4 text-center text-gray-500 dark:text-gray-400">
        <p class="text-sm">No new notifications</p>
    </div>
    """
