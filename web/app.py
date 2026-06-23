from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generator import load_manifest
from generator.exporter import render_png_bytes
from generator.manifest import iter_templates, resolve_template_path, template_key, template_lookup
from generator.models import ChapterConfig, ChapterInfo, EventConfig, GenerationConfig, OutputConfig
from generator.packager import create_zip, generate_all
from generator.renderer import SVGRenderer

app = FastAPI(title="School of AI Template Generator")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def _parse_speakers(raw: str) -> list[str]:
    if not raw.strip():
        return []
    if raw.strip().startswith("["):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return [item.strip() for item in raw.split(",") if item.strip()]


def _build_config(
    city: str,
    tagline: str,
    url: str,
    accent_color: str,
    event_title: str,
    event_date: str,
    speakers: str,
    platforms: list[str],
    logo_path: str | None = None,
) -> ChapterConfig:
    event = None
    if event_title or event_date or speakers:
        event = EventConfig(
            title=event_title,
            date=event_date,
            speakers=_parse_speakers(speakers),
        )

    return ChapterConfig(
        chapter=ChapterInfo(
            city=city,
            tagline=tagline,
            url=url,
            accent_color=accent_color,
            logo=logo_path,
        ),
        event=event,
        output=OutputConfig(
            platforms=platforms,
            formats=["png", "webp"],
            scale=1,
            output_dir="output",
        ),
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    manifest = load_manifest()
    platform_options = [
        {"id": platform_id, "label": platform.label}
        for platform_id, platform in manifest.platforms.items()
    ]
    template_options = []
    for platform_id, template in iter_templates(manifest):
        template_options.append(
            {
                "id": template.id,
                "key": template_key(platform_id, template),
                "platform": platform_id,
                "label": template.label or template.placement,
                "size": f"{template.width}x{template.height}",
            }
        )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "platforms": platform_options,
            "template_options": template_options,
            "defaults": {
                "city": "San Francisco",
                "tagline": "Learn AI Together",
                "url": "https://schoolof.ai/sf",
                "accent_color": "#FF6B00",
                "event_title": "Intro to LLMs",
                "event_date": "March 15, 2026",
                "speakers": "Jane Doe, John Smith",
            },
        },
    )


@app.get("/api/templates")
async def api_templates() -> JSONResponse:
    manifest = load_manifest()
    payload = []
    for platform_id, platform in manifest.platforms.items():
        payload.append(
            {
                "id": platform_id,
                "label": platform.label,
                "templates": [
                    {
                        "id": template.id,
                        "key": template_key(platform_id, template),
                        "label": template.label or template.placement,
                        "width": template.width,
                        "height": template.height,
                        "aspect": template.aspect,
                        "safe_zone": template.safe_zone.model_dump() if template.safe_zone else None,
                    }
                    for template in platform.templates
                ],
            }
        )
    return JSONResponse(payload)


@app.post("/api/preview")
async def api_preview(
    city: str = Form(...),
    tagline: str = Form("Learn AI Together"),
    url: str = Form(""),
    accent_color: str = Form("#FF6B00"),
    event_title: str = Form(""),
    event_date: str = Form(""),
    speakers: str = Form(""),
    template_id: str = Form(...),
    show_safe_zone: str = Form("false"),
    logo: UploadFile | None = File(None),
) -> Response:
    manifest = load_manifest()
    lookup = template_lookup(manifest)
    if template_id not in lookup:
        return JSONResponse({"error": "Unknown template"}, status_code=404)

    platform_id, template = lookup[template_id]
    logo_path = None
    temp_dir = Path(tempfile.mkdtemp(prefix="soai-preview-"))

    if logo and logo.filename:
        logo_path = temp_dir / logo.filename
        logo_path.write_bytes(await logo.read())

    config = _build_config(
        city=city,
        tagline=tagline,
        url=url,
        accent_color=accent_color,
        event_title=event_title,
        event_date=event_date,
        speakers=speakers,
        platforms=[platform_id],
        logo_path=str(logo_path) if logo_path else None,
    )

    renderer = SVGRenderer(config, base_dir=temp_dir)
    svg_content = renderer.render(template, resolve_template_path(template))

    if show_safe_zone.lower() in {"true", "1", "on", "yes"} and template.safe_zone:
        zone = template.safe_zone
        overlay = (
            f'<rect x="{zone.x}" y="{zone.y}" width="{zone.w}" height="{zone.h}" '
            f'fill="none" stroke="#00FF88" stroke-width="4" stroke-dasharray="12 8" />'
        )
        svg_content = svg_content.replace("</svg>", f"{overlay}</svg>")

    png_bytes = render_png_bytes(svg_content, template.width, template.height)
    if not png_bytes:
        return JSONResponse({"error": "Failed to render preview"}, status_code=500)

    return Response(content=png_bytes, media_type="image/png")


@app.post("/api/generate")
async def api_generate(
    city: str = Form(...),
    tagline: str = Form("Learn AI Together"),
    url: str = Form(""),
    accent_color: str = Form("#FF6B00"),
    event_title: str = Form(""),
    event_date: str = Form(""),
    speakers: str = Form(""),
    platforms: str = Form(""),
    logo: UploadFile | None = File(None),
) -> Response:
    selected_platforms = [item.strip() for item in platforms.split(",") if item.strip()]
    temp_dir = Path(tempfile.mkdtemp(prefix="soai-generate-"))
    logo_path = None

    if logo and logo.filename:
        logo_path = temp_dir / logo.filename
        logo_path.write_bytes(await logo.read())

    config = _build_config(
        city=city,
        tagline=tagline,
        url=url,
        accent_color=accent_color,
        event_title=event_title,
        event_date=event_date,
        speakers=speakers,
        platforms=selected_platforms or list(load_manifest().platforms.keys()),
        logo_path=str(logo_path) if logo_path else None,
    )
    config.output.scale = 1

    result = generate_all(
        GenerationConfig(config=config, platforms=selected_platforms or None),
        config_dir=temp_dir,
    )

    if not result.zip_path or not result.zip_path.exists():
        return JSONResponse({"error": "Failed to create ZIP"}, status_code=500)

    return Response(
        content=result.zip_path.read_bytes(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="school-of-ai-{config.slug()}.zip"'
        },
    )