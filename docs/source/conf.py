# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'zeusdb'
copyright = '2025, ZeusDB'
author = 'ZeusDB'
release = '0.0.7'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinx_sitemap",
]

templates_path = ['_templates']
exclude_patterns = []

# -- Sitemap configuration ---------------------------------------------------
html_baseurl = 'https://docs.zeusdb.com/'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']
html_favicon = "_static/favicon.ico"
html_extra_path = ['robots.txt']

html_theme_options = {
    "navbar_start": ["navbar-logo"],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/ZeusDB/zeusdb",
            "icon": "fab fa-github",
        },
    ],
    "logo": {
        "text": "ZeusDB",
        "image_light": "_static/zeusdb-logo.svg",
        "image_dark": "_static/zeusdb-logo.svg",
    },
    "show_nav_level": 2,  # Controls how deep nested sidebar nav goes
    "navigation_with_keys": True, # enables keyboard navigation shortcuts between documentation pages using your left and right arrow keys.
    "secondary_sidebar_items": [],  # <– disables "On this page" sidebar
}

#myst_enable_extensions = ["colon_fence"]
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "fieldlist",
    "attrs_block",
    "dollarmath",
    "linkify",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3


