import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio

from .app_window import MainWindow


class MarkdownVaultApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="de.hannemann.markdown-vault",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        win = MainWindow(app)
        win.present()


def main():
    app = MarkdownVaultApp()
    return app.run(sys.argv)
