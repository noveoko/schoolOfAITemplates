"""Migrate legacy SVGs and generate scaffold templates."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = PROJECT_ROOT / "Social_Media_Assets" / "original_templates"
SVG_ROOT = PROJECT_ROOT / "templates" / "svg"

LEGACY_MAP = {
    "Facebook_Fan_Page_Header.svg": "facebook/page_cover.svg",
    "Facebook_Fan_Page_Square_Image.svg": "facebook/profile_legacy.svg",
    "Facebook_Group_Cover_Photo.svg": "facebook/group_cover.svg",
    "Facebook_Group_Header.svg": "facebook/group_header.svg",
    "Linkedin_Post_Header_Image.svg": "linkedin/post_landscape.svg",
    "TwitterProfileHeader.svg": "x/header.svg",
    "TwitterProfilePicture.svg": "x/profile.svg",
    "Meetupcom_Group_Photo.svg": "meetup/group_photo.svg",
}

DEFAULTS = {
    "city": "Warsaw",
    "tagline": "Learn AI Together",
    "event_title": "Intro to LLMs",
    "event_date": "March 15, 2026",
    "url": "schoolof.ai/chapter",
    "speakers": "Jane Doe, John Smith",
    "accent_color": "#FF6B00",
    "background": "#1A1A2E",
}


def patch_legacy_svg(source: Path, destination: Path) -> None:
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "xml")

    for block in soup.find_all("text"):
        tspan = block.find("tspan", id="tspan165")
        if tspan and tspan.get_text(strip=True):
            block["data-field"] = "city"
            tspan.string = DEFAULTS["city"]
        title = block.find("title", id="title169")
        if title:
            title.string = DEFAULTS["city"]

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(str(soup), encoding="utf-8")


def scaffold_svg(
    destination: Path,
    width: int,
    height: int,
    fields: list[str],
    title: str,
) -> None:
    accent = DEFAULTS["accent_color"]
    bg = DEFAULTS["background"]

    logo_block = ""
    if "logo" in fields:
        logo_size = min(width, height) // 5
        logo_x = width * 0.08
        logo_y = height * 0.12
        logo_block = (
            f'<image data-field="logo" x="{logo_x}" y="{logo_y}" '
            f'width="{logo_size}" height="{logo_size}" '
            f'preserveAspectRatio="xMidYMid meet" href="" />'
        )

    text_blocks = []
    y_cursor = height * 0.45
    x_text = width * 0.08
    max_text_width = width * 0.84

    field_styles = {
        "city": ("School of AI", 0.09, "bold"),
        "tagline": (DEFAULTS["tagline"], 0.04, "normal"),
        "event_title": (DEFAULTS["event_title"], 0.055, "bold"),
        "event_date": (DEFAULTS["event_date"], 0.038, "normal"),
        "speakers": (DEFAULTS["speakers"], 0.032, "normal"),
        "url": (DEFAULTS["url"], 0.03, "normal"),
    }

    for field in ["city", "tagline", "event_title", "event_date", "speakers", "url"]:
        if field not in fields:
            continue
        label, size_ratio, weight = field_styles[field]
        font_size = max(16, int(height * size_ratio))
        y_cursor += font_size * 1.4
        text_blocks.append(
            f'<text data-field="{field}" x="{x_text}" y="{y_cursor}" '
            f'fill="#FFFFFF" font-family="Arial, Helvetica, sans-serif" '
            f'font-size="{font_size}px" font-weight="{weight}">'
            f"<tspan>{label}</tspan></text>"
        )

    accent_height = max(8, int(height * 0.012))
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="{bg}"/>
  <rect data-field="accent_color" x="0" y="{height - accent_height}" width="{width}" height="{accent_height}" fill="{accent}"/>
  <rect data-field="accent_color" x="0" y="0" width="{int(width * 0.06)}" height="{height}" fill="{accent}" opacity="0.85"/>
  {logo_block}
  <text x="{x_text}" y="{height * 0.18}" fill="#AAAAAA" font-family="Arial, Helvetica, sans-serif" font-size="{max(12, int(height * 0.025))}px">{title}</text>
  {''.join(text_blocks)}
</svg>
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def resize_svg_canvas(source: Path, destination: Path, width: int, height: int) -> None:
    text = source.read_text(encoding="utf-8")
    text = re.sub(r'width="[0-9.]+"', f'width="{width}"', text, count=1)
    text = re.sub(r'height="[0-9.]+"', f'height="{height}"', text, count=1)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


SCAFFOLDS = [
    ("facebook/feed_image.svg", 1200, 630, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Facebook Feed"),
    ("facebook/story.svg", 1080, 1920, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Facebook Story"),
    ("facebook/event_cover.svg", 1920, 1005, ["city", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Facebook Event"),
    ("facebook/profile.svg", 360, 360, ["city", "logo", "accent_color"], "Facebook Profile"),
    ("instagram/feed_portrait.svg", 1080, 1350, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Instagram Feed"),
    ("instagram/feed_square.svg", 1080, 1080, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Instagram Square"),
    ("instagram/story.svg", 1080, 1920, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Instagram Story"),
    ("instagram/profile.svg", 320, 320, ["city", "logo", "accent_color"], "Instagram Profile"),
    ("linkedin/personal_banner.svg", 1584, 396, ["city", "tagline", "url", "logo", "accent_color"], "LinkedIn Banner"),
    ("linkedin/post_square.svg", 1200, 1200, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "LinkedIn Square"),
    ("linkedin/company_banner.svg", 1128, 191, ["city", "tagline", "url", "logo", "accent_color"], "LinkedIn Company"),
    ("linkedin/newsletter.svg", 744, 400, ["city", "tagline", "event_title", "logo", "accent_color"], "LinkedIn Newsletter"),
    ("x/post_image.svg", 1600, 900, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "X Post"),
    ("youtube/channel_art.svg", 2560, 1440, ["city", "tagline", "url", "logo", "accent_color"], "YouTube Channel"),
    ("youtube/thumbnail.svg", 1280, 720, ["city", "event_title", "event_date", "logo", "accent_color", "speakers"], "YouTube Thumbnail"),
    ("youtube/shorts_cover.svg", 1080, 1920, ["city", "tagline", "event_title", "logo", "accent_color"], "YouTube Shorts"),
    ("tiktok/profile.svg", 400, 400, ["city", "logo", "accent_color"], "TikTok Profile"),
    ("tiktok/cover.svg", 1080, 1920, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "TikTok Cover"),
    ("pinterest/standard_pin.svg", 1000, 1500, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Pinterest Pin"),
    ("threads/feed_portrait.svg", 1080, 1350, ["city", "tagline", "event_title", "event_date", "url", "logo", "accent_color", "speakers"], "Threads Feed"),
]


def main() -> None:
    for legacy_name, target_rel in LEGACY_MAP.items():
        source = LEGACY_DIR / legacy_name
        target = SVG_ROOT / target_rel
        if not source.exists():
            print(f"skip missing legacy: {legacy_name}")
            continue
        patch_legacy_svg(source, target)
        print(f"migrated {legacy_name} -> {target_rel}")

    legacy_profile = SVG_ROOT / "facebook/profile_legacy.svg"
    fb_profile = SVG_ROOT / "facebook/profile.svg"
    if legacy_profile.exists() and not fb_profile.exists():
        resize_svg_canvas(legacy_profile, fb_profile, 360, 360)
        print("resized facebook profile to 360x360")

    for rel_path, width, height, fields, title in SCAFFOLDS:
        destination = SVG_ROOT / rel_path
        if destination.exists():
            continue
        scaffold_svg(destination, width, height, fields, title)
        print(f"scaffolded {rel_path}")

    linkedin_post = SVG_ROOT / "linkedin/post_landscape.svg"
    if linkedin_post.exists():
        text = linkedin_post.read_text(encoding="utf-8")
        if 'height="644"' in text:
            text = text.replace('height="644"', 'height="627"', 1)
            linkedin_post.write_text(text, encoding="utf-8")
            print("updated linkedin post landscape height to 627")


if __name__ == "__main__":
    main()