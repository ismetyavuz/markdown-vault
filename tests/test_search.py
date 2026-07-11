import unittest
import tempfile
import os
from pathlib import Path

from src.git_integration import is_git_repo, get_status, get_diff, stage_and_commit


class TestGitIntegration(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        os.system(f"git init {self._tmpdir}")
        os.system(f"git -C {self._tmpdir} config user.email 'test@test.com'")
        os.system(f"git -C {self._tmpdir} config user.name 'Test'")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_is_git_repo(self):
        self.assertTrue(is_git_repo(self._tmpdir))

    def test_not_git_repo(self):
        self.assertFalse(is_git_repo("/tmp"))

    def test_status_empty(self):
        status = get_status(self._tmpdir)
        self.assertEqual(len(status), 0)

    def test_status_untracked(self):
        Path(self._tmpdir, "test.md").write_text("hello")
        status = get_status(self._tmpdir)
        self.assertTrue(len(status) > 0)

    def test_commit(self):
        Path(self._tmpdir, "test.md").write_text("hello")
        ok, _ = stage_and_commit(self._tmpdir, ["test.md"], "Initial commit")
        self.assertTrue(ok)
        status = get_status(self._tmpdir)
        self.assertEqual(len(status), 0)


if __name__ == "__main__":
    unittest.main()
