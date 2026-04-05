# Sphinx configuration for django-payment-midtrans
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to sys.path so autodoc can find the package
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../example"))

# Mock Django setup for autodoc
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.config.settings")

import django
try:
    django.setup()
except Exception:
    pass

# -- Project information -----------------------------------------------------

project = "django-payment-midtrans"
copyright = "2024, Danang Haris Setiawan"
author = "Danang Haris Setiawan"
release = "1.0.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Markdown support
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = []

html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
}

html_context = {
    "display_github": True,
    "github_user": "rissets",
    "github_repo": "django-payment-midtrans",
    "github_version": "main",
    "conf_py_path": "/docs/",
}

# -- Napoleon settings (Google/NumPy docstrings) ----------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Intersphinx mapping ----------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "celery": ("https://docs.celeryq.dev/en/stable/", None),
}

# -- Autodoc settings --------------------------------------------------------

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
