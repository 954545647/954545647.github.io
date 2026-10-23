"""Merge a draft scene package (scenic.json + photos + map) into the visitor workspace at api/scenics.

Usage: python3 tools/add_scenic.py scenes/<scene-id>

The visitor build reads every scene from api/scenics, so this script converts the package to the
same schema-7 entry the existing five scenes use, copies the photos and map image under
/assets/scenics/<id>/, and replaces any previous entry with the same id.
"""
import json
import shutil
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
API = SITE / "api" / "scenics"
SPOT_KEYS = ("id", "name", "description", "guide", "notice", "x", "y", "factSource", "heading", "scene", "narration")
CREDIT_KEYS = ("title", "url", "source", "license", "licenseUrl", "artist", "date", "description", "path",
               "retrieved", "changes")


def convert(pkg: Path):
    draft = json.loads((pkg / "scenic.json").read_text(encoding="utf-8"))
    sid = draft["id"]
    published = draft["published"]
    dest = SITE / "assets" / "scenics" / sid

    map_src = pkg / "map.png"
    map_url = published["map"]["url"]
    (SITE / map_url.lstrip("/")).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(map_src, SITE / map_url.lstrip("/"))

    spots = []
    for raw in published["spots"]:
        spot = {k: raw[k] for k in SPOT_KEYS}
        front = raw["photos"]["front"]
        credit = front["credit"]
        target = SITE / front["url"].lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pkg / credit["localFile"], target)
        spot["photos"] = {"front": {
            "url": front["url"],
            "name": front["name"],
            "kind": "real",
            "credit": {
                "title": credit["title"],
                "url": credit["url"],
                "source": credit["source"],
                "license": credit["license"],
                "licenseUrl": credit["licenseUrl"],
                "artist": credit["artist"],
                "date": credit["date"],
                "description": f"{raw['name']} · Wikimedia Commons",
                "path": front["url"],
                "retrieved": credit["retrieved"],
                "changes": "缩放至 1280px 宽；页面缩略图按容器裁切。",
            },
            "accepted": True,
        }}
        spot["revision"] = 0
        spot["confirmedRevision"] = None
        spot["world"] = None
        spots.append(spot)

    entry = {
        "schema": 7,
        "id": sid,
        "publishNumber": draft.get("publishNumber") or 1,
        "publishedAt": draft.get("publishedAt"),
        "published": {"title": published["title"], "intro": published["intro"],
                      "map": {k: published["map"][k] for k in ("url", "name", "legend", "custom")},
                      "spots": spots},
    }
    if published.get("mapPackage"):
        entry["published"]["mapPackage"] = published["mapPackage"]
    return sid, entry, dest


def main():
    pkg = Path(sys.argv[1]).resolve()
    sid, entry, dest = convert(pkg)
    data = json.loads(API.read_text(encoding="utf-8"))
    scenics = [s for s in data["workspace"]["scenics"] if s["id"] != sid]
    scenics.append(entry)
    data["workspace"]["scenics"] = scenics
    API.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    copied = sum(1 for p in dest.rglob("*") if p.is_file())
    print(f"{sid}: {len(entry['published']['spots'])} spots, {copied} asset files, "
          f"workspace now has {len(scenics)} scenes")


if __name__ == "__main__":
    main()
