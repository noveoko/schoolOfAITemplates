from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

FieldName = Literal[
    "city",
    "tagline",
    "event_title",
    "event_date",
    "url",
    "logo",
    "accent_color",
    "speakers",
]

ExportFormat = Literal["png", "webp", "svg"]


class SafeZone(BaseModel):
    x: int = 0
    y: int = 0
    w: int
    h: int


class TemplateSpec(BaseModel):
    id: str
    file: str
    width: int
    height: int
    aspect: str
    placement: str
    label: str = ""
    safe_zone: SafeZone | None = None
    exports: list[ExportFormat] = Field(default_factory=lambda: ["png", "webp"])
    scale: int = 2
    fields: list[FieldName] = Field(default_factory=list)
    legacy: bool = False


class PlatformSpec(BaseModel):
    label: str
    templates: list[TemplateSpec]


class Manifest(BaseModel):
    version: str = "2026.1"
    brand_defaults: dict[str, str] = Field(default_factory=dict)
    platforms: dict[str, PlatformSpec]


class EventConfig(BaseModel):
    title: str = ""
    date: str = ""
    speakers: list[str] = Field(default_factory=list)

    @property
    def speakers_text(self) -> str:
        return ", ".join(self.speakers)


class ChapterInfo(BaseModel):
    city: str
    tagline: str = "Learn AI Together"
    url: str = ""
    accent_color: str = "#FF6B00"
    logo: str | None = None

    @field_validator("accent_color")
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("accent_color must be a hex color like #FF6B00")
        return value.upper()


class OutputConfig(BaseModel):
    platforms: list[str] = Field(default_factory=list)
    formats: list[ExportFormat] = Field(default_factory=lambda: ["png", "webp"])
    scale: int = 2
    output_dir: str = "output"


class ChapterConfig(BaseModel):
    chapter: ChapterInfo
    event: EventConfig | None = None
    output: OutputConfig = Field(default_factory=OutputConfig)

    @classmethod
    def from_city(cls, city: str, **kwargs) -> "ChapterConfig":
        return cls(chapter=ChapterInfo(city=city, **kwargs))

    def slug(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.chapter.city.lower()).strip("-")
        return slug or "chapter"

    def resolve_logo_path(self, base_dir: Path | None = None) -> Path | None:
        if not self.chapter.logo:
            return None
        path = Path(self.chapter.logo)
        if not path.is_absolute() and base_dir:
            path = (base_dir / path).resolve()
        return path if path.exists() else None

    def field_values(self) -> dict[str, str]:
        values = {
            "city": self.chapter.city,
            "tagline": self.chapter.tagline,
            "url": self.chapter.url,
            "accent_color": self.chapter.accent_color,
        }
        if self.event:
            values["event_title"] = self.event.title
            values["event_date"] = self.event.date
            values["speakers"] = self.event.speakers_text
        else:
            values["event_title"] = ""
            values["event_date"] = ""
            values["speakers"] = ""
        return values


class GenerationConfig(BaseModel):
    config: ChapterConfig
    template_ids: list[str] | None = None
    platforms: list[str] | None = None


class GeneratedAsset(BaseModel):
    platform: str
    template_id: str
    placement: str
    label: str
    width: int
    height: int
    svg_path: Path
    png_path: Path | None = None
    webp_path: Path | None = None


class GenerationResult(BaseModel):
    output_dir: Path
    assets: list[GeneratedAsset]
    zip_path: Path | None = None

    model_config = {"arbitrary_types_allowed": True}


class ValidationIssue(BaseModel):
    template_id: str
    platform: str
    field: str
    message: str
    severity: Literal["warning", "error"] = "warning"