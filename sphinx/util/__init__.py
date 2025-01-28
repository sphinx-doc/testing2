"""Utility functions for Sphinx."""

from __future__ import annotations

import os
import posixpath
import re
from typing import TYPE_CHECKING

from sphinx.errors import FiletypeNotFoundError

if TYPE_CHECKING:
    import hashlib
    from collections.abc import Callable
    from types import ModuleType
    from typing import Any

# Generally useful regular expressions.
ws_re: re.Pattern[str] = re.compile(r'\s+')
url_re: re.Pattern[str] = re.compile(r'(?P<schema>.+)://.*')

# High-level utility functions.


def docname_join(basedocname: str, docname: str) -> str:
    return posixpath.normpath(posixpath.join('/' + basedocname, '..', docname))[1:]


def get_filetype(
    source_suffix: dict[str, str], filename: str | os.PathLike[str]
) -> str:
    for suffix, filetype in source_suffix.items():
        if os.fspath(filename).endswith(suffix):
            # If default filetype (None), considered as restructuredtext.
            return filetype or 'restructuredtext'
    raise FiletypeNotFoundError


def _md5(data: bytes = b'', **_kw: Any) -> hashlib._Hash:
    """Deprecated wrapper around hashlib.md5

    To be removed in Sphinx 9.0
    """
    import hashlib

    return hashlib.md5(data, usedforsecurity=False)


def _sha1(data: bytes = b'', **_kw: Any) -> hashlib._Hash:
    """Deprecated wrapper around hashlib.sha1

    To be removed in Sphinx 9.0
    """
    import hashlib

    return hashlib.sha1(data, usedforsecurity=False)


def __getattr__(name: str) -> Any:
    from sphinx.deprecation import _deprecation_warning

    obj: Callable[..., Any]
    mod: ModuleType

    # RemovedInSphinx90Warning
    if name == 'split_index_msg':
        from sphinx.util.index_entries import split_index_msg as obj

        canonical_name = f'{obj.__module__}.{obj.__qualname__}'
        _deprecation_warning(__name__, name, canonical_name, remove=(9, 0))
        return obj

    if name == 'split_into':
        from sphinx.util.index_entries import _split_into as obj

        _deprecation_warning(__name__, name, '', remove=(9, 0))
        return obj

    if name == 'ExtensionError':
        from sphinx.errors import ExtensionError as obj  # NoQA: N813

        canonical_name = f'{obj.__module__}.{obj.__qualname__}'
        _deprecation_warning(__name__, name, canonical_name, remove=(9, 0))
        return obj

    if name in {'md5', 'sha1'}:
        obj = globals()[f'_{name}']
        canonical_name = f'hashlib.{name}'
        _deprecation_warning(__name__, name, canonical_name, remove=(9, 0))
        return obj

    # RemovedInSphinx10Warning

    if name in {'DownloadFiles', 'FilenameUniqDict'}:
        from sphinx.util import _files as mod

        obj = getattr(mod, name)
        _deprecation_warning(__name__, name, '', remove=(10, 0))
        return obj

    if name == 'import_object':
        from sphinx.util._importer import import_object

        _deprecation_warning(__name__, name, '', remove=(10, 0))
        return import_object

    # Re-exported for backwards compatibility,
    # but not currently deprecated

    if name == 'encode_uri':
        from sphinx.util._uri import encode_uri

        return encode_uri

    if name == 'isurl':
        from sphinx.util._uri import is_url

        return is_url

    if name == 'parselinenos':
        from sphinx.util._lines import parse_line_num_spec

        return parse_line_num_spec

    if name == 'patfilter':
        from sphinx.util.matching import patfilter

        return patfilter

    if name == 'strip_escape_sequences':
        from sphinx._cli.util.errors import strip_escape_sequences

        return strip_escape_sequences

    if name in {
        'caption_ref_re',
        'explicit_title_re',
        'nested_parse_with_titles',
        'split_explicit_title',
    }:
        from sphinx.util import nodes as mod

        return getattr(mod, name)

    if name in {
        'SEP',
        'copyfile',
        'ensuredir',
        'make_filename',
        'os_path',
        'relative_uri',
    }:
        from sphinx.util import osutil as mod

        return getattr(mod, name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)
