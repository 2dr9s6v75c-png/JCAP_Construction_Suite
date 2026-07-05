import os
import shutil
import re
from config import settings
from core.documents.document_paths import (
    get_project_root_folder,
    ensure_project_procurement_folders,
    get_material_request_folder,
    ensure_material_request_folder
)


PROJECT_PROCUREMENT_FOLDERS = [
    "01 Material Requests",
    "02 Supplier RFQ",
    "03 Supplier Quotations",
    "04 Quotation Evaluation",
    "05 Purchase Orders",
    "06 Delivery Receipts",
    "07 Invoices",
    "08 Supporting Documents",
    "09 Archive",
]


def sanitize_folder_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    name = re.sub(r"\s+", " ", name)
    return name


def get_project_folder_name(project_code: str, project_name: str) -> str:
    project_code = project_code or "NO-CODE"
    project_name = project_name or "Unnamed Project"
    return sanitize_folder_name(f"{project_code} - {project_name}")


def get_project_root_folder(project_code: str, project_name: str) -> str:
    project_folder = get_project_folder_name(project_code, project_name)
    return os.path.join(settings.DOCUMENT_ROOT, project_folder)


def ensure_project_procurement_folders(project_code: str, project_name: str) -> str:
    project_root = get_project_root_folder(project_code, project_name)

    os.makedirs(project_root, exist_ok=True)

    for folder_name in PROJECT_PROCUREMENT_FOLDERS:
        os.makedirs(os.path.join(project_root, folder_name), exist_ok=True)

    return project_root


def get_material_request_folder(project_code: str, project_name: str, request_no: str) -> str:
    project_root = get_project_root_folder(project_code, project_name)

    return os.path.join(
        project_root,
        "01 Material Requests",
        request_no
    )


def ensure_material_request_folder(project_code: str, project_name: str, request_no: str) -> str:
    ensure_project_procurement_folders(project_code, project_name)

    folder_path = get_material_request_folder(
        project_code,
        project_name,
        request_no
    )

    os.makedirs(folder_path, exist_ok=True)

    return folder_path


def copy_attachments_to_request_folder(
    attachments: list[str],
    project_code: str,
    project_name: str,
    request_no: str
) -> list[dict]:
    destination_folder = ensure_material_request_folder(
        project_code,
        project_name,
        request_no
    )

    saved_files = []

    for source_path in attachments:
        if not os.path.isfile(source_path):
            continue

        original_filename = os.path.basename(source_path)
        safe_filename = sanitize_folder_name(original_filename)
        destination_path = os.path.join(destination_folder, safe_filename)

        base_name, extension = os.path.splitext(safe_filename)
        counter = 1

        while os.path.exists(destination_path):
            safe_filename = f"{base_name} ({counter}){extension}"
            destination_path = os.path.join(destination_folder, safe_filename)
            counter += 1

        shutil.copy2(source_path, destination_path)

        saved_files.append({
            "original_filename": original_filename,
            "stored_filename": safe_filename,
            "folder_path": destination_folder,
            "relative_module": "01 Material Requests",
            "file_size": os.path.getsize(destination_path),
            "file_extension": extension.replace(".", "").lower()
        })

    return saved_files