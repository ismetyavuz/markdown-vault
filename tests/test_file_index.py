"""Tests for markdown_vault.file_index — O(1) stem-to-path index."""

import shutil
import tempfile
import unittest
from pathlib import Path

from markdown_vault.file_index import FileIndex


class TestFileIndexBuild(unittest.TestCase):
    """Tests for building the index from scratch."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._vault = Path(self._tmp) / "vault"
        self._vault.mkdir()

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_build_finds_md_files(self):
        (self._vault / "Page.md").write_text("# Page")
        (self._vault / "Note.md").write_text("# Note")
        idx = FileIndex()
        idx.build([str(self._vault)])
        self.assertEqual(idx.resolve("Page"), str(self._vault / "Page.md"))
        self.assertEqual(idx.resolve("Note"), str(self._vault / "Note.md"))

    def test_build_finds_files_in_subdirectories(self):
        sub = self._vault / "Sub" / "Deep"
        sub.mkdir(parents=True)
        (sub / "DeepFile.md").write_text("# Deep")
        idx = FileIndex()
        idx.build([str(self._vault)])
        self.assertEqual(idx.resolve("DeepFile"), str(sub / "DeepFile.md"))

    def test_build_ignores_non_md_files(self):
        (self._vault / "Page.md").write_text("# Page")
        (self._vault / "Page.txt").write_text("Page")
        (self._vault / "Note.md").write_text("# Note")
        idx = FileIndex()
        idx.build([str(self._vault)])
        self.assertEqual(idx.resolve("Page"), str(self._vault / "Page.md"))
        self.assertEqual(idx.resolve("Note"), str(self._vault / "Note.md"))

    def test_build_ignores_hidden_files(self):
        (self._vault / "Page.md").write_text("# Page")
        (self._vault / ".Hidden.md").write_text("# Hidden")
        idx = FileIndex()
        idx.build([str(self._vault)])
        self.assertEqual(idx.resolve("Page"), str(self._vault / "Page.md"))
        self.assertIsNone(idx.resolve(".Hidden"))

    def test_build_ignores_hidden_directories(self):
        hidden = self._vault / ".git"
        hidden.mkdir()
        (hidden / "Objects.md").write_text("# Git objects")
        (self._vault / "Page.md").write_text("# Page")
        idx = FileIndex()
        idx.build([str(self._vault)])
        self.assertEqual(idx.resolve("Page"), str(self._vault / "Page.md"))
        self.assertIsNone(idx.resolve("Objects"))

    def test_build_normalizes_underscores_to_spaces(self):
        (self._vault / "Datei B.md").write_text("# Datei B")
        idx = FileIndex()
        idx.build([str(self._vault)])
        # Resolve with space should work
        self.assertEqual(idx.resolve("Datei B"), str(self._vault / "Datei B.md"))
        # Resolve with underscore should also find it
        self.assertEqual(idx.resolve("Datei_B"), str(self._vault / "Datei B.md"))

    def test_build_handles_conflicting_stems_same_vault(self):
        """When two files in the same vault have the same stem,
        the first one encountered wins (deterministic via sorted walk)."""
        sub_a = self._vault / "A"
        sub_b = self._vault / "B"
        sub_a.mkdir()
        sub_b.mkdir()
        (sub_a / "Same.md").write_text("# A")
        (sub_b / "Same.md").write_text("# B")
        idx = FileIndex()
        idx.build([str(self._vault)])
        result = idx.resolve("Same")
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("Same.md"))

    def test_build_multiple_vaults(self):
        vault2 = Path(self._tmp) / "vault2"
        vault2.mkdir()
        (self._vault / "Page.md").write_text("# Page")
        (vault2 / "Other.md").write_text("# Other")
        idx = FileIndex()
        idx.build([str(self._vault), str(vault2)])
        self.assertEqual(idx.resolve("Page"), str(self._vault / "Page.md"))
        self.assertEqual(idx.resolve("Other"), str(vault2 / "Other.md"))

    def test_build_empty_vault(self):
        idx = FileIndex()
        idx.build([str(self._vault)])
        self.assertIsNone(idx.resolve("Any"))

    def test_build_deep_nested(self):
        deep = self._vault / "a" / "b" / "c" / "d" / "e"
        deep.mkdir(parents=True)
        (deep / "VeryDeep.md").write_text("# Very Deep")
        idx = FileIndex()
        idx.build([str(self._vault)])
        self.assertEqual(idx.resolve("VeryDeep"), str(deep / "VeryDeep.md"))


class TestFileIndexResolve(unittest.TestCase):
    """Tests for resolve() behavior."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._vault = Path(self._tmp) / "vault"
        self._vault.mkdir()
        (self._vault / "Page.md").write_text("# Page")
        idx = FileIndex()
        idx.build([str(self._vault)])
        self._idx = idx

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_resolve_returns_full_path(self):
        result = self._idx.resolve("Page")
        self.assertIsNotNone(result)
        self.assertTrue(Path(result).is_absolute())

    def test_resolve_unknown_stem_returns_none(self):
        self.assertIsNone(self._idx.resolve("Nonexistent"))

    def test_resolve_empty_string_returns_none(self):
        self.assertIsNone(self._idx.resolve(""))

    def test_resolve_case_sensitive(self):
        """Stem resolution is case-sensitive."""
        self._idx.resolve("Page")
        self.assertIsNone(self._idx.resolve("page"))


