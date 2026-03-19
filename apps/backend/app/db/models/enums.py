from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SqlEnum


class RoleEnum(str, Enum):
    USER = "user"
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"


class ProjectMembershipRoleEnum(str, Enum):
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    MANAGER = "manager"


class DocumentStatusEnum(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ProviderModeEnum(str, Enum):
    OPENAI_API = "openai_api"


def db_enum(enum_cls: type[Enum], *, name: str | None = None) -> SqlEnum:
    return SqlEnum(
        enum_cls,
        name=name or enum_cls.__name__.lower(),
        values_callable=lambda enum_values: [item.value for item in enum_values],
    )
