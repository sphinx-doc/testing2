"""Utilities parsing and analyzing Python code."""

from __future__ import annotations

import tokenize
from importlib import import_module
from typing import TYPE_CHECKING, Any, Literal

from sphinx.errors import PycodeError
from sphinx.pycode.parser import Parser
from sphinx.util._pathlib import _StrPath

if TYPE_CHECKING:
    import os
    from inspect import Signature


class ModuleAnalyzer:
    annotations: dict[tuple[str, str], str]
    attr_docs: dict[tuple[str, str], list[str]]
    finals: list[str]
    overloads: dict[str, list[Signature]]
    tagorder: dict[str, int]
    tags: dict[str, tuple[str, int, int]]

    # cache for analyzer objects -- caches both by module and file name
    cache: dict[tuple[Literal['file', 'module'], str | _StrPath], Any] = {}

    @staticmethod
    def get_module_source(modname: str) -> tuple[_StrPath | None, str | None]:
        """Try to find the source code for a module.

        Returns ('filename', 'source'). One of it can be None if
        no filename or source found
        """
        try:
            mod = import_module(modname)
        except Exception as err:
            raise PycodeError('error importing %r' % modname, err) from err
        loader = getattr(mod, '__loader__', None)
        filename: str | None = getattr(mod, '__file__', None)
        if loader and getattr(loader, 'get_source', None):
            # prefer Native loader, as it respects #coding directive
            try:
                source = loader.get_source(modname)
                if source:
                    mod_path = None if filename is None else _StrPath(filename)
                    # no exception and not None - it must be module source
                    return mod_path, source
            except ImportError:
                pass  # Try other "source-mining" methods
        if filename is None and loader and getattr(loader, 'get_filename', None):
            # have loader, but no filename
            try:
                filename = loader.get_filename(modname)
            except ImportError as err:
                raise PycodeError(
                    'error getting filename for %r' % modname, err
                ) from err
        if filename is None:
            # all methods for getting filename failed, so raise...
            raise PycodeError('no source found for module %r' % modname)
        mod_path = _StrPath(filename).resolve()
        if mod_path.suffix in {'.pyo', '.pyc'}:
            mod_path_pyw = mod_path.with_suffix('.pyw')
            if not mod_path.is_file() and mod_path_pyw.is_file():
                mod_path = mod_path_pyw
            else:
                mod_path = mod_path.with_suffix('.py')
        elif mod_path.suffix not in {'.py', '.pyw'}:
            msg = f'source is not a .py file: {mod_path!r}'
            raise PycodeError(msg)

        if not mod_path.is_file():
            msg = f'source file is not present: {mod_path!r}'
            raise PycodeError(msg)
        return mod_path, None

    @classmethod
    def for_string(
        cls: type[ModuleAnalyzer],
        string: str,
        modname: str,
        srcname: str | os.PathLike[str] = '<string>',
    ) -> ModuleAnalyzer:
        return cls(string, modname, srcname)

    @classmethod
    def for_file(
        cls: type[ModuleAnalyzer], filename: str | os.PathLike[str], modname: str
    ) -> ModuleAnalyzer:
        filename = _StrPath(filename)
        if ('file', filename) in cls.cache:
            return cls.cache['file', filename]
        try:
            with tokenize.open(filename) as f:
                string = f.read()
            obj = cls(string, modname, filename)
            cls.cache['file', filename] = obj
        except Exception as err:
            raise PycodeError('error opening %r' % filename, err) from err
        return obj

    @classmethod
    def for_module(cls: type[ModuleAnalyzer], modname: str) -> ModuleAnalyzer:
        if ('module', modname) in cls.cache:
            entry = cls.cache['module', modname]
            if isinstance(entry, PycodeError):
                raise entry
            return entry

        try:
            filename, source = cls.get_module_source(modname)
            if source is not None:
                obj = cls.for_string(source, modname, filename or '<string>')
            elif filename is not None:
                obj = cls.for_file(filename, modname)
        except PycodeError as err:
            cls.cache['module', modname] = err
            raise
        cls.cache['module', modname] = obj
        return obj

    def __init__(
        self, source: str, modname: str, srcname: str | os.PathLike[str]
    ) -> None:
        self.modname = modname  # name of the module
        self.srcname = str(srcname)  # name of the source file

        # cache the source code as well
        self.code = source

        self._analyzed = False

    def analyze(self) -> None:
        """Analyze the source code."""
        if self._analyzed:
            return

        try:
            parser = Parser(self.code)
            parser.parse()

            self.attr_docs = {}
            for scope, comment in parser.comments.items():
                if comment:
                    self.attr_docs[scope] = [*comment.splitlines(), '']
                else:
                    self.attr_docs[scope] = ['']

            self.annotations = parser.annotations
            self.finals = parser.finals
            self.overloads = parser.overloads
            self.tags = parser.definitions
            self.tagorder = parser.deforders
            self._analyzed = True
        except Exception as exc:
            msg = f'parsing {self.srcname!r} failed: {exc!r}'
            raise PycodeError(msg) from exc

    def find_attr_docs(self) -> dict[tuple[str, str], list[str]]:
        """Find class and module-level attributes and their documentation."""
        self.analyze()
        return self.attr_docs

    def find_tags(self) -> dict[str, tuple[str, int, int]]:
        """Find class, function and method definitions and their location."""
        self.analyze()
        return self.tags
