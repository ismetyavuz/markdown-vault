import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, GObject


class SearchBar(Gtk.Box):
    __gsignals__ = {
        "file-selected": (GObject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, get_vault_paths=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._get_vault_paths = get_vault_paths
        self.set_visible(False)

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        input_box.set_margin_top(6)
        input_box.set_margin_bottom(6)
        input_box.set_margin_start(8)
        input_box.set_margin_end(8)

        self._entry = Gtk.SearchEntry()
        self._entry.set_hexpand(True)
        self._entry.connect("activate", self._on_search)
        self._entry.connect("stop-search", lambda _e: self.set_visible(False))
        input_box.append(self._entry)

        search_btn = Gtk.Button(label="Search")
        search_btn.connect("clicked", self._on_search)
        input_box.append(search_btn)

        self.append(input_box)

        self._results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._results_box)
        scrolled.set_max_content_height(300)
        self.append(scrolled)

    def focus(self):
        self.set_visible(True)
        self._entry.grab_focus()

    def _on_search(self, _widget=None):
        query = self._entry.get_text().strip()
        for child in list(self._results_box):
            self._results_box.remove(child)
        if not query or not self._get_vault_paths:
            return
        results = self._search_vaults(query)
        if not results:
            lbl = Gtk.Label(label="No results found")
            lbl.set_xalign(0)
            lbl.set_margin_start(8)
            lbl.set_margin_top(4)
            self._results_box.append(lbl)
            return
        for filepath, line_num, line_text in results[:50]:
            btn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            btn.add_css_class("search-result")
            btn.set_margin_start(4)
            btn.set_margin_end(4)

            loc = Gtk.Label(label=f"{Path(filepath).name}:{line_num}")
            loc.add_css_class("dim-label")
            loc.set_xalign(0)
            btn.append(loc)

            preview = Gtk.Label(label=line_text.strip()[:100])
            preview.set_xalign(0)
            preview.set_ellipsize(3)
            btn.append(preview)

            event = Gtk.GestureClick()
            event.connect("released", lambda _g, _n, _x, _y, p=filepath: self.emit("file-selected", p))
            btn.add_controller(event)

            self._results_box.append(btn)

    def _search_vaults(self, query: str) -> list[tuple[str, int, str]]:
        results = []
        query_lower = query.lower()
        for vault_path in self._get_vault_paths():
            for root, _dirs, files in os.walk(vault_path):
                for fname in files:
                    if not fname.endswith(".md"):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            for i, line in enumerate(f, 1):
                                if query_lower in line.lower():
                                    results.append((fpath, i, line))
                    except Exception:
                        continue
        return results
