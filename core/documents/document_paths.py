from pathlib import Path
from config.settings import DOCUMENT_ROOT


MATERIAL_REQUESTS_FOLDER = "01 Material Requests"
SUPPLIER_RFQ_FOLDER = "02 Supplier RFQ"
SUPPLIER_QUOTATIONS_FOLDER = "03 Supplier Quotations"
QUOTATION_EVALUATION_FOLDER = "04 Quotation Evaluation"
PURCHASE_ORDERS_FOLDER = "05 Purchase Orders"
DELIVERY_RECEIPTS_FOLDER = "06 Delivery Receipts"
INVOICES_FOLDER = "07 Invoices"
SUPPORTING_DOCUMENTS_FOLDER = "08 Supporting Documents"
ARCHIVE_FOLDER = "09 Archive"


def get_document_root() -> Path:
    return Path(DOCUMENT_ROOT)


def get_project_folder(project_code: str, project_name: str) -> Path:
    project_code = project_code or "NO-CODE"
    project_name = project_name or "Unnamed Project"

    return get_document_root() / f"{project_code} - {project_name}"


def get_project_procurement_folders(project_code: str, project_name: str) -> list[Path]:
    project_folder = get_project_folder(project_code, project_name)

    return [
        project_folder / MATERIAL_REQUESTS_FOLDER,
        project_folder / SUPPLIER_RFQ_FOLDER,
        project_folder / SUPPLIER_QUOTATIONS_FOLDER,
        project_folder / QUOTATION_EVALUATION_FOLDER,
        project_folder / PURCHASE_ORDERS_FOLDER,
        project_folder / DELIVERY_RECEIPTS_FOLDER,
        project_folder / INVOICES_FOLDER,
        project_folder / SUPPORTING_DOCUMENTS_FOLDER,
        project_folder / ARCHIVE_FOLDER,
    ]


def get_material_requests_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / MATERIAL_REQUESTS_FOLDER


def get_material_request_folder(
    project_code: str,
    project_name: str,
    folder_name: str,
) -> Path:
    return get_material_requests_root(project_code, project_name) / folder_name


def get_supplier_rfq_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / SUPPLIER_RFQ_FOLDER


def get_supplier_quotation_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / SUPPLIER_QUOTATIONS_FOLDER


def get_purchase_order_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / PURCHASE_ORDERS_FOLDER


def get_delivery_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / DELIVERY_RECEIPTS_FOLDER


def get_invoice_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / INVOICES_FOLDER


def get_supporting_documents_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / SUPPORTING_DOCUMENTS_FOLDER


def get_archive_root(project_code: str, project_name: str) -> Path:
    return get_project_folder(project_code, project_name) / ARCHIVE_FOLDER