import os
import jwt
import uuid
from typing import Annotated
from pydantic import BaseModel
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlmodel import Session, select
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from api.models import (
    UserResponse,
    UserRequest,
    DeleteUserRequest,
)

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.constants import UserRole
from src.database import get_session, Users, Tokens
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)

load_dotenv()

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 1440)
ADMIN_ACCESS_TOKEN = os.getenv("ADMIN_ACCESS_TOKEN") or str(uuid.uuid4())

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")

user_router = APIRouter()


logger.critical("ADMIN_ACCESS_TOKEN: %s", ADMIN_ACCESS_TOKEN)


class Token(BaseModel):
    """
    Token model

    Attributes:
        access_token (str): Access token
        token_type (str): Token type
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password

    Args:
        plain_password (str): Plain password
        hashed_password (str): Hashed password

    Returns:
        bool: True if password is verified else False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get hashed password

    Args:
        password (str): Password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def get_user(
    session: Session,
    username: str | None = None,
) -> Users:
    """
    Get user by username

    Args:
        session (Session): Database session
        username (str | None): Username
        email (str | None): Email

    Returns:
        Users: User object if found

    Raises:
        ValueError: If username or email is not provided
    """

    if not username:
        raise ValueError("Username is required")
    with session as session_db:
        query = select(Users).where(
            Users.username == username,
        )
        user = session_db.exec(query).first()

        session_db.close()
        return user


def authenticate_user(session: Session, username: str, password: str) -> Users | bool:
    """
    Authenticate user

    Args:
        session (Session): Database session
        username (str): Username
        password (str): Password

    Returns:
        Users: User object if authenticated else `False`
    """
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(
    data: dict, expires_delta: timedelta | None = None, long_term_token: bool = False
) -> str:
    """
    Create access token

    Args:
        data (dict): Data to encode
        expires_delta (timedelta): Expiry time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    to_encode.update({"long_term_token": long_term_token})
    to_encode.update({"created_at": str(datetime.now(timezone.utc))})

    # Add expiry time if provided, if no provided, then token will never expire
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_user_token(
    token: str,
    session: Annotated[Session, Depends(get_session)],
) -> Users:
    """
    Decode user from token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = get_user(session=session, username=token_data.username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db_session: Annotated[Session, Depends(get_session)],
):
    """
    Returns the current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        long_term_token = payload.get("long_term_token")
        if long_term_token:
            with db_session as session:
                query_token = select(Tokens).where(Tokens.token == token)
                token = session.exec(query_token).first()

                if not token:
                    logger.warning("Token not found !!!")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token!!!",
                    )

        token_data = TokenData(username=username)
    except Exception as e:
        logger.error("Error in get_current_user: %s", e)
        raise credentials_exception

    user = get_user(session=db_session, username=token_data.username)

    if user is None:
        raise credentials_exception

    return user


@user_router.post(
    "/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_new_user(
    userInfo: UserRequest, db_session: Annotated[Session, Depends(get_session)]
):
    """
    Endpoint to create a new user
    """
    username = userInfo.username
    email = userInfo.email
    password = userInfo.password
    admin_access_token = userInfo.admin_access_token

    with db_session as session:
        user = get_user(session, username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered",
            )

        role = UserRole.USER
        if admin_access_token is not None:
            if admin_access_token == ADMIN_ACCESS_TOKEN:
                role = UserRole.ADMIN
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Key not match, forbidden to create admin user",
                )

        new_user = Users(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        session.close()

        return new_user


@user_router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: Annotated[Session, Depends(get_session)],
):
    """
    Endpoint to login and get access token
    """
    user = authenticate_user(db_session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@user_router.get("/me", response_model=UserResponse)
async def current_user(current_user: Users = Depends(get_current_user)):
    """
    Endpoint to get current user logged in
    """
    return current_user


@user_router.delete("/delete", response_class=JSONResponse)
async def delete_user(
    delete_user_request: DeleteUserRequest,
    db_session: Annotated[Session, Depends(get_session)],
):
    """
    Endpoint to delete a user
    """
    allow_to_delete = ADMIN_ACCESS_TOKEN == delete_user_request.admin_access_token

    if not allow_to_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden to delete user"
        )

    with db_session as session:
        user = get_user(session, delete_user_request.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        session.delete(user)
        session.commit()
        session.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"User: {delete_user_request.username} deleted"},
        )
