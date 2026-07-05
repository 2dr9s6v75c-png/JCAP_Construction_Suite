import os
import shutil
import re

from core.documents.document_paths import (
    get_project_folder,
    get_project_procurement_folders,
    get_material_request_folder,
)


def sanitize_folder_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    name = re.sub(r"\s+", " ", name)
    return name


def ensure_project_procurement_folders(project_code: str, project_name: str) -> str:
    project_root = get_project_folder(project_code, project_name)
    project_root.mkdir(parents=True, exist_ok=True)

    for folder_path in get_project_procurement_folders(project_code, project_name):
        folder_path.mkdir(parents=True, exist_ok=True)

    return str(project_root)


def ensure_material_request_folder(project_code: str, project_name: str, request_no: str) -> str:
    ensure_project_procurement_folders(project_code, project_name)

    folder_path = get_material_request_folder(
        project_code,
        project_name,
        request_no,
    )

    folder_path.mkdir(parents=True, exist_ok=True)

    return str(folder_path)


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