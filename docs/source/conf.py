# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys

project = 'mrpac'
copyright = '2023, Yasin Abdulkadir'
author = 'Yasin Abdulkadir'
release = '1.5.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc.typehints",
]
# extensions.append('autoapi.extension')
# autoapi_dirs = ['../../src']

autosummary_generate = True
# autodoc_default_options = {
#     "members": None,
#     "no-inherited-members": None,
# }

autodoc_typehints = 'description'

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True
templates_path = ['_templates']
exclude_patterns = []

# intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/{.major}".format(sys.version_info), None),
    "pydicom": ("https://pydicom.github.io/pydicom/stable", None),
}



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
