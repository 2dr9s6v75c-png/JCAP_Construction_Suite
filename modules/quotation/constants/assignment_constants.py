"""
JCAP Construction Suite
Material Request Assignment Constants

Centralized business constants used by material-request assignment services,
repositories, processes, and tests.

Engineering standards:
    ES-002 - No Magic Strings
    ES-009 - Stable Public APIs
"""

from __future__ import annotations


# =============================================================================
# Assignment Defaults
# =============================================================================

DEFAULT_ASSIGNMENT_REMARKS = "Assigned for quotation processing."


# =============================================================================
# Validation Limits
# =============================================================================

MAX_ACTIVE_ASSIGNMENTS = 5
MAX_ASSIGNMENT_REMARK_LENGTH = 500


__all__ = [
    "DEFAULT_ASSIGNMENT_REMARKS",
    "MAX_ACTIVE_ASSIGNMENTS",
    "MAX_ASSIGNMENT_REMARK_LENGTH",
]