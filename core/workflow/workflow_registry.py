from __future__ import annotations

from core.workflow.material_request_workflow import MATERIAL_REQUEST_WORKFLOW
from core.workflow.workflow_engine import WorkflowEngine


workflow_engine = WorkflowEngine()
workflow_engine.register(MATERIAL_REQUEST_WORKFLOW)
