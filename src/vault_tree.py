import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, GLib, GdkPixbuf, GObject


FILE_ICON = "text-x-generic-symbolic"
FOLDER_ICON = "folder-symbolic"
FOLDER_OPEN_ICON = "folder-open-symbolic"
MARKDOWN_ICON = "text-x-preview-symbolic"


def _file_sort_key(model, iter_a, iter_b, _data):
    name_a = model.get_value(iter_a, 0)
    name_b = model.get_value(iter_b, 0)
    is_dir_a = model.get_value(iter_a, 2)
    is_dir_b = model.get_value(iter_b, 2)
    if is_dir_a and not is_dir_b:
        return -1
    if not is_dir_a and is_dir_b:
        return 1
    return GLib.strcmp0(name_a.lower(), name_b.lower())


class VaultTree(Gtk.Box):
    __gsignals__ = {
        "file-selected": (GObject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, on_file_selected=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._on_file_selected = on_file_selected
        self._vault_paths: list[str] = []

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.set_margin_top(6)
        header.set_margin_bottom(6)
        header.set_margin_start(8)
        header.set_margin_end(8)

        title = Gtk.Label(label="Vaults")
        title.add_css_class("heading")
        title.set_xalign(0)
        title.set_hexpand(True)
        header.append(title)

        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.add_css_class("flat")
        add_btn.add_css_class("circular")
        add_btn.set_tooltip_text("Add vault")
        add_btn.connect("clicked", self._on_add_vault)
        header.append(add_btn)

        self.append(header)

        self._store = Gtk.TreeStore(str, str, bool, str, str)
        self._store.set_sort_func(0, _file_sort_key, None)
        self._store.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self._tree_view = Gtk.TreeView(model=self._store)
        self._tree_view.set_headers_visible(False)
        self._tree_view.set_activate_on_single_click(True)
        self._tree_view.connect("row-activated", self._on_row_activated)

        renderer_text = Gtk.CellRendererText()
        renderer_text.set_property("ellipsize", 3)
        column = Gtk.TreeViewColumn()
        column.pack_start(renderer_text, True)
        column.add_attribute(renderer_text, "text", 0)
        self._tree_view.append_column(column)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._tree_view)
        scrolled.set_vexpand(True)
        self.append(scrolled)

    def set_vaults(self, vault_paths: list[str]):
        self._vault_paths = vault_paths
        self._store.clear()
        for vp in vault_paths:
            self._add_directory(Path(vp), None)

    def _add_directory(self, path: Path, parent_iter):
        dir_iter = self._store.append(parent_iter, [path.name, str(path), True, FOLDER_ICON, ""])
        try:
            entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                self._add_directory(entry, dir_iter)
            elif entry.suffix.lower() == ".md":
                self._store.append(dir_iter, [entry.name, str(entry), False, FILE_ICON, "markdown"])

    def _on_row_activated(self, tree_view, path, column):
        iter_ = self._store.get_iter(path)
        is_dir = self._store.get_value(iter_, 2)
        if not is_dir:
            file_path = self._store.get_value(iter_, 1)
            if self._on_file_selected:
                self._on_file_selected(file_path)

    def _on_add_vault(self, _btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Vault Directory")
        dialog.select_folder(None, None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if folder:
            path = folder.get_path()
            if path and path not in self._vault_paths:
                self._vault_paths.append(path)
                self._add_directory(Path(path), None)
                self.emit("file-selected", path)

    def refresh(self):
        self.set_vaults(self._vault_paths)

    def get_vault_paths(self) -> list[str]:
        return list(self._vault_paths)