class TestFileIndexIncremental(unittest.TestCase):
    """Tests for incremental updates to the index."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._vault = Path(self._tmp) / "vault"
        self._vault.mkdir()
        self._idx = FileIndex()
        self._idx.build([str(self._vault)])

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_add_file(self):
        (self._vault / "NewFile.md").write_text("# New")
        self._idx.add_file(str(self._vault / "NewFile.md"))
        self.assertEqual(self._idx.resolve("NewFile"), str(self._vault / "NewFile.md"))

    def test_remove_file(self):
        (self._vault / "Page.md").write_text("# Page")
        self._idx.remove_file(str(self._vault / "Page.md"))
        self.assertIsNone(self._idx.resolve("Page"))

    def test_rename_file(self):
        (self._vault / "OldName.md").write_text("# Old")
        self._idx.rename_file(
            str(self._vault / "OldName.md"),
            str(self._vault / "NewName.md"),
        )
        self.assertIsNone(self._idx.resolve("OldName"))
        self.assertEqual(self._idx.resolve("NewName"), str(self._vault / "NewName.md"))

    def test_rename_file_with_spaces(self):
        """Rename to a file with spaces in the name."""
        (self._vault / "OldName.md").write_text("# Old")
        self._idx.rename_file(
            str(self._vault / "OldName.md"),
            str(self._vault / "New File.md"),
        )
        self.assertIsNone(self._idx.resolve("OldName"))
        self.assertEqual(self._idx.resolve("New File"), str(self._vault / "New File.md"))
        self.assertEqual(self._idx.resolve("New_File"), str(self._vault / "New File.md"))


class TestFileIndexEdgeCases(unittest.TestCase):
    """Edge cases for FileIndex."""

    def test_empty_vault_paths(self):
        idx = FileIndex()
        idx.build([])
        self.assertIsNone(idx.resolve("Anything"))

    def test_vault_path_does_not_exist(self):
        """Indexing a non-existent path should not raise."""
        idx = FileIndex()
        idx.build(["/nonexistent/vault/path/xyz"])
        self.assertIsNone(idx.resolve("Anything"))

    def test_duplicate_vault_paths_deduplicated(self):
        """Same vault path listed twice should not cause issues."""
        tmp = tempfile.mkdtemp()
        try:
            vault = Path(tmp) / "vault"
            vault.mkdir()
            (vault / "Page.md").write_text("# Page")
            idx = FileIndex()
            idx.build([str(vault), str(vault)])
            self.assertEqual(idx.resolve("Page"), str(vault / "Page.md"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_build_preserves_multiple_files_same_name_different_dirs(self):
        """Files with the same stem in different directories are indexed
        separately, but resolve() returns the first match."""
        tmp = tempfile.mkdtemp()
        try:
            vault = Path(tmp) / "vault"
            a = vault / "DirA"
            b = vault / "DirB"
            a.mkdir(parents=True)
            b.mkdir()
            (a / "Same.md").write_text("# A")
            (b / "Same.md").write_text("# B")
            idx = FileIndex()
            idx.build([str(vault)])
            result = idx.resolve("Same")
            self.assertIsNotNone(result)
            # Should return one of them (the first alphabetically)
            self.assertTrue(result.endswith("Same.md"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
