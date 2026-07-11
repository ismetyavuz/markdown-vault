"""Markdown Vault — application entry point.

Creates the ``Adw.Application`` instance and launches the main window.
Run this module directly with ``python3 -m src.main``.
"""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from .app_window import MainWindow


class MarkdownVaultApp(Adw.Application):
    """Top-level application object."""

    def __init__(self) -> None:
        super().__init__(
            application_id="de.hannemann.markdown-vault",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.connect("activate", self._on_activate)
        self._setup_accels()

    def _setup_accels(self) -> None:
        """Register global keyboard shortcuts."""
        self.set_accels_for_action("win.toggle-sidebar", ["<Control>b"])
        self.set_accels_for_action("win.toggle-search", ["<Control>f"])
        self.set_accels_for_action("win.save", ["<Control>s"])
        self.set_accels_for_action("win.close-tab", ["<Control>w"])

    def _on_activate(self, app: "MarkdownVaultApp") -> None:
        """Present the main window when the application is activated."""
        win = MainWindow(app)
        win.present()


def main() -> int:
    """Application entry point."""
    app = MarkdownVaultApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
