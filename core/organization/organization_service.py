from core.database.connection import get_connection

from core.database.repositories.department_repository import (
    DepartmentRepository,
)
from core.database.repositories.job_title_repository import (
    JobTitleRepository,
)
from core.database.repositories.permission_repository import (
    PermissionRepository,
)
from core.database.repositories.role_repository import (
    RoleRepository,
)
from core.database.repositories.user_repository import (
    UserRepository,
)

from core.logging.activity_logger import ActivityLogger
from core.security.password_service import hash_password
from core.security.permissions import PermissionService


class OrganizationService:
    """
    Central business service for organization and administration data.

    Views and other application services should use OrganizationService
    instead of accessing organization repositories directly.

    OrganizationService owns organization business rules.

    Repositories own PostgreSQL data-access logic.
    """

    EMPLOYEE_NUMBER_PREFIX = "JCAP"
    EMPLOYEE_NUMBER_DIGITS = 4

    # ============================================================
    # USERS
    # ============================================================

    @classmethod
    def get_users(cls) -> list[dict]:
        return UserRepository.get_all()

    @classmethod
    def get_active_users(cls) -> list[dict]:
        return UserRepository.get_active()

    @classmethod
    def get_user(cls, user_id):
        if not user_id:
            return None

        return UserRepository.get_by_id(user_id)

    @classmethod
    def get_user_by_username(cls, username: str):
        username = cls._clean_text(username)

        if not username:
            return None

        return UserRepository.get_by_username(username)

    @classmethod
    def get_user_by_employee_number(
        cls,
        employee_number: str,
    ):
        employee_number = cls._clean_text(
            employee_number
        )

        if not employee_number:
            return None

        return UserRepository.get_by_employee_number(
            employee_number
        )

    # ============================================================
    # USER ACCOUNT MANAGEMENT
    # ============================================================

    @classmethod
    def create_user(
        cls,
        data: dict,
        current_user: dict,
    ) -> str:
        cls._require_user_management_permission(
            current_user
        )

        username = cls._clean_text(
            data.get("username")
        ).lower()

        password = cls._clean_text(
            data.get("password")
        )

        full_name = cls._clean_text(
            data.get("full_name")
        )

        email = cls._clean_text(
            data.get("email")
        )

        phone = cls._clean_text(
            data.get("phone")
        )

        role_id = data.get("role_id")
        department_id = data.get("department_id")
        job_title_id = data.get("job_title_id")

        if not username:
            raise ValueError(
                "Username is required."
            )

        if not password:
            raise ValueError(
                "Password is required."
            )

        if len(password) < 8:
            raise ValueError(
                "Password must contain at least 8 characters."
            )

        if not full_name:
            raise ValueError(
                "Full name is required."
            )

        if not role_id:
            raise ValueError(
                "Role is required."
            )

        if not department_id:
            raise ValueError(
                "Department is required."
            )

        if not job_title_id:
            raise ValueError(
                "Job title is required."
            )

        conn = get_connection()
        cur = conn.cursor()

        try:
            if UserRepository.username_exists(
                username,
                cursor=cur,
            ):
                raise ValueError(
                    "Username already exists."
                )

            role = RoleRepository.get_by_id(
                role_id,
                cursor=cur,
            )

            if not role or not role["is_active"]:
                raise ValueError(
                    "Selected role is invalid or inactive."
                )

            department = DepartmentRepository.get_by_id(
                department_id,
                cursor=cur,
            )

            if (
                not department
                or not department["is_active"]
            ):
                raise ValueError(
                    "Selected department is invalid or inactive."
                )

            job_title = JobTitleRepository.get_by_id(
                job_title_id,
                cursor=cur,
            )

            if (
                not job_title
                or not job_title["is_active"]
            ):
                raise ValueError(
                    "Selected job title is invalid or inactive."
                )

            if (
                job_title["department_id"]
                != str(department_id)
            ):
                raise ValueError(
                    "Selected job title does not belong "
                    "to the selected department."
                )

            employee_number = (
                cls._generate_employee_number_in_transaction(
                    cursor=cur
                )
            )

            password_hash = hash_password(
                password
            )

            legacy_role = cls._get_legacy_role_name(
                role["role_name"]
            )

            user_id = UserRepository.create(
                {
                    "employee_number": employee_number,
                    "username": username,
                    "password_hash": password_hash,
                    "full_name": full_name,
                    "legacy_role": legacy_role,
                    "role_id": role_id,
                    "department_id": department_id,
                    "job_title_id": job_title_id,
                    "email": email or None,
                    "phone": phone or None,
                    "is_active": True,
                    "created_by": current_user["id"],
                    "updated_by": current_user["id"],
                },
                cursor=cur,
            )

            ActivityLogger.log_create(
                cur,
                user_id=current_user["id"],
                module=ActivityLogger.MODULE_ADMINISTRATION,
                record_id=user_id,
                details=(
                    f"Created user account "
                    f"{employee_number} - {full_name}"
                ),
            )

            conn.commit()

            return user_id

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    @classmethod
    def update_user(
        cls,
        user_id,
        data: dict,
        current_user: dict,
    ) -> bool:
        cls._require_user_management_permission(
            current_user
        )

        if not user_id:
            raise ValueError(
                "User ID is required."
            )

        conn = get_connection()
        cur = conn.cursor()

        try:
            existing_user = UserRepository.get_by_id(
                user_id,
                cursor=cur,
            )

            if not existing_user:
                raise ValueError(
                    "User account was not found."
                )

            update_data = {}

            if "username" in data:
                username = cls._clean_text(
                    data.get("username")
                ).lower()

                if not username:
                    raise ValueError(
                        "Username is required."
                    )

                if UserRepository.username_exists(
                    username,
                    exclude_user_id=user_id,
                    cursor=cur,
                ):
                    raise ValueError(
                        "Username already exists."
                    )

                update_data["username"] = username

            if "full_name" in data:
                full_name = cls._clean_text(
                    data.get("full_name")
                )

                if not full_name:
                    raise ValueError(
                        "Full name is required."
                    )

                update_data["full_name"] = full_name

            if "email" in data:
                email = cls._clean_text(
                    data.get("email")
                )

                update_data["email"] = (
                    email or None
                )

            if "phone" in data:
                phone = cls._clean_text(
                    data.get("phone")
                )

                update_data["phone"] = (
                    phone or None
                )

            final_role_id = data.get(
                "role_id",
                existing_user["role_id"],
            )

            final_department_id = data.get(
                "department_id",
                existing_user["department_id"],
            )

            final_job_title_id = data.get(
                "job_title_id",
                existing_user["job_title_id"],
            )

            role = None
            department = None
            job_title = None

            if final_role_id:
                role = RoleRepository.get_by_id(
                    final_role_id,
                    cursor=cur,
                )

                if (
                    not role
                    or not role["is_active"]
                ):
                    raise ValueError(
                        "Selected role is invalid or inactive."
                    )

            if final_department_id:
                department = (
                    DepartmentRepository.get_by_id(
                        final_department_id,
                        cursor=cur,
                    )
                )

                if (
                    not department
                    or not department["is_active"]
                ):
                    raise ValueError(
                        "Selected department is invalid or inactive."
                    )

            if final_job_title_id:
                job_title = (
                    JobTitleRepository.get_by_id(
                        final_job_title_id,
                        cursor=cur,
                    )
                )

                if (
                    not job_title
                    or not job_title["is_active"]
                ):
                    raise ValueError(
                        "Selected job title is invalid or inactive."
                    )

            if (
                job_title
                and department
                and job_title["department_id"]
                != str(final_department_id)
            ):
                raise ValueError(
                    "Selected job title does not belong "
                    "to the selected department."
                )

            if "role_id" in data:
                update_data["role_id"] = (
                    final_role_id
                )

                update_data["role"] = (
                    cls._get_legacy_role_name(
                        role["role_name"]
                    )
                )

            if "department_id" in data:
                update_data["department_id"] = (
                    final_department_id
                )

            if "job_title_id" in data:
                update_data["job_title_id"] = (
                    final_job_title_id
                )

            if "password" in data:
                password = cls._clean_text(
                    data.get("password")
                )

                if not password:
                    raise ValueError(
                        "Password cannot be blank."
                    )

                if len(password) < 8:
                    raise ValueError(
                        "Password must contain at least 8 characters."
                    )

                update_data["password_hash"] = (
                    hash_password(password)
                )

            update_data["updated_by"] = (
                current_user["id"]
            )

            updated = UserRepository.update(
                user_id,
                update_data,
                cursor=cur,
            )

            if not updated:
                raise ValueError(
                    "No user account changes were saved."
                )

            ActivityLogger.log_update(
                cur,
                user_id=current_user["id"],
                module=ActivityLogger.MODULE_ADMINISTRATION,
                record_id=user_id,
                details=(
                    f"Updated user account "
                    f"{existing_user['employee_number']} - "
                    f"{existing_user['full_name']}"
                ),
            )

            conn.commit()

            return True

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    @classmethod
    def enable_user(
        cls,
        user_id,
        current_user: dict,
    ) -> bool:
        cls._require_user_management_permission(
            current_user
        )

        return cls._set_user_active_state(
            user_id,
            True,
            current_user,
        )

    @classmethod
    def disable_user(
        cls,
        user_id,
        current_user: dict,
    ) -> bool:
        cls._require_user_management_permission(
            current_user
        )

        if str(user_id) == str(
            current_user.get("id")
        ):
            raise ValueError(
                "You cannot disable your own user account."
            )

        return cls._set_user_active_state(
            user_id,
            False,
            current_user,
        )

    @classmethod
    def _set_user_active_state(
        cls,
        user_id,
        enabled: bool,
        current_user: dict,
    ) -> bool:
        if not user_id:
            raise ValueError(
                "User ID is required."
            )

        conn = get_connection()
        cur = conn.cursor()

        try:
            user = UserRepository.get_by_id(
                user_id,
                cursor=cur,
            )

            if not user:
                raise ValueError(
                    "User account was not found."
                )

            if enabled:
                if user["is_active"]:
                    raise ValueError(
                        "User account is already enabled."
                    )

                changed = UserRepository.enable(
                    user_id,
                    cursor=cur,
                )

                action = "Enabled"

            else:
                if not user["is_active"]:
                    raise ValueError(
                        "User account is already disabled."
                    )

                changed = UserRepository.disable(
                    user_id,
                    cursor=cur,
                )

                action = "Disabled"

            if not changed:
                raise RuntimeError(
                    "User account status was not changed."
                )

            ActivityLogger.log_update(
                cur,
                user_id=current_user["id"],
                module=ActivityLogger.MODULE_ADMINISTRATION,
                record_id=user_id,
                details=(
                    f"{action} user account "
                    f"{user['employee_number']} - "
                    f"{user['full_name']}"
                ),
            )

            conn.commit()

            return True

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    # ============================================================
    # ROLES
    # ============================================================

    @classmethod
    def get_roles(cls) -> list[dict]:
        return RoleRepository.get_all()

    @classmethod
    def get_active_roles(cls) -> list[dict]:
        return RoleRepository.get_active()

    @classmethod
    def get_role(cls, role_id):
        if not role_id:
            return None

        return RoleRepository.get_by_id(
            role_id
        )

    # ============================================================
    # DEPARTMENTS
    # ============================================================

    @classmethod
    def get_departments(cls) -> list[dict]:
        return DepartmentRepository.get_all()

    @classmethod
    def get_active_departments(cls) -> list[dict]:
        return DepartmentRepository.get_active()

    @classmethod
    def get_department(cls, department_id):
        if not department_id:
            return None

        return DepartmentRepository.get_by_id(
            department_id
        )

    # ============================================================
    # JOB TITLES
    # ============================================================

    @classmethod
    def get_job_titles(cls) -> list[dict]:
        return JobTitleRepository.get_all()

    @classmethod
    def get_active_job_titles(cls) -> list[dict]:
        return JobTitleRepository.get_active()

    @classmethod
    def get_job_title(cls, job_title_id):
        if not job_title_id:
            return None

        return JobTitleRepository.get_by_id(
            job_title_id
        )

    @classmethod
    def get_job_titles_by_department(
        cls,
        department_id,
        *,
        active_only=True,
    ) -> list[dict]:
        if not department_id:
            return []

        return JobTitleRepository.get_by_department(
            department_id,
            active_only=active_only,
        )

    # ============================================================
    # PERMISSIONS
    # ============================================================

    @classmethod
    def get_permissions(cls) -> list[dict]:
        return PermissionRepository.get_all()

    @classmethod
    def get_role_permissions(
        cls,
        role_id,
    ) -> list[dict]:
        if not role_id:
            return []

        return PermissionRepository.get_by_role(
            role_id
        )

    @classmethod
    def role_has_permission(
        cls,
        role_id,
        permission_name: str,
    ) -> bool:
        permission_name = cls._clean_text(
            permission_name
        )

        if not role_id or not permission_name:
            return False

        return (
            PermissionRepository
            .role_has_permission_name(
                role_id,
                permission_name,
            )
        )

    # ============================================================
    # EMPLOYEE NUMBER
    # ============================================================

    @classmethod
    def generate_employee_number(cls) -> str:
        """
        Generate the next available employee number.

        Current format:

            JCAP-0001
            JCAP-0002
            JCAP-0003

        Employee-number configuration will later move to
        System Settings.
        """

        users = UserRepository.get_all()

        return cls._calculate_next_employee_number(
            users
        )

    @classmethod
    def _generate_employee_number_in_transaction(
        cls,
        *,
        cursor,
    ) -> str:
        users = UserRepository.get_all(
            cursor=cursor
        )

        employee_number = (
            cls._calculate_next_employee_number(
                users
            )
        )

        while UserRepository.employee_number_exists(
            employee_number,
            cursor=cursor,
        ):
            employee_number = (
                cls._increment_employee_number(
                    employee_number
                )
            )

        return employee_number

    @classmethod
    def _calculate_next_employee_number(
        cls,
        users: list[dict],
    ) -> str:
        prefix = cls.EMPLOYEE_NUMBER_PREFIX.upper()
        expected_prefix = f"{prefix}-"

        highest_number = 0

        for user in users:
            employee_number = cls._clean_text(
                user.get("employee_number")
            ).upper()

            if not employee_number.startswith(
                expected_prefix
            ):
                continue

            number_part = employee_number[
                len(expected_prefix):
            ]

            if not number_part.isdigit():
                continue

            highest_number = max(
                highest_number,
                int(number_part),
            )

        next_number = highest_number + 1

        return (
            f"{prefix}-"
            f"{next_number:0{cls.EMPLOYEE_NUMBER_DIGITS}d}"
        )

    @classmethod
    def _increment_employee_number(
        cls,
        employee_number: str,
    ) -> str:
        prefix = cls.EMPLOYEE_NUMBER_PREFIX.upper()
        expected_prefix = f"{prefix}-"

        if not employee_number.startswith(
            expected_prefix
        ):
            raise ValueError(
                "Invalid employee number format."
            )

        number_part = employee_number[
            len(expected_prefix):
        ]

        if not number_part.isdigit():
            raise ValueError(
                "Invalid employee number sequence."
            )

        next_number = int(number_part) + 1

        return (
            f"{prefix}-"
            f"{next_number:0{cls.EMPLOYEE_NUMBER_DIGITS}d}"
        )

    # ============================================================
    # DASHBOARD COUNTS
    # ============================================================

    @classmethod
    def get_organization_summary(cls) -> dict:
        total_users = UserRepository.count_users()
        active_users = UserRepository.count_active()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "disabled_users": max(
                total_users - active_users,
                0,
            ),
            "roles": RoleRepository.count_roles(),
            "active_roles": RoleRepository.count_active(),
            "departments": (
                DepartmentRepository.count_departments()
            ),
            "active_departments": (
                DepartmentRepository.count_active()
            ),
            "job_titles": (
                JobTitleRepository.count_job_titles()
            ),
            "active_job_titles": (
                JobTitleRepository.count_active()
            ),
            "permissions": (
                PermissionRepository.count_permissions()
            ),
        }

    # ============================================================
    # INTERNAL SECURITY HELPERS
    # ============================================================

    @classmethod
    def _require_user_management_permission(
        cls,
        current_user: dict,
    ) -> None:
        if not PermissionService.can_manage_users(
            current_user
        ):
            raise PermissionError(
                "You do not have permission to manage user accounts."
            )

    # ============================================================
    # LEGACY ROLE COMPATIBILITY
    # ============================================================

    @classmethod
    def _get_legacy_role_name(
        cls,
        role_name: str,
    ) -> str:
        """
        Translate the new database role names into role text understood
        by the current Version 0.9 permission and login code.

        This compatibility layer is temporary and can be removed after
        authentication and PermissionService use role_id / database
        permissions exclusively.
        """

        normalized_role = cls._clean_text(
            role_name
        ).lower()

        compatibility_map = {
            "system administrator": "Administrator",
            "purchasing manager": "Purchasing Manager",
            "purchasing officer": "Purchasing Officer",
            "project engineer": "Project Engineer",
            "warehouse personnel": "Warehouse",
            "accounting personnel": "Accounting",
            "project manager": "Project Manager",
            "executive / management": "Viewer",
            "viewer / auditor": "Viewer",
        }

        return compatibility_map.get(
            normalized_role,
            role_name,
        )

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _clean_text(value) -> str:
        if value is None:
            return ""

        return str(value).strip()