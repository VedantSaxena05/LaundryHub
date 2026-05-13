from typing import Union
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Student, Staff
from app.schemas.auth import UserRole
from app.services.auth_service import decode_token, get_student_by_id, get_staff_by_id
from app.utils.exceptions import UnauthorizedError, ForbiddenError

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Union[Student, Staff]:
    """
    Validates the Bearer token and returns the ORM user object.
    Works for students, staff, and admins — role is embedded in the JWT.
    """
    payload = decode_token(credentials.credentials)
    user_id = UUID(payload.sub)

    if payload.role == UserRole.student:
        user = get_student_by_id(db, user_id)
    else:
        user = get_staff_by_id(db, user_id)

    if not user:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    # Attach role so downstream code can read it without another DB hit
    user._jwt_role = payload.role
    return user


def require_role(*roles: UserRole):
    """
    Returns a FastAPI dependency that enforces one of the given roles.

    Usage:
        @router.get("/admin-only")
        def endpoint(user = Depends(require_role(UserRole.admin))):
            ...
    """
    def _checker(user: Union[Student, Staff] = Depends(get_current_user)):
        if not hasattr(user, "_jwt_role") or user._jwt_role not in roles:
            raise ForbiddenError(
                f"Requires role(s): {', '.join(r.value for r in roles)}"
            )
        return user
    return _checker


# Convenience aliases
require_student = require_role(UserRole.student)
require_staff   = require_role(UserRole.staff, UserRole.admin)
require_admin   = require_role(UserRole.admin)