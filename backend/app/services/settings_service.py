"""
系统设置、公告和高亮映射服务
"""
import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.models.setting import Setting


DEFAULT_SETTINGS: dict[str, Any] = {
    "pdf_style": {
        "latex_engine": "xelatex",
        "document_class": "article",
        "font_size": "12pt",
        "page_geometry": "a4paper,margin=2cm",
        "main_font": "PingFang SC",
        "mono_font": "Menlo",
        "line_stretch": "1.25",
        "header_latex": "",
        "footer_latex": "\\thepage",
        "preamble_latex": "",
    },
    "upload": {
        "max_upload_size_mb": 10,
        "allowed_extensions": [
            ".py", ".java", ".js", ".ts", ".md", ".txt", ".c", ".cpp",
            ".h", ".hpp", ".css", ".html", ".xml", ".json", ".yml",
            ".yaml", ".sql", ".sh", ".bat", ".png", ".jpg", ".jpeg",
            ".gif", ".bmp", ".webp",
        ],
        "max_project_size_mb": 100,
    },
    "manual": {
        "enable_global_variables": True,
    },
}


def _latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in str(value))


def _migrate_pdf_style(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return dict(DEFAULT_SETTINGS["pdf_style"])

    migrated = {**DEFAULT_SETTINGS["pdf_style"], **value}
    if "page_margin" in value and "page_geometry" not in value:
        migrated["page_geometry"] = f"a4paper,margin={value.get('page_margin') or '2cm'}"
    if "font_family" in value and "main_font" not in value:
        migrated["main_font"] = str(value.get("font_family") or "PingFang SC").split(",")[0].strip()
    if "font_size" in value and str(value.get("font_size") or "").endswith("px"):
        migrated["font_size"] = str(value.get("font_size") or "12px").replace("px", "pt")
    if "header_text" in value and "header_latex" not in value:
        migrated["header_latex"] = _latex_escape(str(value.get("header_text") or ""))
    if "footer_text" in value and "footer_latex" not in value:
        footer_text = str(value.get("footer_text") or "").strip()
        migrated["footer_latex"] = "\\thepage" if footer_text in {"", "页码", "page", "counter(page)"} else _latex_escape(footer_text)

    for legacy_key in ("font_family", "page_margin", "header_text", "footer_text"):
        migrated.pop(legacy_key, None)
    return migrated


class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.ensure_defaults()

    def ensure_defaults(self) -> None:
        for key, value in DEFAULT_SETTINGS.items():
            existing = self.db.query(Setting).filter(Setting.key == key).first()
            if not existing:
                self.db.add(Setting(key=key, value=json.dumps(value, ensure_ascii=False)))
            elif key == "pdf_style":
                try:
                    current = json.loads(existing.value)
                except json.JSONDecodeError:
                    current = {}
                migrated = _migrate_pdf_style(current)
                if migrated != current:
                    existing.value = json.dumps(migrated, ensure_ascii=False)
        self.db.commit()

    async def get_settings(self) -> dict[str, Any]:
        self.ensure_defaults()
        settings = self.db.query(Setting).order_by(Setting.key).all()
        return {
            item.key: json.loads(item.value)
            for item in settings
        }

    async def update_setting(self, key: str, value: Any) -> dict[str, Any]:
        if key not in DEFAULT_SETTINGS:
            raise ValueError("不支持的设置项")
        if not isinstance(value, dict):
            raise ValueError("设置值必须是 JSON 对象")

        setting = self.db.query(Setting).filter(Setting.key == key).first()
        if not setting:
            setting = Setting(key=key, value="{}")
            self.db.add(setting)

        setting.value = json.dumps(value, ensure_ascii=False)
        self.db.commit()
        return await self.get_settings()

    def announcement_to_dict(self, announcement: Announcement) -> dict[str, Any]:
        return {
            "id": announcement.id,
            "title": announcement.title,
            "body_markdown": announcement.body_markdown,
            "status": announcement.status,
            "published_at": announcement.published_at,
            "created_at": announcement.created_at,
            "updated_at": announcement.updated_at,
        }

    async def get_announcements(self, include_archived: bool = True) -> list[dict[str, Any]]:
        query = self.db.query(Announcement)
        if not include_archived:
            query = query.filter(Announcement.status != "archived")
        announcements = query.order_by(Announcement.created_at.desc()).all()
        return [self.announcement_to_dict(item) for item in announcements]

    async def create_announcement(self, data: dict[str, Any]) -> dict[str, Any]:
        title = str(data.get("title", "")).strip()
        body_markdown = str(data.get("body_markdown", "")).strip()
        if not title or not body_markdown:
            raise KeyError("title")

        status = data.get("status", "draft")
        if status not in {"draft", "published", "archived"}:
            raise ValueError("公告状态无效")

        announcement = Announcement(
            title=title,
            body_markdown=body_markdown,
            status=status,
            published_at=datetime.now() if status == "published" else None,
        )
        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)
        return self.announcement_to_dict(announcement)

    async def update_announcement(self, announcement_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        announcement = self.db.query(Announcement).filter(
            Announcement.id == announcement_id
        ).first()
        if not announcement:
            return None

        if "title" in data:
            title = str(data["title"]).strip()
            if not title:
                raise ValueError("公告标题不能为空")
            announcement.title = title
        if "body_markdown" in data:
            body_markdown = str(data["body_markdown"]).strip()
            if not body_markdown:
                raise ValueError("公告正文不能为空")
            announcement.body_markdown = body_markdown
        if "status" in data:
            status = data["status"]
            if status not in {"draft", "published", "archived"}:
                raise ValueError("公告状态无效")
            announcement.status = status
            announcement.published_at = datetime.now() if status == "published" else announcement.published_at

        self.db.commit()
        self.db.refresh(announcement)
        return self.announcement_to_dict(announcement)

    async def delete_announcement(self, announcement_id: int) -> bool:
        announcement = self.db.query(Announcement).filter(
            Announcement.id == announcement_id
        ).first()
        if not announcement:
            return False
        self.db.delete(announcement)
        self.db.commit()
        return True
