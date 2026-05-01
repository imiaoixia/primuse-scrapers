#!/usr/bin/env python3
"""Regenerate index.json and bundle.json from individual source configs."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 1
META_FIELDS = ("id", "name", "version", "icon", "color", "capabilities")


def load_sources():
    sources = []
    for path in sorted(ROOT.glob("*.json")):
        if path.name in {"index.json", "bundle.json"}:
            continue
        with path.open(encoding="utf-8") as f:
            cfg = json.load(f)
        if "id" not in cfg:
            print(f"skip {path.name}: missing id", file=sys.stderr)
            continue
        sources.append((path.name, cfg))
    return sources


def build_index(sources, now):
    return {
        "schema": SCHEMA_VERSION,
        "updatedAt": now,
        "bundleUrl": "bundle.json",
        "sources": [
            {**{k: cfg[k] for k in META_FIELDS if k in cfg}, "url": filename}
            for filename, cfg in sources
        ],
    }


def build_bundle(sources, now):
    return {
        "schema": SCHEMA_VERSION,
        "updatedAt": now,
        "sources": [cfg for _, cfg in sources],
    }


def main():
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    sources = load_sources()
    if not sources:
        print("no source configs found", file=sys.stderr)
        sys.exit(1)

    (ROOT / "index.json").write_text(
        json.dumps(build_index(sources, now), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (ROOT / "bundle.json").write_text(
        json.dumps(build_bundle(sources, now), ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"wrote index.json + bundle.json ({len(sources)} sources, {now})")


if __name__ == "__main__":
    main()
