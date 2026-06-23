from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generator import generate_all, load_manifest
from generator.models import ChapterConfig, GenerationConfig
from generator.packager import validate_config


def load_chapter_config(path: Path) -> ChapterConfig:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return ChapterConfig.model_validate(data)


def cmd_generate(args: argparse.Namespace) -> int:
    if args.quick:
        config = ChapterConfig.from_city(args.city or "Test City")
        if args.output_dir:
            config.output.output_dir = args.output_dir
    else:
        config_path = Path(args.config)
        config = load_chapter_config(config_path)
        config_dir = config_path.parent
        if args.output_dir:
            config.output.output_dir = args.output_dir
    else_config_dir = config_dir if not args.quick else None

    platforms = [item.strip() for item in args.platform.split(",")] if args.platform else None
    generation = GenerationConfig(config=config, platforms=platforms)

    result = generate_all(generation, config_dir=else_config_dir if not args.quick else None)

    print(f"Generated {len(result.assets)} assets in {result.output_dir}")
    if result.zip_path:
        print(f"ZIP: {result.zip_path}")
    return 0


def cmd_list_templates(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    rows = []
    for platform_id, platform in manifest.platforms.items():
        for template in platform.templates:
            rows.append(
                {
                    "platform": platform_id,
                    "id": template.id,
                    "label": template.label or template.placement,
                    "size": f"{template.width}x{template.height}",
                    "aspect": template.aspect,
                    "legacy": template.legacy,
                }
            )

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            legacy = " (legacy)" if row["legacy"] else ""
            print(
                f"{row['platform']:12} {row['id']:18} {row['size']:12} "
                f"{row['aspect']:6} {row['label']}{legacy}"
            )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    config = load_chapter_config(config_path)
    platforms = [item.strip() for item in args.platform.split(",")] if args.platform else None
    generation = GenerationConfig(config=config, platforms=platforms)
    issues = validate_config(generation, config_dir=config_path.parent)

    if not issues:
        print("No validation issues found.")
        return 0

    errors = 0
    for issue in issues:
        prefix = issue.severity.upper()
        print(f"[{prefix}] {issue.platform}/{issue.template_id} {issue.field}: {issue.message}")
        if issue.severity == "error":
            errors += 1

    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="School of AI social media template generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate template assets")
    generate_parser.add_argument("--config", help="Path to chapter YAML config")
    generate_parser.add_argument("--city", help="Quick mode: chapter city name")
    generate_parser.add_argument("--quick", action="store_true", help="Quick mode using --city only")
    generate_parser.add_argument("--platform", help="Comma-separated platform filter")
    generate_parser.add_argument("--output-dir", help="Output directory root")
    generate_parser.set_defaults(func=cmd_generate)

    list_parser = subparsers.add_parser("list-templates", help="List available templates")
    list_parser.add_argument("--json", action="store_true", help="Output JSON")
    list_parser.set_defaults(func=cmd_list_templates)

    validate_parser = subparsers.add_parser("validate", help="Validate config against templates")
    validate_parser.add_argument("--config", required=True, help="Path to chapter YAML config")
    validate_parser.add_argument("--platform", help="Comma-separated platform filter")
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate" and not args.quick and not args.config:
        parser.error("generate requires --config or --quick with --city")

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())