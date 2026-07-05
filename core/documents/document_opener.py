import os
import subprocess
from pathlib import Path


class DocumentOpener:
    @staticmethod
    def open_folder(folder_path):
        path = Path(folder_path)

        if not path.exists():
            raise FileNotFoundError(f"Folder not found: {path}")

        os.startfile(str(path))

    @staticmethod
    def open_file(file_path):
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        os.startfile(str(path))