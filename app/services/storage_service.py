import os
import shutil
from abc import ABC, abstractmethod
from fastapi import UploadFile
from app.core.config import settings

class StorageService(ABC):
    @abstractmethod
    async def save_file(self, file: UploadFile, filename: str) -> str:
        pass
        
    @abstractmethod
    def get_file(self, file_path: str) -> str:
        pass
        
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        pass
        
    @abstractmethod
    def get_url(self, file_path: str) -> str:
        pass

class LocalStorageService(StorageService):
    def __init__(self):
        self.storage_path = settings.STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        
    async def save_file(self, file: UploadFile, filename: str) -> str:
        file_path = os.path.join(self.storage_path, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path
        
    def get_file(self, file_path: str) -> str:
        return file_path
        
    def delete_file(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
        
    def get_url(self, file_path: str) -> str:
        return f"/files/{os.path.basename(file_path)}"

class S3StorageService(StorageService):
    def save_file(self, file: UploadFile, filename: str) -> str:
        raise NotImplementedError("Configure S3")
        
    def get_file(self, file_path: str) -> str:
        raise NotImplementedError("Configure S3")
        
    def delete_file(self, file_path: str) -> bool:
        raise NotImplementedError("Configure S3")
        
    def get_url(self, file_path: str) -> str:
        raise NotImplementedError("Configure S3")
