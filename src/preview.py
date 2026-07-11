import markdown
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, WebKit


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="file://{css_path}">
</head>
<body>
<div class="markdown-body">
{content}
</div>
</body>
</html>"""


class Preview(Gtk.ScrolledWindow):
    def __init__(self, css_path: str = ""):
        super().__init__()
        self._css_path = css_path

        self._web_view = WebKit.WebView()
        self._web_view.set_vexpand(True)
        self._web_view.set_hexpand(True)

        settings = self._web_view.get_settings()
        settings.set_enable_javascript(False)

        self.set_child(self._web_view)

    def update(self, markdown_text: str, base_dir: str = ""):
        extensions = [
            "markdown.extensions.fenced_code",
            "markdown.extensions.tables",
            "markdown.extensions.toc",
            "markdown.extensions.wikilinks",
        ]
        extension_configs = {"markdown.extensions.wikilinks": {"base_url": ""}}
        html_content = markdown.markdown(
            markdown_text, extensions=extensions, extension_configs=extension_configs
        )

        css_path = self._css_path
        if not css_path:
            import importlib.resources
            try:
                css_path = str(importlib.resources.files("data").joinpath("css/style.css"))
            except Exception:
                css_path = ""

        full_html = HTML_TEMPLATE.format(
            css_path=css_path, content=html_content
        )

        self._web_view.load_html(full_html, f"file://{base_dir}/" if base_dir else None)

    def update_from_text(self, text: str, base_dir: str = ""):
        self.update(text, base_dir)
