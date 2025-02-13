"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import functools
import itertools
import operator
import sys
from typing import TYPE_CHECKING
from unittest.mock import Mock
from warnings import catch_warnings

import pytest

from sphinx import addnodes
from sphinx.ext.autodoc import ALL, ModuleLevelDocumenter, Options

# NEVER import these objects from sphinx.ext.autodoc directly
from sphinx.ext.autodoc.directive import DocumenterBridge

from tests.test_extensions.autodoc_util import do_autodoc

try:
    # Enable pyximport to test cython module
    import pyximport

    pyximport.install()
except ImportError:
    pyximport = None

if TYPE_CHECKING:
    from typing import Any

    from sphinx.environment import BuildEnvironment


def make_directive_bridge(env: BuildEnvironment) -> DocumenterBridge:
    options = Options(
        inherited_members=False,
        undoc_members=False,
        private_members=False,
        special_members=False,
        imported_members=False,
        show_inheritance=False,
        no_index=False,
        annotation=None,
        synopsis='',
        platform='',
        deprecated=False,
        members=[],
        member_order='alphabetical',
        exclude_members=set(),
        ignore_module_all=False,
    )

    directive = DocumenterBridge(
        env=env,
        reporter=None,
        options=options,
        lineno=0,
        state=Mock(),
    )
    directive.state.document.settings.tab_width = 8

    return directive


processed_signatures = []


@pytest.mark.sphinx('html', testroot='root')
def test_parse_name(app):
    def verify(objtype, name, result):
        inst = app.registry.documenters[objtype](directive, name)
        assert inst.parse_name()
        assert (inst.modname, inst.objpath, inst.args, inst.retann) == result

    directive = make_directive_bridge(app.env)

    # for modules
    verify('module', 'test_ext_autodoc', ('test_ext_autodoc', [], None, None))
    verify('module', 'test.test_ext_autodoc', ('test.test_ext_autodoc', [], None, None))
    verify('module', 'test(arg)', ('test', [], 'arg', None))
    assert 'signature arguments' in app.warning.getvalue()

    # for functions/classes
    verify(
        'function',
        'test_ext_autodoc.raises',
        ('test_ext_autodoc', ['raises'], None, None),
    )
    verify(
        'function',
        'test_ext_autodoc.raises(exc) -> None',
        ('test_ext_autodoc', ['raises'], 'exc', 'None'),
    )
    directive.env.current_document.autodoc_module = 'test_ext_autodoc'
    verify('function', 'raises', ('test_ext_autodoc', ['raises'], None, None))
    directive.env.current_document.autodoc_module = ''

    directive.env.ref_context['py:module'] = 'test_ext_autodoc'
    verify('function', 'raises', ('test_ext_autodoc', ['raises'], None, None))
    verify('class', 'Base', ('test_ext_autodoc', ['Base'], None, None))

    # for members
    directive.env.ref_context['py:module'] = 'sphinx.testing.util'
    verify(
        'method',
        'SphinxTestApp.cleanup',
        ('sphinx.testing.util', ['SphinxTestApp', 'cleanup'], None, None),
    )
    directive.env.ref_context['py:module'] = 'sphinx.testing.util'
    directive.env.ref_context['py:class'] = 'Foo'
    directive.env.current_document.autodoc_class = 'SphinxTestApp'
    verify(
        'method',
        'cleanup',
        ('sphinx.testing.util', ['SphinxTestApp', 'cleanup'], None, None),
    )
    verify(
        'method',
        'SphinxTestApp.cleanup',
        ('sphinx.testing.util', ['SphinxTestApp', 'cleanup'], None, None),
    )


@pytest.mark.sphinx('html', testroot='root')
def test_format_signature(app):
    def process_signature(app, what, name, obj, options, args, retann):
        processed_signatures.append((what, name))
        if name == 'bar':
            return '42', None
        return None

    def skip_member(app, what, name, obj, skip, options):
        if name in {'__special1__', '__special2__'}:
            return skip
        if name.startswith('__'):
            return True
        if name == 'skipmeth':
            return True
        return None

    app.connect('autodoc-process-signature', process_signature)
    app.connect('autodoc-skip-member', skip_member)

    directive = make_directive_bridge(app.env)

    def formatsig(objtype, name, obj, args, retann):
        inst = app.registry.documenters[objtype](directive, name)
        inst.fullname = name
        inst.doc_as_attr = False  # for class objtype
        inst.parent = object  # dummy
        inst.object = obj
        inst.objpath = [name]
        inst.args = args
        inst.retann = retann
        res = inst.format_signature()
        print(res)
        return res

    # no signatures for modules
    assert formatsig('module', 'test', None, None, None) == ''

    # test for functions
    def f(a, b, c=1, **d):
        pass

    def g(a='\n'):
        pass

    assert formatsig('function', 'f', f, None, None) == '(a, b, c=1, **d)'
    assert formatsig('function', 'f', f, 'a, b, c, d', None) == '(a, b, c, d)'
    assert formatsig('function', 'g', g, None, None) == r"(a='\n')"

    if sys.version_info >= (3, 12):
        for params, expect in [
            ('(a=1)', '(a=1)'),
            ('(a: int=1)', '(a: int = 1)'),  # auto whitespace formatting
            ('(a:list[T]   =[], b=None)', '(a: list[T] = [], b=None)'),  # idem
        ]:
            ns = {}
            exec(f'def f[T]{params}: pass', ns)  # NoQA: S102
            f = ns['f']
            assert formatsig('function', 'f', f, None, None) == expect
            assert formatsig('function', 'f', f, '...', None) == '(...)'
            assert formatsig('function', 'f', f, '...', '...') == '(...) -> ...'

            exec(f'def f[T]{params} -> list[T]: return []', ns)  # NoQA: S102
            f = ns['f']
            assert formatsig('function', 'f', f, None, None) == f'{expect} -> list[T]'
            assert formatsig('function', 'f', f, '...', None) == '(...)'
            assert formatsig('function', 'f', f, '...', '...') == '(...) -> ...'

    # TODO(picnixz): add more test cases for PEP-695 classes as well (though
    # complex cases are less likely to appear and are painful to test).

    # test for classes
    class D:
        pass

    class E:
        def __init__(self):
            pass

    # an empty init and no init are the same
    for C in (D, E):
        assert formatsig('class', 'D', C, None, None) == '()'

    class SomeMeta(type):
        def __call__(cls, a, b=None):
            return type.__call__(cls, a, b)

    # these three are all equivalent
    class F:
        def __init__(self, a, b=None):
            pass

    class FNew:
        def __new__(cls, a, b=None):
            return super().__new__(cls)

    class FMeta(metaclass=SomeMeta):
        pass

    # and subclasses should always inherit
    class G(F):
        pass

    class GNew(FNew):
        pass

    class GMeta(FMeta):
        pass

    # subclasses inherit
    for C in (F, FNew, FMeta, G, GNew, GMeta):
        assert formatsig('class', 'C', C, None, None) == '(a, b=None)'
    assert formatsig('class', 'C', D, 'a, b', 'X') == '(a, b) -> X'

    class ListSubclass(list):  # NoQA: FURB189
        pass

    # only supported if the python implementation decides to document it
    if getattr(list, '__text_signature__', None) is not None:
        assert formatsig('class', 'C', ListSubclass, None, None) == '(iterable=(), /)'
    else:
        assert formatsig('class', 'C', ListSubclass, None, None) == ''

    class ExceptionSubclass(Exception):
        pass

    # Exception has no __text_signature__ at least in Python 3.11
    if getattr(Exception, '__text_signature__', None) is None:
        assert formatsig('class', 'C', ExceptionSubclass, None, None) == ''

    # __init__ have signature at first line of docstring
    directive.env.config.autoclass_content = 'both'

    class F2:
        """some docstring for F2."""

        def __init__(self, *args, **kw):
            """__init__(a1, a2, kw1=True, kw2=False)

            some docstring for __init__.
            """

    class G2(F2):
        pass

    assert formatsig('class', 'F2', F2, None, None) == '(a1, a2, kw1=True, kw2=False)'
    assert formatsig('class', 'G2', G2, None, None) == '(a1, a2, kw1=True, kw2=False)'

    # test for methods
    class H:
        def foo1(self, b, *c):
            pass

        def foo2(b, *c):  # NoQA: N805
            pass

        def foo3(self, d='\n'):
            pass

    assert formatsig('method', 'H.foo', H.foo1, None, None) == '(b, *c)'
    assert formatsig('method', 'H.foo', H.foo1, 'a', None) == '(a)'
    assert formatsig('method', 'H.foo', H.foo2, None, None) == '(*c)'
    assert formatsig('method', 'H.foo', H.foo3, None, None) == r"(d='\n')"

    # test bound methods interpreted as functions
    assert formatsig('function', 'foo', H().foo1, None, None) == '(b, *c)'
    assert formatsig('function', 'foo', H().foo2, None, None) == '(*c)'
    assert formatsig('function', 'foo', H().foo3, None, None) == r"(d='\n')"

    # test exception handling (exception is caught and args is '')
    directive.env.config.autodoc_docstring_signature = False
    assert formatsig('function', 'int', int, None, None) == ''

    # test processing by event handler
    assert formatsig('method', 'bar', H.foo1, None, None) == '42'

    # test functions created via functools.partial
    from functools import partial

    curried1 = partial(lambda a, b, c: None, 'A')
    assert formatsig('function', 'curried1', curried1, None, None) == '(b, c)'
    curried2 = partial(lambda a, b, c=42: None, 'A')
    assert formatsig('function', 'curried2', curried2, None, None) == '(b, c=42)'
    curried3 = partial(lambda a, b, *c: None, 'A')
    assert formatsig('function', 'curried3', curried3, None, None) == '(b, *c)'
    curried4 = partial(lambda a, b, c=42, *d, **e: None, 'A')
    assert (
        formatsig('function', 'curried4', curried4, None, None) == '(b, c=42, *d, **e)'
    )


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_process_signature_typing_generic(app):
    actual = do_autodoc(app, 'class', 'target.generic_class.A', {})

    assert list(actual) == [
        '',
        '.. py:class:: A(a, b=None)',
        '   :module: target.generic_class',
        '',
        '   docstring for A',
        '',
    ]


