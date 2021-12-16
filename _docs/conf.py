# -*- coding: utf-8 -*-
from sphinx.ext.autodoc import between
from datetime import date
import sys
import os

try:
    from importlib.metadata import version

    __version__ = version('wbia-vtool')
except Exception:
    __version__ = 'latest'

sys.path.append(sys.path.insert(0, os.path.abspath('../')))

autosummary_generate = True

modindex_common_prefix = ['_']

master_doc = 'index'

html_theme = 'sphinx_rtd_theme'
html_theme_path = [
    '_themes',
]

html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
        'donate.html',
    ]
}

# -- Project information -----------------------------------------------------

project = 'wbia-vtool'
copyright = f'{date.today().year}, Wild Me'
author = 'Wild Me (wildme.org)'
version = __version__
release = version

# -- General configuration ---------------------------------------------------

MOCK_MODULES = []
if len(MOCK_MODULES) > 0:
    import mock

    for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = mock.Mock()

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.doctest',
    'sphinx.ext.imgmath',
    'sphinx.ext.todo',
    # For Google Sytle Docstrs
    'sphinx.ext.napoleon',
    'alabaster',
]

# -- Extension configuration -------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://docs.scipy.org/doc/numpy/', None),
}

autosectionlabel_prefix_document = True

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


def setup(app):
    # Register a sphinx.ext.autodoc.between listener to ignore everything
    # between lines that contain the word IGNORE
    app.connect('autodoc-process-docstring', between('^.*IGNORE.*$', exclude=True))
    return app
