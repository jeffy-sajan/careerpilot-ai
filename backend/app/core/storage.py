import abc
import uuid
from pathlib import Path
from typing import Tuple


class StorageProvider(abc.ABC):
    """
    Abstract Base Class defining the contract for file storage providers.
    Allows swapping local file storage with cloud storage providers (e.g. Supabase, S3).
    """

    @abc.abstractmethod
    async def save_file(self, file_bytes: bytes, user_id: uuid.UUID, original_filename: str) -> Tuple[str, str]:
        """
        Saves a file to storage under a generated UUID name.

        Args:
            file_bytes: The raw content of the file.
            user_id: The ID of the user uploading the file.
            original_filename: The original name of the file (to extract the extension).

        Returns:
            Tuple[str, str]: (storage_path, file_url)
                - storage_path: Relative internal path/key (e.g., "resumes/{user_id}/{uuid}.pdf")
                - file_url: Accessible URL or dummy path for local usage.
        """
        pass

    @abc.abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """
        Deletes a file from storage at the specified path.

        Args:
            storage_path: The relative internal path/key of the file.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass

    @abc.abstractmethod
    async def file_exists(self, storage_path: str) -> bool:
        """
        Checks if a file exists in storage.

        Args:
            storage_path: The relative internal path/key of the file.

        Returns:
            bool: True if it exists, False otherwise.
        """
    @abc.abstractmethod
    async def read_file(self, storage_path: str) -> bytes:
        """
        Reads a file from storage and returns its bytes.

        Args:
            storage_path: The relative internal path/key of the file.

        Returns:
            bytes: The raw content of the file.
        """
        pass


class LocalStorageProvider(StorageProvider):
    """
    Local file system implementation of StorageProvider.
    Saves files under a base uploads directory.
    """

    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir).resolve()

    def _get_absolute_path(self, storage_path: str) -> Path:
        """
        Constructs an absolute path and verifies it stays within base_dir 
        to prevent directory traversal attacks.
        """
        resolved = (self.base_dir / storage_path).resolve()
        if not resolved.is_relative_to(self.base_dir):
            raise ValueError("Path traversal attempt detected.")
        return resolved

    async def save_file(self, file_bytes: bytes, user_id: uuid.UUID, original_filename: str) -> Tuple[str, str]:
        # Extract extension safely
        ext = Path(original_filename).suffix.lower()
        
        # Generate unique file name to prevent naming collisions
        unique_name = f"{uuid.uuid4()}{ext}"
        
        # Storage path relative to base directory
        relative_path = f"resumes/{user_id}/{unique_name}"
        abs_path = self._get_absolute_path(relative_path)
        
        # Ensure target directories exist
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file bytes to disk
        with open(abs_path, "wb") as f:
            f.write(file_bytes)
            
        # For local development, URL is an internal API endpoint that streams the file
        file_url = f"/api/v1/resumes/download/{relative_path}"
        return relative_path, file_url

    async def delete_file(self, storage_path: str) -> bool:
        try:
            abs_path = self._get_absolute_path(storage_path)
            if abs_path.exists() and abs_path.is_file():
                abs_path.unlink()
                
                # Recursively clean up parent user directories if they become empty
                parent_dir = abs_path.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                return True
            return False
        except Exception:
            return False

    async def file_exists(self, storage_path: str) -> bool:
        try:
            abs_path = self._get_absolute_path(storage_path)
            return abs_path.exists() and abs_path.is_file()
        except Exception:
            return False

    async def read_file(self, storage_path: str) -> bytes:
        try:
            abs_path = self._get_absolute_path(storage_path)
            if not abs_path.exists() or not abs_path.is_file():
                raise FileNotFoundError(f"File not found: {storage_path}")
            # Use synchronous open as it is local file read
            with open(abs_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file from local storage: {str(e)}") from e

