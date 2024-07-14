"""Sphinx test suite utilities"""

from __future__ import annotations

__all__ = ('SphinxTestApp', 'SphinxTestAppWrapperForSkipBuilding')

import contextlib
import os
import sys
from io import StringIO
from types import MappingProxyType
from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import directives, roles

import sphinx.application
import sphinx.locale
import sphinx.pycode
from sphinx.testing.matcher import LineMatcher
from sphinx.util.console import strip_colors
from sphinx.util.docutils import additional_nodes

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path
    from typing import Any, ClassVar
    from xml.etree.ElementTree import ElementTree

    from docutils.nodes import Node
    from typing_extensions import Unpack

    from sphinx.testing.matcher.options import CompleteOptions, Options


def assert_node(node: Node, cls: Any = None, xpath: str = "", **kwargs: Any) -> None:
    if cls:
        if isinstance(cls, list):
            assert_node(node, cls[0], xpath=xpath, **kwargs)
            if cls[1:]:
                if isinstance(cls[1], tuple):
                    assert_node(node, cls[1], xpath=xpath, **kwargs)
                else:
                    assert isinstance(node, nodes.Element), \
                        'The node%s does not have any children' % xpath
                    assert len(node) == 1, \
                        'The node%s has %d child nodes, not one' % (xpath, len(node))
                    assert_node(node[0], cls[1:], xpath=xpath + "[0]", **kwargs)
        elif isinstance(cls, tuple):
            assert isinstance(node, (list, nodes.Element)), \
                'The node%s does not have any items' % xpath
            assert len(node) == len(cls), \
                'The node%s has %d child nodes, not %r' % (xpath, len(node), len(cls))
            for i, nodecls in enumerate(cls):
                path = xpath + "[%d]" % i
                assert_node(node[i], nodecls, xpath=path, **kwargs)
        elif isinstance(cls, str):
            assert node == cls, f'The node {xpath!r} is not {cls!r}: {node!r}'
        else:
            assert isinstance(node, cls), \
                f'The node{xpath} is not subclass of {cls!r}: {node!r}'

    if kwargs:
        assert isinstance(node, nodes.Element), \
            'The node%s does not have any attributes' % xpath

        for key, value in kwargs.items():
            if key not in node:
                if (key := key.replace('_', '-')) not in node:
                    msg = f'The node{xpath} does not have {key!r} attribute: {node!r}'
                    raise AssertionError(msg)
            assert node[key] == value, \
                f'The node{xpath}[{key}] is not {value!r}: {node[key]!r}'


# keep this to restrict the API usage and to have a correct return type
def etree_parse(path: str | os.PathLike[str]) -> ElementTree:
    """Parse a file into a (safe) XML element tree."""
    from defusedxml.ElementTree import parse as xml_parse

    return xml_parse(path)


class _SphinxLineMatcher(LineMatcher):
    default_options: ClassVar[CompleteOptions] = LineMatcher.default_options.copy()
    default_options['keep_ansi'] = False
    default_options['strip'] = True


