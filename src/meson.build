py = import('python').find_installation('python3')

python_sources = [
  '__init__.py',
  'main.py',
  'app_window.py',
  'config.py',
  'editor.py',
  'preview.py',
  'vault_tree.py',
  'tabs.py',
  'sidebar.py',
  'search.py',
  'tags.py',
  'git_integration.py',
]

install_data(
  python_sources,
  install_dir: py.get_install_dir() / 'markdown_vault',
  preserve_path: true,
)
