# RBAC

## Roles

### User

- Login
- Ask questions over processed documents
- View chat sessions/messages (when enabled)
- Read-only project-scoped documents in projects where the user is a member

### Contributor

Includes `User` permissions plus:

- Upload documents within assigned projects
- Reprocess documents within assigned projects
- Delete/manage project documents within assigned projects
- View ingestion job status/logs

### Project Manager

Project membership role `manager` acts as the project owner in the PoC:

- Update project name/description
- Add existing system users to the project
- Change project membership roles
- Enable/disable membership
- Remove members
- Cannot create global users or change system-wide settings

### Admin

Includes `Contributor` permissions plus:

- User management (create/update/activate/deactivate/reset password)
- Create projects and assign the initial project owner
- Override access across all projects
- Manage provider switching and model category mappings
- Manage OpenAI API key (set/test/rotate/remove)
- Configure RAG/prompt/eval/telemetry settings
- Run evaluations and compare runs

## Enforcement

RBAC is enforced in two places:

- Backend route dependencies (`require_roles`) are authoritative
- Frontend route guards improve UX but do not replace backend checks

## Auth Model

- Access token: JWT (short-lived), stored in frontend memory only
- Refresh token: opaque token in HttpOnly cookie
- Deactivated users cannot authenticate or refresh
- Project membership is additive to the global user role; users must exist globally before a project manager can assign them to a project

## Audit Expectations

Admin actions should generate audit logs, especially:

- user creation/role changes/password reset
- provider switch and model mapping changes
- secret management operations
- document deletion
- eval run execution
