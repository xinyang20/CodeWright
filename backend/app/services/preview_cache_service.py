"""
预览 PDF 磁盘缓存

按"项目内容指纹 + 选项指纹"缓存编译产物，避免每次打开预览都重新跑 xelatex。
缓存文件命名：``preview_<project_id>_<sha1>.pdf``，每个项目只保留最新签名对应的文件，
其它旧签名在保存新结果时被清理。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from app.paths import EXPORTS_DIR

# 缓存模式版本：当 PdfService 的渲染管线发生不向后兼容的变化时，
# 把这个常量手动 + 1，旧缓存自然失效，无需手工清理。
CACHE_SCHEMA_VERSION = "v4"


def _cache_dir() -> Path:
    target = EXPORTS_DIR / "preview_cache"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _serialize_datetime(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def compute_signature(
    project: Any,
    items: Optional[Iterable[Any]],
    sections: Optional[Iterable[Any]],
    options: dict[str, Any],
) -> str:
    """返回稳定的内容指纹（hex sha1）。所有进入 PDF 的可变信号都参与计算。"""
    payload: dict[str, Any] = {
        "schema": CACHE_SCHEMA_VERSION,
        "project": {
            "id": project.id,
            "name": project.project_name,
            "type": project.project_type,
            "owner_id": project.owner_id,
            "updated_at": _serialize_datetime(getattr(project, "updated_at", None)),
            "config_json": project.config_json or "",
        },
        "items": [],
        "sections": [],
        "options": _normalize_options_for_hash(options),
    }

    for item in items or []:
        uploaded_file = item.file
        try:
            file_mtime = os.path.getmtime(uploaded_file.storage_path)
        except OSError:
            file_mtime = 0.0
        payload["items"].append({
            "file_id": item.file_id,
            "display_name": item.display_name or uploaded_file.original_filename,
            "language_override": item.language_override or "",
            "order_index": item.order_index,
            "include_in_export": bool(item.include_in_export),
            "file_size": uploaded_file.file_size,
            "file_mtime": int(file_mtime),
            "file_created_at": _serialize_datetime(getattr(uploaded_file, "created_at", None)),
        })

    for section in sections or []:
        payload["sections"].append({
            "id": section.id,
            "title": section.title,
            "body_markdown": section.body_markdown,
            "image_file_id": section.image_file_id,
            "order_index": section.order_index,
            "updated_at": _serialize_datetime(getattr(section, "updated_at", None)),
        })

    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def _normalize_options_for_hash(options: dict[str, Any]) -> dict[str, Any]:
    """Sort + stringify the options so equivalent dicts produce the same key."""
    if not options:
        return {}
    return {key: options[key] for key in sorted(options)}


def cache_path(project_id: int, signature: str) -> Path:
    return _cache_dir() / f"preview_{project_id}_{signature}.pdf"


def load(project_id: int, signature: str) -> Optional[bytes]:
    """命中缓存返回字节，未命中返回 None。"""
    path = cache_path(project_id, signature)
    if not path.exists():
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def save(project_id: int, signature: str, pdf_bytes: bytes) -> Optional[Path]:
    """保存最新签名结果，并清理同项目的过期缓存。"""
    if not pdf_bytes:
        return None
    target = cache_path(project_id, signature)
    try:
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(pdf_bytes)
        tmp.replace(target)
    except OSError:
        return None

    _prune_other(project_id, keep_signature=signature)
    return target


def invalidate(project_id: int) -> None:
    """删除指定项目的所有缓存。可在外层显式调用，例如批量上传完成后。"""
    _prune_other(project_id, keep_signature=None)


def _prune_other(project_id: int, keep_signature: Optional[str]) -> None:
    directory = _cache_dir()
    prefix = f"preview_{project_id}_"
    for file in directory.glob(f"{prefix}*.pdf"):
        if keep_signature is not None and file.name == f"{prefix}{keep_signature}.pdf":
            continue
        try:
            file.unlink()
        except OSError:
            continue