class SphinxTestApp(sphinx.application.Sphinx):
    """A subclass of :class:`~sphinx.application.Sphinx` for tests.

    The constructor uses some better default values for the initialization
    parameters and supports arbitrary keywords stored in the :attr:`extras`
    read-only mapping.

    It is recommended to use::

        @pytest.mark.sphinx('html')
        def test(app):
            app = ...

    instead of::

        def test():
            app = SphinxTestApp('html', srcdir=srcdir)

    In the former case, the 'app' fixture takes care of setting the source
    directory, whereas in the latter, the user must provide it themselves.
    """

    # see https://github.com/sphinx-doc/sphinx/pull/12089 for the
    # discussion on how the signature of this class should be used

    def __init__(
        self,
        /,  # to allow 'self' as an extras
        buildername: str = 'html',
        srcdir: Path | None = None,
        builddir: Path | None = None,  # extra constructor argument
        freshenv: bool = False,  # argument is not in the same order as in the superclass
        confoverrides: dict[str, Any] | None = None,
        status: StringIO | None = None,
        warning: StringIO | None = None,
        tags: Sequence[str] = (),
        docutils_conf: str | None = None,  # extra constructor argument
        parallel: int = 0,
        # additional arguments at the end to keep the signature
        verbosity: int = 0,  # argument is not in the same order as in the superclass
        keep_going: bool = False,
        warningiserror: bool = False,  # argument is not in the same order as in the superclass
        # unknown keyword arguments
        **extras: Any,
    ) -> None:
        assert srcdir is not None

        if verbosity == -1:
            quiet = True
            verbosity = 0
        else:
            quiet = False

        if status is None:
            # ensure that :attr:`status` is a StringIO and not sys.stdout
            # but allow the stream to be /dev/null by passing verbosity=-1
            status = None if quiet else StringIO()
        elif not isinstance(status, StringIO):
            err = "%r must be an io.StringIO object, got: %s" % ('status', type(status))
            raise TypeError(err)

        if warning is None:
            # ensure that :attr:`warning` is a StringIO and not sys.stderr
            # but allow the stream to be /dev/null by passing verbosity=-1
            warning = None if quiet else StringIO()
        elif not isinstance(warning, StringIO):
            err = '%r must be an io.StringIO object, got: %s' % ('warning', type(warning))
            raise TypeError(err)

        self.docutils_conf_path = srcdir / 'docutils.conf'
        if docutils_conf is not None:
            self.docutils_conf_path.write_text(docutils_conf, encoding='utf8')

        if builddir is None:
            builddir = srcdir / '_build'

        confdir = srcdir
        outdir = builddir.joinpath(buildername)
        outdir.mkdir(parents=True, exist_ok=True)
        doctreedir = builddir.joinpath('doctrees')
        doctreedir.mkdir(parents=True, exist_ok=True)
        if confoverrides is None:
            confoverrides = {}

        self._saved_path = sys.path.copy()
        self.extras: Mapping[str, Any] = MappingProxyType(extras)
        """Extras keyword arguments."""

        try:
            super().__init__(
                srcdir, confdir, outdir, doctreedir, buildername,
                confoverrides=confoverrides, status=status, warning=warning,
                freshenv=freshenv, warningiserror=warningiserror, tags=tags,
                verbosity=verbosity, parallel=parallel, keep_going=keep_going,
                pdb=False,
            )
        except Exception:
            self.cleanup()
            raise

    @property
    def status(self) -> StringIO:
        """The in-memory text I/O for the application status messages."""
        # sphinx.application.Sphinx uses StringIO for a quiet stream
        assert isinstance(self._status, StringIO)
        return self._status

    @property
    def warning(self) -> StringIO:
        """The in-memory text I/O for the application warning messages."""
        # sphinx.application.Sphinx uses StringIO for a quiet stream
        assert isinstance(self._warning, StringIO)
        return self._warning

    def stdout(self, /, **options: Unpack[Options]) -> LineMatcher:
        """Create a line matcher object for the status messages."""
        return _SphinxLineMatcher(self.status, **options)

    def stderr(self, /, **options: Unpack[Options]) -> LineMatcher:
        """Create a line matcher object for the warning messages."""
        return _SphinxLineMatcher(self.warning, **options)

    def cleanup(self, doctrees: bool = False) -> None:
        sys.path[:] = self._saved_path
        _clean_up_global_state()
        with contextlib.suppress(FileNotFoundError):
            os.remove(self.docutils_conf_path)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} buildername={self.builder.name!r}>'

    def build(self, force_all: bool = False, filenames: list[str] | None = None) -> None:
        self.env._pickled_doctree_cache.clear()
        super().build(force_all, filenames)


class SphinxTestAppWrapperForSkipBuilding:
    """A wrapper for SphinxTestApp.

    This class is used to speed up the test by skipping ``app.build()``
    if it has already been built and there are any output files.
    """

    def __init__(self, app_: SphinxTestApp) -> None:
        self.app = app_

    def __getattr__(self, name: str) -> Any:
        return getattr(self.app, name)

    def build(self, *args: Any, **kwargs: Any) -> None:
        if not os.listdir(self.app.outdir):
            # if listdir is empty, do build.
            self.app.build(*args, **kwargs)
            # otherwise, we can use built cache


def _clean_up_global_state() -> None:
    # clean up Docutils global state
    directives._directives.clear()  # type: ignore[attr-defined]
    roles._roles.clear()  # type: ignore[attr-defined]
    for node in additional_nodes:
        delattr(nodes.GenericNodeVisitor, f'visit_{node.__name__}')
        delattr(nodes.GenericNodeVisitor, f'depart_{node.__name__}')
        delattr(nodes.SparseNodeVisitor, f'visit_{node.__name__}')
        delattr(nodes.SparseNodeVisitor, f'depart_{node.__name__}')
    additional_nodes.clear()

    # clean up Sphinx global state
    sphinx.locale.translators.clear()

    # clean up autodoc global state
    sphinx.pycode.ModuleAnalyzer.cache.clear()


# deprecated name -> (object to return, canonical path or '', removal version)
_DEPRECATED_OBJECTS: dict[str, tuple[Any, str, tuple[int, int]]] = {
    'strip_escseq': (strip_colors, 'sphinx.util.console.strip_colors', (9, 0)),
}


def __getattr__(name: str) -> Any:
    if name not in _DEPRECATED_OBJECTS:
        msg = f'module {__name__!r} has no attribute {name!r}'
        raise AttributeError(msg)

    from sphinx.deprecation import _deprecation_warning

    deprecated_object, canonical_name, remove = _DEPRECATED_OBJECTS[name]
    _deprecation_warning(__name__, name, canonical_name, remove=remove)
    return deprecated_object
