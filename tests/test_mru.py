"""Tests for MRU tab management (src/mru.py)."""

import tempfile
import unittest
from pathlib import Path

from src.mru import MRUManager, MRUSwitcher


class TestMRUManager(unittest.TestCase):
    """Tests for the MRUManager business logic."""

    def setUp(self):
        self.mru = MRUManager()
        self._tmp = tempfile.mkdtemp()
        self._files = []
        for name in ("a.md", "b.md", "c.md"):
            p = Path(self._tmp) / name
            p.touch()
            self._files.append(str(p))

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _path(self, idx: int) -> str:
        return self._files[idx]

    # ── push ────────────────────────────────────────────────────────

    def test_push_adds_to_list(self):
        self.mru.push(self._path(0))
        self.assertEqual(self.mru.tabs, [self._path(0)])

    def test_push_moves_to_front(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.mru.push(self._path(2))
        self.assertEqual(self.mru.tabs, [
            self._path(2), self._path(1), self._path(0),
        ])

    def test_push_moves_existing_to_front(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.mru.push(self._path(0))
        self.assertEqual(self.mru.tabs, [self._path(0), self._path(1)])

    def test_push_resets_position(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.mru.push(self._path(2))
        self.mru.next()
        self.mru.push(self._path(1))
        self.assertEqual(self.mru.pos, 0)

    def test_push_returns_copy(self):
        self.mru.push(self._path(0))
        tabs = self.mru.tabs
        tabs.append("/x.md")
        self.assertEqual(self.mru.tabs, [self._path(0)])

    # ── next / prev ────────────────────────────────────────────────

    def test_next_returns_none_when_empty(self):
        self.assertIsNone(self.mru.next())

    def test_next_returns_none_with_one_tab(self):
        self.mru.push(self._path(0))
        self.assertIsNone(self.mru.next())

    def test_next_advances_position(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.mru.push(self._path(2))
        result = self.mru.next()
        self.assertEqual(result, self._path(1))
        self.assertEqual(self.mru.pos, 1)

    def test_next_clamps_at_end(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.mru.next()  # pos=1
        result = self.mru.next()  # already at end
        self.assertEqual(result, self._path(0))
        self.assertEqual(self.mru.pos, 1)

    def test_prev_returns_none_at_start(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.assertIsNone(self.mru.prev())

    def test_prev_goes_back(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.mru.push(self._path(2))
        self.mru.next()  # pos=1
        result = self.mru.prev()
        self.assertEqual(result, self._path(2))
        self.assertEqual(self.mru.pos, 0)

    def test_next_returns_none_for_missing_file(self):
        self.mru.push("/nonexistent_file_xyz.md")
        self.mru.push(self._path(0))
        # MRU = [a.md, nonexistent], pos=0, next tries pos=1 = missing → None
        result = self.mru.next()
        self.assertIsNone(result)

    # ── list_for_switcher ──────────────────────────────────────────

    def test_list_for_switcher_returns_copy(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        result = self.mru.list_for_switcher()
        result.append("/x.md")
        self.assertEqual(self.mru.tabs, [self._path(1), self._path(0)])

    def test_list_for_switcher_order(self):
        self.mru.push(self._path(0))
        self.mru.push(self._path(1))
        self.mru.push(self._path(2))
        self.assertEqual(self.mru.list_for_switcher(), [
            self._path(2), self._path(1), self._path(0),
        ])

    def test_list_for_switcher_empty(self):
        self.assertEqual(self.mru.list_for_switcher(), [])


class TestMRUSwitcherStructure(unittest.TestCase):
    """Structural tests for the MRUSwitcher GTK widget."""

    def _source(self) -> str:
        return (Path(__file__).resolve().parent.parent / "src" / "mru.py").read_text(
            encoding="utf-8"
        )

    def test_module_has_mru_switcher_class(self):
        self.assertIn("class MRUSwitcher", self._source())

    def test_has_is_open_classmethod(self):
        self.assertIn("def is_open(cls)", self._source())

    def test_has_instance_class_attribute(self):
        self.assertIn("_instance", self._source())

    def test_has_commit_method(self):
        self.assertIn("def _commit(self)", self._source())

    def test_has_cancel_method(self):
        self.assertIn("def _cancel(self)", self._source())

    def test_has_key_pressed_handler(self):
        self.assertIn("def _on_key_pressed(self", self._source())

    def test_has_key_released_handler(self):
        self.assertIn("def _on_key_released(self", self._source())

    def test_has_close_request_handler(self):
        self.assertIn("def _on_close_request(self", self._source())

    def test_singleton_resets_on_close(self):
        self.assertIn("MRUSwitcher._instance = None", self._source())

    def test_ctrl_release_commits(self):
        src = self._source()
        self.assertIn("KEY_Control_L", src)
        self.assertIn("KEY_Control_R", src)


class TestMRUManagerSingleton(unittest.TestCase):
    """Test MRUSwitcher._instance class-level singleton tracking."""

    def setUp(self):
        self._saved = MRUSwitcher._instance

    def tearDown(self):
        MRUSwitcher._instance = self._saved

    def test_is_open_false_initially(self):
        MRUSwitcher._instance = None
        self.assertFalse(MRUSwitcher.is_open())

    def test_is_open_true_when_set(self):
        MRUSwitcher._instance = "fake"
        self.assertTrue(MRUSwitcher.is_open())


if __name__ == "__main__":
    unittest.main()
