"""Build the small public A-you guide payload from published scenic content."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = ("sun-yat-sen", "qijiang-park")


def build():
    source = json.loads((ROOT / "api/scenics").read_text())
    published = {item["id"]: item["published"] for item in source["workspace"]["scenics"] if item.get("published")}
    scenes = []
    for scene_id in SCENES:
        scene = published[scene_id]
        spots = []
        for spot in scene["spots"]:
            photo = spot.get("photos", {}).get("front", {})
            spots.append({
                "id": spot["id"], "name": spot["name"],
                "description": spot.get("description", ""),
                "guide": spot.get("guide", ""),
                "factSource": spot.get("factSource", ""),
                "photo": photo.get("url", ""),
                "credit": photo.get("credit", {}),
            })
        scenes.append({"id": scene_id, "title": scene["title"], "intro": scene.get("intro", ""), "spots": spots})
    target = ROOT / "assets/ayou/content-v1.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"scenes": scenes}, ensure_ascii=False, separators=(",", ":")))
    print(f"A-you: {len(scenes)} scenes, {sum(len(s['spots']) for s in scenes)} spots, {target.stat().st_size} bytes")


if __name__ == "__main__":
    build()
