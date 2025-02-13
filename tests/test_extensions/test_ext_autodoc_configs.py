"""Test the autodoc extension.  This tests mainly for config variables"""

from __future__ import annotations

import platform
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

from sphinx.testing import restructuredtext

from tests.test_extensions.autodoc_util import do_autodoc

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

IS_PYPY = platform.python_implementation() == 'PyPy'


@contextmanager
def overwrite_file(path: Path, content: str) -> Iterator[None]:
    current_content = path.read_bytes() if path.exists() else None
    try:
        path.write_text(content, encoding='utf-8')
        yield
    finally:
        if current_content is not None:
            path.write_bytes(current_content)
        else:
            path.unlink()


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_class(app):
    app.config.autoclass_content = 'class'
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.autoclass_content', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.autoclass_content',
        '',
        '',
        '.. py:class:: A()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, no __new__',
        '',
        '',
        '.. py:class:: B()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__(no docstring), no __new__',
        '',
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__(no docstring)',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.autoclass_content',
        '',
        '   A class having both __init__ and __new__',
        '',
        '',
        '.. py:class:: G()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __init__ without docstring.',
        '',
        '',
        '.. py:class:: H()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __new__ without docstring.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_init(app):
    app.config.autoclass_content = 'init'
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.autoclass_content', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.autoclass_content',
        '',
        '',
        '.. py:class:: A()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, no __new__',
        '',
        '',
        '.. py:class:: B()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__(no docstring), no __new__',
        '',
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__(no docstring)',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.autoclass_content',
        '',
        '   __new__ docstring',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: G()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: H()',
        '   :module: target.autoclass_content',
        '',
        '   __new__ docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_signature_mixed(app):
    app.config.autodoc_class_signature = 'mixed'
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.classes.Bar', options)
    assert list(actual) == [
        '',
        '.. py:class:: Bar(x, y)',
        '   :module: target.classes',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_signature_separated_init(app):
    app.config.autodoc_class_signature = 'separated'
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.classes.Bar', options)
    assert list(actual) == [
        '',
        '.. py:class:: Bar',
        '   :module: target.classes',
        '',
        '',
        '   .. py:method:: Bar.__init__(x, y)',
        '      :module: target.classes',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_signature_separated_new(app):
    app.config.autodoc_class_signature = 'separated'
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.classes.Baz', options)
    assert list(actual) == [
        '',
        '.. py:class:: Baz',
        '   :module: target.classes',
        '',
        '',
        '   .. py:method:: Baz.__new__(cls, x, y)',
        '      :module: target.classes',
        '      :staticmethod:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_both(app):
    app.config.autoclass_content = 'both'
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.autoclass_content', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.autoclass_content',
        '',
        '',
        '.. py:class:: A()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, no __new__',
        '',
        '',
        '.. py:class:: B()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__(no docstring), no __new__',
        '',
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__(no docstring)',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__',
        '',
        '   __new__ docstring',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.autoclass_content',
        '',
        '   A class having both __init__ and __new__',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: G()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __init__ without docstring.',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: H()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __new__ without docstring.',
        '',
        '   __new__ docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherit_docstrings(app):
    assert app.config.autodoc_inherit_docstrings is True  # default
    actual = do_autodoc(app, 'method', 'target.inheritance.Derived.inheritedmeth')
    assert list(actual) == [
        '',
        '.. py:method:: Derived.inheritedmeth()',
        '   :module: target.inheritance',
        '',
        '   Inherited function.',
        '',
    ]

    # disable autodoc_inherit_docstrings
    app.config.autodoc_inherit_docstrings = False
    actual = do_autodoc(app, 'method', 'target.inheritance.Derived.inheritedmeth')
    assert list(actual) == [
        '',
        '.. py:method:: Derived.inheritedmeth()',
        '   :module: target.inheritance',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherit_docstrings_for_inherited_members(app):
    options = {
        'members': None,
        'inherited-members': None,
    }

    assert app.config.autodoc_inherit_docstrings is True  # default
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert list(actual) == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.inheritance',
        '',
        '',
        '   .. py:method:: Derived.another_inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Another inherited function.',
        '',
        '',
        '   .. py:attribute:: Derived.inheritedattr',
        '      :module: target.inheritance',
        '      :value: None',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Derived.inheritedclassmeth()',
        '      :module: target.inheritance',
        '      :classmethod:',
        '',
        '      Inherited class method.',
        '',
        '',
        '   .. py:method:: Derived.inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Inherited function.',
        '',
        '',
        '   .. py:method:: Derived.inheritedstaticmeth(cls)',
        '      :module: target.inheritance',
        '      :staticmethod:',
        '',
        '      Inherited static method.',
        '',
    ]

    # disable autodoc_inherit_docstrings
    app.config.autodoc_inherit_docstrings = False
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert list(actual) == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.inheritance',
        '',
        '',
        '   .. py:method:: Derived.another_inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Another inherited function.',
        '',
        '',
        '   .. py:method:: Derived.inheritedclassmeth()',
        '      :module: target.inheritance',
        '      :classmethod:',
        '',
        '      Inherited class method.',
        '',
        '',
        '   .. py:method:: Derived.inheritedstaticmeth(cls)',
        '      :module: target.inheritance',
        '      :staticmethod:',
        '',
        '      Inherited static method.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_docstring_signature(app):
    options = {'members': None, 'special-members': '__init__, __new__'}
    actual = do_autodoc(app, 'class', 'target.DocstringSig', options)
    assert list(actual) == [
        '',
        # FIXME: Ideally this would instead be: `DocstringSig(d, e=1)` but
        # currently `ClassDocumenter` does not apply the docstring signature
        # logic when extracting a signature from a __new__ or __init__ method.
        '.. py:class:: DocstringSig(*new_args, **new_kwargs)',
        '   :module: target',
        '',
        '',
        '   .. py:method:: DocstringSig.__init__(self, a, b=1) -> None',
        '      :module: target',
        '',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.__new__(cls, d, e=1) -> DocstringSig',
        '      :module: target',
        '      :staticmethod:',
        '',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth(FOO, BAR=1) -> BAZ',
        '      :module: target',
        '',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth2()',
        '      :module: target',
        '',
        '      First line, no signature',
        '      Second line followed by indentation::',
        '',
        '          indented line',
        '',
        '',
        '   .. py:property:: DocstringSig.prop1',
        '      :module: target',
        '',
        '      First line of docstring',
        '',
        '',
        '   .. py:property:: DocstringSig.prop2',
        '      :module: target',
        '',
        '      First line of docstring',
        '      Second line of docstring',
        '',
    ]

    # disable autodoc_docstring_signature
    app.config.autodoc_docstring_signature = False
    actual = do_autodoc(app, 'class', 'target.DocstringSig', options)
    assert list(actual) == [
        '',
        '.. py:class:: DocstringSig(*new_args, **new_kwargs)',
        '   :module: target',
        '',
        '',
        '   .. py:method:: DocstringSig.__init__(*init_args, **init_kwargs)',
        '      :module: target',
        '',
        '      __init__(self, a, b=1) -> None',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.__new__(cls, *new_args, **new_kwargs)',
        '      :module: target',
        '      :staticmethod:',
        '',
        '      __new__(cls, d, e=1) -> DocstringSig',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth()',
        '      :module: target',
        '',
        '      meth(FOO, BAR=1) -> BAZ',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth2()',
        '      :module: target',
        '',
        '      First line, no signature',
        '      Second line followed by indentation::',
        '',
        '          indented line',
        '',
        '',
        '   .. py:property:: DocstringSig.prop1',
        '      :module: target',
        '',
        '      DocstringSig.prop1(self)',
        '      First line of docstring',
        '',
        '',
        '   .. py:property:: DocstringSig.prop2',
        '      :module: target',
        '',
        '      First line of docstring',
        '      Second line of docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_and_docstring_signature_class(app):
    app.config.autoclass_content = 'class'
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.docstring_signature', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.docstring_signature',
        '',
        '',
        '.. py:class:: A(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: B(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: C(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.docstring_signature',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_and_docstring_signature_init(app):
    app.config.autoclass_content = 'init'
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.docstring_signature', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.docstring_signature',
        '',
        '',
        '.. py:class:: A(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: B(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: C(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: D(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: E(foo: int, bar: int, baz: int)',
        '              E(foo: str, bar: str, baz: str)',
        '              E(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F(foo: int, bar: int, baz: int)',
        '              F(foo: str, bar: str, baz: str)',
        '              F(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_and_docstring_signature_both(app):
    app.config.autoclass_content = 'both'
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.docstring_signature', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.docstring_signature',
        '',
        '',
        '.. py:class:: A(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: B(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '   B(foo, bar, baz)',
        '',
        '',
        '.. py:class:: C(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '   C(foo, bar, baz)',
        '',
        '',
        '.. py:class:: D(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: E(foo: int, bar: int, baz: int)',
        '              E(foo: str, bar: str, baz: str)',
        '              E(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F(foo: int, bar: int, baz: int)',
        '              F(foo: str, bar: str, baz: str)',
        '              F(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
@pytest.mark.usefixtures('rollback_sysmodules')
def test_mocked_module_imports(app):
    sys.modules.pop('target', None)  # unload target module to clear the module cache

    # no autodoc_mock_imports
    options = {'members': 'TestAutodoc,decorated_function,func,Alias'}
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert list(actual) == []
    assert "autodoc: failed to import module 'need_mocks'" in app.warning.getvalue()

    # with autodoc_mock_imports
    app.config.autodoc_mock_imports = [
        'missing_module',
        'missing_package1',
        'missing_package2',
        'missing_package3',
        'sphinx.missing_module4',
    ]

    app.warning.truncate(0)
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.need_mocks',
        '',
        '',
        '.. py:data:: Alias',
        '   :module: target.need_mocks',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: TestAutodoc()',
        '   :module: target.need_mocks',
        '',
        '   TestAutodoc docstring.',
        '',
        '',
        '   .. py:attribute:: TestAutodoc.Alias',
        '      :module: target.need_mocks',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: TestAutodoc.decorated_method()',
        '      :module: target.need_mocks',
        '',
        '      TestAutodoc::decorated_method docstring',
        '',
        '',
        '.. py:function:: decorated_function()',
        '   :module: target.need_mocks',
        '',
        '   decorated_function docstring',
        '',
        '',
        '.. py:function:: func(arg: missing_module.Class)',
        '   :module: target.need_mocks',
        '',
        '   a function takes mocked object as an argument',
        '',
    ]
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints': 'signature'},
)
def test_autodoc_typehints_signature(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.typehints', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '   :type: int',
        '',
        '',
        '.. py:data:: CONST2',
        '   :module: target.typehints',
        '   :type: int',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: CONST3',
        '   :module: target.typehints',
        '   :type: ~pathlib.PurePosixPath',
        "   :value: PurePosixPath('/a/b/c')",
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math(s: str, o: ~typing.Any = None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :type: int',
        '      :value: 1',
        '',
        '',
        '   .. py:attribute:: Math.CONST3',
        '      :module: target.typehints',
        '      :type: ~pathlib.PurePosixPath',
        "      :value: PurePosixPath('/a/b/c')",
        '',
        '',
        '   .. py:method:: Math.decr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a: str, b: int) -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing() -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.path',
        '      :module: target.typehints',
        '      :type: ~pathlib.PurePosixPath',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '.. py:class:: NewAnnotation(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: T',
        '   :module: target.typehints',
        '',
        '   docstring',
        '',
        "   alias of TypeVar('T', bound=\\ :py:class:`~pathlib.PurePosixPath`)",
        '',
        '',
        '.. py:function:: complex_func(arg1: str, arg2: List[int], arg3: Tuple[int, '
        'Union[str, Unknown]] = None, *args: str, **kwargs: str) -> None',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a: str, b: Optional[str] = None) -> str',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x: tuple[int, int | str]) -> tuple[int, int]',
        '   :module: target.typehints',
        '',
    ]


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints': 'none'},
)
def test_autodoc_typehints_none(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.typehints', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '',
        '',
        '.. py:data:: CONST2',
        '   :module: target.typehints',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: CONST3',
        '   :module: target.typehints',
        "   :value: PurePosixPath('/a/b/c')",
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math(s, o=None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :value: 1',
        '',
        '',
        '   .. py:attribute:: Math.CONST3',
        '      :module: target.typehints',
        "      :value: PurePosixPath('/a/b/c')",
        '',
        '',
        '   .. py:method:: Math.decr(a, b=1)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a, b)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a, b=1)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing()',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.path',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '',
        '',
        '.. py:class:: NewAnnotation(i)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: T',
        '   :module: target.typehints',
        '',
        '   docstring',
        '',
        "   alias of TypeVar('T', bound=\\ :py:class:`~pathlib.PurePosixPath`)",
        '',
        '',
        '.. py:function:: complex_func(arg1, arg2, arg3=None, *args, **kwargs)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a, b=1)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a, b=1)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a, b=None)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x)',
        '   :module: target.typehints',
        '',
    ]


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints': 'none'},
)
def test_autodoc_typehints_none_for_overload(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.overload', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.overload',
        '',
        '',
        '.. py:class:: Bar(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Baz(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Foo(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math()',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Math.sum(x, y=None)',
        '      :module: target.overload',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: sum(x, y=None)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints': 'description'},
    freshenv=True,
)
def test_autodoc_typehints_description(app):
    app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert (
        'target.typehints.incr(a, b=1)\n'
        '\n'
        '   Parameters:\n'
        '      * **a** (*int*)\n'
        '\n'
        '      * **b** (*int*)\n'
        '\n'
        '   Return type:\n'
        '      int\n'
    ) in context
    assert (
        'target.typehints.tuple_args(x)\n'
        '\n'
        '   Parameters:\n'
        '      **x** (*tuple**[**int**, **int** | **str**]*)\n'
        '\n'
        '   Return type:\n'
        '      tuple[int, int]\n'
    ) in context

    # Overloads still get displayed in the signature
    assert (
        'target.overload.sum(x: int, y: int = 0) -> int\n'
        'target.overload.sum(x: float, y: float = 0.0) -> float\n'
        'target.overload.sum(x: str, y: str = None) -> str\n'
        '\n'
        '   docstring\n'
    ) in context


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={
        'autodoc_typehints': 'description',
        'autodoc_typehints_description_target': 'documented',
    },
    copy_test_root=True,
)
def test_autodoc_typehints_description_no_undoc(app):
    # No :type: or :rtype: will be injected for `incr`, which does not have
    # a description for its parameters or its return. `tuple_args` does
    # describe them, so :type: and :rtype: will be added.
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.decr\n'
        '\n'
        '   :returns: decremented number\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '   :param x: arg\n'
        '   :return: another tuple\n',
    ):
        app.build()
    # Restore the original content of the file
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert (
        'target.typehints.incr(a, b=1)\n'
        '\n'
        'target.typehints.decr(a, b=1)\n'
        '\n'
        '   Returns:\n'
        '      decremented number\n'
        '\n'
        '   Return type:\n'
        '      int\n'
        '\n'
        'target.typehints.tuple_args(x)\n'
        '\n'
        '   Parameters:\n'
        '      **x** (*tuple**[**int**, **int** | **str**]*) -- arg\n'
        '\n'
        '   Returns:\n'
        '      another tuple\n'
        '\n'
        '   Return type:\n'
        '      tuple[int, int]\n'
    ) in context


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={
        'autodoc_typehints': 'description',
        'autodoc_typehints_description_target': 'documented_params',
    },
    copy_test_root=True,
)
def test_autodoc_typehints_description_no_undoc_doc_rtype(app):
    # No :type: will be injected for `incr`, which does not have a description
    # for its parameters or its return, just :rtype: will be injected due to
    # autodoc_typehints_description_target. `tuple_args` does describe both, so
    # :type: and :rtype: will be added. `nothing` has no parameters but a return
    # type of None, which will be added.
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.decr\n'
        '\n'
        '   :returns: decremented number\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '   :param x: arg\n'
        '   :return: another tuple\n'
        '\n'
        '.. autofunction:: target.typehints.Math.nothing\n'
        '\n'
        '.. autofunction:: target.typehints.Math.horse\n'
        '\n'
        '   :return: nothing\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'target.typehints.incr(a, b=1)\n'
        '\n'
        '   Return type:\n'
        '      int\n'
        '\n'
        'target.typehints.decr(a, b=1)\n'
        '\n'
        '   Returns:\n'
        '      decremented number\n'
        '\n'
        '   Return type:\n'
        '      int\n'
        '\n'
        'target.typehints.tuple_args(x)\n'
        '\n'
        '   Parameters:\n'
        '      **x** (*tuple**[**int**, **int** | **str**]*) -- arg\n'
        '\n'
        '   Returns:\n'
        '      another tuple\n'
        '\n'
        '   Return type:\n'
        '      tuple[int, int]\n'
        '\n'
        'target.typehints.Math.nothing(self)\n'
        '\n'
        'target.typehints.Math.horse(self, a, b)\n'
        '\n'
        '   Returns:\n'
        '      nothing\n'
        '\n'
        '   Return type:\n'
        '      None\n'
    )


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints': 'description'},
    copy_test_root=True,
)
def test_autodoc_typehints_description_with_documented_init(app):
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'class target.typehints._ClassWithDocumentedInit(x, *args, **kwargs)\n'
        '\n'
        '   Class docstring.\n'
        '\n'
        '   Parameters:\n'
        '      * **x** (*int*)\n'
        '\n'
        '      * **args** (*int*)\n'
        '\n'
        '      * **kwargs** (*int*)\n'
        '\n'
        '   __init__(x, *args, **kwargs)\n'
        '\n'
        '      Init docstring.\n'
        '\n'
        '      Parameters:\n'
        '         * **x** (*int*) -- Some integer\n'
        '\n'
        '         * **args** (*int*) -- Some integer\n'
        '\n'
        '         * **kwargs** (*int*) -- Some integer\n'
        '\n'
        '      Return type:\n'
        '         None\n'
    )


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={
        'autodoc_typehints': 'description',
        'autodoc_typehints_description_target': 'documented',
    },
    copy_test_root=True,
)
def test_autodoc_typehints_description_with_documented_init_no_undoc(app):
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'class target.typehints._ClassWithDocumentedInit(x, *args, **kwargs)\n'
        '\n'
        '   Class docstring.\n'
        '\n'
        '   __init__(x, *args, **kwargs)\n'
        '\n'
        '      Init docstring.\n'
        '\n'
        '      Parameters:\n'
        '         * **x** (*int*) -- Some integer\n'
        '\n'
        '         * **args** (*int*) -- Some integer\n'
        '\n'
        '         * **kwargs** (*int*) -- Some integer\n'
    )


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={
        'autodoc_typehints': 'description',
        'autodoc_typehints_description_target': 'documented_params',
    },
    copy_test_root=True,
)
def test_autodoc_typehints_description_with_documented_init_no_undoc_doc_rtype(app):
    # see test_autodoc_typehints_description_with_documented_init_no_undoc
    # returnvalue_and_documented_params should not change class or method
    # docstring.
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert context == (
        'class target.typehints._ClassWithDocumentedInit(x, *args, **kwargs)\n'
        '\n'
        '   Class docstring.\n'
        '\n'
        '   __init__(x, *args, **kwargs)\n'
        '\n'
        '      Init docstring.\n'
        '\n'
        '      Parameters:\n'
        '         * **x** (*int*) -- Some integer\n'
        '\n'
        '         * **args** (*int*) -- Some integer\n'
        '\n'
        '         * **kwargs** (*int*) -- Some integer\n'
    )


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints': 'description'},
)
def test_autodoc_typehints_description_for_invalid_node(app):
    text = '.. py:function:: hello; world'
    restructuredtext.parse(app, text)  # raises no error


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints': 'both'},
    copy_test_root=True,
)
def test_autodoc_typehints_both(app):
    with overwrite_file(
        app.srcdir / 'index.rst',
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '.. autofunction:: target.overload.sum\n',
    ):
        app.build()
    context = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert (
        'target.typehints.incr(a: int, b: int = 1) -> int\n'
        '\n'
        '   Parameters:\n'
        '      * **a** (*int*)\n'
        '\n'
        '      * **b** (*int*)\n'
        '\n'
        '   Return type:\n'
        '      int\n'
    ) in context
    assert (
        'target.typehints.tuple_args(x: tuple[int, int | str]) -> tuple[int, int]\n'
        '\n'
        '   Parameters:\n'
        '      **x** (*tuple**[**int**, **int** | **str**]*)\n'
        '\n'
        '   Return type:\n'
        '      tuple[int, int]\n'
    ) in context

    # Overloads still get displayed in the signature
    assert (
        'target.overload.sum(x: int, y: int = 0) -> int\n'
        'target.overload.sum(x: float, y: float = 0.0) -> float\n'
        'target.overload.sum(x: str, y: str = None) -> str\n'
        '\n'
        '   docstring\n'
    ) in context


