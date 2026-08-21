import os
import re
import shutil
from pathlib import Path
from typing import Iterable

from core.documents.document_paths import (
    get_project_folder,
    get_project_procurement_folders,
    get_material_request_folder,
    get_material_requests_root,
)


SUPPLIER_QUOTATIONS_FOLDER = "Supplier Quotations"


def sanitize_folder_name(name: str) -> str:
    """Return a Windows-safe folder or filename component."""
    cleaned = str(name or "").strip()
    cleaned = re.sub(r'[<>:"/\\|?*]', "-", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.rstrip(". ")

    if not cleaned:
        raise ValueError("A valid folder or filename is required.")

    return cleaned


def ensure_project_procurement_folders(
    project_code: str,
    project_name: str,
) -> str:
    project_root = get_project_folder(
        project_code,
        project_name,
    )
    project_root.mkdir(parents=True, exist_ok=True)

    for folder_path in get_project_procurement_folders(
        project_code,
        project_name,
    ):
        folder_path.mkdir(parents=True, exist_ok=True)

    return str(project_root)


def ensure_material_request_folder(
    project_code: str,
    project_name: str,
    request_no: str,
) -> str:
    ensure_project_procurement_folders(
        project_code,
        project_name,
    )

    folder_path = get_material_request_folder(
        project_code,
        project_name,
        request_no,
    )
    folder_path.mkdir(parents=True, exist_ok=True)

    return str(folder_path)


def ensure_supplier_quotation_folder(
    project_code: str,
    project_name: str,
    request_no: str,
    supplier_name: str,
) -> str:
    """
    Ensure and return the supplier-specific quotation folder.

    Folder structure:
        <Material Request>/
            Supplier Quotations/
                <Supplier Name>/
    """
    request_folder = Path(
        ensure_material_request_folder(
            project_code,
            project_name,
            request_no,
        )
    )

    supplier_folder = (
        request_folder
        / SUPPLIER_QUOTATIONS_FOLDER
        / sanitize_folder_name(supplier_name)
    )
    supplier_folder.mkdir(parents=True, exist_ok=True)

    return str(supplier_folder)


def _build_unique_destination(
    destination_folder: Path,
    source_filename: str,
) -> tuple[str, Path]:
    safe_filename = sanitize_folder_name(source_filename)
    destination_path = destination_folder / safe_filename

    base_name = destination_path.stem
    extension = destination_path.suffix
    counter = 1

    while destination_path.exists():
        safe_filename = f"{base_name} ({counter}){extension}"
        destination_path = destination_folder / safe_filename
        counter += 1

    return safe_filename, destination_path


def _copy_files(
    source_paths: Iterable[str],
    destination_folder: str | Path,
    *,
    relative_module: str,
) -> list[dict]:
    destination = Path(destination_folder)
    destination.mkdir(parents=True, exist_ok=True)

    saved_files: list[dict] = []

    for source_path_value in source_paths:
        source_path = Path(source_path_value)

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Selected file was not found: {source_path}"
            )

        stored_filename, destination_path = (
            _build_unique_destination(
                destination,
                source_path.name,
            )
        )

        shutil.copy2(source_path, destination_path)

        saved_files.append(
            {
                "original_filename": source_path.name,
                "stored_filename": stored_filename,
                "folder_path": str(destination),
                "relative_module": relative_module,
                "file_size": destination_path.stat().st_size,
                "file_extension": (
                    destination_path.suffix
                    .replace(".", "")
                    .lower()
                ),
                "full_path": str(destination_path),
            }
        )

    return saved_files


def copy_attachments_to_request_folder(
    attachments: list[str],
    project_code: str,
    project_name: str,
    request_no: str,
) -> list[dict]:
    destination_folder = ensure_material_request_folder(
        project_code,
        project_name,
        request_no,
    )

    # Preserve the existing Phase 1 Material Request attachment location.
    return _copy_files(
        attachments,
        destination_folder,
        relative_module="01 Material Requests",
    )


def copy_supplier_quotation_files(
    files: list[str],
    project_code: str,
    project_name: str,
    request_no: str,
    supplier_name: str,
) -> list[dict]:
    """Copy supplier quotation files into the supplier-specific folder."""
    destination_folder = ensure_supplier_quotation_folder(
        project_code=project_code,
        project_name=project_name,
        request_no=request_no,
        supplier_name=supplier_name,
    )

    return _copy_files(
        files,
        destination_folder,
        relative_module=(
            f"Supplier Quotations/"
            f"{sanitize_folder_name(supplier_name)}"
        ),
    )


def delete_stored_file(
    folder_path: str,
    stored_filename: str,
    *,
    missing_ok: bool = True,
) -> bool:
    """Delete one managed file without deleting its parent folder."""
    safe_filename = sanitize_folder_name(stored_filename)
    file_path = Path(folder_path) / safe_filename

    if not file_path.exists():
        if missing_ok:
            return False
        raise FileNotFoundError(
            f"Stored file was not found: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Stored path is not a file: {file_path}"
        )

    file_path.unlink()
    return True


def delete_empty_supplier_quotation_folder(
    folder_path: str,
) -> bool:
    """
    Remove a supplier quotation folder only when it is empty.

    The Material Request and Supplier Quotations parent folders are preserved.
    """
    path = Path(folder_path)

    if not path.exists():
        return False

    if not path.is_dir():
        raise ValueError(
            f"Quotation folder path is not a directory: {path}"
        )

    try:
        path.rmdir()
    except OSError:
        return False

    return True

def delete_material_request_folder(
    project_code: str,
    project_name: str,
    folder_name: str,
    *,
    missing_ok: bool = True,
) -> bool:
    """
    Permanently delete exactly one managed Material Request folder tree.

    Safety rules:
    - The target path is derived only from JCAP document path helpers.
    - The target must remain inside the project's "01 Material Requests" root.
    - The Material Requests root itself can never be deleted.
    - The project root and sibling MR folders are never touched.
    - A missing folder may be treated as already cleaned.

    Returns:
        True if the folder existed and was deleted.
        False if it did not exist and missing_ok=True.
    """
    safe_folder_name = sanitize_folder_name(folder_name)

    material_requests_root = get_material_requests_root(
        project_code,
        project_name,
    ).resolve(strict=False)

    target_folder = get_material_request_folder(
        project_code,
        project_name,
        safe_folder_name,
    ).resolve(strict=False)

    if target_folder == material_requests_root:
        raise ValueError(
            "Refusing to delete the Material Requests root folder."
        )

    try:
        target_folder.relative_to(material_requests_root)
    except ValueError as exc:
        raise ValueError(
            "Refusing to delete a path outside the managed "
            "Material Requests folder."
        ) from exc

    if not target_folder.exists():
        if missing_ok:
            return False

        raise FileNotFoundError(
            f"Material Request folder was not found: {target_folder}"
        )

    if not target_folder.is_dir():
        raise ValueError(
            f"Material Request path is not a directory: {target_folder}"
        )

    shutil.rmtree(target_folder)
    return True