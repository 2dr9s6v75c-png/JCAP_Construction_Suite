from __future__ import annotations

from core.workflow.workflow_engine import WorkflowDefinition


class MaterialRequestState:
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    QUEUED = "Queued"
    ASSIGNED = "Assigned"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In Progress"
    WAITING_CLARIFICATION = "Waiting Clarification"
    WAITING_SUPPLIER_QUOTE = "Waiting Supplier Quote"
    QUOTATION_EVALUATION = "Quotation Evaluation"
    SUPPLIER_SELECTED = "Supplier Selected"
    PO_PREPARATION = "PO Preparation"
    PO_RELEASED = "PO Released"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"

    ALL = (
        DRAFT,
        SUBMITTED,
        QUEUED,
        ASSIGNED,
        ACCEPTED,
        IN_PROGRESS,
        WAITING_CLARIFICATION,
        WAITING_SUPPLIER_QUOTE,
        QUOTATION_EVALUATION,
        SUPPLIER_SELECTED,
        PO_PREPARATION,
        PO_RELEASED,
        COMPLETED,
        ARCHIVED,
    )


class AssignmentState:
    ASSIGNED = "Assigned"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In Progress"
    PAUSED = "Paused"
    REASSIGNED = "Reassigned"
    DECLINED = "Declined"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

    ACTIVE = (ASSIGNED, ACCEPTED, IN_PROGRESS, PAUSED)
    TERMINAL = (REASSIGNED, DECLINED, COMPLETED, CANCELLED)


MATERIAL_REQUEST_WORKFLOW_NAME = "material_request"

MATERIAL_REQUEST_WORKFLOW = WorkflowDefinition(
    name=MATERIAL_REQUEST_WORKFLOW_NAME,
    states=MaterialRequestState.ALL,
    transitions={
        MaterialRequestState.DRAFT: (
            MaterialRequestState.SUBMITTED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.SUBMITTED: (
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.QUEUED: (
            MaterialRequestState.ASSIGNED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.ASSIGNED: (
            MaterialRequestState.ACCEPTED,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.ACCEPTED: (
            MaterialRequestState.IN_PROGRESS,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.IN_PROGRESS: (
            MaterialRequestState.WAITING_CLARIFICATION,
            MaterialRequestState.WAITING_SUPPLIER_QUOTE,
            MaterialRequestState.QUOTATION_EVALUATION,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.WAITING_CLARIFICATION: (
            MaterialRequestState.IN_PROGRESS,
            MaterialRequestState.WAITING_SUPPLIER_QUOTE,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.WAITING_SUPPLIER_QUOTE: (
            MaterialRequestState.WAITING_CLARIFICATION,
            MaterialRequestState.QUOTATION_EVALUATION,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.QUOTATION_EVALUATION: (
            MaterialRequestState.WAITING_SUPPLIER_QUOTE,
            MaterialRequestState.SUPPLIER_SELECTED,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.SUPPLIER_SELECTED: (
            MaterialRequestState.PO_PREPARATION,
            MaterialRequestState.QUOTATION_EVALUATION,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.PO_PREPARATION: (
            MaterialRequestState.PO_RELEASED,
            MaterialRequestState.SUPPLIER_SELECTED,
            MaterialRequestState.QUEUED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.PO_RELEASED: (
            MaterialRequestState.COMPLETED,
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.COMPLETED: (
            MaterialRequestState.ARCHIVED,
        ),
        MaterialRequestState.ARCHIVED: (),
    },
)
