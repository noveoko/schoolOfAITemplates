from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .exporter import ImageExporter
from .manifest import TEMPLATES_ROOT, iter_templates, load_manifest, resolve_template_path
from .models import ChapterConfig, GeneratedAsset, GenerationConfig, GenerationResult
from .renderer import SVGRenderer


def generate_all(
    generation: GenerationConfig,
    manifest_path: Path | None = None,
    config_dir: Path | None = None,
) -> GenerationResult:
    manifest = load_manifest(manifest_path)
    config = generation.config
    platforms = generation.platforms or config.output.platforms or list(manifest.platforms.keys())
    formats = config.output.formats
    scale = config.output.scale

    slug = config.slug()
    output_root = Path(config.output.output_dir) / slug
    svg_dir = output_root / "svg"
    png_dir = output_root / "png"
    webp_dir = output_root / "webp"

    renderer = SVGRenderer(config, base_dir=config_dir)
    exporter = ImageExporter()
    assets: list[GeneratedAsset] = []
    template_filter = set(generation.template_ids or [])

    for platform_id, template in iter_templates(manifest, platforms):
        if template_filter and template.id not in template_filter:
            continue

        source_svg = resolve_template_path(template)
        rendered = renderer.render(template, source_svg)

        base_name = f"{platform_id}/{template.id}"
        svg_base = svg_dir / base_name
        export_paths = exporter.export(rendered, svg_base, template, formats=formats, scale=scale)

        asset = GeneratedAsset(
            platform=platform_id,
            template_id=template.id,
            placement=template.placement,
            label=template.label or template.placement,
            width=template.width,
            height=template.height,
            svg_path=export_paths["svg"],
            png_path=export_paths.get("png"),
            webp_path=export_paths.get("webp"),
        )

        if asset.png_path:
            target_png = png_dir / f"{base_name}.png"
            target_png.parent.mkdir(parents=True, exist_ok=True)
            asset.png_path.replace(target_png)
            asset.png_path = target_png

        if asset.webp_path:
            target_webp = webp_dir / f"{base_name}.webp"
            target_webp.parent.mkdir(parents=True, exist_ok=True)
            asset.webp_path.replace(target_webp)
            asset.webp_path = target_webp

        assets.append(asset)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chapter": config.chapter.model_dump(),
        "event": config.event.model_dump() if config.event else None,
        "assets": [
            {
                "platform": asset.platform,
                "template_id": asset.template_id,
                "placement": asset.placement,
                "label": asset.label,
                "width": asset.width,
                "height": asset.height,
                "png": str(asset.png_path) if asset.png_path else None,
                "webp": str(asset.webp_path) if asset.webp_path else None,
            }
            for asset in assets
        ],
    }
    (output_root / "manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    zip_path = create_zip(output_root, assets, slug)
    return GenerationResult(output_dir=output_root, assets=assets, zip_path=zip_path)


def create_zip(output_root: Path, assets: list[GeneratedAsset], slug: str) -> Path:
    zip_path = output_root / f"school-of-ai-{slug}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for asset in assets:
            for path in (asset.png_path, asset.webp_path, asset.svg_path):
                if path and path.exists():
                    archive.write(path, arcname=path.relative_to(output_root).as_posix())
        manifest_json = output_root / "manifest.json"
        if manifest_json.exists():
            archive.write(manifest_json, arcname="manifest.json")
    return zip_path


def validate_config(
    generation: GenerationConfig,
    manifest_path: Path | None = None,
    config_dir: Path | None = None,
) -> list:
    from .models import ValidationIssue

    manifest = load_manifest(manifest_path)
    config = generation.config
    platforms = generation.platforms or config.output.platforms or list(manifest.platforms.keys())
    renderer = SVGRenderer(config, base_dir=config_dir)
    issues: list[ValidationIssue] = []

    for platform_id, template in iter_templates(manifest, platforms):
        source_svg = resolve_template_path(template)
        for issue in renderer.validate(template, source_svg):
            issue.platform = platform_id
            issues.append(issue)

        if source_svg.exists():
            soup_text = source_svg.read_text(encoding="utf-8")
            declared_w = f'width="{template.width}"'
            declared_h = f'height="{template.height}"'
            if declared_w not in soup_text or declared_h not in soup_text:
                issues.append(
                    ValidationIssue(
                        template_id=template.id,
                        platform=platform_id,
                        field="dimensions",
                        message=(
                            f"SVG dimensions may not match manifest "
                            f"({template.width}x{template.height})"
                        ),
                        severity="warning",
                    )
                )

    return issues