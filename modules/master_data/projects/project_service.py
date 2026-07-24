from __future__ import annotations

from typing import Any

from core.database.transaction_manager import TransactionManager
from core.logging.activity_logger import ActivityLogger
from core.security.permissions import PermissionService
from modules.master_data.projects.project_repository import ProjectRepository


class ProjectService:
    """
    Business service for Project Master records.

    Responsibilities:
    - Enforce Project Master permissions.
    - Validate and normalize user input.
    - Validate the selected Client Master record.
    - Generate sequential project codes.
    - Prevent duplicate active project names per client.
    - Coordinate database transactions.
    - Write activity logs in the same transaction.
    """

    PROJECT_CODE_PREFIX = "PRJ"
    PROJECT_CODE_DIGITS = 6

    # Transaction-scoped PostgreSQL advisory lock used only while
    # generating the next Project Master code.
    PROJECT_CODE_LOCK_KEY = 741002

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    @classmethod
    def get_by_id(
        cls,
        project_id: Any,
        *,
        current_user: dict | None,
    ) -> dict | None:
        cls._require_permission(
            current_user,
            PermissionService.can_view_projects,
            "You do not have permission to view Project Master records.",
        )

        if not project_id:
            raise ValueError("A project ID is required.")

        return ProjectRepository.get_by_id(project_id)

    @classmethod
    def get_by_code(
        cls,
        project_code: str,
        *,
        current_user: dict | None,
    ) -> dict | None:
        cls._require_permission(
            current_user,
            PermissionService.can_view_projects,
            "You do not have permission to view Project Master records.",
        )

        clean_code = cls._clean_required_text(
            project_code,
            "Project code",
            maximum_length=50,
        )

        return ProjectRepository.get_by_code(clean_code)

    @classmethod
    def get_all(
        cls,
        status_filter: str = "Active",
        *,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_projects,
            "You do not have permission to view Project Master records.",
        )

        return ProjectRepository.get_all(
            status_filter=cls._normalize_status_filter(
                status_filter
            ),
        )

    @classmethod
    def get_active(
        cls,
        *,
        current_user: dict | None,
    ) -> list[dict]:
        return cls.get_all(
            status_filter="Active",
            current_user=current_user,
        )

    @classmethod
    def get_by_client(
        cls,
        client_id: Any,
        status_filter: str = "Active",
        *,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_projects,
            "You do not have permission to view Project Master records.",
        )

        if not client_id:
            raise ValueError("A client ID is required.")

        return ProjectRepository.get_by_client(
            client_id,
            status_filter=cls._normalize_status_filter(
                status_filter
            ),
        )

    @classmethod
    def search(
        cls,
        search_text: str = "",
        status_filter: str = "Active",
        *,
        client_id: Any | None = None,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_projects,
            "You do not have permission to view Project Master records.",
        )

        return ProjectRepository.search(
            search_text=str(search_text or "").strip(),
            status_filter=cls._normalize_status_filter(
                status_filter
            ),
            client_id=client_id,
        )

    # ============================================================
    # CREATE
    # ============================================================

    @classmethod
    def create_project(
        cls,
        data: dict,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_create_projects,
            "You do not have permission to create Project Master records.",
        )

        user_id = cls._get_user_id(current_user)
        clean_data = cls._validate_and_clean(data)

        with TransactionManager() as cursor:
            cls._require_active_client(
                clean_data["client_id"],
                cursor=cursor,
            )

            if ProjectRepository.active_project_name_exists(
                client_id=clean_data["client_id"],
                project_name=clean_data["project_name"],
                cursor=cursor,
            ):
                raise ValueError(
                    "An active project with the same name already "
                    "exists for the selected client."
                )

            # Prevent concurrent users from generating the same code.
            cursor.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (cls.PROJECT_CODE_LOCK_KEY,),
            )

            project_code = cls._generate_next_code(
                cursor=cursor,
            )

            project = ProjectRepository.create(
                project_code=project_code,
                project_name=clean_data["project_name"],
                client_id=clean_data["client_id"],
                remarks=clean_data["remarks"],
                created_by=user_id,
                cursor=cursor,
            )

            if not project:
                raise RuntimeError(
                    "The Project Master record was not created."
                )

            ActivityLogger.log_create(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=project["id"],
                details=(
                    f"Created Project Master record "
                    f"{project['project_code']} - "
                    f"{project['project_name']} "
                    f"for client {project['client_name']}."
                ),
            )

            return project

    # ============================================================
    # UPDATE
    # ============================================================

    @classmethod
    def update_project(
        cls,
        project_id: Any,
        data: dict,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_edit_projects,
            "You do not have permission to edit Project Master records.",
        )

        if not project_id:
            raise ValueError("A project ID is required.")

        user_id = cls._get_user_id(current_user)
        clean_data = cls._validate_and_clean(data)

        with TransactionManager() as cursor:
            existing = ProjectRepository.get_by_id(
                project_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Project Master record was not found."
                )

            if not existing["is_active"]:
                raise ValueError(
                    "Inactive Project Master records cannot be edited. "
                    "Restore the project before editing it."
                )

            cls._require_active_client(
                clean_data["client_id"],
                cursor=cursor,
            )

            if ProjectRepository.active_project_name_exists(
                client_id=clean_data["client_id"],
                project_name=clean_data["project_name"],
                exclude_project_id=project_id,
                cursor=cursor,
            ):
                raise ValueError(
                    "An active project with the same name already "
                    "exists for the selected client."
                )

            updated = ProjectRepository.update(
                project_id,
                project_name=clean_data["project_name"],
                client_id=clean_data["client_id"],
                remarks=clean_data["remarks"],
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Project Master record was not updated."
                )

            ActivityLogger.log_update(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Updated Project Master record "
                    f"{updated['project_code']} - "
                    f"{updated['project_name']} "
                    f"for client {updated['client_name']}."
                ),
            )

            return updated

    # ============================================================
    # ARCHIVE / RESTORE
    # ============================================================

    @classmethod
    def deactivate_project(
        cls,
        project_id: Any,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_archive_projects,
            "You do not have permission to archive Project Master records.",
        )

        if not project_id:
            raise ValueError("A project ID is required.")

        user_id = cls._get_user_id(current_user)

        with TransactionManager() as cursor:
            existing = ProjectRepository.get_by_id(
                project_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Project Master record was not found."
                )

            if not existing["is_active"]:
                raise ValueError(
                    "The selected project is already inactive."
                )

            updated = ProjectRepository.deactivate(
                project_id,
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Project Master record was not archived."
                )

            ActivityLogger.log_archive(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Archived Project Master record "
                    f"{updated['project_code']} - "
                    f"{updated['project_name']}."
                ),
            )

            return updated

    @classmethod
    def restore_project(
        cls,
        project_id: Any,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_restore_projects,
            "You do not have permission to restore Project Master records.",
        )

        if not project_id:
            raise ValueError("A project ID is required.")

        user_id = cls._get_user_id(current_user)

        with TransactionManager() as cursor:
            existing = ProjectRepository.get_by_id(
                project_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Project Master record was not found."
                )

            if existing["is_active"]:
                raise ValueError(
                    "The selected project is already active."
                )

            cls._require_active_client(
                existing["client_id"],
                cursor=cursor,
                restore_message=True,
            )

            if ProjectRepository.active_project_name_exists(
                client_id=existing["client_id"],
                project_name=existing["project_name"],
                exclude_project_id=project_id,
                cursor=cursor,
            ):
                raise ValueError(
                    "This project cannot be restored because another "
                    "active project under the same client already uses "
                    "the same name."
                )

            updated = ProjectRepository.restore(
                project_id,
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Project Master record was not restored."
                )

            ActivityLogger.log_restore(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Restored Project Master record "
                    f"{updated['project_code']} - "
                    f"{updated['project_name']}."
                ),
            )

            return updated

    # Compatibility aliases for UI naming.
    archive_project = deactivate_project
    activate_project = restore_project

    # ============================================================
    # CODE GENERATION
    # ============================================================

    @classmethod
    def _generate_next_code(
        cls,
        *,
        cursor,
    ) -> str:
        highest_number = ProjectRepository.get_highest_code_number(
            prefix=cls.PROJECT_CODE_PREFIX,
            cursor=cursor,
        )

        next_number = highest_number + 1

        while True:
            project_code = (
                f"{cls.PROJECT_CODE_PREFIX}-"
                f"{next_number:0{cls.PROJECT_CODE_DIGITS}d}"
            )

            if not ProjectRepository.project_code_exists(
                project_code,
                cursor=cursor,
            ):
                return project_code

            next_number += 1

    # ============================================================
    # VALIDATION
    # ============================================================

    @classmethod
    def _validate_and_clean(
        cls,
        data: dict | None,
    ) -> dict:
        if not isinstance(data, dict):
            raise ValueError(
                "Project data must be supplied as a dictionary."
            )

        project_name = cls._clean_required_text(
            data.get("project_name"),
            "Project name",
            maximum_length=255,
        )

        client_id = data.get("client_id")

        if not client_id:
            raise ValueError("Client is required.")

        remarks = cls._clean_optional_text(
            data.get("remarks"),
        )

        return {
            "project_name": project_name,
            "client_id": client_id,
            "remarks": remarks,
        }

    @classmethod
    def _require_active_client(
        cls,
        client_id: Any,
        *,
        cursor,
        restore_message: bool = False,
    ) -> None:
        if ProjectRepository.client_exists(
            client_id,
            active_only=True,
            cursor=cursor,
        ):
            return

        if ProjectRepository.client_exists(
            client_id,
            active_only=False,
            cursor=cursor,
        ):
            if restore_message:
                raise ValueError(
                    "This project cannot be restored because its "
                    "Client Master record is inactive. Restore the "
                    "client first."
                )

            raise ValueError(
                "The selected Client Master record is inactive. "
                "Select an active client."
            )

        raise ValueError(
            "The selected Client Master record was not found."
        )

    @staticmethod
    def _clean_required_text(
        value: Any,
        field_name: str,
        *,
        maximum_length: int | None = None,
    ) -> str:
        clean_value = str(value or "").strip()

        if not clean_value:
            raise ValueError(f"{field_name} is required.")

        if maximum_length and len(clean_value) > maximum_length:
            raise ValueError(
                f"{field_name} must not exceed "
                f"{maximum_length} characters."
            )

        return clean_value

    @staticmethod
    def _clean_optional_text(
        value: Any,
        *,
        maximum_length: int | None = None,
    ) -> str | None:
        clean_value = str(value or "").strip()

        if not clean_value:
            return None

        if maximum_length and len(clean_value) > maximum_length:
            raise ValueError(
                f"Value must not exceed {maximum_length} characters."
            )

        return clean_value

    @staticmethod
    def _normalize_status_filter(
        status_filter: str,
    ) -> str:
        normalized = str(
            status_filter or "Active"
        ).strip().lower()

        if normalized == "all":
            return "All"

        if normalized == "inactive":
            return "Inactive"

        return "Active"

    # ============================================================
    # SECURITY HELPERS
    # ============================================================

    @staticmethod
    def _get_user_id(
        current_user: dict | None,
    ) -> Any:
        if not current_user:
            raise PermissionError(
                "An authenticated user is required."
            )

        user_id = (
            current_user.get("id")
            or current_user.get("user_id")
        )

        if not user_id:
            raise PermissionError(
                "The authenticated user does not contain a user ID."
            )

        return user_id

    @staticmethod
    def _require_permission(
        current_user: dict | None,
        permission_check,
        error_message: str,
    ) -> None:
        if not current_user:
            raise PermissionError(
                "An authenticated user is required."
            )

        if not permission_check(current_user):
            raise PermissionError(error_message)