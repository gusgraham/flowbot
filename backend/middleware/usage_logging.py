"""
Usage Logging Middleware

Logs API requests to admin_usage_log for cost tracking purposes.
Only logs module-level requests (FSM, FSA, WQ, VER, SSD) and associates with authenticated users.
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlmodel import Session, select
from jose import jwt, JWTError

from database import engine
from domain.admin import UsageLog, ModuleWeight

# Module route prefixes mapped to module names
MODULE_PREFIXES: Dict[str, str] = {
    "/api/fsm": "FSM",
    "/api/fsa": "FSA",
    "/api/wq": "WQ",
    "/api/verification": "VER",
    "/api/ssd": "SSD",
}

# Exclude certain paths from logging (e.g., list endpoints that are called frequently)
EXCLUDE_PATTERNS = [
    # Add any high-frequency endpoints you want to exclude here
]

# Cache module weights to avoid DB lookup on every request
_weight_cache: Dict[str, float] = {}
_weight_cache_time: float = 0
WEIGHT_CACHE_TTL = 300  # 5 minutes


def get_module_from_path(path: str) -> Optional[str]:
    """Extract module name from request path."""
    for prefix, module in MODULE_PREFIXES.items():
        if path.startswith(prefix):
            return module
    return None


def get_user_id_from_token(request: Request) -> Optional[int]:
    """Extract user ID from JWT token in Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        # Import here to avoid circular imports
        from services.auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")  # Token stores username in 'sub'
        
        if not username:
            return None
        
        # Look up user_id by username
        from domain.auth import User
        with Session(engine) as session:
            user = session.exec(select(User).where(User.username == username)).first()
            return user.id if user else None
    except JWTError:
        return None
    except Exception:
        return None


def get_module_weight(module: str) -> float:
    """Get weight for a module (cached)."""
    global _weight_cache, _weight_cache_time
    
    current_time = datetime.now().timestamp()
    
    # Refresh cache if expired
    if current_time - _weight_cache_time > WEIGHT_CACHE_TTL:
        try:
            with Session(engine) as session:
                weights = session.exec(select(ModuleWeight)).all()
                _weight_cache = {w.module: w.weight for w in weights}
                _weight_cache_time = current_time
        except Exception:
            pass  # Keep old cache on error
    
    return _weight_cache.get(module, 1.0)


def log_usage(user_id: int, module: str, weight: float):
    """Log a usage entry (runs in background to not slow down request)."""
    try:
        with Session(engine) as session:
            log_entry = UsageLog(
                user_id=user_id,
                module=module,
                weight=weight,
                timestamp=datetime.now()
            )
            session.add(log_entry)
            session.commit()
    except Exception as e:
        # Don't fail the request if logging fails
        print(f"Warning: Failed to log usage: {e}")


class UsageLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API usage for cost tracking."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Only log certain HTTP methods (skip OPTIONS, etc.)
        if request.method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)
        
        # Check if this is a module request
        path = request.url.path
        module = get_module_from_path(path)
        
        if not module:
            return await call_next(request)
        
        # Check exclusion patterns
        for pattern in EXCLUDE_PATTERNS:
            if pattern in path:
                return await call_next(request)
        
        # Get user ID from token
        user_id = get_user_id_from_token(request)
        
        # Process the request first
        response = await call_next(request)
        
        # Only log successful requests with authenticated users
        if user_id and 200 <= response.status_code < 400:
            weight = get_module_weight(module)
            # Run logging in background to not delay response
            asyncio.create_task(asyncio.to_thread(log_usage, user_id, module, weight))
        
        return response