@pytest.mark.sphinx('text', testroot='ext-autodoc')
def test_autodoc_type_aliases(app):
    # default
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.autodoc_type_aliases', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.autodoc_type_aliases',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr1',
        '      :module: target.autodoc_type_aliases',
        '      :type: ~fractions.Fraction | int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr2',
        '      :module: target.autodoc_type_aliases',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Foo.method1(x: ~fractions.Fraction | float) -> ~fractions.Fraction | float',
        '      :module: target.autodoc_type_aliases',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Foo.method2(x: ~fractions.Fraction) -> ~fractions.Fraction',
        '                  Foo.method2(x: float) -> float',
        '                  Foo.method2(x: ~fractions.Fraction | float) -> ~fractions.Fraction | float',
        '      :module: target.autodoc_type_aliases',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: mult(x: int, y: int) -> int',
        '                 mult(x: float, y: float) -> float',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: print_value(x: ~fractions.Fraction | float) -> None',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: prod(x: tuple[float, float]) -> float',
        '                 prod(x: tuple[~fractions.Fraction, float]) -> ~fractions.Fraction',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: read(r: ~io.BytesIO) -> ~io.StringIO',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: sum(x: float, y: float) -> float',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable',
        '   :module: target.autodoc_type_aliases',
        '   :type: int',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable2',
        '   :module: target.autodoc_type_aliases',
        '   :type: int',
        '   :value: None',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable3',
        '   :module: target.autodoc_type_aliases',
        '   :type: int | None',
        '',
        '   docstring',
        '',
    ]

    # define aliases
    app.config.autodoc_type_aliases = {
        'myint': 'myint',
        'myfrac': 'my.module.myfrac',
        'io.StringIO': 'my.module.StringIO',
    }
    actual = do_autodoc(app, 'module', 'target.autodoc_type_aliases', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.autodoc_type_aliases',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr1',
        '      :module: target.autodoc_type_aliases',
        "      :type: ~fractions.Fraction | TypeAliasForwardRef('myint')",
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr2',
        '      :module: target.autodoc_type_aliases',
        '      :type: myint',
        '',
        '      docstring',
        '',
        '',
        "   .. py:method:: Foo.method1(x: ~fractions.Fraction | TypeAliasForwardRef('my.module.myfrac')) -> ~fractions.Fraction | TypeAliasForwardRef('my.module.myfrac')",
        '      :module: target.autodoc_type_aliases',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Foo.method2(x: ~fractions.Fraction) -> ~fractions.Fraction',
        '                  Foo.method2(x: my.module.myfrac) -> my.module.myfrac',
        "                  Foo.method2(x: ~fractions.Fraction | TypeAliasForwardRef('my.module.myfrac')) -> ~fractions.Fraction | TypeAliasForwardRef('my.module.myfrac')",
        '      :module: target.autodoc_type_aliases',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: mult(x: int, y: int) -> int',
        '                 mult(x: my.module.myfrac, y: my.module.myfrac) -> my.module.myfrac',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        ".. py:function:: print_value(x: ~fractions.Fraction | TypeAliasForwardRef('my.module.myfrac')) -> None",
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        ".. py:function:: prod(x: tuple[float, TypeAliasForwardRef('my.module.myfrac')]) -> float",
        "                 prod(x: tuple[~fractions.Fraction, TypeAliasForwardRef('my.module.myfrac')]) -> ~fractions.Fraction",
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: read(r: ~io.BytesIO) -> my.module.StringIO',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: sum(x: my.module.myfrac, y: my.module.myfrac) -> my.module.myfrac',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable',
        '   :module: target.autodoc_type_aliases',
        '   :type: myint',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable2',
        '   :module: target.autodoc_type_aliases',
        '   :type: myint',
        '   :value: None',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable3',
        '   :module: target.autodoc_type_aliases',
        '   :type: myint | None',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx(
    'text',
    testroot='ext-autodoc',
    srcdir='autodoc_typehints_description_and_type_aliases',
    confoverrides={
        'autodoc_typehints': 'description',
        'autodoc_type_aliases': {'myfrac': 'my.module.myfrac'},
    },
)
def test_autodoc_typehints_description_and_type_aliases(app):
    with overwrite_file(
        app.srcdir / 'autodoc_type_aliases.rst',
        '.. autofunction:: target.autodoc_type_aliases.sum',
    ):
        app.build()
    context = (app.outdir / 'autodoc_type_aliases.txt').read_text(encoding='utf8')
    assert context == (
        'target.autodoc_type_aliases.sum(x, y)\n'
        '\n'
        '   docstring\n'
        '\n'
        '   Parameters:\n'
        '      * **x** (*my.module.myfrac*)\n'
        '\n'
        '      * **y** (*my.module.myfrac*)\n'
        '\n'
        '   Return type:\n'
        '      my.module.myfrac\n'
    )


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints_format': 'fully-qualified'},
)
def test_autodoc_typehints_format_fully_qualified(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.typehints', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '   :type: int',
        '',
        '',
        '.. py:data:: CONST2',
        '   :module: target.typehints',
        '   :type: int',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: CONST3',
        '   :module: target.typehints',
        '   :type: pathlib.PurePosixPath',
        "   :value: PurePosixPath('/a/b/c')",
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math(s: str, o: typing.Any = None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :type: int',
        '      :value: 1',
        '',
        '',
        '   .. py:attribute:: Math.CONST3',
        '      :module: target.typehints',
        '      :type: pathlib.PurePosixPath',
        "      :value: PurePosixPath('/a/b/c')",
        '',
        '',
        '   .. py:method:: Math.decr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a: str, b: int) -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing() -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.path',
        '      :module: target.typehints',
        '      :type: pathlib.PurePosixPath',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '.. py:class:: NewAnnotation(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: T',
        '   :module: target.typehints',
        '',
        '   docstring',
        '',
        "   alias of TypeVar('T', bound=\\ :py:class:`pathlib.PurePosixPath`)",
        '',
        '',
        '.. py:function:: complex_func(arg1: str, arg2: List[int], arg3: Tuple[int, '
        'Union[str, Unknown]] = None, *args: str, **kwargs: str) -> None',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a: str, b: Optional[str] = None) -> str',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x: tuple[int, int | str]) -> tuple[int, int]',
        '   :module: target.typehints',
        '',
    ]


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints_format': 'fully-qualified'},
)
def test_autodoc_typehints_format_fully_qualified_for_class_alias(app):
    actual = do_autodoc(app, 'class', 'target.classes.Alias')
    assert list(actual) == [
        '',
        '.. py:attribute:: Alias',
        '   :module: target.classes',
        '',
        '   alias of :py:class:`target.classes.Foo`',
    ]


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints_format': 'fully-qualified'},
)
def test_autodoc_typehints_format_fully_qualified_for_generic_alias(app):
    actual = do_autodoc(app, 'data', 'target.genericalias.L')
    assert list(actual) == [
        '',
        '.. py:data:: L',
        '   :module: target.genericalias',
        '',
        '   A list of Class',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`target.genericalias.Class`]',
        '',
    ]


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'autodoc_typehints_format': 'fully-qualified'},
)
def test_autodoc_typehints_format_fully_qualified_for_newtype_alias(app):
    actual = do_autodoc(app, 'class', 'target.typevar.T6')
    assert list(actual) == [
        '',
        '.. py:class:: T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`datetime.date`',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_options(app):
    if (3, 11, 7) <= sys.version_info < (3, 12) or sys.version_info >= (3, 12, 1):
        list_of_weak_references = '      list of weak references to the object'
    else:
        list_of_weak_references = '      list of weak references to the object (if defined)'  # fmt: skip

    # no settings
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: target.CustomIter' not in actual
    actual = do_autodoc(app, 'module', 'target')
    assert '.. py:function:: function_to_be_imported(app)' not in actual

    # with :members:
    app.config.autodoc_default_options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: = True
    app.config.autodoc_default_options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: and :undoc-members:
    app.config.autodoc_default_options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' in actual

    # with :special-members:
    # Note that :members: must be *on* for :special-members: to work.
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert list_of_weak_references in actual

    # :exclude-members: None - has no effect. Unlike :members:,
    # :special-members:, etc. where None == "include all", here None means
    # "no/false/off".
    app.config.autodoc_default_options = {
        'members': None,
        'exclude-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None,
        'exclude-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert list_of_weak_references in actual
    assert '   .. py:method:: CustomIter.snafucate()' in actual
    assert '      Makes this snafucated.' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_options_with_values(app):
    if (3, 11, 7) <= sys.version_info < (3, 12) or sys.version_info >= (3, 12, 1):
        list_of_weak_references = '      list of weak references to the object'
    else:
        list_of_weak_references = '      list of weak references to the object (if defined)'  # fmt: skip

    # with :members:
    app.config.autodoc_default_options = {'members': 'val1,val2'}
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :member-order:
    app.config.autodoc_default_options = {
        'members': None,
        'member-order': 'bysource',
    }
    actual = do_autodoc(app, 'class', 'target.Class')
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_string',
    ]

    # with :special-members:
    app.config.autodoc_default_options = {
        'special-members': '__init__,__iter__',
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert list_of_weak_references not in actual

    # with :exclude-members:
    app.config.autodoc_default_options = {
        'members': None,
        'exclude-members': 'val1',
    }
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None,
        'exclude-members': '__weakref__,snafucate',
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert list_of_weak_references not in actual
    assert '   .. py:method:: CustomIter.snafucate()' not in actual
    assert '      Makes this snafucated.' not in actual
