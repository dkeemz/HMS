from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

AUTH_RATE = "10/minute"
MFA_VERIFY_RATE = "5/minute"
PASSWORD_RATE = "5/minute"
GENERAL_RATE = "100/minute"
