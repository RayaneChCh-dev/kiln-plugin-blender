"""Output file names and task ids never collide."""

import base64
import importlib
import sys
import types
from unittest import mock

import pytest
from fpb import naming, net

PROMPT = "Noa, a blocky kid with a mustard hood up, walks to the door"


def test_same_prompt_same_second_gives_different_names():
    with mock.patch.object(naming.time, "time", return_value=1793755827.5):
        first, second = naming.stamp(PROMPT, "mp4"), naming.stamp(PROMPT, "mp4")
    assert first != second
    assert first[:8].isdigit()
    assert first.split("-")[2] == "500"  # milliseconds after the time
    assert "-noa-a-blocky-kid-with-a-mustard-hood-up-" in first
    assert first.endswith(".mp4")


def test_names_keep_date_time_and_slug_first():
    name = naming.stamp("  !!  ", "png")
    date, clock, millis, slug, unique = name.removesuffix(".png").split("-")
    assert (len(date), len(clock), len(millis)) == (8, 6, 3)
    assert slug == "result" and len(unique) == 6


def test_names_sort_by_time():
    with mock.patch.object(naming.time, "time", return_value=1793755827.001):
        early = naming.stamp("zzz", "png")
    with mock.patch.object(naming.time, "time", return_value=1793755827.002):
        late = naming.stamp("aaa", "png")
    assert sorted([late, early]) == [early, late]


def test_claim_never_returns_an_existing_path(tmp_path):
    dest = tmp_path / "a.mp4"
    assert naming.claim(dest) == dest
    assert naming.claim(dest) == tmp_path / "a-2.mp4"
    assert naming.claim(dest) == tmp_path / "a-3.mp4"


def _data_url(payload):
    return "data:video/mp4;base64," + base64.b64encode(payload).decode()


def test_download_does_not_overwrite_an_existing_file(tmp_path):
    dest = tmp_path / "videos" / "clip.mp4"
    dest.parent.mkdir()
    dest.write_bytes(b"first paid clip")
    path = net.download(_data_url(b"second clip"), dest)
    assert path == tmp_path / "videos" / "clip-2.mp4"
    assert dest.read_bytes() == b"first paid clip"
    assert path.read_bytes() == b"second clip"


def test_download_over_http_does_not_overwrite(tmp_path):
    dest = tmp_path / "clip.mp4"
    dest.write_bytes(b"first")
    response = mock.MagicMock()
    response.__enter__.return_value.read.side_effect = [b"second", b""]
    with mock.patch.object(net.urllib.request, "urlopen", return_value=response):
        path = net.download("https://example.invalid/clip.mp4", dest)
    assert (dest.read_bytes(), path.read_bytes()) == (b"first", b"second")


def test_task_ids_are_distinct_and_json_safe():
    with mock.patch.object(naming.time, "time", return_value=1793755827.042):
        ids = [naming.task_id() for _ in range(1000)]
    assert len(set(ids)) == 1000
    assert all(i.replace("-", "").isalnum() and len(i) <= 20 for i in ids)


class _Anything(types.ModuleType):
    """Stand-in for bpy, enough to import the modules: `bpy.types.X` is a class, anything else
    is another stand-in, and calling one returns None."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        if self.__name__ == "bpy.types":
            return type(name, (), {})
        return _Anything(f"{self.__name__}.{name}")

    def __call__(self, *args, **kwargs):
        return None


@pytest.fixture
def bpy_modules(monkeypatch):
    monkeypatch.setitem(sys.modules, "bpy", _Anything("bpy"))
    names = ("fpb.tasks", "fpb.prefs", "fpb.claude_models", "fpb.mcpserver.tools")
    yield lambda name: importlib.import_module(name)
    for name in names:
        sys.modules.pop(name, None)


def test_1000_tasks_in_a_tight_loop_have_distinct_ids(bpy_modules):
    tasks = bpy_modules("fpb.tasks")
    with mock.patch.object(naming.time, "time", return_value=1793755827.042):
        ids = {tasks.Task("video").id for _ in range(1000)}
    assert len(ids) == 1000


def test_task_status_returns_exactly_one_task(bpy_modules):
    tasks = bpy_modules("fpb.tasks")
    tools = bpy_modules("fpb.mcpserver.tools")
    with mock.patch.object(naming.time, "time", return_value=1793755827.042):
        first, second = tasks.Task("video: Noa"), tasks.Task("video: Noa")
    with mock.patch.object(tasks, "TASKS", [second, first]):
        found = tools.task_status(first.id)
        assert [t["id"] for t in found] == [first.id]
        assert len(tools.task_status()) == 2
