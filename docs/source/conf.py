# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib
import sys
import tomli


# -- Path setup --------------------------------------------------------------

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, PROJECT_ROOT/"src")


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Konashi5 SDK (Python)'
copyright = '2022, Yukai Engineering Inc.'
author = 'Yukai Engineering Inc.'

with open(PROJECT_ROOT/"pyproject.toml", "rb") as f:
    version = release = tomli.load(f)["project"]["version"]


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
