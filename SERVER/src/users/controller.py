from fastapi import APIRouter, status

from ..database.core import DBSession
from . import model
from . import service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix='/users',
    tags=["Users"]
)

@router.get("/me", response_model=model.UserResponse)
def get_current_user(current_user: CurrentUser, db: DBSession):
    return service.get_user_by_id(db, current_user.get_uuid())

@router.put("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_change: model.PasswordChange,
    db: DBSession,
    current_user: CurrentUser
):
    service.change_password(db, current_user.get_uuid(), password_change)