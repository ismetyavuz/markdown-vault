import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, GLib, GObject


class Tab:
    def __init__(self, file_path: str, title: str, editor, preview):
        self.file_path = file_path
        self.title = title
        self.editor = editor
        self.preview = preview
        self.view_mode = "edit"


class TabBar(Gtk.Box):
    __gsignals__ = {
        "tab-changed": (GObject.SIGNAL_RUN_LAST, None, (str,)),
        "tab-closed": (GObject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, on_tab_changed=None, on_tab_closed=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._on_tab_changed = on_tab_changed
        self._on_tab_closed = on_tab_closed
        self._tabs: dict[str, Tab] = {}
        self._current_path: str | None = None

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._box.add_css_class("tab-bar")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._box)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.HORIZONTAL, Gtk.PolicyType.NEVER)
        self.append(scrolled)

    def add_tab(self, file_path: str, editor, preview) -> Tab:
        if file_path in self._tabs:
            self.set_active_tab(file_path)
            return self._tabs[file_path]

        from pathlib import Path
        title = Path(file_path).name
        tab = Tab(file_path, title, editor, preview)
        self._tabs[file_path] = tab

        btn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn.add_css_class("tab")
        btn.set_margin_top(4)
        btn.set_margin_bottom(4)
        btn.set_margin_start(2)
        btn.set_margin_end(2)

        label = Gtk.Label(label=title)
        label.set_ellipsize(3)
        btn.append(label)

        close_btn = Gtk.Button(icon_name="window-close-symbolic")
        close_btn.add_css_class("flat")
        close_btn.add_css_class("circular")
        close_btn.set_size_request(24, 24)
        close_btn.connect("clicked", lambda _b, p=file_path: self._close_tab(p))
        btn.append(close_btn)

        btn._file_path = file_path
        event_box = Gtk.GestureClick()
        event_box.connect("released", lambda _g, _n, _x, _y, p=file_path: self.set_active_tab(p))
        btn.add_controller(event_box)

        self._box.append(btn)
        self.set_active_tab(file_path)
        return tab

    def set_active_tab(self, file_path: str):
        if file_path not in self._tabs:
            return
        self._current_path = file_path
        for child in self._box:
            if hasattr(child, "_file_path"):
                child.add_css_class("tab")
                is_active = child._file_path == file_path
                if is_active:
                    child.add_css_class("active")
                else:
                    child.remove_css_class("active")
        if self._on_tab_changed:
            self._on_tab_changed(file_path)

    def _close_tab(self, file_path: str):
        if file_path in self._tabs:
            tab = self._tabs.pop(file_path)
            for child in self._box:
                if hasattr(child, "_file_path") and child._file_path == file_path:
                    self._box.remove(child)
                    break
            if self._on_tab_closed:
                self._on_tab_closed(file_path)
            if self._current_path == file_path:
                remaining = list(self._tabs.keys())
                if remaining:
                    self.set_active_tab(remaining[-1])
                else:
                    self._current_path = None

    def get_current_tab(self) -> Tab | None:
        if self._current_path and self._current_path in self._tabs:
            return self._tabs[self._current_path]
        return None

    def get_current_path(self) -> str | None:
        return self._current_path

    def has_tabs(self) -> bool:
        return len(self._tabs) > 0

    def get_all_paths(self) -> list[str]:
        return list(self._tabs.keys())
