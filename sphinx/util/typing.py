"""
    sphinx.util.typing
    ~~~~~~~~~~~~~~~~~~

    The composit types for Sphinx.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import typing
from typing import Any, Callable, Dict, List, Tuple, TypeVar, Union

from docutils import nodes
from docutils.parsers.rst.states import Inliner


# An entry of Directive.option_spec
DirectiveOption = Callable[[str], Any]

# Text like nodes which are initialized with text and rawsource
TextlikeNode = Union[nodes.Text, nodes.TextElement]

# type of None
NoneType = type(None)

# path matcher
PathMatcher = Callable[[str], bool]

# common role functions
RoleFunction = Callable[[str, str, str, int, Inliner, Dict[str, Any], List[str]],
                        Tuple[List[nodes.Node], List[nodes.system_message]]]

# title getter functions for enumerable nodes (see sphinx.domains.std)
TitleGetter = Callable[[nodes.Node], str]

# inventory data on memory
Inventory = Dict[str, Dict[str, Tuple[str, str, str, str]]]


def stringify(annotation: Any) -> str:
    """Stringify type annotation object."""
    if isinstance(annotation, str):
        return annotation
    elif isinstance(annotation, TypeVar):  # type: ignore
        return annotation.__name__
    elif not annotation:
        return repr(annotation)
    elif annotation is NoneType:  # type: ignore
        return 'None'
    elif (getattr(annotation, '__module__', None) == 'builtins' and
          hasattr(annotation, '__qualname__')):
        return annotation.__qualname__
    elif annotation is Ellipsis:
        return '...'

    if sys.version_info >= (3, 7):  # py37+
        return _stringify_py37(annotation)
    else:
        return _stringify_py36(annotation)


def _stringify_py37(annotation: Any) -> str:
    """stringify() for py37+."""
    module = getattr(annotation, '__module__', None)
    if module == 'typing':
        if getattr(annotation, '_name', None):
            qualname = annotation._name
        elif getattr(annotation, '__qualname__', None):
            qualname = annotation.__qualname__
        elif getattr(annotation, '__forward_arg__', None):
            qualname = annotation.__forward_arg__
        else:
            qualname = stringify(annotation.__origin__)  # ex. Union
    elif hasattr(annotation, '__qualname__'):
        qualname = '%s.%s' % (module, annotation.__qualname__)
    else:
        qualname = repr(annotation)

    if getattr(annotation, '__args__', None):
        if qualname == 'Union':
            if len(annotation.__args__) == 2 and annotation.__args__[1] is NoneType:  # type: ignore  # NOQA
                return 'Optional[%s]' % stringify(annotation.__args__[0])
            else:
                args = ', '.join(stringify(a) for a in annotation.__args__)
                return '%s[%s]' % (qualname, args)
        elif qualname == 'Callable':
            args = ', '.join(stringify(a) for a in annotation.__args__[:-1])
            returns = stringify(annotation.__args__[-1])
            return '%s[[%s], %s]' % (qualname, args, returns)
        elif str(annotation).startswith('typing.Annotated'):  # for py39+
            return stringify(annotation.__args__[0])
        elif annotation._special:
            return qualname
        else:
            args = ', '.join(stringify(a) for a in annotation.__args__)
            return '%s[%s]' % (qualname, args)

    return qualname


def _stringify_py36(annotation: Any) -> str:
    """stringify() for py36."""
    module = getattr(annotation, '__module__', None)
    if module == 'typing':
        if getattr(annotation, '_name', None):
            qualname = annotation._name
        elif getattr(annotation, '__qualname__', None):
            qualname = annotation.__qualname__
        elif getattr(annotation, '__forward_arg__', None):
            qualname = annotation.__forward_arg__
        elif getattr(annotation, '__origin__', None):
            qualname = stringify(annotation.__origin__)  # ex. Union
        else:
            qualname = repr(annotation).replace('typing.', '')
    elif hasattr(annotation, '__qualname__'):
        qualname = '%s.%s' % (module, annotation.__qualname__)
    else:
        qualname = repr(annotation)

    if (isinstance(annotation, typing.TupleMeta) and  # type: ignore
            not hasattr(annotation, '__tuple_params__')):  # for Python 3.6
        params = annotation.__args__
        if params:
            param_str = ', '.join(stringify(p) for p in params)
            return '%s[%s]' % (qualname, param_str)
        else:
            return qualname
    elif isinstance(annotation, typing.GenericMeta):
        params = None
        if annotation.__args__ is None or len(annotation.__args__) <= 2:  # type: ignore  # NOQA
            params = annotation.__args__  # type: ignore
        else:  # typing.Callable
            args = ', '.join(stringify(arg) for arg
                             in annotation.__args__[:-1])  # type: ignore
            result = stringify(annotation.__args__[-1])  # type: ignore
            return '%s[[%s], %s]' % (qualname, args, result)
        if params is not None:
            param_str = ', '.join(stringify(p) for p in params)
            return '%s[%s]' % (qualname, param_str)
    elif (hasattr(annotation, '__origin__') and
          annotation.__origin__ is typing.Union):
        params = annotation.__args__
        if params is not None:
            if len(params) == 2 and params[1] is NoneType:  # type: ignore
                return 'Optional[%s]' % stringify(params[0])
            else:
                param_str = ', '.join(stringify(p) for p in params)
                return 'Union[%s]' % param_str

    return qualname
