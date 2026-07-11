import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GLib, GObject

from .vault_tree import VaultTree
from .editor import Editor
from .preview import Preview
from .tabs import TabBar
from .sidebar import Sidebar
from .search import SearchBar
from . import config


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Markdown Vault")
        self.set_default_size(1200, 800)

        self._view_mode = "edit"

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(vbox)

        toolbar = self._build_toolbar()
        vbox.append(toolbar)

        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_wide_handle(True)

        self._vault_tree = VaultTree(on_file_selected=self._on_file_selected)
        self._vault_tree.connect("file-selected", self._on_vault_path_added)
        main_paned.set_start_child(self._vault_tree)
        main_paned.set_resize_start_child(True)
        main_paned.set_shrink_start_child(False)

        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._tab_bar = TabBar(
            on_tab_changed=self._on_tab_changed,
            on_tab_closed=self._on_tab_closed,
        )
        center_box.append(self._tab_bar)

        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        center_box.append(self._content_stack)

        self._editor = Editor()
        self._preview = Preview()
        self._split_box = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self._split_box.set_start_child(self._editor)
        self._split_box.set_end_child(self._preview)
        self._split_box.set_position(600)

        self._content_stack.add_named(self._editor, "edit")
        self._content_stack.add_named(self._preview, "render")
        self._content_stack.add_named(self._split_box, "split")
        self._content_stack.set_visible_child_name("edit")

        main_paned.set_end_child(center_box)
        main_paned.set_resize_end_child(True)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        outer_box.append(main_paned)

        self._sidebar = Sidebar()
        self._sidebar.connect("file-open-requested", self._on_file_open_requested)
        outer_box.append(self._sidebar)

        vbox.append(outer_box)

        self._search_bar = SearchBar(get_vault_paths=self._vault_tree.get_vault_paths)
        self._search_bar.connect("file-selected", self._on_file_selected)
        vbox.append(self._search_bar)

        self._setup_actions()
        self._load_vaults()

    def _build_toolbar(self):
        header = Adw.HeaderBar()

        self._menu_btn = Gtk.MenuButton()
        self._menu_btn.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append("Add Vault", "win.add-vault")
        menu.append("Toggle Sidebar", "win.toggle-sidebar")
        menu.append("Toggle Search", "win.toggle-search")
        menu.append("Preferences", "win.preferences")
        self._menu_btn.set_menu_model(menu)
        header.pack_end(self._menu_btn)

        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        for mode, icon, tooltip in [
            ("edit", "document-edit-symbolic", "Edit"),
            ("render", "document-properties-symbolic", "Render"),
            ("split", "view-dual-symbolic", "Split"),
        ]:
            btn = Gtk.ToggleButton(icon_name=icon)
            btn.set_tooltip_text(tooltip)
            btn.set_group(None)
            btn._mode = mode
            btn.connect("toggled", self._on_view_mode_toggled)
            if mode == "edit":
                btn.set_active(True)
            view_box.append(btn)
        header.set_title_widget(view_box)

        return header

    def _setup_actions(self):
        action = Gio.SimpleAction.new("add-vault", None)
        action.connect("activate", lambda *_: self._on_add_vault())
        self.add_action(action)

        action = Gio.SimpleAction.new("toggle-sidebar", None)
        action.connect("activate", lambda *_: self._toggle_sidebar())
        self.add_action(action)
        self.set_accels_for_action("win.toggle-sidebar", ["<Control>b"])

        action = Gio.SimpleAction.new("toggle-search", None)
        action.connect("activate", lambda *_: self._toggle_search())
        self.add_action(action)
        self.set_accels_for_action("win.toggle-search", ["<Control>f"])

        action = Gio.SimpleAction.new("save", None)
        action.connect("activate", lambda *_: self._save_current())
        self.add_action(action)
        self.set_accels_for_action("win.save", ["<Control>s"])

        action = Gio.SimpleAction.new("close-tab", None)
        action.connect("activate", lambda *_: self._close_current_tab())
        self.add_action(action)
        self.set_accels_for_action("win.close-tab", ["<Control>w"])

    def _load_vaults(self):
        vaults = config.load_vaults()
        paths = [v["path"] for v in vaults]
        self._vault_tree.set_vaults(paths)
        self._sidebar.set_vault_paths(paths)

    def _on_file_selected(self, file_path: str):
        tab = self._tab_bar.add_tab(file_path, self._editor, self._preview)
        self._editor.open_file(file_path)
        self._update_preview()
        self._sidebar.update_for_file(file_path, self._editor.get_text())

    def _on_tab_changed(self, file_path: str):
        tab = self._tab_bar.get_current_tab()
        if tab:
            self._editor.open_file(file_path)
            self._update_preview()
            self._sidebar.update_for_file(file_path, self._editor.get_text())

    def _on_tab_closed(self, file_path: str):
        if not self._tab_bar.has_tabs():
            self._editor._buffer.set_text("")
            self._editor._file_path = None
            self._sidebar.update_for_file(None)

    def _on_view_mode_toggled(self, toggle_btn):
        if toggle_btn.get_active():
            mode = toggle_btn._mode
            self._view_mode = mode
            self._content_stack.set_visible_child_name(mode)
            if mode in ("render", "split"):
                self._update_preview()

    def _on_vault_path_added(self, _tree, path: str):
        vaults = config.load_vaults()
        if not any(v["path"] == path for v in vaults):
            from pathlib import Path
            name = Path(path).name
            config.add_vault(name, path)
            self._sidebar.set_vault_paths(self._vault_tree.get_vault_paths())

    def _on_add_vault(self):
        pass

    def _toggle_sidebar(self):
        self._sidebar.set_visible(not self._sidebar.get_visible())

    def _toggle_search(self):
        self._search_bar.focus()

    def _update_preview(self):
        text = self._editor.get_text()
        base_dir = ""
        if self._editor.file_path:
            from pathlib import Path
            base_dir = str(Path(self._editor.file_path).parent)
        self._preview.update_from_text(text, base_dir)
        self._sidebar.update_for_file(self._editor.file_path, text)

    def _save_current(self):
        self._editor.save()

    def _close_current_tab(self):
        path = self._tab_bar.get_current_path()
        if path:
            self._tab_bar._close_tab(path)

    def _on_file_open_requested(self, _sidebar, file_path: str):
        self._on_file_selected(file_path)
