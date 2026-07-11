import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, GObject

from . import git_integration, tags
from pathlib import Path


class Sidebar(Gtk.Box):
    __gsignals__ = {
        "file-open-requested": (GObject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_size_request(250, -1)
        self.set_visible(False)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.append(self._stack)

        self._outline_page = self._build_outline_page()
        self._stack.add_titled(self._outline_page, "outline", "Outline")

        self._backlinks_page = self._build_backlinks_page()
        self._stack.add_titled(self._backlinks_page, "backlinks", "Backlinks")

        self._git_page = self._build_git_page()
        self._stack.add_titled(self._git_page, "git", "Git")

        self._details_page = self._build_details_page()
        self._stack.add_titled(self._details_page, "details", "Details")

        switcher = Gtk.StackSwitcher(stack=self._stack)
        switcher.set_margin_top(6)
        switcher.set_margin_bottom(6)
        self.append(switcher)

        self._current_file: str | None = None
        self._vault_paths: list[str] = []

    def _build_outline_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._outline_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._outline_list.set_margin_top(8)
        self._outline_list.set_margin_start(8)
        self._outline_list.set_margin_end(8)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._outline_list)
        scrolled.set_vexpand(True)
        box.append(scrolled)
        return box

    def _build_backlinks_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._backlinks_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._backlinks_list.set_margin_top(8)
        self._backlinks_list.set_margin_start(8)
        self._backlinks_list.set_margin_end(8)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._backlinks_list)
        scrolled.set_vexpand(True)
        box.append(scrolled)
        return box

    def _build_git_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        self._git_status_label = Gtk.Label(label="No git repo")
        self._git_status_label.set_xalign(0)
        self._git_status_label.set_wrap(True)
        box.append(self._git_status_label)

        self._git_diff_label = Gtk.Label(label="")
        self._git_diff_label.set_xalign(0)
        self._git_diff_label.set_wrap(True)
        self._git_diff_label.add_css_class("mono")
        box.append(self._git_diff_label)

        return box

    def _build_details_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        self._details_label = Gtk.Label(label="No file open")
        self._details_label.set_xalign(0)
        self._details_label.set_wrap(True)
        box.append(self._details_label)

        return box

    def set_vault_paths(self, paths: list[str]):
        self._vault_paths = list(paths)

    def update_for_file(self, file_path: str | None, text: str = ""):
        self._current_file = file_path
        self._update_outline(file_path, text)
        self._update_backlinks(file_path)
        self._update_git(file_path)
        self._update_details(file_path, text)

    def _update_outline(self, file_path: str | None, text: str):
        for child in list(self._outline_list):
            self._outline_list.remove(child)
        if not text:
            return
        import re
        for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE):
            level = len(match.group(1))
            heading = match.group(2)
            btn = Gtk.Label(label=f"{'  ' * (level - 1)}{heading}")
            btn.set_xalign(0)
            btn.add_css_class("outline-item")
            btn.set_size_request(-1, 28)
            self._outline_list.append(btn)

    def _update_backlinks(self, file_path: str | None):
        for child in list(self._backlinks_list):
            self._backlinks_list.remove(child)
        if not file_path or not self._vault_paths:
            lbl = Gtk.Label(label="No backlinks")
            lbl.set_xalign(0)
            self._backlinks_list.append(lbl)
            return
        backlinks = tags.find_backlinks(Path(file_path), self._vault_paths)
        if not backlinks:
            lbl = Gtk.Label(label="No backlinks found")
            lbl.set_xalign(0)
            self._backlinks_list.append(lbl)
            return
        for bl in backlinks:
            btn = Gtk.Button(label=bl.name)
            btn.add_css_class("flat")
            btn.set_xalign(0)
            btn.connect("clicked", lambda _b, p=str(bl): self.emit("file-open-requested", p))
            self._backlinks_list.append(btn)

    def _update_git(self, file_path: str | None):
        if not file_path:
            self._git_status_label.set_text("No file open")
            self._git_diff_label.set_text("")
            return
        from pathlib import Path
        repo_dir = Path(file_path).parent
        if not git_integration.is_git_repo(repo_dir):
            self._git_status_label.set_text("Not a git repository")
            self._git_diff_label.set_text("")
            return
        status = git_integration.get_status(repo_dir)
        if status:
            lines = [f"{e['status']} {e['path']}" for e in status]
            self._git_status_label.set_text("\n".join(lines))
        else:
            self._git_status_label.set_text("Working tree clean")
        diff = git_integration.get_diff(repo_dir)
        self._git_diff_label.set_text(diff[:2000] if diff else "")

    def _update_details(self, file_path: str | None, text: str):
        if not file_path:
            self._details_label.set_text("No file open")
            return
        p = Path(file_path)
        stat = p.stat()
        words = len(text.split()) if text else 0
        lines = text.count("\n") + 1 if text else 0
        from datetime import datetime
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        info = (
            f"File: {p.name}\n"
            f"Path: {p.parent}\n"
            f"Words: {words}\n"
            f"Lines: {lines}\n"
            f"Size: {stat.st_size} bytes\n"
            f"Modified: {modified}"
        )
        self._details_label.set_text(info)
