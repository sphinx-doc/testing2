"""Creates reST files corresponding to Python modules for code documentation.

Parses a directory tree looking for Python modules and packages and creates
ReST files appropriately to create code documentation with Sphinx.  It also
creates a modules index (named modules.<suffix>).

This is derived from the "sphinx-autopackage" script, which is:
Copyright 2008 Société des arts technologiques (SAT),
https://sat.qc.ca/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sphinx
from sphinx.ext.apidoc._cli import main

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

__all__: Sequence[str] = 'main', 'setup'


def setup(app: Sphinx) -> ExtensionMetadata:
    from sphinx.ext.apidoc._extension import run_apidoc

    # Require autodoc
    app.setup_extension('sphinx.ext.autodoc')
    app.add_config_value('apidoc_defaults', {}, 'env', types=frozenset({dict}))
    app.add_config_value('apidoc_modules', (), 'env', types=frozenset((list, tuple)))
    app.connect('builder-inited', run_apidoc)
    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
    }
