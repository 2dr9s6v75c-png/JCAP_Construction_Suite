"""
JCAP Construction Suite
Material Request Assignment Test Constants

Shared deterministic values used across assignment service tests.
"""

from __future__ import annotations

from uuid import UUID


# ---------------------------------------------------------------------------
# Deterministic identifiers
# ---------------------------------------------------------------------------

MATERIAL_REQUEST_ID = UUID(
    "00000000-0000-0000-0000-000000001001"
)
SECOND_MATERIAL_REQUEST_ID = UUID(
    "00000000-0000-0000-0000-000000001002"
)

ASSIGNMENT_ID = UUID(
    "00000000-0000-0000-0000-000000002001"
)
SECOND_ASSIGNMENT_ID = UUID(
    "00000000-0000-0000-0000-000000002002"
)

ASSIGNED_BY_ID = UUID(
    "00000000-0000-0000-0000-000000004001"
)
ASSIGNED_TO_ID = UUID(
    "00000000-0000-0000-0000-000000004002"
)
SECOND_ASSIGNED_TO_ID = UUID(
    "00000000-0000-0000-0000-000000004003"
)


# ---------------------------------------------------------------------------
# User data
# ---------------------------------------------------------------------------

ASSIGNING_USERNAME = "assigning.user"
ASSIGNING_FULL_NAME = "Assigning User"
ASSIGNING_ROLE = "Administrator"

ASSIGNED_USERNAME = "assigned.user"
ASSIGNED_FULL_NAME = "Assigned User"

SECOND_ASSIGNED_USERNAME = "second.assigned.user"
SECOND_ASSIGNED_FULL_NAME = "Second Assigned User"


# ---------------------------------------------------------------------------
# Material Request data
# ---------------------------------------------------------------------------

MATERIAL_REQUEST_NUMBER = "MR-2026-0001"
SECOND_MATERIAL_REQUEST_NUMBER = "MR-2026-0002"


# ---------------------------------------------------------------------------
# Assignment data
# ---------------------------------------------------------------------------

DEFAULT_REMARKS = "Assigned for quotation processing."
REASSIGNMENT_REMARKS = "Reassigned due to workload balancing."
EMPTY_REMARKS = ""

DEFAULT_OFFICER_WORKLOAD = 0
WORKLOAD_BELOW_LIMIT = 4
WORKLOAD_AT_LIMIT = 5
WORKLOAD_ABOVE_LIMIT = 6


# ---------------------------------------------------------------------------
# Common validation and authorization messages
# ---------------------------------------------------------------------------

PERMISSION_DENIED_MESSAGE = (
    "You do not have permission to assign material requests."
)
ACTIVE_ASSIGNMENT_EXISTS_MESSAGE = (
    "The material request already has an active assignment."
)
OFFICER_WORKLOAD_LIMIT_MESSAGE = (
    "The selected officer has reached the assignment workload limit."
)
INVALID_MATERIAL_REQUEST_ID_MESSAGE = (
    "material_request_id must be a valid UUID."
)
INVALID_ASSIGNED_TO_ID_MESSAGE = (
    "assigned_to must be a valid UUID."
)
INVALID_CURRENT_USER_MESSAGE = (
    "A valid current user is required."
)
INVALID_ASSIGNED_BY_ID_MESSAGE = (
    "current_user id must be a valid UUID."
)