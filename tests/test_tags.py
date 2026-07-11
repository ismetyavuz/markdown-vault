import unittest
from pathlib import Path

from src.tags import parse_wikilinks, resolve_link, find_backlinks


class TestTags(unittest.TestCase):
    def test_parse_simple(self):
        links = parse_wikilinks("See [[MyPage]] for details.")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], ("MyPage", None))

    def test_parse_alias(self):
        links = parse_wikilinks("See [[MyPage|display]] here.")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], ("MyPage", "display"))

    def test_parse_multiple(self):
        text = "[[A]] and [[B|label]] and [[C]]"
        links = parse_wikilinks(text)
        self.assertEqual(len(links), 3)

    def test_parse_none(self):
        links = parse_wikilinks("No links here.")
        self.assertEqual(len(links), 0)

    def test_resolve_link(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir()
            target = vault / "Page.md"
            target.write_text("# Page")
            current = vault / "Current.md"
            result = resolve_link("Page", current, [str(vault)])
            self.assertEqual(result, target)

    def test_find_backlinks(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / "A.md").write_text("Link to [[B]]")
            (vault / "B.md").write_text("# B")
            backlinks = find_backlinks(vault / "B.md", [str(vault)])
            self.assertEqual(len(backlinks), 1)
            self.assertEqual(backlinks[0].name, "A.md")


if __name__ == "__main__":
    import tempfile
    unittest.main()
