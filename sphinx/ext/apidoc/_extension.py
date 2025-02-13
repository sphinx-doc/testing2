"""Sphinx extension for auto-generating API documentation."""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from sphinx._cli.util.colour import bold
from sphinx.ext.apidoc._generate import create_modules_toc_file, recurse_tree
from sphinx.ext.apidoc._shared import LOGGER, ApidocOptions, _remove_old_files
from sphinx.locale import __

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from sphinx.application import Sphinx

_BOOL_KEYS = frozenset({
    'followlinks',
    'separatemodules',
    'includeprivate',
    'noheadings',
    'modulefirst',
    'implicit_namespaces',
})
_ALLOWED_KEYS = _BOOL_KEYS | frozenset({
    'path',
    'destination',
    'exclude_patterns',
    'automodule_options',
    'maxdepth',
})


def run_apidoc(app: Sphinx) -> None:
    """Run the apidoc extension."""
    apidoc_defaults: dict[str, Any] = app.config.apidoc_defaults
    apidoc_modules: Sequence[dict[str, Any]] = app.config.apidoc_modules
    srcdir: Path = app.srcdir
    confdir: Path = app.confdir

    LOGGER.info(bold(__('Running apidoc')))

    if not isinstance(apidoc_defaults, dict):
        LOGGER.warning(__('apidoc_defaults must be a dict'), type='apidoc')
        return

    module_options: dict[str, Any]
    for i, module_options in enumerate(apidoc_modules):
        _run_apidoc_module(
            i,
            defaults=apidoc_defaults,
            options=module_options,
            srcdir=srcdir,
            confdir=confdir,
        )


def _run_apidoc_module(
    i: int,
    *,
    defaults: dict[str, Any],
    options: dict[str, Any],
    srcdir: Path,
    confdir: Path,
) -> None:
    """Run apidoc for a single module."""
    options = defaults | options
    args = _parse_module_options(i, options=options, srcdir=srcdir, confdir=confdir)
    if args is None:
        return

    exclude_patterns_compiled: list[re.Pattern[str]] = [
        re.compile(fnmatch.translate(exclude)) for exclude in args.exclude_pattern
    ]

    written_files, modules = recurse_tree(
        args.module_path, exclude_patterns_compiled, args, args.templatedir
    )
    if args.tocfile:
        written_files.append(
            create_modules_toc_file(modules, args, args.tocfile, args.templatedir)
        )
    if args.remove_old:
        _remove_old_files(written_files, args.destdir, args.suffix)


def _parse_module_options(
    i: int, *, options: dict[str, Any], srcdir: Path, confdir: Path
) -> ApidocOptions | None:
    if not isinstance(options, dict):
        LOGGER.warning(__('apidoc_modules item %i must be a dict'), i, type='apidoc')
        return None

    # module path should be absolute or relative to the conf directory
    try:
        path = Path(os.fspath(options['path']))
    except KeyError:
        LOGGER.warning(
            __("apidoc_modules item %i must have a 'path' key"), i, type='apidoc'
        )
        return None
    except TypeError:
        LOGGER.warning(
            __("apidoc_modules item %i 'path' must be a string"), i, type='apidoc'
        )
        return None
    module_path = confdir / path
    if not module_path.is_dir():
        LOGGER.warning(
            __("apidoc_modules item %i 'path' is not an existing folder: %s"),
            i,
            module_path,
            type='apidoc',
        )
        return None

    # destination path should be relative to the source directory
    try:
        destination = Path(os.fspath(options['destination']))
    except KeyError:
        LOGGER.warning(
            __("apidoc_modules item %i must have a 'destination' key"),
            i,
            type='apidoc',
        )
        return None
    except TypeError:
        LOGGER.warning(
            __("apidoc_modules item %i 'destination' must be a string"),
            i,
            type='apidoc',
        )
        return None
    if destination.is_absolute():
        LOGGER.warning(
            __("apidoc_modules item %i 'destination' should be a relative path"),
            i,
            type='apidoc',
        )
        return None
    dest_path = srcdir / destination
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        LOGGER.warning(
            __('apidoc_modules item %i cannot create destination directory: %s'),
            i,
            exc.strerror,
            type='apidoc',
        )
        return None

    # exclude patterns should be absolute or relative to the conf directory
    exclude_patterns: list[str] = [
        str(confdir / pattern)
        for pattern in _check_list_of_strings(i, options, key='exclude_patterns')
    ]

    # TODO template_dir

    maxdepth = 4
    if 'maxdepth' in options:
        if not isinstance(options['maxdepth'], int):
            LOGGER.warning(
                __("apidoc_modules item %i '%s' must be an int"),
                i,
                'maxdepth',
                type='apidoc',
            )
        else:
            maxdepth = options['maxdepth']

    extra_options = {}
    for key in sorted(_BOOL_KEYS):
        if key not in options:
            continue
        if not isinstance(options[key], bool):
            LOGGER.warning(
                __("apidoc_modules item %i '%s' must be a boolean"),
                i,
                key,
                type='apidoc',
            )
            continue
        extra_options[key] = options[key]

    if _options := _check_list_of_strings(i, options, key='automodule_options'):
        automodule_options = set(_options)
    else:
        # TODO per-module automodule_options
        automodule_options = {'members', 'undoc-members', 'show-inheritance'}

    if diff := set(options) - _ALLOWED_KEYS:
        LOGGER.warning(
            __('apidoc_modules item %i has unexpected keys: %s'),
            i,
            ', '.join(sorted(diff)),
            type='apidoc',
        )

    return ApidocOptions(
        destdir=dest_path,
        module_path=module_path,
        exclude_pattern=exclude_patterns,
        automodule_options=automodule_options,
        maxdepth=maxdepth,
        quiet=True,
        **extra_options,
    )


def _check_list_of_strings(
    index: int, options: dict[str, Any], *, key: str
) -> list[str]:
    """Check that a key's value is a list of strings in the options.

    :returns: the value of the key, or the empty list if invalid.
    """
    if key not in options:
        return []
    if not isinstance(options[key], list | tuple | set | frozenset):
        LOGGER.warning(
            __("apidoc_modules item %i '%s' must be a sequence"),
            index,
            key,
            type='apidoc',
        )
        return []
    for item in options[key]:
        if not isinstance(item, str):
            LOGGER.warning(
                __("apidoc_modules item %i '%s' must contain strings"),
                index,
                key,
                type='apidoc',
            )
            return []
    return options[key]
