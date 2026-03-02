"""OPA policy client with async HTTP queries.

Provides ``check_permission()`` and ``get_allowed_actions()`` to query a
running OPA server.  When OPA is unreachable **and** the application is
running in dev mode (``OPA_URL`` points to localhost), a built-in
fallback permission matrix is used so that development can continue
without a live OPA server.  In production the fail-closed principle
always applies.
"""
import logging
import httpx
from config import settings
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.rbac import Role, Permission, RolePermission

logger = logging.getLogger(__name__)

OPA_URL = settings.OPA_URL
_POLICY_PATH = "/v1/data/veritas/authz"

# Fallback matrix for dev mode
_FALLBACK_PERMISSIONS = {
    "it_admin": {
        "users": ["list", "create", "delete", "update", "read"],
        "rbac": ["list", "update"],
        "system": ["read", "write"],
        "documents": ["view_all", "upload", "delete_any"],
        "workflows": ["list", "create", "delete", "view_all", "update"],
        "ai_analysis": ["view_any"],
        "audit_logs": ["view_all", "view_own"],
    },
    "paralegal": {
        "documents": ["view_own", "upload"],
        "ai_analysis": ["view_own"],
        "workflows": ["list"],
    },
    "associate": {
        "documents": ["view_all", "upload"],
        "ai_analysis": ["view_any", "run"],
        "workflows": ["list", "run"],
    },
    "partner": {
        "documents": ["view_all", "upload", "delete_any"],
        "ai_analysis": ["view_any", "run", "approve"],
        "workflows": ["list", "run", "approve"],
    }
}

def _is_dev_mode() -> bool:
    """Return True if we are likely in a dev environment."""
    return "localhost" in OPA_URL or "127.0.0.1" in OPA_URL

def _fallback_check(role: str, resource: str, action: str) -> bool:
    """Check against the fallback matrix."""
    role_perms = _FALLBACK_PERMISSIONS.get(role, {})
    return action in role_perms.get(resource, [])

def _fallback_actions(role: str) -> list[dict[str, str]]:
    """Return all actions from the fallback matrix."""
    role_perms = _FALLBACK_PERMISSIONS.get(role, {})
    actions = []
    for resource, acts in role_perms.items():
        for action in acts:
            actions.append({"resource": resource, "action": action})
    return actions

def _check_db_permission(role_name: str, resource: str, action: str) -> bool | None:
    """Check database for permission. Returns None if role/permission not found."""
    db = SessionLocal()
    try:
        # Permission name in DB is formatted as "resource/action"
        perm_name = f"{resource}/{action}"
        result = (
            db.query(RolePermission.allowed)
            .join(Role, Role.id == RolePermission.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .filter(Role.name == role_name, Permission.name == perm_name)
            .first()
        )
        return bool(result[0]) if result else None
    except Exception as e:
        logger.error("Error checking DB permission: %s", e)
        return None
    finally:
        db.close()


def _get_db_allowed_actions(role_name: str) -> list[dict[str, str]] | None:
    """Get all allowed actions for a role from the database."""
    db = SessionLocal()
    try:
        results = (
            db.query(Permission.name)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, Role.id == RolePermission.role_id)
            .filter(Role.name == role_name, RolePermission.allowed == True)
            .all()
        )
        actions = []
        for (name,) in results:
            if "/" in name:
                res, act = name.split("/", 1)
                actions.append({"resource": res, "action": act})
            else:
                actions.append({"resource": name, "action": "read"})
        return actions if actions else None
    except Exception as e:
        logger.error("Error fetching DB allowed actions: %s", e)
        return None
    finally:
        db.close()


def _get_client() -> httpx.AsyncClient:
    """Return an async httpx client."""
    return httpx.AsyncClient(timeout=2.0)

async def check_permission(role: str, resource: str, action: str) -> bool:
    """Query OPA, then DB, then fallback matrix."""
    from services.metrics_service import OPA_DECISION_LATENCY
    import time

    start_time = time.time()
    try:
        # 1. Try OPA (Production approach)
        try:
            async with _get_client() as client:
                resp = await client.post(
                    f"{OPA_URL}{_POLICY_PATH}/allow",
                    json={"input": {"role": role, "resource": resource, "action": action}},
                )
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result is not None:
                        return bool(result)
        except Exception:
            pass

        # 2. Try Database (Dynamic RBAC)
        db_allowed = _check_db_permission(role, resource, action)
        if db_allowed is not None:
            return db_allowed

        # 3. Fallback to static matrix (Safe default)
        if _is_dev_mode():
            return _fallback_check(role, resource, action)
        
        return False
    finally:
        OPA_DECISION_LATENCY.observe(time.time() - start_time)


async def get_allowed_actions(role: str) -> list[dict[str, str]]:
    """Return all allowed actions from OPA or DB."""
    try:
        async with _get_client() as client:
            resp = await client.post(
                f"{OPA_URL}{_POLICY_PATH}/allowed_actions",
                json={"input": {"role": role}},
            )
            if resp.status_code == 200:
                result = resp.json().get("result")
                if result is not None:
                    return result
    except Exception:
        pass

    db_actions = _get_db_allowed_actions(role)
    if db_actions is not None:
        return db_actions

    if _is_dev_mode():
        return _fallback_actions(role)
    
    return []
