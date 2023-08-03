"""Preserve function defaults.

Preserve the default argument values of function signatures in source code
and keep them not evaluated for readability.
"""

from __future__ import annotations

import ast
import inspect
from types import LambdaType
from typing import Any

import sphinx
from sphinx.application import Sphinx
from sphinx.locale import __
from sphinx.pycode.ast import unparse as ast_unparse
from sphinx.util import logging

logger = logging.getLogger(__name__)


class DefaultValue:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name


_LAMBDA_NAME = (lambda: None).__name__


def _islambda(v):
    return isinstance(v, LambdaType) and v.__name__ == _LAMBDA_NAME


def get_arguments(obj: Any) -> ast.arguments | None:
    """Get ast.arguments object from living object.
    This tries to parse original code for living object and returns
    AST node for given *obj*.
    """
    try:
        source = inspect.getsource(obj)
        if source.startswith((' ', r'\t')):
            # subject is placed inside class or block.  To read its docstring,
            # this adds if-block before the declaration.
            module = ast.parse('if True:\n' + source)
            subject = module.body[0].body[0]  # type: ignore[attr-defined]
        else:
            module = ast.parse(source)
            subject = module.body[0]
    except (OSError, TypeError):  # failed to load source code
        return None
    except SyntaxError:
        if _islambda(obj):
            # most likely a multi-line arising from detecting a lambda, e.g.:
            #
            # class Foo:
            #   x = property(
            #           lambda self: 1, doc="..."))
            return None

        # Other syntax errors that are not due to the fact that we are
        # documenting a lambda function are propagated (in particular,
        # if a lambda function is renamed by the user, the SyntaxError is
        # propagated).
        raise

    def _get_arguments(x: Any) -> ast.arguments | None:
        if isinstance(x, (ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda)):
            return x.args
        if isinstance(x, (ast.Assign, ast.AnnAssign)):
            return _get_arguments(x.value)
        return None

    return _get_arguments(subject)


def get_default_value(lines: list[str], position: ast.AST) -> str | None:
    try:
        if position.lineno == position.end_lineno:
            line = lines[position.lineno - 1]
            return line[position.col_offset:position.end_col_offset]
        else:
            # multiline value is not supported now
            return None
    except (AttributeError, IndexError):
        return None


def update_defvalue(app: Sphinx, obj: Any, bound_method: bool) -> None:
    """Update defvalue info of *obj* using type_comments."""
    if not app.config.autodoc_preserve_defaults:
        return

    try:
        lines = inspect.getsource(obj).splitlines()
        if lines[0].startswith((' ', r'\t')):
            lines.insert(0, '')  # insert a dummy line to follow what get_arguments() does.
    except (OSError, TypeError):
        lines = []

    try:
        args = get_arguments(obj)
        if args is None:
            # If the object is a built-in, we won't be always able to recover
            # the function definition and its arguments. This happens if *obj*
            # is the `__init__` method generated automatically for dataclasses.
            return

        if args.defaults or args.kw_defaults:
            sig = inspect.signature(obj)
            defaults = list(args.defaults)
            kw_defaults = list(args.kw_defaults)
            parameters = list(sig.parameters.values())
            for i, param in enumerate(parameters):
                if param.default is param.empty:
                    if param.kind == param.KEYWORD_ONLY:
                        # Consume kw_defaults for kwonly args
                        kw_defaults.pop(0)
                else:
                    if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                        default = defaults.pop(0)
                        value = get_default_value(lines, default)
                        if value is None:
                            value = ast_unparse(default)
                        parameters[i] = param.replace(default=DefaultValue(value))
                    else:
                        default = kw_defaults.pop(0)  # type: ignore[assignment]
                        value = get_default_value(lines, default)
                        if value is None:
                            value = ast_unparse(default)
                        parameters[i] = param.replace(default=DefaultValue(value))

            if bound_method and inspect.ismethod(obj):
                # classmethods
                cls = inspect.Parameter('cls', inspect.Parameter.POSITIONAL_OR_KEYWORD)
                parameters.insert(0, cls)

            sig = sig.replace(parameters=parameters)
            if bound_method and inspect.ismethod(obj):
                # classmethods can't be assigned __signature__ attribute.
                obj.__dict__['__signature__'] = sig
            else:
                obj.__signature__ = sig
    except (AttributeError, TypeError):
        # failed to update signature (ex. built-in or extension types)
        pass
    except NotImplementedError as exc:  # failed to ast.unparse()
        logger.warning(__("Failed to parse a default argument value for %r: %s"), obj, exc)


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value('autodoc_preserve_defaults', False, True)
    app.connect('autodoc-before-process-signature', update_defvalue)

    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
    }
