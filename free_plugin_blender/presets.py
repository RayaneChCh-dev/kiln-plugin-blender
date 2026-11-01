"""The Meshy animation library (`data/animations.json`) and its search. No bpy."""

from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).with_name("data") / "animations.json"
CATEGORIES = (
    ("ALL", "All"),
    ("WalkAndRun", "Walk & run"),
    ("BodyMovements", "Body"),
    ("DailyActions", "Daily"),
    ("Fighting", "Fighting"),
    ("Dancing", "Dancing"),
)
PRESET_COST = "≈ $0.32"  # fal-ai/meshy/rigging with an animation: the rig is redone each time
# key, label, price, fal.ai endpoint. All take the same input and return an SMPL-H FBX; the first is the default.
MOTION_MODELS = (
    ("hunyuan", "Hunyuan Motion", "≈ $0.08", "fal-ai/hunyuan-motion"),
    ("hunyuan_fast", "Hunyuan Motion Fast", "≈ $0.06", "fal-ai/hunyuan-motion/fast"),
)
MOTION_DURATIONS = ((2.0, "Quick"), (3.0, "Short"), (5.0, "Normal"), (8.0, "Long"), (12.0, "Maximum"))

_cache: list[dict] | None = None


def motion_model(key: str) -> dict:
    """The motion model of `key`, or the default one when it is unknown."""
    entry = next((m for m in MOTION_MODELS if m[0] == key), MOTION_MODELS[0])
    return dict(zip(("key", "label", "cost", "endpoint"), entry))


def all_presets() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = json.loads(PATH.read_text())["presets"]
    return _cache


def get(preset_id: int) -> dict | None:
    return next((p for p in all_presets() if p["id"] == preset_id), None)


def search(query="", category="ALL", in_place_only=False, presets=None) -> list[dict]:
    """Presets whose name, sub-category or category contain every word of the query."""
    words = query.lower().split()
    found = []
    for preset in all_presets() if presets is None else presets:
        if category != "ALL" and preset["category"] != category:
            continue
        if in_place_only and not preset["in_place"]:
            continue
        haystack = f"{preset['name']} {preset['sub']} {preset['category']}".lower()
        if all(word in haystack for word in words):
            found.append(preset)
    return sorted(found, key=lambda p: (p["category"], p["sub"], p["name"]))
