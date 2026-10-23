import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.core.security import hash_password, new_session_token, verify_password
from app.models.session import UserSession
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def issue_session(user: User, session: Session, request: Request) -> AuthResponse:
    token, token_hash = new_session_token()
    expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        hours=request.app.state.settings.session_ttl_hours
    )
    session.add(UserSession(id=str(uuid4()), user_id=user.id, token_hash=token_hash, expires_at=expires))
    session.commit()
    return AuthResponse(access_token=token, user=user)


def current_user(
    session: DatabaseSession, authorization: Annotated[str | None, Header()] = None
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required.")
    token = authorization.split(" ", 1)[1].strip()
    record = session.scalar(select(UserSession).where(UserSession.token_hash == hashlib.sha256(token.encode()).hexdigest()))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not record or record.expires_at <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid.")
    user = session.get(User, record.user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid.")
    return user


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest, request: Request, session: DatabaseSession):
    email = payload.email.lower()
    if session.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists.")
    user = User(id=str(uuid4()), email=email, full_name=payload.full_name.strip(),
                password_hash=hash_password(payload.password))
    session.add(user)
    session.flush()
    return issue_session(user, session, request)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, session: DatabaseSession):
    user = session.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    return issue_session(user, session, request)


@router.get("/me", response_model=UserResponse)
def profile(user: Annotated[User, Depends(current_user)]):
    return user


@router.get("/profile", response_model=UserResponse)
def profile_alias(user: Annotated[User, Depends(current_user)]):
    return user


@router.post("/logout", status_code=204)
def logout(session: DatabaseSession, authorization: Annotated[str | None, Header()] = None):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        record = session.scalar(select(UserSession).where(UserSession.token_hash == hashlib.sha256(token.encode()).hexdigest()))
        if record:
            session.delete(record)
            session.commit()
