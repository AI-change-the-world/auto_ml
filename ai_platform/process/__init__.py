from typing import Optional

from pydantic import BaseModel


class DirectoryModel(BaseModel):
    files_dir: str
    results_dir: Optional[str]


class BaseProcess:
    def create_temp_dir(self, session_id: str):
        """创建临时文件夹，用于存储中间结果"""
