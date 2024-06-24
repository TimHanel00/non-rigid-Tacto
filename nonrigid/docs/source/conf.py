# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../src/'))
sys.path.insert(0, os.path.abspath('../../src/core'))
sys.path.insert(0, os.path.abspath('../../src/core/objects'))
sys.path.insert(0, os.path.abspath('../../src/utils'))
sys.path.insert(0, os.path.abspath('../../src/blocks/'))
sys.path.insert(0, os.path.abspath('../../src/blocks/displacement'))


# -- Project information -----------------------------------------------------

project = 'nonrigid_datageneration'
copyright = '2022, NCT'
author = 'NCT'

# The full version, including alpha/beta/rc tags
release = '0.0.1'

master_doc = 'index'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
    'sphinx.ext.autosummary',  # Create neat summary tables
#    'sphinx.ext.autosectionlabel'
]
autosummary_generate = True  # Turn on sphinx.ext.autosummary

# Add napoleon to the extensions list
extensions += ['sphinx.ext.napoleon']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

#autosectionlabel_prefix_document = True
     
highlight_language = 'python3'

# To choose if we want to include init functions in the docs
# napoleon_include_init_with_doc = True

# Pull the __init__ docstring into the class description:
autoclass_content = 'both'
