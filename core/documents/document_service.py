from modules.quotation.services.material_request_service import get_material_request
from core.documents.document_paths import get_material_request_folder
from core.documents.document_opener import DocumentOpener


class DocumentService:
    @staticmethod
    def open_material_request_folder(material_request_id: str):
        request = get_material_request(material_request_id)

        if not request:
            raise ValueError("Material Request not found.")

        folder_path = get_material_request_folder(
            project_code=request["project_code"],
            project_name=request["project_name"],
            folder_name=request["folder_name"],
        )

        DocumentOpener.open_folder(folder_path)

    @staticmethod
    def get_material_request_attachment_path(material_request_id: str, stored_filename: str):
        request = get_material_request(material_request_id)

        if not request:
            raise ValueError("Material Request not found.")

        folder_path = get_material_request_folder(
            project_code=request["project_code"],
            project_name=request["project_name"],
            folder_name=request["folder_name"],
        )

        return folder_path / stored_filename

    @staticmethod
    def open_material_request_attachment(material_request_id: str, stored_filename: str):
        file_path = DocumentService.get_material_request_attachment_path(
            material_request_id,
            stored_filename,
        )

        DocumentOpener.open_file(file_path)