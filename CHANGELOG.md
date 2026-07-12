# JCAP Construction Suite

## 1.0.0-dev.1

### Added
- Project architecture
- PostgreSQL database connection
- Authentication system
- Login screen
- Dashboard shell
- Git project structure
- Development standards

# v0.9.0-alpha

## Added

### Core Framework
- PermissionService
- NotificationService
- ActivityLogger
- DocumentLifecycle

### Material Request Module
- Material Request creation
- Edit Material Request
- Record Collaboration Banner
- Record Locking
- Automatic Unlock
- Force Unlock
- Archive Material Request
- Restore Material Request
- Attachment Management
- Activity Timeline

### UI
- Reusable Details Header
- Summary Cards
- Modular Information Sections

### Architecture
- Framework v1 stabilization
- Centralized services
- Reusable components

### Administration and Organization Backend

- Added standardized repository data-access architecture
- Added UserRepository
- Added RoleRepository
- Added DepartmentRepository
- Added JobTitleRepository
- Added PermissionRepository
- Added OrganizationService
- Added employee number generation
- Added centralized user account creation
- Added bcrypt password handling for new accounts
- Added user account update support
- Added user enable and disable support
- Added self-disable protection
- Added centralized user management permission enforcement
- Added administration activity logging
- Added legacy role compatibility during permission migration
- Verified new user accounts with existing authentication system
### Added
- Added JCAP Construction Suite RBAC v1 permission registry.
- Added approved default permission matrix for 9 system roles.
- Added database-driven PermissionService.
- Added fully hydrated RBAC authentication session data.
- Added role-focused Roles & Permissions Administration UI.
- Added protected System Administrator permission rules.
- Added detailed role permission change audit logging.
- Added RBAC-controlled Material Request creation UI and navigation guards.

### Fixed
- Fixed authenticated user sessions missing role_id and organization role data.
- Fixed live RBAC permission changes not reflecting in Material Request UI.