@pytest.mark.sphinx('html', testroot='root')
def test_autodoc_process_signature_typehints(app):
    captured = []

    def process_signature(*args):
        captured.append(args)

    app.connect('autodoc-process-signature', process_signature)

    def func(x: int, y: int) -> int:  # type: ignore[empty-body]
        pass

    directive = make_directive_bridge(app.env)
    inst = app.registry.documenters['function'](directive, 'func')
    inst.fullname = 'func'
    inst.object = func
    inst.objpath = ['func']
    inst.format_signature()
    assert captured == [
        (app, 'function', 'func', func, directive.genopt, '(x: int, y: int)', 'int')
    ]


@pytest.mark.sphinx('html', testroot='root')
def test_get_doc(app):
    directive = make_directive_bridge(app.env)

    def getdocl(objtype, obj):
        inst = app.registry.documenters[objtype](directive, 'tmp')
        inst.parent = object  # dummy
        inst.object = obj
        inst.objpath = [obj.__name__]
        inst.doc_as_attr = False
        inst.format_signature()  # handle docstring signatures!
        ds = inst.get_doc()
        # for testing purposes, concat them and strip the empty line at the end
        res = functools.reduce(operator.iadd, ds, [])[:-1]
        print(res)
        return res

    # objects without docstring
    def f():
        pass

    assert getdocl('function', f) == []

    # standard function, diverse docstring styles...
    def f():
        """Docstring"""

    def g():
        """Docstring"""

    for func in (f, g):
        assert getdocl('function', func) == ['Docstring']

    # first line vs. other lines indentation
    def f():
        """First line

        Other
          lines
        """

    assert getdocl('function', f) == ['First line', '', 'Other', '  lines']

    # charset guessing (this module is encoded in utf-8)
    def f():
        """Döcstring"""

    assert getdocl('function', f) == ['Döcstring']

    # verify that method docstrings get extracted in both normal case
    # and in case of bound method posing as a function
    class J:
        def foo(self):
            """Method docstring"""

    assert getdocl('method', J.foo) == ['Method docstring']
    assert getdocl('function', J().foo) == ['Method docstring']


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_new_documenter(app):
    class MyDocumenter(ModuleLevelDocumenter):
        objtype = 'integer'
        directivetype = 'integer'
        priority = 100

        @classmethod
        def can_document_member(cls, member, membername, isattr, parent):
            return isinstance(member, int)

        def document_members(self, all_members=False):
            return

    app.add_autodocumenter(MyDocumenter)

    options = {'members': 'integer'}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '',
        '',
        '.. py:integer:: integer',
        '   :module: target',
        '',
        '   documentation for the integer',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_attrgetter_using(app):
    directive = make_directive_bridge(app.env)
    directive.genopt['members'] = ALL

    directive.genopt['inherited_members'] = False
    with catch_warnings(record=True):
        _assert_getter_works(app, directive, 'class', 'target.Class', ['meth'])

    directive.genopt['inherited_members'] = True
    with catch_warnings(record=True):
        _assert_getter_works(
            app, directive, 'class', 'target.inheritance.Derived', ['inheritedmeth']
        )


