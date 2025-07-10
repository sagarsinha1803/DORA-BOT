from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from typing import Annotated
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from ..entities.users import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from . import model
import logging
from ..exceptions import AuthenticationError

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_TIME = os.getenv("ACCESS_TOKEN_EXPIRE_TIME")

oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hased_password: str) -> bool:
    return bcrypt_context.verify(plain_password, hased_password)

def get_password_hash(plain_password: str) -> str:
    return bcrypt_context.hash(plain_password)

def authenticate_user(email: str, password: str, db: Session) -> User | bool:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logging.warning(f"Authentication failed for user: {email}. User not found.")
        return False
    if not verify_password(password, user.hashed_password):
        logging.warning(f'Authentication failed for user: {email}. Incorrect password.')
        return False
    return user

def create_access_token(email: str, user_id: UUID, expires_delta: timedelta) -> str:
    encode = {
        'sub': email,
        'id': str(user_id),
        'exp': datetime.now(timezone.utc) + expires_delta
    }

    return jwt.encode(encode, algorithm=ALGORITHM, key=SECRET_KEY)

def verify_token(token: str) -> model.TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('id')
        return model.TokenData(user_id=user_id)
    except JWTError as e:
        logging.warning(f"Token verification failed: {str(e)}")
        raise AuthenticationError()
    
def register_user(db: Session, register_user_requests: model.RegisterUserRequest) -> None:
    try:
        new_user = User(
            id=uuid4(),
            email=register_user_requests.email,
            first_name=register_user_requests.first_name,
            last_name=register_user_requests.last_name,
            hashed_password=get_password_hash(register_user_requests.password)
        )
        db.add(new_user)
        db.commit()
    except Exception as e:
        logging.error(f"Failed to register user: {register_user_requests.email}. Error: {str(e)}")
        raise

def get_current_user(token: Annotated[str, Depends(oauth_bearer)]) -> model.TokenData:
    return verify_token(token)

CurrentUser = Annotated[model.TokenData, Depends(get_current_user)]

def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session) -> model.Token:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise AuthenticationError()
    token = create_access_token(user.email, user.id, timedelta(minutes=float(ACCESS_TOKEN_EXPIRE_TIME)))
    return model.Token(access_token=token, token_type='bearer')