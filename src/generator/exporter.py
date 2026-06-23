from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from .models import ExportFormat, TemplateSpec


def _export_png_cairosvg(svg_content: str, png_path: Path, width: int, height: int) -> bool:
    try:
        import cairosvg

        cairosvg.svg2png(
            bytestring=svg_content.encode("utf-8"),
            write_to=str(png_path),
            output_width=width,
            output_height=height,
        )
        return True
    except (ImportError, OSError):
        return False


def _export_png_svglib(svg_content: str, png_path: Path, width: int, height: int) -> bool:
    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import svg2rlg

        drawing = svg2rlg(BytesIO(svg_content.encode("utf-8")))
        if drawing is None:
            return False

        scale_x = width / drawing.width
        scale_y = height / drawing.height
        drawing.width = width
        drawing.height = height
        drawing.scale(scale_x, scale_y)
        renderPM.drawToFile(drawing, str(png_path), fmt="PNG")
        return True
    except Exception:
        return False


def render_png_bytes(svg_content: str, width: int, height: int) -> bytes | None:
    temp = BytesIO()
    try:
        import cairosvg

        return cairosvg.svg2png(
            bytestring=svg_content.encode("utf-8"),
            output_width=width,
            output_height=height,
        )
    except (ImportError, OSError):
        pass

    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import svg2rlg

        drawing = svg2rlg(BytesIO(svg_content.encode("utf-8")))
        if drawing is None:
            return None
        scale_x = width / drawing.width
        scale_y = height / drawing.height
        drawing.width = width
        drawing.height = height
        drawing.scale(scale_x, scale_y)
        renderPM.drawToFile(drawing, temp, fmt="PNG")
        return temp.getvalue()
    except Exception:
        return None


class ImageExporter:
    def export(
        self,
        svg_content: str,
        output_base: Path,
        template: TemplateSpec,
        formats: list[ExportFormat] | None = None,
        scale: int | None = None,
    ) -> dict[str, Path]:
        formats = formats or list(template.exports)
        scale = scale or template.scale
        output_base.parent.mkdir(parents=True, exist_ok=True)

        results: dict[str, Path] = {}
        svg_path = output_base.with_suffix(".svg")
        svg_path.write_text(svg_content, encoding="utf-8")
        results["svg"] = svg_path

        width = template.width * scale
        height = template.height * scale
        png_bytes: bytes | None = None

        if "png" in formats:
            png_path = output_base.with_suffix(".png")
            if _export_png_cairosvg(svg_content, png_path, width, height):
                results["png"] = png_path
            elif _export_png_svglib(svg_content, png_path, width, height):
                results["png"] = png_path
            else:
                png_bytes = render_png_bytes(svg_content, width, height)
                if png_bytes:
                    png_path.write_bytes(png_bytes)
                    results["png"] = png_path

        if "webp" in formats:
            webp_path = output_base.with_suffix(".webp")
            if not png_bytes:
                if results.get("png"):
                    image = Image.open(results["png"])
                else:
                    png_bytes = render_png_bytes(svg_content, width, height)
                    if not png_bytes:
                        return results
                    image = Image.open(BytesIO(png_bytes))
            else:
                image = Image.open(BytesIO(png_bytes))
            image.save(webp_path, format="WEBP", quality=90)
            results["webp"] = webp_path

        return results