def _assert_getter_works(app, directive, objtype, name, attrs=(), **kw):
    getattr_spy = []

    def _special_getattr(obj, attr_name, *defargs):
        if attr_name in attrs:
            getattr_spy.append((obj, attr_name))
            return None
        return getattr(obj, attr_name, *defargs)

    app.add_autodoc_attrgetter(type, _special_getattr)

    getattr_spy.clear()
    app.registry.documenters[objtype](directive, name).generate(**kw)

    hooked_members = {s[1] for s in getattr_spy}
    documented_members = {s[1] for s in processed_signatures}
    for attr in attrs:
        fullname = f'{name}.{attr}'
        assert attr in hooked_members
        assert fullname not in documented_members, f'{fullname!r} not intercepted'


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_py_module(app):
    # without py:module
    actual = do_autodoc(app, 'method', 'Class.meth')
    assert list(actual) == []
    assert (
        "don't know which module to import for autodocumenting 'Class.meth'"
    ) in app.warning.getvalue()

    # with py:module
    app.env.ref_context['py:module'] = 'target'
    app.warning.truncate(0)

    actual = do_autodoc(app, 'method', 'Class.meth')
    assert list(actual) == [
        '',
        '.. py:method:: Class.meth()',
        '   :module: target',
        '',
        '   Function.',
        '',
    ]
    assert (
        "don't know which module to import for autodocumenting 'Class.meth'"
    ) not in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_decorator(app):
    actual = do_autodoc(app, 'decorator', 'target.decorator.deco1')
    assert list(actual) == [
        '',
        '.. py:decorator:: deco1',
        '   :module: target.decorator',
        '',
        '   docstring for deco1',
        '',
    ]

    actual = do_autodoc(app, 'decorator', 'target.decorator.deco2')
    assert list(actual) == [
        '',
        '.. py:decorator:: deco2(condition, message)',
        '   :module: target.decorator',
        '',
        '   docstring for deco2',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_exception(app):
    actual = do_autodoc(app, 'exception', 'target.CustomEx')
    assert list(actual) == [
        '',
        '.. py:exception:: CustomEx',
        '   :module: target',
        '',
        '   My custom exception.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_warnings(app):
    app.env.current_document.docname = 'dummy'

    # can't import module
    do_autodoc(app, 'module', 'unknown')
    assert "failed to import module 'unknown'" in app.warning.getvalue()

    # missing function
    do_autodoc(app, 'function', 'unknown')
    assert "import for autodocumenting 'unknown'" in app.warning.getvalue()

    do_autodoc(app, 'function', 'target.unknown')
    assert (
        "failed to import function 'unknown' from module 'target'"
    ) in app.warning.getvalue()

    # missing method
    do_autodoc(app, 'method', 'target.Class.unknown')
    assert (
        "failed to import method 'Class.unknown' from module 'target'"
    ) in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_attributes(app):
    options = {
        'synopsis': 'Synopsis',
        'platform': 'Platform',
        'deprecated': None,
    }
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '   :synopsis: Synopsis',
        '   :platform: Platform',
        '   :deprecated:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_members(app):
    # default (no-members)
    actual = do_autodoc(app, 'class', 'target.inheritance.Base')
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
    ]

    # default ALL-members
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # default specific-members
    options = {'members': 'inheritedmeth,inheritedstaticmeth'}
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # ALL-members override autodoc_default_options
    options = {'members': None}
    app.config.autodoc_default_options['members'] = 'inheritedstaticmeth'
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # members override autodoc_default_options
    options = {'members': 'inheritedmeth'}
    app.config.autodoc_default_options['members'] = 'inheritedstaticmeth'
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:method:: Base.inheritedmeth()',
    ]

    # members extends autodoc_default_options
    options = {'members': '+inheritedmeth'}
    app.config.autodoc_default_options['members'] = 'inheritedstaticmeth'
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_exclude_members(app):
    options = {
        'members': None,
        'exclude-members': 'inheritedmeth,inheritedstaticmeth',
    }
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # members vs exclude-members
    options = {
        'members': 'inheritedmeth',
        'exclude-members': 'inheritedmeth',
    }
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
    ]

    # + has no effect when autodoc_default_options are not present
    options = {
        'members': None,
        'exclude-members': '+inheritedmeth,inheritedstaticmeth',
    }
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # exclude-members overrides autodoc_default_options
    options = {
        'members': None,
        'exclude-members': 'inheritedmeth',
    }
    app.config.autodoc_default_options['exclude-members'] = 'inheritedstaticmeth'
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]

    # exclude-members extends autodoc_default_options
    options = {
        'members': None,
        'exclude-members': '+inheritedmeth',
    }
    app.config.autodoc_default_options['exclude-members'] = 'inheritedstaticmeth'
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # no exclude-members causes use autodoc_default_options
    options = {'members': None}
    app.config.autodoc_default_options['exclude-members'] = (
        'inheritedstaticmeth,inheritedmeth'
    )
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
    ]

    # empty exclude-members cancels autodoc_default_options
    options = {
        'members': None,
        'exclude-members': None,
    }
    app.config.autodoc_default_options['exclude-members'] = (
        'inheritedstaticmeth,inheritedmeth'
    )
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base()',
        '   .. py:attribute:: Base.inheritedattr',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_undoc_members(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]

    # use autodoc_default_options
    options = {'members': None}
    app.config.autodoc_default_options['undoc-members'] = None
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]

    # options negation work check
    options = {
        'members': None,
        'no-undoc-members': None,
    }
    app.config.autodoc_default_options['undoc-members'] = None
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_undoc_members_for_metadata_only(app):
    # metadata only member is not displayed
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.metadata', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.metadata',
        '',
    ]

    # metadata only member is displayed when undoc-member given
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.metadata', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.metadata',
        '',
        '',
        '.. py:function:: foo()',
        '   :module: target.metadata',
        '',
        '   :meta metadata-only-docstring:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherited_members(app):
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert list(filter(lambda l: 'method::' in l, actual)) == [
        '   .. py:method:: Derived.another_inheritedmeth()',
        '   .. py:method:: Derived.inheritedclassmeth()',
        '   .. py:method:: Derived.inheritedmeth()',
        '   .. py:method:: Derived.inheritedstaticmeth(cls)',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherited_members_Base(app):
    options = {
        'members': None,
        'inherited-members': 'Base',
        'special-members': None,
    }

    # check methods for object class are shown
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert '   .. py:method:: Derived.inheritedmeth()' in actual
    assert '   .. py:method:: Derived.inheritedclassmeth' not in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherited_members_None(app):
    options = {
        'members': None,
        'inherited-members': 'None',
        'special-members': None,
    }

    # check methods for object class are shown
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert '   .. py:method:: Derived.__init__()' in actual
    assert '   .. py:method:: Derived.__str__()' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_imported_members(app):
    options = {
        'members': None,
        'imported-members': None,
        'ignore-module-all': None,
    }
    actual = do_autodoc(app, 'module', 'target', options)
    assert (
        '.. py:function:: function_to_be_imported(app: ~sphinx.application.Sphinx | None) -> str'
    ) in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_special_members(app):
    # specific special methods
    options = {
        'undoc-members': None,
        'special-members': '__init__,__special1__',
    }
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
    ]

    # combination with specific members
    options = {
        'members': 'attr,docattr',
        'undoc-members': None,
        'special-members': '__init__,__special1__',
    }
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
    ]

    # all special methods
    options = {
        'members': None,
        'undoc-members': None,
        'special-members': None,
    }
    if sys.version_info >= (3, 13, 0, 'alpha', 5):
        options['exclude-members'] = '__static_attributes__,__firstlineno__'
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class.__annotations__',
        '   .. py:attribute:: Class.__dict__',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:attribute:: Class.__module__',
        '   .. py:method:: Class.__special1__()',
        '   .. py:method:: Class.__special2__()',
        '   .. py:attribute:: Class.__weakref__',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]

    # specific special methods from autodoc_default_options
    options = {'undoc-members': None}
    app.config.autodoc_default_options['special-members'] = '__special2__'
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__special2__()',
    ]

    # specific special methods option with autodoc_default_options
    options = {
        'undoc-members': None,
        'special-members': '__init__,__special1__',
    }
    app.config.autodoc_default_options['special-members'] = '__special2__'
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
    ]

    # specific special methods merge with autodoc_default_options
    options = {
        'undoc-members': None,
        'special-members': '+__init__,__special1__',
    }
    app.config.autodoc_default_options['special-members'] = '__special2__'
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
        '   .. py:method:: Class.__special2__()',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_ignore_module_all(app):
    # default (no-ignore-module-all)
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(filter(lambda l: 'class::' in l, actual)) == [
        '.. py:class:: Class(arg)',
    ]

    # ignore-module-all
    options = {
        'members': None,
        'ignore-module-all': None,
    }
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(filter(lambda l: 'class::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '.. py:class:: CustomDict',
        '.. py:class:: InnerChild()',
        '.. py:class:: InstAttCls()',
        '.. py:class:: Outer()',
        '   .. py:class:: Outer.Inner()',
        '.. py:class:: StrRepr',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_noindex(app):
    options = {'no-index': None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '   :no-index:',
        '',
    ]

    # TODO: :no-index: should be propagated to children of target item.

    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(actual) == [
        '',
        '.. py:class:: Base()',
        '   :no-index:',
        '   :module: target.inheritance',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_subclass_of_builtin_class(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.CustomDict', options)
    assert list(actual) == [
        '',
        '.. py:class:: CustomDict',
        '   :module: target',
        '',
        '   Docstring.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inner_class(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.Outer', options)
    assert list(actual) == [
        '',
        '.. py:class:: Outer()',
        '   :module: target',
        '',
        '   Foo',
        '',
        '',
        '   .. py:class:: Outer.Inner()',
        '      :module: target',
        '',
        '      Foo',
        '',
        '',
        '      .. py:method:: Outer.Inner.meth()',
        '         :module: target',
        '',
        '         Foo',
        '',
        '',
        '   .. py:attribute:: Outer.factory',
        '      :module: target',
        '',
        '      alias of :py:class:`dict`',
    ]

    actual = do_autodoc(app, 'class', 'target.Outer.Inner', options)
    assert list(actual) == [
        '',
        '.. py:class:: Inner()',
        '   :module: target.Outer',
        '',
        '   Foo',
        '',
        '',
        '   .. py:method:: Inner.meth()',
        '      :module: target.Outer',
        '',
        '      Foo',
        '',
    ]

    options['show-inheritance'] = None
    actual = do_autodoc(app, 'class', 'target.InnerChild', options)
    assert list(actual) == [
        '',
        '.. py:class:: InnerChild()',
        '   :module: target',
        '',
        '   Bases: :py:class:`~target.Outer.Inner`',
        '',
        '   InnerChild docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_classmethod(app):
    actual = do_autodoc(app, 'method', 'target.inheritance.Base.inheritedclassmeth')
    assert list(actual) == [
        '',
        '.. py:method:: Base.inheritedclassmeth()',
        '   :module: target.inheritance',
        '   :classmethod:',
        '',
        '   Inherited class method.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_staticmethod(app):
    actual = do_autodoc(app, 'method', 'target.inheritance.Base.inheritedstaticmeth')
    assert list(actual) == [
        '',
        '.. py:method:: Base.inheritedstaticmeth(cls)',
        '   :module: target.inheritance',
        '   :staticmethod:',
        '',
        '   Inherited static method.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_descriptor(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.descriptor.Class', options)
    assert list(actual) == [
        '',
        '.. py:class:: Class()',
        '   :module: target.descriptor',
        '',
        '',
        '   .. py:attribute:: Class.descr',
        '      :module: target.descriptor',
        '',
        '      Descriptor instance docstring.',
        '',
        '',
        '   .. py:property:: Class.prop',
        '      :module: target.descriptor',
        '',
        '      Property.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_cached_property(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.cached_property.Foo', options)
    assert list(actual) == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.cached_property',
        '',
        '',
        '   .. py:property:: Foo.prop',
        '      :module: target.cached_property',
        '      :type: int',
        '',
        '',
        '   .. py:property:: Foo.prop_with_type_comment',
        '      :module: target.cached_property',
        '      :type: int',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_member_order(app):
    # case member-order='bysource'
    options = {
        'members': None,
        'member-order': 'bysource',
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.undocmeth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class._private_inst_attr',
    ]

    # case member-order='groupwise'
    options = {
        'members': None,
        'member-order': 'groupwise',
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        # class methods
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        # static methods
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:method:: Class.b_staticmeth()',
        # regular methods
        '   .. py:method:: Class.excludemeth()',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.undocmeth()',
        '   .. py:attribute:: Class._private_inst_attr',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:attribute:: Class.udocattr',
    ]

    # case member-order=None
    options = {
        'members': None,
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class._private_inst_attr',
        '   .. py:method:: Class.a_staticmeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:method:: Class.b_staticmeth()',
        '   .. py:attribute:: Class.docattr',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_module_member_order(app):
    # case member-order='bysource'
    options = {
        'members': 'foo, Bar, baz, qux, Quux, foobar',
        'member-order': 'bysource',
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.sort_by_all', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:module:: target.sort_by_all',
        '.. py:function:: baz()',
        '.. py:function:: foo()',
        '.. py:class:: Bar()',
        '.. py:class:: Quux()',
        '.. py:function:: foobar()',
        '.. py:function:: qux()',
    ]

    # case member-order='bysource' and ignore-module-all
    options = {
        'members': 'foo, Bar, baz, qux, Quux, foobar',
        'member-order': 'bysource',
        'undoc-members': None,
        'ignore-module-all': None,
    }
    actual = do_autodoc(app, 'module', 'target.sort_by_all', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:module:: target.sort_by_all',
        '.. py:function:: foo()',
        '.. py:class:: Bar()',
        '.. py:function:: baz()',
        '.. py:function:: qux()',
        '.. py:class:: Quux()',
        '.. py:function:: foobar()',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_module_scope(app):
    app.env.current_document.autodoc_module = 'target'
    actual = do_autodoc(app, 'attribute', 'Class.mdocattr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.mdocattr',
        '   :module: target',
        '   :value: <_io.StringIO object>',
        '',
        '   should be documented as well - süß',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_scope(app):
    app.env.current_document.autodoc_module = 'target'
    app.env.current_document.autodoc_class = 'Class'
    actual = do_autodoc(app, 'attribute', 'mdocattr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.mdocattr',
        '   :module: target',
        '   :value: <_io.StringIO object>',
        '',
        '   should be documented as well - süß',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_attributes(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.AttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: AttCls()',
        '   :module: target',
        '',
        '',
        '   .. py:attribute:: AttCls.a1',
        '      :module: target',
        '      :value: hello world',
        '',
        '',
        '   .. py:attribute:: AttCls.a2',
        '      :module: target',
        '      :value: None',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_instance_attributes(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.InstAttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :value: 'a'",
        '',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca2',
        '      :module: target',
        "      :value: 'b'",
        '',
        '      Doc comment for InstAttCls.ca2. One line only.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca3',
        '      :module: target',
        "      :value: 'c'",
        '',
        '      Docstring for class attribute InstAttCls.ca3.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ia2',
        '      :module: target',
        '',
        '      Docstring for instance attribute InstAttCls.ia2.',
        '',
    ]

    # pick up arbitrary attributes
    options = {
        'members': 'ca1,ia1',
    }
    actual = do_autodoc(app, 'class', 'target.InstAttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :value: 'a'",
        '',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '',
        '',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_instance_attributes(app):
    actual = do_autodoc(app, 'attribute', 'target.InstAttCls.ia1')
    assert list(actual) == [
        '',
        '.. py:attribute:: InstAttCls.ia1',
        '   :module: target',
        '',
        '   Doc comment for instance attribute InstAttCls.ia1',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_slots(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.slots', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.slots',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Bar.attr1',
        '      :module: target.slots',
        '      :type: int',
        '',
        '      docstring of attr1',
        '',
        '',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.slots',
        '',
        '      docstring of instance attr2',
        '',
        '',
        '   .. py:attribute:: Bar.attr3',
        '      :module: target.slots',
        '',
        '',
        '.. py:class:: Baz()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Baz.attr',
        '      :module: target.slots',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr',
        '      :module: target.slots',
        '',
    ]


class _EnumFormatter:
    def __init__(self, name: str, *, module: str = 'target.enums') -> None:
        self.name = name
        self.module = module

    @property
    def target(self) -> str:
        """The autodoc target class."""
        return f'{self.module}.{self.name}'

    def subtarget(self, name: str) -> str:
        """The autodoc sub-target (an attribute, method, etc)."""
        return f'{self.target}.{name}'

    def _node(
        self,
        role: str,
        name: str,
        doc: str,
        *,
        args: str,
        indent: int,
        **options: Any,
    ) -> list[str]:
        prefix = indent * ' '
        tab = ' ' * 3

        def rst_option(name: str, value: Any) -> str:
            value = '' if value == 1 else value  # note True == 1.
            return f'{prefix}{tab}:{name}: {value!s}'.rstrip()

        lines = [
            '',
            f'{prefix}.. py:{role}:: {name}{args}',
            f'{prefix}{tab}:module: {self.module}',
            *itertools.starmap(rst_option, options.items()),
        ]
        if doc:
            lines.extend(['', f'{prefix}{tab}{doc}'])
        lines.append('')
        return lines

    def entry(
        self,
        entry_name: str,
        doc: str = '',
        *,
        role: str,
        args: str = '',
        indent: int = 3,
        **rst_options: Any,
    ) -> list[str]:
        """Get the RST lines for a named attribute, method, etc."""
        qualname = f'{self.name}.{entry_name}'
        return self._node(role, qualname, doc, args=args, indent=indent, **rst_options)

    def preamble_lookup(
        self, doc: str, *, indent: int = 0, **options: Any
    ) -> list[str]:
        assert doc, (
            f'enumeration class {self.target!r} should have an explicit docstring'
        )

        args = self._preamble_args(functional_constructor=False)
        return self._preamble(doc=doc, args=args, indent=indent, **options)

    def preamble_constructor(
        self, doc: str, *, indent: int = 0, **options: Any
    ) -> list[str]:
        assert doc, (
            f'enumeration class {self.target!r} should have an explicit docstring'
        )

        args = self._preamble_args(functional_constructor=True)
        return self._preamble(doc=doc, args=args, indent=indent, **options)

    def _preamble(
        self, *, doc: str, args: str, indent: int = 0, **options: Any
    ) -> list[str]:
        """Generate the preamble of the class being documented."""
        return self._node('class', self.name, doc, args=args, indent=indent, **options)

    @staticmethod
    def _preamble_args(functional_constructor: bool = False):
        """EnumType.__call__() is a dual-purpose method:

        * Look an enum member (valid only if the enum has members)
        * Create a new enum class (functional API)
        """
        if sys.version_info[:2] >= (3, 14):
            if functional_constructor:
                return (
                    '(new_class_name, /, names, *, module=None, '
                    'qualname=None, type=None, start=1, boundary=None)'
                )
            else:
                return '(*values)'
        if sys.version_info[:2] >= (3, 13) or sys.version_info[:3] >= (3, 12, 3):
            if functional_constructor:
                return (
                    '(new_class_name, /, names, *, module=None, '
                    'qualname=None, type=None, start=1, boundary=None)'
                )
            else:
                return '(*values)'
        if sys.version_info[:2] >= (3, 12):
            return (
                '(value, names=None, *values, module=None, '
                'qualname=None, type=None, start=1, boundary=None)'
            )
        return '(value)'

    def method(
        self,
        name: str,
        doc: str,
        *flags: str,
        args: str = '()',
        indent: int = 3,
    ) -> list[str]:
        rst_options = dict.fromkeys(flags, '')
        return self.entry(
            name, doc, role='method', args=args, indent=indent, **rst_options
        )

    def member(self, name: str, value: Any, doc: str, *, indent: int = 3) -> list[str]:
        rst_options = {'value': repr(value)}
        return self.entry(name, doc, role='attribute', indent=indent, **rst_options)


@pytest.fixture
def autodoc_enum_options() -> dict[str, object]:
    """Default autodoc options to use when testing enum's documentation."""
    return {'members': None, 'undoc-members': None}


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumCls')
    options = autodoc_enum_options | {'private-members': None}

    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method(
            'say_goodbye', 'a classmethod says good-bye to you.', 'classmethod'
        ),
        *fmt.method('say_hello', 'a method says hello to you.'),
        *fmt.member('val1', 12, 'doc for val1'),
        *fmt.member('val2', 23, 'doc for val2'),
        *fmt.member('val3', 34, 'doc for val3'),
        *fmt.member('val4', 34, ''),  # val4 is alias of val3
    ]

    # Inherited members exclude the native Enum API (in particular
    # the 'name' and 'value' properties), unless they were explicitly
    # redefined by the user in one of the bases.
    actual = do_autodoc(app, 'class', fmt.target, options | {'inherited-members': None})
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method(
            'say_goodbye', 'a classmethod says good-bye to you.', 'classmethod'
        ),
        *fmt.method('say_hello', 'a method says hello to you.'),
        *fmt.member('val1', 12, 'doc for val1'),
        *fmt.member('val2', 23, 'doc for val2'),
        *fmt.member('val3', 34, 'doc for val3'),
        *fmt.member('val4', 34, ''),  # val4 is alias of val3
    ]

    # checks for an attribute of EnumCls
    actual = do_autodoc(app, 'attribute', fmt.subtarget('val1'))
    assert list(actual) == fmt.member('val1', 12, 'doc for val1', indent=0)


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class_with_data_type(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithDataType')

    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.member('x', 'x', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'inherited'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.member('x', 'x', ''),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class_with_mixin_type(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinType')

    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'docstring', 'classmethod'),
        *fmt.method('say_hello', 'docstring'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class_with_mixin_type_and_inheritence(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinTypeInherit')

    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('say_goodbye', 'inherited', 'classmethod'),
        *fmt.method('say_hello', 'inherited'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class_with_mixin_enum_type(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinEnumType')

    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        # override() is overridden at the class level so it should be rendered
        *fmt.method('override', 'overridden'),
        # say_goodbye() and say_hello() are not rendered since they are inherited
        *fmt.member('x', 'x', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('override', 'overridden'),
        *fmt.method('say_goodbye', 'inherited', 'classmethod'),
        *fmt.method('say_hello', 'inherited'),
        *fmt.member('x', 'x', ''),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class_with_mixin_and_data_type(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithMixinAndDataType')

    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('say_goodbye', 'overridden', 'classmethod'),
        *fmt.method('say_hello', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    # add the special member __str__ (but not the inherited members)
    options = autodoc_enum_options | {'special-members': '__str__'}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('__str__', 'overridden'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('say_goodbye', 'overridden', 'classmethod'),
        *fmt.method('say_hello', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('say_goodbye', 'overridden', 'classmethod'),
        *fmt.method('say_hello', 'overridden'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_with_parent_enum(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumClassWithParentEnum')

    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('isupper', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    # add the special member __str__ (but not the inherited members)
    options = autodoc_enum_options | {'special-members': '__str__'}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.method('__str__', 'overridden'),
        *fmt.method('isupper', 'overridden'),
        *fmt.member('x', 'X', ''),
    ]

    options = autodoc_enum_options | {'inherited-members': None}
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_lookup('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'overridden'),
        *fmt.method('override', 'inherited'),
        *fmt.method('say_goodbye', 'inherited', 'classmethod'),
        *fmt.method('say_hello', 'inherited'),
        *fmt.entry('value', 'uppercased', role='property'),
        *fmt.member('x', 'X', ''),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_sunder_method(app, autodoc_enum_options):
    PRIVATE = {'private-members': None}  # sunder methods are recognized as private

    fmt = _EnumFormatter('EnumSunderMissingInNonEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options | PRIVATE)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumSunderMissingInEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options | PRIVATE)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumSunderMissingInDataType')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options | PRIVATE)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumSunderMissingInClass')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options | PRIVATE)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'docstring', 'classmethod', args='(value)'),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_inherited_sunder_method(app, autodoc_enum_options):
    options = autodoc_enum_options | {
        'private-members': None,
        'inherited-members': None,
    }

    fmt = _EnumFormatter('EnumSunderMissingInNonEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'inherited', 'classmethod', args='(value)'),
    ]

    fmt = _EnumFormatter('EnumSunderMissingInEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'inherited', 'classmethod', args='(value)'),
    ]

    fmt = _EnumFormatter('EnumSunderMissingInDataType')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'inherited', 'classmethod', args='(value)'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'inherited'),
    ]

    fmt = _EnumFormatter('EnumSunderMissingInClass')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.method('_missing_', 'docstring', 'classmethod', args='(value)'),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_custom_name_property(app, autodoc_enum_options):
    fmt = _EnumFormatter('EnumNamePropertyInNonEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumNamePropertyInEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumNamePropertyInDataType')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [*fmt.preamble_constructor('this is enum class')]

    fmt = _EnumFormatter('EnumNamePropertyInClass')
    actual = do_autodoc(app, 'class', fmt.target, autodoc_enum_options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'docstring', role='property'),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_inherited_custom_name_property(app, autodoc_enum_options):
    options = autodoc_enum_options | {'inherited-members': None}

    fmt = _EnumFormatter('EnumNamePropertyInNonEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'inherited', role='property'),
    ]

    fmt = _EnumFormatter('EnumNamePropertyInEnumMixin')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'inherited', role='property'),
    ]

    fmt = _EnumFormatter('EnumNamePropertyInDataType')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('dtype', 'docstring', role='property'),
        *fmt.method('isupper', 'inherited'),
        *fmt.entry('name', 'inherited', role='property'),
    ]

    fmt = _EnumFormatter('EnumNamePropertyInClass')
    actual = do_autodoc(app, 'class', fmt.target, options)
    assert list(actual) == [
        *fmt.preamble_constructor('this is enum class'),
        *fmt.entry('name', 'docstring', role='property'),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_descriptor_class(app):
    options = {
        'members': 'CustomDataDescriptor,CustomDataDescriptor2',
    }
    actual = do_autodoc(app, 'module', 'target.descriptor', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.descriptor',
        '',
        '',
        '.. py:class:: CustomDataDescriptor(doc)',
        '   :module: target.descriptor',
        '',
        '   Descriptor class docstring.',
        '',
        '',
        '   .. py:method:: CustomDataDescriptor.meth()',
        '      :module: target.descriptor',
        '',
        '      Function.',
        '',
        '',
        '.. py:class:: CustomDataDescriptor2(doc)',
        '   :module: target.descriptor',
        '',
        '   Descriptor class with custom metaclass docstring.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_automethod_for_builtin(app):
    actual = do_autodoc(app, 'method', 'builtins.int.__add__')
    assert list(actual) == [
        '',
        '.. py:method:: int.__add__(value, /)',
        '   :module: builtins',
        '',
        '   Return self+value.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_automethod_for_decorated(app):
    actual = do_autodoc(app, 'method', 'target.decorator.Bar.meth')
    assert list(actual) == [
        '',
        '.. py:method:: Bar.meth(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_abstractmethods(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.abstractmethods', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.abstractmethods',
        '',
        '',
        '.. py:class:: Base()',
        '   :module: target.abstractmethods',
        '',
        '',
        '   .. py:method:: Base.abstractmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '',
        '',
        '   .. py:method:: Base.classmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :classmethod:',
        '',
        '',
        '   .. py:method:: Base.coroutinemeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :async:',
        '',
        '',
        '   .. py:method:: Base.meth()',
        '      :module: target.abstractmethods',
        '',
        '',
        '   .. py:property:: Base.prop',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '',
        '',
        '   .. py:method:: Base.staticmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :staticmethod:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_partialfunction(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.partialfunction', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.partialfunction',
        '',
        '',
        '.. py:function:: func1(a, b, c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func1',
        '',
        '',
        '.. py:function:: func2(b, c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func1',
        '',
        '',
        '.. py:function:: func3(c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func3',
        '',
        '',
        '.. py:function:: func4()',
        '   :module: target.partialfunction',
        '',
        '   docstring of func3',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_imported_partialfunction_should_not_shown_without_imported_members(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.imported_members', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.imported_members',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_bound_method(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.bound_method', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.bound_method',
        '',
        '',
        '.. py:function:: bound_method()',
        '   :module: target.bound_method',
        '',
        '   Method docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_partialmethod(app):
    expected = [
        '',
        '.. py:class:: Cell()',
        '   :module: target.partialmethod',
        '',
        '   An example for partialmethod.',
        '',
        '   refs: https://docs.python.jp/3/library/functools.html#functools.partialmethod',
        '',
        '',
        '   .. py:method:: Cell.set_alive()',
        '      :module: target.partialmethod',
        '',
        '      Make a cell alive.',
        '',
        '',
        '   .. py:method:: Cell.set_state(state)',
        '      :module: target.partialmethod',
        '',
        '      Update state of cell to *state*.',
        '',
    ]

    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.partialmethod.Cell', options)
    assert list(actual) == expected


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_partialmethod_undoc_members(app):
    expected = [
        '',
        '.. py:class:: Cell()',
        '   :module: target.partialmethod',
        '',
        '   An example for partialmethod.',
        '',
        '   refs: https://docs.python.jp/3/library/functools.html#functools.partialmethod',
        '',
        '',
        '   .. py:method:: Cell.set_alive()',
        '      :module: target.partialmethod',
        '',
        '      Make a cell alive.',
        '',
        '',
        '   .. py:method:: Cell.set_dead()',
        '      :module: target.partialmethod',
        '',
        '',
        '   .. py:method:: Cell.set_state(state)',
        '      :module: target.partialmethod',
        '',
        '      Update state of cell to *state*.',
        '',
    ]

    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.partialmethod.Cell', options)
    assert list(actual) == expected


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_typed_instance_variables(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.typed_vars', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typed_vars',
        '',
        '',
        '.. py:attribute:: Alias',
        '   :module: target.typed_vars',
        '',
        '   alias of :py:class:`~target.typed_vars.Derived`',
        '',
        '.. py:class:: Class()',
        '   :module: target.typed_vars',
        '',
        '',
        '   .. py:attribute:: Class.attr1',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Class.attr2',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Class.attr3',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Class.attr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr4',
        '',
        '',
        '   .. py:attribute:: Class.attr5',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr5',
        '',
        '',
        '   .. py:attribute:: Class.attr6',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr6',
        '',
        '',
        '   .. py:attribute:: Class.descr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      This is descr4',
        '',
        '',
        '.. py:class:: Derived()',
        '   :module: target.typed_vars',
        '',
        '',
        '   .. py:attribute:: Derived.attr7',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '.. py:data:: attr1',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr1',
        '',
        '',
        '.. py:data:: attr2',
        '   :module: target.typed_vars',
        '   :type: str',
        '',
        '   attr2',
        '',
        '',
        '.. py:data:: attr3',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr3',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_typed_inherited_instance_variables(app):
    options = {
        'members': None,
        'undoc-members': None,
        'inherited-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.typed_vars.Derived', options)
    assert list(actual) == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.typed_vars',
        '',
        '',
        '   .. py:attribute:: Derived.attr1',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Derived.attr2',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Derived.attr3',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '',
        '',
        '   .. py:attribute:: Derived.attr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr4',
        '',
        '',
        '   .. py:attribute:: Derived.attr5',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr5',
        '',
        '',
        '   .. py:attribute:: Derived.attr6',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '      attr6',
        '',
        '',
        '   .. py:attribute:: Derived.attr7',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Derived.descr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_GenericAlias(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.genericalias', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.genericalias',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.genericalias',
        '',
        '',
        '   .. py:attribute:: Class.T',
        '      :module: target.genericalias',
        '',
        '      A list of int',
        '',
        '      alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
        '',
        '.. py:data:: L',
        '   :module: target.genericalias',
        '',
        '   A list of Class',
        '',
        '   alias of :py:class:`~typing.List`\\ '
        '[:py:class:`~target.genericalias.Class`]',
        '',
        '',
        '.. py:data:: T',
        '   :module: target.genericalias',
        '',
        '   A list of int',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_TypeVar(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.typevar', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typevar',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.typevar',
        '',
        '',
        '   .. py:class:: Class.T1',
        '      :module: target.typevar',
        '',
        '      T1',
        '',
        "      alias of TypeVar('T1')",
        '',
        '',
        '   .. py:class:: Class.T6',
        '      :module: target.typevar',
        '',
        '      T6',
        '',
        '      alias of :py:class:`~datetime.date`',
        '',
        '',
        '.. py:class:: T1',
        '   :module: target.typevar',
        '',
        '   T1',
        '',
        "   alias of TypeVar('T1')",
        '',
        '',
        '.. py:class:: T3',
        '   :module: target.typevar',
        '',
        '   T3',
        '',
        "   alias of TypeVar('T3', int, str)",
        '',
        '',
        '.. py:class:: T4',
        '   :module: target.typevar',
        '',
        '   T4',
        '',
        "   alias of TypeVar('T4', covariant=True)",
        '',
        '',
        '.. py:class:: T5',
        '   :module: target.typevar',
        '',
        '   T5',
        '',
        "   alias of TypeVar('T5', contravariant=True)",
        '',
        '',
        '.. py:class:: T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`~datetime.date`',
        '',
        '',
        '.. py:class:: T7',
        '   :module: target.typevar',
        '',
        '   T7',
        '',
        "   alias of TypeVar('T7', bound=\\ :py:class:`int`)",
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_Annotated(app):
    options = {
        'members': None,
        'member-order': 'bysource',
    }
    actual = do_autodoc(app, 'module', 'target.annotated', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.annotated',
        '',
        '',
        '.. py:class:: FuncValidator(func: function)',
        '   :module: target.annotated',
        '',
        '',
        '.. py:class:: MaxLen(max_length: int, whitelisted_words: list[str])',
        '   :module: target.annotated',
        '',
        '',
        '.. py:data:: ValidatedString',
        '   :module: target.annotated',
        '',
        '   Type alias for a validated string.',
        '',
        '   alias of :py:class:`~typing.Annotated`\\ [:py:class:`str`, '
        ':py:class:`~target.annotated.FuncValidator`\\ (func=\\ :py:class:`~target.annotated.validate`)]',
        '',
        '',
        ".. py:function:: hello(name: ~typing.Annotated[str, 'attribute']) -> None",
        '   :module: target.annotated',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: AnnotatedAttributes()',
        '   :module: target.annotated',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: AnnotatedAttributes.name',
        '      :module: target.annotated',
        "      :type: ~typing.Annotated[str, 'attribute']",
        '',
        '      Docstring about the ``name`` attribute.',
        '',
        '',
        '   .. py:attribute:: AnnotatedAttributes.max_len',
        '      :module: target.annotated',
        "      :type: list[~typing.Annotated[str, ~target.annotated.MaxLen(max_length=10, whitelisted_words=['word_one', 'word_two'])]]",
        '',
        '      Docstring about the ``max_len`` attribute.',
        '',
        '',
        '   .. py:attribute:: AnnotatedAttributes.validated',
        '      :module: target.annotated',
        '      :type: ~typing.Annotated[str, ~target.annotated.FuncValidator(func=~target.annotated.validate)]',
        '',
        '      Docstring about the ``validated`` attribute.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_TYPE_CHECKING(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.TYPE_CHECKING', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.TYPE_CHECKING',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.TYPE_CHECKING',
        '',
        '',
        '   .. py:attribute:: Foo.attr1',
        '      :module: target.TYPE_CHECKING',
        '      :type: ~io.StringIO',
        '',
        '',
        '.. py:function:: spam(ham: ~collections.abc.Iterable[str]) -> tuple[~gettext.NullTranslations, bool]',
        '   :module: target.TYPE_CHECKING',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_TYPE_CHECKING_circular_import(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'circular_import', options)
    assert list(actual) == [
        '',
        '.. py:module:: circular_import',
        '',
    ]
    assert sys.modules['circular_import'].a is sys.modules['circular_import.a']


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatch(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.singledispatch', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.singledispatch',
        '',
        '',
        '.. py:function:: func(arg, kwarg=None)',
        '                 func(arg: float, kwarg=None)',
        '                 func(arg: int, kwarg=None)',
        '                 func(arg: str, kwarg=None)',
        '                 func(arg: dict, kwarg=None)',
        '   :module: target.singledispatch',
        '',
        '   A function for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.singledispatchmethod', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.singledispatchmethod',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.singledispatchmethod',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.meth(arg, kwarg=None)',
        '                  Foo.meth(arg: float, kwarg=None)',
        '                  Foo.meth(arg: int, kwarg=None)',
        '                  Foo.meth(arg: str, kwarg=None)',
        '                  Foo.meth(arg: dict, kwarg=None)',
        '      :module: target.singledispatchmethod',
        '',
        '      A method for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod_automethod(app):
    options = {}
    actual = do_autodoc(app, 'method', 'target.singledispatchmethod.Foo.meth', options)
    assert list(actual) == [
        '',
        '.. py:method:: Foo.meth(arg, kwarg=None)',
        '               Foo.meth(arg: float, kwarg=None)',
        '               Foo.meth(arg: int, kwarg=None)',
        '               Foo.meth(arg: str, kwarg=None)',
        '               Foo.meth(arg: dict, kwarg=None)',
        '   :module: target.singledispatchmethod',
        '',
        '   A method for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod_classmethod(app):
    options = {'members': None}
    actual = do_autodoc(
        app, 'module', 'target.singledispatchmethod_classmethod', options
    )

    assert list(actual) == [
        '',
        '.. py:module:: target.singledispatchmethod_classmethod',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.singledispatchmethod_classmethod',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.class_meth(arg, kwarg=None)',
        '                  Foo.class_meth(arg: float, kwarg=None)',
        '                  Foo.class_meth(arg: int, kwarg=None)',
        '                  Foo.class_meth(arg: str, kwarg=None)',
        '                  Foo.class_meth(arg: dict, kwarg=None)',
        '      :module: target.singledispatchmethod_classmethod',
        '      :classmethod:',
        '',
        '      A class method for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod_classmethod_automethod(app):
    options = {}
    actual = do_autodoc(
        app, 'method', 'target.singledispatchmethod_classmethod.Foo.class_meth', options
    )

    assert list(actual) == [
        '',
        '.. py:method:: Foo.class_meth(arg, kwarg=None)',
        '               Foo.class_meth(arg: float, kwarg=None)',
        '               Foo.class_meth(arg: int, kwarg=None)',
        '               Foo.class_meth(arg: str, kwarg=None)',
        '               Foo.class_meth(arg: dict, kwarg=None)',
        '   :module: target.singledispatchmethod_classmethod',
        '   :classmethod:',
        '',
        '   A class method for general use.',
        '',
    ]


@pytest.mark.skipif(
    sys.version_info[:2] >= (3, 13),
    reason='Cython does not support Python 3.13 yet.',
)
@pytest.mark.skipif(pyximport is None, reason='cython is not installed')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_cython(app):
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.cython', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.cython',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.cython',
        '',
        '   Docstring.',
        '',
        '',
        '   .. py:method:: Class.meth(name: str, age: int = 0) -> None',
        '      :module: target.cython',
        '',
        '      Docstring.',
        '',
        '',
        '.. py:function:: foo(x: int, *args, y: str, **kwargs)',
        '   :module: target.cython',
        '',
        '   Docstring.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_final(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.final', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.final',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.final',
        '   :final:',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Class.meth1()',
        '      :module: target.final',
        '      :final:',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Class.meth2()',
        '      :module: target.final',
        '',
        '      docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_overload(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.overload', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.overload',
        '',
        '',
        '.. py:class:: Bar(x: int, y: int)',
        '              Bar(x: str, y: str)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Baz(x: int, y: int)',
        '              Baz(x: str, y: str)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Foo(x: int, y: int)',
        '              Foo(x: str, y: str)',
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
        '   .. py:method:: Math.sum(x: int, y: int = 0) -> int',
        '                  Math.sum(x: float, y: float = 0.0) -> float',
        '                  Math.sum(x: str, y: str = None) -> str',
        '      :module: target.overload',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: sum(x: int, y: int = 0) -> int',
        '                 sum(x: float, y: float = 0.0) -> float',
        '                 sum(x: str, y: str = None) -> str',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_overload2(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.overload2', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.overload2',
        '',
        '',
        '.. py:class:: Baz(x: int, y: int)',
        '              Baz(x: str, y: str)',
        '   :module: target.overload2',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_pymodule_for_ModuleLevelDocumenter(app):
    app.env.ref_context['py:module'] = 'target.classes'
    actual = do_autodoc(app, 'class', 'Foo')
    assert list(actual) == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.classes',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_pymodule_for_ClassLevelDocumenter(app):
    app.env.ref_context['py:module'] = 'target.methods'
    actual = do_autodoc(app, 'method', 'Base.meth')
    assert list(actual) == [
        '',
        '.. py:method:: Base.meth()',
        '   :module: target.methods',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_pyclass_for_ClassLevelDocumenter(app):
    app.env.ref_context['py:module'] = 'target.methods'
    app.env.ref_context['py:class'] = 'Base'
    actual = do_autodoc(app, 'method', 'meth')
    assert list(actual) == [
        '',
        '.. py:method:: Base.meth()',
        '   :module: target.methods',
        '',
    ]


@pytest.mark.sphinx('dummy', testroot='ext-autodoc')
def test_autodoc(app):
    app.build(force_all=True)

    content = app.env.get_doctree('index')
    assert isinstance(content[3], addnodes.desc)
    assert content[3][0].astext() == 'autodoc_dummy_module.test()'
    assert content[3][1].astext() == 'Dummy function using dummy.*'

    # issue sphinx-doc/sphinx#2437
    assert content[11][-1].astext() == (
        """Dummy class Bar with alias.



my_name

alias of Foo"""
    )
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_name_conflict(app):
    actual = do_autodoc(app, 'class', 'target.name_conflict.foo')
    assert list(actual) == [
        '',
        '.. py:class:: foo()',
        '   :module: target.name_conflict',
        '',
        '   docstring of target.name_conflict::foo.',
        '',
    ]

    actual = do_autodoc(app, 'class', 'target.name_conflict.foo.bar')
    assert list(actual) == [
        '',
        '.. py:class:: bar()',
        '   :module: target.name_conflict.foo',
        '',
        '   docstring of target.name_conflict.foo::bar.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_name_mangling(app):
    options = {
        'members': None,
        'undoc-members': None,
        'private-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.name_mangling', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.name_mangling',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: target.name_mangling',
        '',
        '',
        '   .. py:attribute:: Bar._Baz__email',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '      a member having mangled-like name',
        '',
        '',
        '   .. py:attribute:: Bar.__address',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.name_mangling',
        '',
        '',
        '   .. py:attribute:: Foo.__age',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '',
        '   .. py:attribute:: Foo.__name',
        '      :module: target.name_mangling',
        '      :value: None',
        '',
        '      name of Foo',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_type_union_operator(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.pep604', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.pep604',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.pep604',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr',
        '      :module: target.pep604',
        '      :type: int | str',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Foo.meth(x: int | str, y: int | str) -> int | str',
        '      :module: target.pep604',
        '',
        '      docstring',
        '',
        '',
        '.. py:data:: attr',
        '   :module: target.pep604',
        '   :type: int | str',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: sum(x: int | str, y: int | str) -> int | str',
        '   :module: target.pep604',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_hide_value(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.hide_value', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.hide_value',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.SENTINEL1',
        '      :module: target.hide_value',
        '',
        '      docstring',
        '',
        '      :meta hide-value:',
        '',
        '',
        '   .. py:attribute:: Foo.SENTINEL2',
        '      :module: target.hide_value',
        '',
        '      :meta hide-value:',
        '',
        '',
        '.. py:data:: SENTINEL1',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '   :meta hide-value:',
        '',
        '',
        '.. py:data:: SENTINEL2',
        '   :module: target.hide_value',
        '',
        '   :meta hide-value:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_canonical(app):
    options = {
        'members': None,
        'imported-members': None,
    }
    actual = do_autodoc(app, 'module', 'target.canonical', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.canonical',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: target.canonical',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.canonical',
        '   :canonical: target.canonical.original.Foo',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.meth()',
        '      :module: target.canonical',
        '',
        '      docstring',
        '',
    ]


def bounded_typevar_rst(name, bound):
    return [
        '',
        f'.. py:class:: {name}',
        '   :module: target.literal',
        '',
        '   docstring',
        '',
        f'   alias of TypeVar({name!r}, bound={bound})',
        '',
    ]


def function_rst(name, sig):
    return [
        '',
        f'.. py:function:: {name}({sig})',
        '   :module: target.literal',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc', freshenv=True)
def test_literal_render(app):
    # autodoc_typehints_format can take 'short' or 'fully-qualified' values
    # and this will be interpreted as 'smart' or 'fully-qualified-except-typing' by restify()
    # and 'smart' or 'fully-qualified' by stringify_annotation().

    options = {
        'members': None,
        'exclude-members': 'MyEnum',
    }
    app.config.autodoc_typehints_format = 'short'
    actual = do_autodoc(app, 'module', 'target.literal', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`~target.literal.MyEnum.a`, '
            r':py:attr:`~target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: ~typing.Literal[1234, 'abcd']"),
        *function_rst('foo', 'x: ~typing.Literal[MyEnum.a, MyEnum.b]'),
    ]

    # restify() assumes that 'fully-qualified' is 'fully-qualified-except-typing'
    # because it is more likely that a user wants to suppress 'typing.*'
    app.config.autodoc_typehints_format = 'fully-qualified'
    actual = do_autodoc(app, 'module', 'target.literal', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`target.literal.MyEnum.a`, '
            r':py:attr:`target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: typing.Literal[1234, 'abcd']"),
        *function_rst(
            'foo',
            'x: typing.Literal[target.literal.MyEnum.a, target.literal.MyEnum.b]',
        ),
    ]


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    freshenv=True,
    confoverrides={'python_display_short_literal_types': True},
)
def test_literal_render_pep604(app):
    options = {
        'members': None,
        'exclude-members': 'MyEnum',
    }
    app.config.autodoc_typehints_format = 'short'
    actual = do_autodoc(app, 'module', 'target.literal', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`~target.literal.MyEnum.a`, '
            r':py:attr:`~target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: 1234 | 'abcd'"),
        *function_rst('foo', 'x: MyEnum.a | MyEnum.b'),
    ]

    # restify() assumes that 'fully-qualified' is 'fully-qualified-except-typing'
    # because it is more likely that a user wants to suppress 'typing.*'
    app.config.autodoc_typehints_format = 'fully-qualified'
    actual = do_autodoc(app, 'module', 'target.literal', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.literal',
        '',
        *bounded_typevar_rst('T', r"\ :py:obj:`~typing.Literal`\ [1234, 'abcd']"),
        *bounded_typevar_rst(
            'U',
            r'\ :py:obj:`~typing.Literal`\ ['
            r':py:attr:`target.literal.MyEnum.a`, '
            r':py:attr:`target.literal.MyEnum.b`]',
        ),
        *function_rst('bar', "x: 1234 | 'abcd'"),
        *function_rst('foo', 'x: target.literal.MyEnum.a | target.literal.MyEnum.b'),
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_no_index_entry(app):
    # modules can use no-index-entry
    options = {'no-index-entry': None}
    actual = do_autodoc(app, 'module', 'target.module', options)
    assert '   :no-index-entry:' in list(actual)

    # classes can use no-index-entry
    actual = do_autodoc(app, 'class', 'target.classes.Foo', options)
    assert '   :no-index-entry:' in list(actual)

    # functions can use no-index-entry
    actual = do_autodoc(app, 'function', 'target.functions.func', options)
    assert '   :no-index-entry:' in list(actual)

    # modules respect no-index-entry in autodoc_default_options
    app.config.autodoc_default_options = {'no-index-entry': True}
    actual = do_autodoc(app, 'module', 'target.module')
    assert '   :no-index-entry:' in list(actual)

    # classes respect config-level no-index-entry
    actual = do_autodoc(app, 'class', 'target.classes.Foo')
    assert '   :no-index-entry:' in list(actual)

    # functions respect config-level no-index-entry
    actual = do_autodoc(app, 'function', 'target.functions.func')
    assert '   :no-index-entry:' in list(actual)
