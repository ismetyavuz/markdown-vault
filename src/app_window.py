"""Markdown Vault — main application window.

Assembles the three-panel layout (vault tree | editor/preview | sidebar),
the tab bar, and the bottom search bar.  Each open file gets its own
``Editor`` and ``Preview`` instance so that buffer state and scroll
position are preserved across tab switches.

Dark mode is controlled via ``Adw.StyleManager`` and exposed through
the hamburger menu.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio

from .vault_tree import VaultTree
from .editor import Editor
from .preview import Preview
from .tabs import TabBar
from .sidebar import Sidebar
from .search import SearchBar
from . import config


def _apply_theme(color_scheme: int) -> None:
    """Set the application-wide colour scheme."""
    Adw.StyleManager.get_default().set_color_scheme(color_scheme)


class MainWindow(Adw.ApplicationWindow):
    """Top-level application window."""

    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title="Markdown Vault")
        self.set_default_size(1200, 800)

        self._view_mode: str = "edit"
        self._setup_complete = False

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(root)

        root.append(self._build_header())

        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_wide_handle(True)

        self._vault_tree = VaultTree()
        self._vault_tree.connect("file-selected", self._on_file_selected_from_tree)
        main_paned.set_start_child(self._vault_tree)
        main_paned.set_resize_start_child(True)
        main_paned.set_shrink_start_child(False)

        centre = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._tab_bar = TabBar()
        self._tab_bar.connect("tab-changed", self._on_tab_changed)
        self._tab_bar.connect("tab-closed", self._on_tab_closed)
        centre.append(self._tab_bar)

        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        centre.append(self._content_stack)

        main_paned.set_end_child(centre)
        main_paned.set_resize_end_child(True)

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        outer.append(main_paned)

        self._sidebar = Sidebar()
        self._sidebar.connect("file-open-requested", self._on_sidebar_file_requested)
        outer.append(self._sidebar)

        root.append(outer)

        self._search_bar = SearchBar(get_vault_paths=self._vault_tree.get_vault_paths)
        self._search_bar.connect("file-selected", self._on_search_result_selected)
        root.append(self._search_bar)

        self._register_actions()
        self._load_vaults()

        # Mark setup complete so toggles stop firing.
        self._setup_complete = True

    # ── Header ─────────────────────────────────────────────────────

    def _build_header(self) -> Adw.HeaderBar:
        header = Adw.HeaderBar()

        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        group = None
        for mode, icon, tooltip in (
            ("edit", "document-edit-symbolic", "Edit"),
            ("render", "document-properties-symbolic", "Render"),
            ("split", "view-dual-symbolic", "Split"),
        ):
            btn = Gtk.ToggleButton(icon_name=icon)
            btn.set_tooltip_text(tooltip)
            if group is None:
                group = btn
            else:
                btn.set_group(group)
            btn._mode = mode  # type: ignore[attr-defined]
            btn.connect("toggled", self._on_view_mode_toggled)
            if mode == "edit":
                btn.set_active(True)
            view_box.append(btn)
        header.set_title_widget(view_box)

        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()

        theme_section = Gio.Menu()
        theme_section.append("Follow System", "win.theme-system")
        theme_section.append("Light Mode", "win.theme-light")
        theme_section.append("Dark Mode", "win.theme-dark")
        menu.append_section(None, theme_section)

        action_section = Gio.Menu()
        action_section.append("Add Vault", "win.add-vault")
        action_section.append("Toggle Sidebar", "win.toggle-sidebar")
        action_section.append("Full-Text Search", "win.toggle-search")
        menu.append_section(None, action_section)

        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        return header

    # ── Actions (keyboard shortcuts are set on the App) ────────────

    def _register_actions(self) -> None:
        for name, scheme in (
            ("theme-system", Adw.ColorScheme.DEFAULT),
            ("theme-light", Adw.ColorScheme.FORCE_LIGHT),
            ("theme-dark", Adw.ColorScheme.FORCE_DARK),
        ):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _a, s=scheme: _apply_theme(s))
            self.add_action(action)

        action = Gio.SimpleAction.new("add-vault", None)
        action.connect("activate", lambda *_: self._vault_tree._on_add_vault_clicked(None))
        self.add_action(action)

        action = Gio.SimpleAction.new("toggle-sidebar", None)
        action.connect("activate", lambda *_: self._toggle_sidebar())
        self.add_action(action)

        action = Gio.SimpleAction.new("toggle-search", None)
        action.connect("activate", lambda *_: self._toggle_search())
        self.add_action(action)

        action = Gio.SimpleAction.new("save", None)
        action.connect("activate", lambda *_: self._save_current())
        self.add_action(action)

        action = Gio.SimpleAction.new("close-tab", None)
        action.connect("activate", lambda *_: self._close_current_tab())
        self.add_action(action)

    # ── Vault loading ──────────────────────────────────────────────

    def _load_vaults(self) -> None:
        vaults = config.load_vaults()
        paths = [v["path"] for v in vaults]
        self._vault_tree.set_vaults(paths)
        self._sidebar.set_vault_paths(paths)

    # ── File opening ───────────────────────────────────────────────

    def _open_file(self, file_path: str) -> None:
        """Open *file_path* in a new or existing tab."""
        for path in self._tab_bar.get_all_paths():
            if path == file_path:
                self._tab_bar.set_active_tab(file_path)
                return

        editor = Editor()
        preview = Preview()
        editor.open_file(file_path)

        self._tab_bar.add_tab(file_path, editor, preview)

        split = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        split.set_start_child(editor)
        split.set_end_child(preview)
        split.set_position(600)

        self._content_stack.add_named(split, file_path)
        self._content_stack.set_visible_child_name(file_path)

        self._refresh_preview()
        self._sidebar.update_for_file(file_path, editor.get_text())

    # ── Tab callbacks ──────────────────────────────────────────────

    def _on_file_selected_from_tree(self, _tree, file_path: str) -> None:
        self._open_file(file_path)

    def _on_tab_changed(self, _tab_bar, file_path: str) -> None:
        tab = self._tab_bar.get_current_tab()
        if not tab:
            return
        self._content_stack.set_visible_child_name(file_path)
        self._refresh_preview()
        self._sidebar.update_for_file(file_path, tab.editor.get_text())

    def _on_tab_closed(self, _tab_bar, file_path: str) -> None:
        child = self._content_stack.get_child_by_name(file_path)
        if child:
            self._content_stack.remove(child)
        if not self._tab_bar.has_tabs():
            self._sidebar.update_for_file(None)

    def _on_sidebar_file_requested(self, _sidebar, file_path: str) -> None:
        self._open_file(file_path)

    def _on_search_result_selected(self, _search_bar, file_path: str) -> None:
        self._open_file(file_path)

    # ── View mode ──────────────────────────────────────────────────

    def _on_view_mode_toggled(self, toggle_btn: Gtk.ToggleButton) -> None:
        if not self._setup_complete:
            return
        if not toggle_btn.get_active():
            return
        tab = self._tab_bar.get_current_tab()
        if not tab:
            return
        tab.view_mode = toggle_btn._mode  # type: ignore[attr-defined]
        self._refresh_preview()

    # ── Preview ────────────────────────────────────────────────────

    def _refresh_preview(self) -> None:
        """Update the preview for the current tab."""
        tab = self._tab_bar.get_current_tab()
        if not tab:
            return
        text = tab.editor.get_text()
        base_dir = str(tab.editor.file_path.parent) if tab.editor.file_path else ""
        tab.preview.update_from_text(text, base_dir)

    # ── Misc ───────────────────────────────────────────────────────

    def _toggle_sidebar(self) -> None:
        self._sidebar.set_visible(not self._sidebar.get_visible())

    def _toggle_search(self) -> None:
        self._search_bar.focus()

    def _save_current(self) -> None:
        tab = self._tab_bar.get_current_tab()
        if tab:
            tab.editor.save()

    def _close_current_tab(self) -> None:
        path = self._tab_bar.get_current_path()
        if path:
            self._tab_bar.close_tab(path)
