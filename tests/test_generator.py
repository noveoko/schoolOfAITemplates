from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generator import load_manifest
from generator.manifest import iter_templates, resolve_template_path
from generator.models import ChapterConfig
from generator.renderer import SVGRenderer


def test_manifest_loads_all_templates():
    manifest = load_manifest()
    templates = list(iter_templates(manifest))
    assert len(templates) >= 25
    for platform_id, template in templates:
        path = resolve_template_path(template)
        assert path.exists(), f"Missing template file: {path}"


def test_renderer_substitutes_fields(tmp_path: Path):
    manifest = load_manifest()
    _, template = next(
        item for item in iter_templates(manifest) if item[1].id == "feed_portrait" and item[0] == "instagram"
    )
    config = ChapterConfig.from_city("Testville", tagline="AI Builders", url="schoolof.ai/test")
    renderer = SVGRenderer(config)
    rendered = renderer.render(template, resolve_template_path(template))
    assert "Testville" in rendered
    assert "AI Builders" in rendered
    assert "schoolof.ai/test" in rendered


def test_example_config_parses():
    config_path = PROJECT_ROOT / "configs" / "chapter.example.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = ChapterConfig.model_validate(data)
    assert config.chapter.city == "San Francisco"
    assert config.event is not None
    assert len(config.event.speakers) == 2