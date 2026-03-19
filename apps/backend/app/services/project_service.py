from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session

from app.db.models import Project, ProjectMembership, User
from app.db.models.enums import ProjectMembershipRoleEnum
from app.services.project_access_service import ProjectAccessService


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "project"


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.access = ProjectAccessService(db)

    def _ensure_unique_slug(self, slug: str, *, exclude_project_id: str | None = None) -> None:
        stmt = select(Project).where(Project.slug == slug, Project.deleted_at.is_(None))
        if exclude_project_id:
            stmt = stmt.where(Project.id != exclude_project_id)
        if self.db.scalar(stmt.limit(1)):
            raise HTTPException(status_code=409, detail="Project slug already exists")

    def list_projects_for_user(self, *, user: User) -> tuple[list[tuple[Project, ProjectMembership | None]], int]:
        rows = self.access.list_accessible_projects(user=user, include_inactive=True)
        return rows, len(rows)

    def get_project_for_user(self, *, project_id: str, user: User) -> tuple[Project, ProjectMembership | None]:
        return self.access.require_project_role(project_id=project_id, user=user, minimum_role="viewer", allow_inactive_project=True)

    def create_project(
        self,
        *,
        actor: User,
        name: str,
        owner_user_id: str,
        slug: str | None,
        description: str | None,
    ) -> Project:
        if not self.access.is_admin(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create projects")
        owner = self.db.get(User, owner_user_id)
        if owner is None:
            raise HTTPException(status_code=404, detail="Owner user not found")
        if not owner.is_active:
            raise HTTPException(status_code=400, detail="Owner user must be active")
        project_slug = _slugify(slug or name)
        self._ensure_unique_slug(project_slug)
        project = Project(
            name=name.strip(),
            slug=project_slug,
            description=description,
            is_active=True,
            created_by_user_id=actor.id,
        )
        self.db.add(project)
        self.db.flush()

        self.db.add(
            ProjectMembership(
                project_id=project.id,
                user_id=owner.id,
                role=ProjectMembershipRoleEnum.MANAGER.value,
                is_active=True,
                created_by_user_id=actor.id,
            )
        )
        self.db.flush()
        return project

    def update_project(
        self,
        *,
        project_id: str,
        actor: User,
        name: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        archive: bool | None = None,
    ) -> Project:
        project, _membership = self.access.require_project_role(project_id=project_id, user=actor, minimum_role="manager", allow_inactive_project=True)
        if name is not None:
            project.name = name.strip()
        if slug is not None:
            slug_norm = _slugify(slug)
            self._ensure_unique_slug(slug_norm, exclude_project_id=project.id)
            project.slug = slug_norm
        if description is not None:
            project.description = description
        if is_active is not None:
            project.is_active = bool(is_active)
        if archive is True:
            project.archived_at = project.archived_at or project.updated_at
            project.is_active = False
        elif archive is False:
            project.archived_at = None
            project.is_active = True
        self.db.flush()
        return project

    def delete_project(self, *, project_id: str, actor: User) -> Project:
        if not self.access.is_admin(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete projects")
        project = self.access.get_project(project_id, allow_inactive=True)
        project.deleted_at = project.deleted_at or project.updated_at
        project.is_active = False
        self.db.flush()
        return project

    def list_members(self, *, project_id: str, actor: User) -> tuple[list[tuple[ProjectMembership, User]], int]:
        _project, _membership = self.access.require_project_role(project_id=project_id, user=actor, minimum_role="viewer", allow_inactive_project=True)
        rows = self.db.execute(
            select(ProjectMembership, User)
            .join(User, User.id == ProjectMembership.user_id)
            .where(ProjectMembership.project_id == project_id)
            .order_by(
                case(
                    (ProjectMembership.role == ProjectMembershipRoleEnum.MANAGER.value, 0),
                    (ProjectMembership.role == ProjectMembershipRoleEnum.CONTRIBUTOR.value, 1),
                    else_=2,
                ),
                User.display_name.asc(),
                User.username.asc(),
            )
        ).all()
        pairs = [(row[0], row[1]) for row in rows]
        return pairs, len(pairs)

    def list_assignable_users(self, *, project_id: str, actor: User, search: str | None = None) -> tuple[list[User], int]:
        _project, _membership = self.access.require_project_role(
            project_id=project_id,
            user=actor,
            minimum_role="manager",
            allow_inactive_project=True,
        )
        existing_member_ids = list(
            self.db.scalars(select(ProjectMembership.user_id).where(ProjectMembership.project_id == project_id)).all()
        )
        stmt = select(User).where(User.is_active.is_(True))
        if existing_member_ids:
            stmt = stmt.where(User.id.notin_(existing_member_ids))
        if search:
            pattern = f"%{search.strip()}%"
            if pattern != "%%":
                stmt = stmt.where(
                    or_(
                        User.username.ilike(pattern),
                        User.email.ilike(pattern),
                        User.display_name.ilike(pattern),
                    )
                )
        items = list(self.db.scalars(stmt.order_by(User.display_name.asc(), User.username.asc())).all())
        return items, len(items)

    def _count_active_managers(self, *, project_id: str) -> int:
        rows = self.db.scalars(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.is_active.is_(True),
                ProjectMembership.role == ProjectMembershipRoleEnum.MANAGER.value,
            )
        ).all()
        return len(list(rows))

    def _would_remove_last_active_manager(
        self,
        *,
        membership: ProjectMembership,
        next_role: str | None = None,
        next_is_active: bool | None = None,
    ) -> bool:
        current_role = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
        current_is_active = bool(membership.is_active)
        resulting_role = next_role or current_role
        resulting_is_active = current_is_active if next_is_active is None else bool(next_is_active)
        currently_active_manager = current_role == ProjectMembershipRoleEnum.MANAGER.value and current_is_active
        remains_active_manager = resulting_role == ProjectMembershipRoleEnum.MANAGER.value and resulting_is_active
        if not currently_active_manager or remains_active_manager:
            return False
        return self._count_active_managers(project_id=membership.project_id) <= 1

    def add_member(self, *, project_id: str, actor: User, user_id: str, role: str, is_active: bool = True) -> ProjectMembership:
        _project, _membership = self.access.require_project_role(project_id=project_id, user=actor, minimum_role="manager", allow_inactive_project=True)
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive users cannot be assigned to a project")
        existing = self.db.scalar(
            select(ProjectMembership).where(ProjectMembership.project_id == project_id, ProjectMembership.user_id == user_id).limit(1)
        )
        if existing:
            raise HTTPException(status_code=409, detail="User is already a member of this project")
        membership = ProjectMembership(
            project_id=project_id,
            user_id=user_id,
            role=ProjectMembershipRoleEnum(role).value,
            is_active=is_active,
            created_by_user_id=actor.id,
        )
        self.db.add(membership)
        self.db.flush()
        return membership

    def update_member(self, *, project_id: str, target_user_id: str, actor: User, role: str | None, is_active: bool | None) -> ProjectMembership:
        _project, _membership = self.access.require_project_role(project_id=project_id, user=actor, minimum_role="manager", allow_inactive_project=True)
        membership = self.db.scalar(
            select(ProjectMembership)
            .where(ProjectMembership.project_id == project_id, ProjectMembership.user_id == target_user_id)
            .limit(1)
        )
        if membership is None:
            raise HTTPException(status_code=404, detail="Project membership not found")
        if self._would_remove_last_active_manager(membership=membership, next_role=role, next_is_active=is_active):
            raise HTTPException(status_code=400, detail="Project must retain at least one active manager")
        if role is not None:
            membership.role = ProjectMembershipRoleEnum(role).value
        if is_active is not None:
            membership.is_active = bool(is_active)
        self.db.flush()
        return membership

    def remove_member(self, *, project_id: str, target_user_id: str, actor: User) -> ProjectMembership:
        _project, _membership = self.access.require_project_role(project_id=project_id, user=actor, minimum_role="manager", allow_inactive_project=True)
        membership = self.db.scalar(
            select(ProjectMembership)
            .where(ProjectMembership.project_id == project_id, ProjectMembership.user_id == target_user_id)
            .limit(1)
        )
        if membership is None:
            raise HTTPException(status_code=404, detail="Project membership not found")
        if self._would_remove_last_active_manager(membership=membership):
            raise HTTPException(status_code=400, detail="Project must retain at least one active manager")
        self.db.delete(membership)
        self.db.flush()
        return membership

    def bootstrap_project_for_admin(self, *, actor: User, name: str = "Default Project") -> Project:
        existing = self.db.scalar(select(Project).where(Project.deleted_at.is_(None)).limit(1))
        if existing:
            return existing
        return self.create_project(
            actor=actor,
            name=name,
            owner_user_id=actor.id,
            slug=None,
            description="Bootstrap project",
        )
