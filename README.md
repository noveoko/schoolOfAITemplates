# School of AI: Social Media Graphic Generator

Generate 2026-ready, platform-specific social media assets for School of AI city chapters.

Supports **Facebook, Instagram, LinkedIn, X, YouTube, TikTok, Pinterest, Threads, and Meetup** with correct dimensions, safe zones, and full branding configuration.

## Features

- **27 templates** across 9 platforms (2026 dimensions)
- **Full branding config**: city, tagline, logo, accent color, event title/date, speakers, URL
- **Batch CLI** for chapter packs (PNG, WebP, SVG, ZIP)
- **Web UI** for live preview and download
- **Legacy compatibility**: `python customizesvg.py "Your City"` still works

## Requirements

- Python 3.10+
- Optional: Cairo libraries for faster PNG export via `cairosvg` (falls back to `svglib` automatically)

## Install

```bash
pip install -r requirements.txt
```

## Quick Start (CLI)

```bash
# Quick mode (city name only)
python cli.py generate --quick --city "San Francisco"

# Full config
python cli.py generate --config configs/chapter.example.yaml

# Filter platforms
python cli.py generate --config configs/chapter.example.yaml --platform instagram,linkedin

# List templates
python cli.py list-templates

# Validate config
python cli.py validate --config configs/chapter.example.yaml
```

Legacy entry point:

```bash
python customizesvg.py "Your City Name"
```

## Web UI

```bash
uvicorn web.app:app --reload
```

Open `http://127.0.0.1:8000` to preview templates and download a ZIP pack.

## Configuration

Copy `configs/chapter.example.yaml` and customize:

```yaml
chapter:
  city: "San Francisco"
  tagline: "Learn AI Together"
  url: "https://schoolof.ai/sf"
  accent_color: "#FF6B00"
  logo: "./assets/chapter-logo.png"

event:
  title: "Intro to LLMs"
  date: "March 15, 2026"
  speakers: ["Jane Doe", "John Smith"]

output:
  platforms: [facebook, instagram, linkedin, x, youtube, tiktok, pinterest, threads, meetup]
  formats: [png, webp]
  scale: 2
  output_dir: output
```

## 2026 Platform Templates

| Platform | Templates | Key sizes |
|----------|-----------|-----------|
| Facebook | 7 | 851×315 cover, 360×360 profile, 1200×630 feed, 1080×1920 story, 1920×1005 event |
| Instagram | 4 | 1080×1350 feed (recommended), 1080×1080 square, 1080×1920 story, 320×320 profile |
| LinkedIn | 5 | 1584×396 banner, 1200×627 post, 1200×1200 square, 1128×191 company, 744×400 newsletter |
| X | 3 | 1500×500 header, 400×400 profile, 1600×900 post |
| YouTube | 3 | 2560×1440 channel art, 1280×720 thumbnail, 1080×1920 Shorts |
| TikTok | 2 | 400×400 profile, 1080×1920 cover |
| Pinterest | 1 | 1000×1500 pin |
| Threads | 1 | 1080×1350 feed |
| Meetup | 1 | 600×338 group photo |

Template metadata and safe zones live in [`templates/manifest.yaml`](templates/manifest.yaml).

## Output

Generated assets are written to `output/{chapter-slug}/`:

- `svg/` — customized SVG files
- `png/` — retina-ready PNG exports
- `webp/` — WebP exports
- `manifest.json` — generation metadata
- `school-of-ai-{slug}.zip` — platform-organized download pack

## Adding a Template

1. Add an SVG to `templates/svg/{platform}/{template_id}.svg` with `data-field` placeholders
2. Register it in `templates/manifest.yaml`
3. Run `python cli.py list-templates` to verify

Rebuild migrated/scaffold templates:

```bash
python scripts/build_templates.py
```

## Project Structure

```
src/generator/     # Core rendering engine
templates/         # Manifest + SVG templates
cli.py             # Command-line interface
web/               # FastAPI preview UI
configs/           # Example chapter configs
scripts/           # Template build utilities
```

## Bugs and Feature Requests

Please create an issue and we'll try to resolve it ASAP.