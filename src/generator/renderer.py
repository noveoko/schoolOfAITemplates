from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

from bs4 import BeautifulSoup

from .models import ChapterConfig, TemplateSpec, ValidationIssue

MIN_FONT_SIZE = 8
FONT_STEP = 1


class SVGRenderer:
    def __init__(self, config: ChapterConfig, base_dir: Path | None = None):
        self.config = config
        self.base_dir = base_dir
        self.values = config.field_values()

    def render(self, template: TemplateSpec, source_svg: Path) -> str:
        with open(source_svg, encoding="utf-8") as handle:
            soup = BeautifulSoup(handle.read(), "xml")

        self._apply_data_fields(soup, template)
        self._apply_legacy_fallback(soup)
        self._apply_logo(soup)
        self._apply_accent_color(soup)
        self._hide_empty_optional_fields(soup, template)
        self._fit_text_to_safe_zone(soup, template)

        return str(soup)

    def validate(self, template: TemplateSpec, source_svg: Path) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        values = self.values

        if "logo" in template.fields and not self.config.resolve_logo_path(self.base_dir):
            issues.append(
                ValidationIssue(
                    template_id=template.id,
                    platform="",
                    field="logo",
                    message="Logo path is missing or file does not exist",
                    severity="warning",
                )
            )

        for field_name in ("city", "tagline", "event_title", "url"):
            if field_name not in template.fields:
                continue
            value = values.get(field_name, "")
            if not value:
                continue
            limit = self._max_chars_for_field(field_name, template)
            if len(value) > limit:
                issues.append(
                    ValidationIssue(
                        template_id=template.id,
                        platform="",
                        field=field_name,
                        message=f"{field_name} is {len(value)} chars; recommended max is {limit}",
                        severity="warning",
                    )
                )

        if not source_svg.exists():
            issues.append(
                ValidationIssue(
                    template_id=template.id,
                    platform="",
                    field="file",
                    message=f"Template file not found: {source_svg}",
                    severity="error",
                )
            )

        return issues

    def _apply_data_fields(self, soup: BeautifulSoup, template: TemplateSpec) -> None:
        for element in soup.find_all(attrs={"data-field": True}):
            field = element.get("data-field")
            if not field or field not in template.fields:
                if field in {"event_title", "event_date", "speakers", "tagline", "url"}:
                    element["display"] = "none"
                    if element.name != "g":
                        element.decompose()
                continue

            value = self.values.get(field, "")
            if field == "logo":
                continue
            if field == "accent_color":
                continue

            self._set_element_text(element, value)

    def _apply_legacy_fallback(self, soup: BeautifulSoup) -> None:
        if soup.find(attrs={"data-field": "city"}):
            return
        for block in soup.find_all("text"):
            tspan = block.find("tspan", id="tspan165")
            if tspan and tspan.string:
                tspan.string.replace_with(self.values["city"])
            title = block.find("title", id="title169")
            if title:
                title.string = self.values["city"]

    def _apply_logo(self, soup: BeautifulSoup) -> None:
        logo_path = self.config.resolve_logo_path(self.base_dir)
        logo_elements = soup.find_all(attrs={"data-field": "logo"})
        if not logo_elements:
            return

        if not logo_path:
            for element in logo_elements:
                element.decompose()
            return

        mime, _ = mimetypes.guess_type(logo_path.name)
        mime = mime or "image/png"
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        href = f"data:{mime};base64,{encoded}"

        for element in logo_elements:
            element["href"] = href
            element["xlink:href"] = href

    def _apply_accent_color(self, soup: BeautifulSoup) -> None:
        color = self.values.get("accent_color", "#FF6B00")
        for element in soup.find_all(attrs={"data-field": "accent_color"}):
            if element.has_attr("fill") and element["fill"] not in {"none", "transparent"}:
                element["fill"] = color
            if element.has_attr("stroke") and element["stroke"] not in {"none", "transparent"}:
                element["stroke"] = color

    def _hide_empty_optional_fields(self, soup: BeautifulSoup, template: TemplateSpec) -> None:
        optional_fields = {"tagline", "event_title", "event_date", "speakers", "url"}
        for field in optional_fields:
            if field not in template.fields:
                continue
            if self.values.get(field):
                continue
            for element in soup.find_all(attrs={"data-field": field}):
                parent = element.parent
                element.decompose()
                if parent and parent.name == "g" and not parent.find(True):
                    parent.decompose()

    def _fit_text_to_safe_zone(self, soup: BeautifulSoup, template: TemplateSpec) -> None:
        if not template.safe_zone:
            return

        max_width = template.safe_zone.w * 0.92
        for element in soup.find_all(["text", "tspan"]):
            if element.get("data-field") not in {"city", "tagline", "event_title", "url", "speakers"}:
                if element.name == "text" and not element.get("data-field"):
                    continue
            font_size = self._current_font_size(element)
            while font_size > MIN_FONT_SIZE:
                estimated = self._estimate_text_width(element, font_size)
                if estimated <= max_width:
                    break
                font_size -= FONT_STEP
                self._set_font_size(element, font_size)

    def _set_element_text(self, element, value: str) -> None:
        tspan = element.find("tspan")
        if tspan:
            tspan.string = value
            return
        if element.string is not None:
            element.string.replace_with(value)
        else:
            element.clear()
            element.append(value)

    def _current_font_size(self, element) -> float:
        style = element.get("style", "")
        match = re.search(r"font-size:([0-9.]+)px", style)
        if match:
            return float(match.group(1))
        if element.has_attr("font-size"):
            return float(str(element["font-size"]).replace("px", ""))
        return 24.0

    def _set_font_size(self, element, size: float) -> None:
        style = element.get("style", "")
        if "font-size:" in style:
            element["style"] = re.sub(r"font-size:[0-9.]+px", f"font-size:{size}px", style)
        else:
            element["style"] = (style + f";font-size:{size}px").strip(";")

    def _estimate_text_width(self, element, font_size: float) -> float:
        text = element.get_text(strip=True)
        return len(text) * font_size * 0.55

    def _max_chars_for_field(self, field_name: str, template: TemplateSpec) -> int:
        width = template.width
        defaults = {
            "city": int(width / 18),
            "tagline": int(width / 12),
            "event_title": int(width / 14),
            "url": int(width / 10),
        }
        return defaults.get(field_name, 80)