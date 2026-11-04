"""Unique names for output files and background tasks (no bpy).

Two generations can finish in the same second with the same prompt, and two tasks
can start in the same millisecond: neither may share a name or an id.
"""

from __future__ import annotations

import itertools
import os
import re
import time
import uuid
from pathlib import Path

_task_ids = itertools.count(1)  # next() is atomic under the GIL, so safe across worker threads


def stamp(prompt, ext):
    """`YYYYMMDD-HHMMSS-mmm-<slug>-<unique>.<ext>`: date and time first, so names sort by time."""
    slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:40].strip("-") or "result"
    now = time.time()
    millis = int(now * 1000) % 1000
    unique = uuid.uuid4().hex[:6]
    return f"{time.strftime('%Y%m%d-%H%M%S', time.localtime(now))}-{millis:03d}-{slug}-{unique}.{ext}"


def claim(dest: Path) -> Path:
    """Create `dest` empty and return it; if it exists, the first free `<stem>-2`, `-3`… instead.

    The file is created atomically (O_EXCL), so two downloads can never get the same path.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    for n in itertools.count(1):
        path = dest if n == 1 else dest.with_name(f"{dest.stem}-{n}{dest.suffix}")
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
        except FileExistsError:
            continue
        return path
    raise AssertionError("unreachable")


def task_id():
    """Short, JSON-safe and unique within the session: millisecond clock in hex, then a counter."""
    return f"{int(time.time() * 1000):x}-{next(_task_ids)}"
