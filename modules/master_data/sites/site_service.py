from __future__ import annotations

from typing import Any

from core.database.transaction_manager import TransactionManager
from core.logging.activity_logger import ActivityLogger
from core.security.permissions import PermissionService
from modules.master_data.sites.site_repository import SiteRepository


class SiteService:
    """
    Business service for Site Master records.

    Responsibilities:
    - Enforce Site Master permissions.
    - Validate and normalize user input.
    - Validate the selected Project Master record.
    - Generate sequential site codes.
    - Prevent duplicate active site names per project.
    - Coordinate database transactions.
    - Write activity logs in the same transaction.
    """

    SITE_CODE_PREFIX = "SIT"
    SITE_CODE_DIGITS = 6

    # Transaction-scoped PostgreSQL advisory lock used only while
    # generating the next Site Master code.
    SITE_CODE_LOCK_KEY = 741003

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    @classmethod
    def get_by_id(
        cls,
        site_id: Any,
        *,
        current_user: dict | None,
    ) -> dict | None:
        cls._require_permission(
            current_user,
            PermissionService.can_view_sites,
            "You do not have permission to view Site Master records.",
        )

        if not site_id:
            raise ValueError("A site ID is required.")

        return SiteRepository.get_by_id(site_id)

    @classmethod
    def get_by_code(
        cls,
        site_code: str,
        *,
        current_user: dict | None,
    ) -> dict | None:
        cls._require_permission(
            current_user,
            PermissionService.can_view_sites,
            "You do not have permission to view Site Master records.",
        )

        clean_code = cls._clean_required_text(
            site_code,
            "Site code",
            maximum_length=50,
        )

        return SiteRepository.get_by_code(clean_code)

    @classmethod
    def get_all(
        cls,
        status_filter: str = "Active",
        *,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_sites,
            "You do not have permission to view Site Master records.",
        )

        return SiteRepository.get_all(
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
    def get_by_project(
        cls,
        project_id: Any,
        status_filter: str = "Active",
        *,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_sites,
            "You do not have permission to view Site Master records.",
        )

        if not project_id:
            raise ValueError("A project ID is required.")

        return SiteRepository.get_by_project(
            project_id,
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
        project_id: Any | None = None,
        client_id: Any | None = None,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_sites,
            "You do not have permission to view Site Master records.",
        )

        return SiteRepository.search(
            search_text=str(search_text or "").strip(),
            status_filter=cls._normalize_status_filter(
                status_filter
            ),
            project_id=project_id,
            client_id=client_id,
        )

    # ============================================================
    # CREATE
    # ============================================================

    @classmethod
    def create_site(
        cls,
        data: dict,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_create_sites,
            "You do not have permission to create Site Master records.",
        )

        user_id = cls._get_user_id(current_user)
        clean_data = cls._validate_and_clean(data)

        with TransactionManager() as cursor:
            cls._require_active_project(
                clean_data["project_id"],
                cursor=cursor,
            )

            if SiteRepository.active_site_name_exists(
                project_id=clean_data["project_id"],
                site_name=clean_data["site_name"],
                cursor=cursor,
            ):
                raise ValueError(
                    "An active site with the same name already "
                    "exists for the selected project."
                )

            # Prevent concurrent users from generating the same code.
            cursor.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (cls.SITE_CODE_LOCK_KEY,),
            )

            site_code = cls._generate_next_code(
                cursor=cursor,
            )

            site = SiteRepository.create(
                site_code=site_code,
                site_name=clean_data["site_name"],
                project_id=clean_data["project_id"],
                remarks=clean_data["remarks"],
                created_by=user_id,
                cursor=cursor,
            )

            if not site:
                raise RuntimeError(
                    "The Site Master record was not created."
                )

            ActivityLogger.log_create(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=site["id"],
                details=(
                    f"Created Site Master record "
                    f"{site['site_code']} - "
                    f"{site['site_name']} "
                    f"for project {site['project_name']}."
                ),
            )

            return site

    # ============================================================
    # UPDATE
    # ============================================================

    @classmethod
    def update_site(
        cls,
        site_id: Any,
        data: dict,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_edit_sites,
            "You do not have permission to edit Site Master records.",
        )

        if not site_id:
            raise ValueError("A site ID is required.")

        user_id = cls._get_user_id(current_user)
        clean_data = cls._validate_and_clean(data)

        with TransactionManager() as cursor:
            existing = SiteRepository.get_by_id(
                site_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Site Master record was not found."
                )

            if not existing["is_active"]:
                raise ValueError(
                    "Inactive Site Master records cannot be edited. "
                    "Restore the site before editing it."
                )

            cls._require_active_project(
                clean_data["project_id"],
                cursor=cursor,
            )

            if SiteRepository.active_site_name_exists(
                project_id=clean_data["project_id"],
                site_name=clean_data["site_name"],
                exclude_site_id=site_id,
                cursor=cursor,
            ):
                raise ValueError(
                    "An active site with the same name already "
                    "exists for the selected project."
                )

            updated = SiteRepository.update(
                site_id,
                site_name=clean_data["site_name"],
                project_id=clean_data["project_id"],
                remarks=clean_data["remarks"],
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Site Master record was not updated."
                )

            ActivityLogger.log_update(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Updated Site Master record "
                    f"{updated['site_code']} - "
                    f"{updated['site_name']} "
                    f"for project {updated['project_name']}."
                ),
            )

            return updated

    # ============================================================
    # ARCHIVE / RESTORE
    # ============================================================

    @classmethod
    def deactivate_site(
        cls,
        site_id: Any,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_archive_sites,
            "You do not have permission to archive Site Master records.",
        )

        if not site_id:
            raise ValueError("A site ID is required.")

        user_id = cls._get_user_id(current_user)

        with TransactionManager() as cursor:
            existing = SiteRepository.get_by_id(
                site_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Site Master record was not found."
                )

            if not existing["is_active"]:
                raise ValueError(
                    "The selected site is already inactive."
                )

            updated = SiteRepository.deactivate(
                site_id,
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Site Master record was not archived."
                )

            ActivityLogger.log_archive(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Archived Site Master record "
                    f"{updated['site_code']} - "
                    f"{updated['site_name']}."
                ),
            )

            return updated

    @classmethod
    def restore_site(
        cls,
        site_id: Any,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_restore_sites,
            "You do not have permission to restore Site Master records.",
        )

        if not site_id:
            raise ValueError("A site ID is required.")

        user_id = cls._get_user_id(current_user)

        with TransactionManager() as cursor:
            existing = SiteRepository.get_by_id(
                site_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Site Master record was not found."
                )

            if existing["is_active"]:
                raise ValueError(
                    "The selected site is already active."
                )

            cls._require_active_project(
                existing["project_id"],
                cursor=cursor,
                restore_message=True,
            )

            if SiteRepository.active_site_name_exists(
                project_id=existing["project_id"],
                site_name=existing["site_name"],
                exclude_site_id=site_id,
                cursor=cursor,
            ):
                raise ValueError(
                    "This site cannot be restored because another "
                    "active site under the same project already uses "
                    "the same name."
                )

            updated = SiteRepository.restore(
                site_id,
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Site Master record was not restored."
                )

            ActivityLogger.log_restore(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Restored Site Master record "
                    f"{updated['site_code']} - "
                    f"{updated['site_name']}."
                ),
            )

            return updated

    # Compatibility aliases for UI naming.
    archive_site = deactivate_site
    activate_site = restore_site

    # ============================================================
    # CODE GENERATION
    # ============================================================

    @classmethod
    def _generate_next_code(
        cls,
        *,
        cursor,
    ) -> str:
        highest_number = SiteRepository.get_highest_code_number(
            prefix=cls.SITE_CODE_PREFIX,
            cursor=cursor,
        )

        next_number = highest_number + 1

        while True:
            site_code = (
                f"{cls.SITE_CODE_PREFIX}-"
                f"{next_number:0{cls.SITE_CODE_DIGITS}d}"
            )

            if not SiteRepository.site_code_exists(
                site_code,
                cursor=cursor,
            ):
                return site_code

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
                "Site data must be supplied as a dictionary."
            )

        site_name = cls._clean_required_text(
            data.get("site_name"),
            "Site name",
            maximum_length=255,
        )

        project_id = data.get("project_id")

        if not project_id:
            raise ValueError("Project is required.")

        remarks = cls._clean_optional_text(
            data.get("remarks"),
        )

        return {
            "site_name": site_name,
            "project_id": project_id,
            "remarks": remarks,
        }

    @classmethod
    def _require_active_project(
        cls,
        project_id: Any,
        *,
        cursor,
        restore_message: bool = False,
    ) -> None:
        if SiteRepository.project_exists(
            project_id,
            active_only=True,
            cursor=cursor,
        ):
            return

        if SiteRepository.project_exists(
            project_id,
            active_only=False,
            cursor=cursor,
        ):
            if restore_message:
                raise ValueError(
                    "This site cannot be restored because its "
                    "Project Master record is inactive. Restore the "
                    "project first."
                )

            raise ValueError(
                "The selected Project Master record is inactive. "
                "Select an active project."
            )

        raise ValueError(
            "The selected Project Master record was not found."
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