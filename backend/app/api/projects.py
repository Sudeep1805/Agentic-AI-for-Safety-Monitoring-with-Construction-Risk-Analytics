from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.api.dependencies import get_session
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectList, ProjectPayload, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def clean_payload(payload: ProjectPayload) -> dict:
    values = payload.model_dump()
    for key, value in values.items():
        if isinstance(value, str):
            values[key] = value.strip() or None
    for key in ("name", "construction_type", "site_address", "city", "state", "status"):
        if not values[key]:
            raise HTTPException(422, f"{key.replace('_', ' ').capitalize()} is required.")
    return values


def ensure_code_available(session: Session, user_id: str, code: str | None, project_id: str | None = None):
    if code:
        query = select(Project).where(Project.user_id == user_id, Project.code == code)
        if project_id:
            query = query.where(Project.id != project_id)
        if session.scalar(query):
            raise HTTPException(409, "A project with this code already exists.")


def find_project(project_id: UUID, session: Session, user_id: str) -> Project:
    project = session.scalar(select(Project).where(Project.id == str(project_id), Project.user_id == user_id))
    if not project:
        raise HTTPException(404, "Project not found.")
    return project


@router.get("", response_model=ProjectList)
def list_projects(session: DatabaseSession, user: Annotated[User, Depends(current_user)]):
    items = session.scalars(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc(), Project.id.desc())
    ).all()
    return ProjectList(items=items, total=len(items))


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectPayload, session: DatabaseSession, user: Annotated[User, Depends(current_user)]):
    values = clean_payload(payload)
    ensure_code_available(session, user.id, values["code"])
    project = Project(id=str(uuid4()), user_id=user.id, **values)
    session.add(project)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "A project with this code already exists.") from None
    session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, session: DatabaseSession, user: Annotated[User, Depends(current_user)]):
    return find_project(project_id, session, user.id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    payload: ProjectPayload,
    session: DatabaseSession,
    user: Annotated[User, Depends(current_user)],
):
    project = find_project(project_id, session, user.id)
    values = clean_payload(payload)
    ensure_code_available(session, user.id, values["code"], project.id)
    for key, value in values.items():
        setattr(project, key, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "A project with this code already exists.") from None
    session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, session: DatabaseSession, user: Annotated[User, Depends(current_user)]):
    project = find_project(project_id, session, user.id)
    session.delete(project)
    session.commit()
