#!/usr/bin/env python3
"""Regenerate index.json and bundle.json from individual source configs."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 1
META_FIELDS = ("id", "name", "version", "icon", "color", "capabilities")


def load_sources(directory=ROOT, schema=SCHEMA_VERSION):
    sources = []
    for path in sorted(directory.glob("*.json")):
        if path.name in {"index.json", "bundle.json"} or ".secrets." in path.name:
            continue
        with path.open(encoding="utf-8") as f:
            cfg = json.load(f)
        if cfg.get("secrets"):
            raise ValueError(f"{path.name}: private parameters cannot be published")
        if "id" not in cfg:
            print(f"skip {path.name}: missing id", file=sys.stderr)
            continue
        if schema >= 2:
            def validate(value):
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key.lower() in {"script", "requestscript", "responsescript", "playlistscript", "cookie", "secrets", "authorization", "proxy-authorization", "x-api-key"}:
                            raise ValueError(f"{path.name}: unsupported executable or private field: {key}")
                        validate(item)
                elif isinstance(value, list):
                    for item in value:
                        validate(item)
            validate(cfg)
        sources.append((path.name, cfg))
    return sources


def build_index(sources, now, schema=SCHEMA_VERSION):
    return {
        "schema": schema,
        "updatedAt": now,
        "bundleUrl": "bundle.json",
        "sources": [
            {**{k: cfg[k] for k in META_FIELDS if k in cfg}, "url": filename}
            for filename, cfg in sources
        ],
    }


def build_bundle(sources, now, schema=SCHEMA_VERSION):
    return {
        "schema": schema,
        "updatedAt": now,
        "sources": [cfg for _, cfg in sources],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default=".", help="Source subdirectory")
    parser.add_argument("--schema", type=int, choices=[1, 2], default=1)
    parser.add_argument("--entry", help="Optional bundle filename at the repository root")
    args = parser.parse_args()
    directory = (ROOT / args.directory).resolve()
    if not directory.is_relative_to(ROOT) or not directory.is_dir():
        parser.error("directory must exist inside the repository")
    if args.entry and (Path(args.entry).name != args.entry or not args.entry.endswith(".json")):
        parser.error("entry must be a JSON filename")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    sources = load_sources(directory, args.schema)
    if not sources:
        print("no source configs found", file=sys.stderr)
        sys.exit(1)

    (directory / "index.json").write_text(
        json.dumps(build_index(sources, now, args.schema), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (directory / "bundle.json").write_text(
        json.dumps(build_bundle(sources, now, args.schema), ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    if args.entry:
        (ROOT / args.entry).write_text((directory / "bundle.json").read_text(encoding="utf-8"), encoding="utf-8")
    print(f"wrote index.json + bundle.json ({len(sources)} sources, {now})")


if __name__ == "__main__":
    main()
