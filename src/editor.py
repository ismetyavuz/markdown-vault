"""Markdown Vault — GtkSourceView-based Markdown editor.

Provides a self-contained editor widget with syntax highlighting,
line numbers, and file I/O.  Each tab gets its own ``Editor`` instance
so that unsaved buffer state is preserved when switching between files.
"""

import logging
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")

from gi.repository import Gtk, GtkSource, GObject, GLib, Adw

logger = logging.getLogger(__name__)


class Editor(Gtk.ScrolledWindow):
    """A source-code editor widget specialised for Markdown files.

    Signals:
        file-changed(str): Emitted when a file is opened.
        modified-changed(bool): Emitted when the modified flag toggles.
    """

    __gsignals__ = {
        "file-changed": (GObject.SIGNAL_RUN_LAST, None, (str,)),
        "modified-changed": (GObject.SIGNAL_RUN_LAST, None, (bool,)),
        "text-changed": (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self) -> None:
        super().__init__()
        self._file_path: str | None = None
        self._debounce_id: int | None = None

        self._buffer = GtkSource.Buffer()
        self._buffer.connect("modified-changed", self._on_buffer_modified)
        self._buffer.connect("changed", self._on_buffer_changed)

        lang_manager = GtkSource.LanguageManager.get_default()
        md_lang = lang_manager.get_language("markdown")
        if md_lang:
            self._buffer.set_language(md_lang)

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

        self.update_color_scheme()

        self.set_child(self._view)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def file_path(self) -> str | None:
        """Absolute path of the currently loaded file, or ``None``."""
        return self._file_path

    @property
    def is_modified(self) -> bool:
        """Whether the buffer has unsaved changes."""
        return self._buffer.get_modified()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_file(self, path: str) -> None:
        """Load *path* into the editor buffer.

        If the file cannot be read, the buffer is cleared and a warning
        is logged.
        """
        self._file_path = path
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to open %s: %s", path, exc)
            text = ""
        self._buffer.begin_irreversible_action()
        self._buffer.set_text(text)
        self._buffer.end_irreversible_action()
        self._buffer.set_modified(False)
        self.emit("file-changed", path)

    def get_text(self) -> str:
        """Return the full buffer content as a string."""
        start = self._buffer.get_start_iter()
        end = self._buffer.get_end_iter()
        return self._buffer.get_text(start, end, True)

    def save(self) -> bool:
        """Write the buffer to ``file_path``.

        Returns ``True`` on success, ``False`` on failure or when no
        file path is set.
        """
        if not self._file_path:
            return False
        try:
            Path(self._file_path).write_text(self.get_text(), encoding="utf-8")
            self._buffer.set_modified(False)
            return True
        except OSError as exc:
            logger.warning("Failed to save %s: %s", self._file_path, exc)
            return False

    def focus(self) -> None:
        """Move keyboard focus to the text view."""
        self._view.grab_focus()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_buffer_modified(self, _buffer: GtkSource.Buffer) -> None:
        self.emit("modified-changed", self.is_modified)

    def _on_buffer_changed(self, _buffer: GtkSource.Buffer) -> None:
        if self._debounce_id is not None:
            GLib.source_remove(self._debounce_id)
        self._debounce_id = GLib.timeout_add(150, self._emit_text_changed)

    def _emit_text_changed(self) -> bool:
        self._debounce_id = None
        self.emit("text-changed")
        return False

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def update_color_scheme(self) -> None:
        """Switch between ``Adwaita`` and ``Adwaita-dark`` to match the
        current libadwaita colour scheme."""
        scheme_id = "Adwaita-dark" if Adw.StyleManager.get_default().get_dark() else "Adwaita"
        sm = GtkSource.StyleSchemeManager.get_default()
        scheme = sm.get_scheme(scheme_id)
        if scheme:
            self._buffer.set_style_scheme(scheme)
