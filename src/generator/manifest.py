from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .models import Manifest, TemplateSpec

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "templates" / "manifest.yaml"
TEMPLATES_ROOT = PROJECT_ROOT / "templates" / "svg"


@lru_cache(maxsize=1)
def load_manifest(path: Path | None = None) -> Manifest:
    manifest_path = path or DEFAULT_MANIFEST_PATH
    with open(manifest_path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Manifest.model_validate(data)


def iter_templates(manifest: Manifest, platforms: list[str] | None = None) -> list[tuple[str, TemplateSpec]]:
    selected = {platform.lower() for platform in platforms} if platforms else None
    results: list[tuple[str, TemplateSpec]] = []
    for platform_id, platform in manifest.platforms.items():
        if selected and platform_id.lower() not in selected:
            continue
        for template in platform.templates:
            results.append((platform_id, template))
    return results


def resolve_template_path(template: TemplateSpec) -> Path:
    return TEMPLATES_ROOT / template.file


def template_key(platform_id: str, template: TemplateSpec) -> str:
    return f"{platform_id}/{template.id}"


def template_lookup(manifest: Manifest) -> dict[str, tuple[str, TemplateSpec]]:
    lookup: dict[str, tuple[str, TemplateSpec]] = {}
    for platform_id, template in iter_templates(manifest):
        lookup[template_key(platform_id, template)] = (platform_id, template)
        lookup[template.id] = (platform_id, template)
    return lookup