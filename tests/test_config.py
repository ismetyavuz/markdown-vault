import unittest
from pathlib import Path
import tempfile
import os

from src.config import load_vaults, save_vaults, add_vault, remove_vault


class TestConfig(unittest.TestCase):
    def setUp(self):
        self._orig_config_dir = None
        import src.config as cfg
        self._cfg = cfg
        self._tmpdir = tempfile.mkdtemp()
        self._cfg.CONFIG_DIR = Path(self._tmpdir)
        self._cfg.CONFIG_FILE = Path(self._tmpdir) / "vaults.yaml"

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_empty(self):
        result = load_vaults()
        self.assertEqual(result, [])

    def test_save_and_load(self):
        vaults = [{"name": "Notes", "path": "/tmp/notes"}]
        save_vaults(vaults)
        loaded = load_vaults()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["name"], "Notes")

    def test_add_vault(self):
        add_vault("Work", "/tmp/work")
        loaded = load_vaults()
        self.assertEqual(len(loaded), 1)

    def test_remove_vault(self):
        add_vault("Work", "/tmp/work")
        remove_vault("/tmp/work")
        loaded = load_vaults()
        self.assertEqual(len(loaded), 0)

    def test_deduplication(self):
        save_vaults([
            {"name": "A", "path": "/tmp/a"},
            {"name": "B", "path": "/tmp/a"},
        ])
        loaded = load_vaults()
        self.assertEqual(len(loaded), 1)


if __name__ == "__main__":
    unittest.main()
