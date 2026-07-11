import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")

from gi.repository import Gtk, GtkSource, Gdk, Gio


class Editor(Gtk.ScrolledWindow):
    def __init__(self, on_changed=None):
        super().__init__()
        self._on_changed = on_changed
        self._file_path = None
        self._modified = False

        self._buffer = GtkSource.Buffer()
        self._buffer.connect("modified-changed", self._on_modified_changed)

        lang_manager = GtkSource.LanguageManager.get_default()
        lang = lang_manager.get_language("markdown")
        if lang:
            self._buffer.set_language(lang)

        scheme_manager = GtkSource.StyleSchemeManager.get_default()
        scheme = scheme_manager.get_scheme("Adwaita")
        if scheme:
            self._buffer.set_style_scheme(scheme)

        self._view = GtkSource.View(buffer=self._buffer)
        self._view.set_monospace(True)
        self._view.set_show_line_numbers(True)
        self._view.set_show_line_marks(True)
        self._view.set_auto_indent(True)
        self._view.set_indent_on_tab(True)
        self._view.set_tab_width(4)
        self._view.set_insert_spaces_instead_of_tabs(True)
        self._view.set_wrap_mode(Gtk.WrapMode.WORD)
        self._view.set_left_margin(12)
        self._view.set_right_margin(12)
        self._view.set_top_margin(8)
        self._view.set_bottom_margin(8)

        self._view.add_css_class("editor-view")

        self.set_child(self._view)

    def _on_modified_changed(self, buffer):
        mod = buffer.get_modified()
        if mod != self._modified:
            self._modified = mod

    @property
    def file_path(self):
        return self._file_path

    @property
    def is_modified(self):
        return self._modified

    def open_file(self, path: str):
        self._file_path = path
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            text = ""
        self._buffer.set_text(text)
        self._buffer.set_modified(False)
        self._modified = False

    def get_text(self) -> str:
        start = self._buffer.get_start_iter()
        end = self._buffer.get_end_iter()
        return self._buffer.get_text(start, end, True)

    def save(self) -> bool:
        if not self._file_path:
            return False
        try:
            text = self.get_text()
            with open(self._file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self._buffer.set_modified(False)
            self._modified = False
            return True
        except Exception:
            return False

    def focus(self):
        self._view.grab_focus()
