"""
文件服务
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.file import UploadedFile

class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("../upload")
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        file_content: bytes
    ) -> UploadedFile:
        """保存上传的文件"""
        # 生成唯一文件名
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        storage_path = self.upload_dir / unique_filename
        
        # 保存文件到磁盘
        with open(storage_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 保存文件信息到数据库
        uploaded_file = UploadedFile(
            original_filename=file.filename,
            storage_path=str(storage_path),
            file_size=len(file_content),
            file_type=file.content_type or "application/octet-stream",
            uploader_id=user_id
        )
        
        self.db.add(uploaded_file)
        self.db.commit()
        self.db.refresh(uploaded_file)
        
        return uploaded_file
    
    async def get_user_files(self, user_id: int) -> List[UploadedFile]:
        """获取用户的文件列表"""
        return self.db.query(UploadedFile).filter(
            UploadedFile.uploader_id == user_id
        ).order_by(UploadedFile.created_at.desc()).all()
    
    async def get_file_by_id(self, file_id: int, user_id: int) -> Optional[UploadedFile]:
        """根据ID获取文件"""
        return self.db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.uploader_id == user_id
        ).first()
    
    async def delete_file(self, file_id: int, user_id: int) -> bool:
        """删除文件"""
        file_record = await self.get_file_by_id(file_id, user_id)
        if not file_record:
            return False
        
        # 删除磁盘文件
        try:
            if os.path.exists(file_record.storage_path):
                os.remove(file_record.storage_path)
        except Exception:
            pass  # 忽略文件删除错误
        
        # 删除数据库记录
        self.db.delete(file_record)
        self.db.commit()
        
        return True
    
    async def read_file_content(self, file_id: int, user_id: int) -> Optional[str]:
        """读取文件内容"""
        file_record = await self.get_file_by_id(file_id, user_id)
        if not file_record:
            return None
        
        try:
            with open(file_record.storage_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_record.storage_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                return None
        except Exception:
            return None
