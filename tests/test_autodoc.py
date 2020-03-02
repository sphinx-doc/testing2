"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from unittest.mock import Mock
from warnings import catch_warnings

import pytest
from docutils.statemachine import ViewList

from sphinx.ext.autodoc import ModuleLevelDocumenter, ALL, Options
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
from sphinx.testing.util import SphinxTestApp, Struct  # NOQA
from sphinx.util import logging
from sphinx.util.docutils import LoggingReporter

app = None


def do_autodoc(app, objtype, name, options=None):
    if options is None:
        options = {}
    app.env.temp_data.setdefault('docname', 'index')  # set dummy docname
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()

    return bridge.result


@pytest.fixture(scope='module', autouse=True)
def setup_module(rootdir, sphinx_test_tempdir):
    try:
        global app
        srcdir = sphinx_test_tempdir / 'autodoc-root'
        if not srcdir.exists():
            (rootdir / 'test-root').copytree(srcdir)
        testroot = rootdir / 'test-ext-autodoc'
        sys.path.append(testroot)
        app = SphinxTestApp(srcdir=srcdir)
        app.builder.env.app = app
        app.builder.env.temp_data['docname'] = 'dummy'
        app.connect('autodoc-process-signature', process_signature)
        app.connect('autodoc-skip-member', skip_member)
        yield
    finally:
        app.cleanup()
        sys.path.remove(testroot)


directive = options = None


@pytest.fixture
def setup_test():
    global options, directive
    global processed_signatures

    options = Options(
        inherited_members = False,
        undoc_members = False,
        private_members = False,
        special_members = False,
        imported_members = False,
        show_inheritance = False,
        noindex = False,
        annotation = None,
        synopsis = '',
        platform = '',
        deprecated = False,
        members = [],
        member_order = 'alphabetic',
        exclude_members = set(),
        ignore_module_all = False,
    )

    directive = Struct(
        env = app.builder.env,
        genopt = options,
        result = ViewList(),
        filename_set = set(),
        state = Mock(),
    )
    directive.state.document.settings.tab_width = 8

    processed_signatures = []

    app._status.truncate(0)
    app._warning.truncate(0)

    yield

    app.registry.autodoc_attrgettrs.clear()


processed_signatures = []


def process_signature(app, what, name, obj, options, args, retann):
    processed_signatures.append((what, name))
    if name == 'bar':
        return '42', None


def skip_member(app, what, name, obj, member_of, skip, options):
    if name in ('__special1__', '__special2__'):
        return skip
    if name.startswith('__'):
        return True
    if name == 'skipmeth':
        return True


@pytest.mark.usefixtures('setup_test')
def test_parse_name():
    logging.setup(app, app._status, app._warning)

    def verify(objtype, name, result):
        inst = app.registry.documenters[objtype](directive, name)
        assert inst.parse_name()
        assert (inst.modname, inst.objpath, inst.args, inst.retann) == result

    # for modules
    verify('module', 'test_autodoc', ('test_autodoc', [], None, None))
    verify('module', 'test.test_autodoc', ('test.test_autodoc', [], None, None))
    verify('module', 'test(arg)', ('test', [], 'arg', None))
    assert 'signature arguments' in app._warning.getvalue()

    # for functions/classes
    verify('function', 'test_autodoc.raises',
           ('test_autodoc', ['raises'], None, None))
    verify('function', 'test_autodoc.raises(exc) -> None',
           ('test_autodoc', ['raises'], 'exc', 'None'))
    directive.env.temp_data['autodoc:module'] = 'test_autodoc'
    verify('function', 'raises', ('test_autodoc', ['raises'], None, None))
    del directive.env.temp_data['autodoc:module']
    directive.env.ref_context['py:module'] = 'test_autodoc'
    verify('function', 'raises', ('test_autodoc', ['raises'], None, None))
    verify('class', 'Base', ('test_autodoc', ['Base'], None, None))

    # for members
    directive.env.ref_context['py:module'] = 'foo'
    verify('method', 'util.SphinxTestApp.cleanup',
           ('util', ['SphinxTestApp', 'cleanup'], None, None))
    directive.env.ref_context['py:module'] = 'util'
    directive.env.ref_context['py:class'] = 'Foo'
    directive.env.temp_data['autodoc:class'] = 'SphinxTestApp'
    verify('method', 'cleanup', ('util', ['SphinxTestApp', 'cleanup'], None, None))
    verify('method', 'SphinxTestApp.cleanup',
           ('util', ['SphinxTestApp', 'cleanup'], None, None))

    # and clean up
    del directive.env.ref_context['py:module']
    del directive.env.ref_context['py:class']
    del directive.env.temp_data['autodoc:class']


@pytest.mark.usefixtures('setup_test')
def test_format_signature():
    def formatsig(objtype, name, obj, args, retann):
        inst = app.registry.documenters[objtype](directive, name)
        inst.fullname = name
        inst.doc_as_attr = False  # for class objtype
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
    assert formatsig('function', 'f', f, None, 'None') == '(a, b, c=1, **d) -> None'
    assert formatsig('function', 'g', g, None, None) == r"(a='\\n')"

    # test for classes
    class D:
        pass

    class E:
        pass
    # no signature for classes without __init__
    for C in (D, E):
        assert formatsig('class', 'D', C, None, None) == ''

    class F:
        def __init__(self, a, b=None):
            pass

    class G(F):
        pass
    for C in (F, G):
        assert formatsig('class', 'C', C, None, None) == '(a, b=None)'
    assert formatsig('class', 'C', D, 'a, b', 'X') == '(a, b) -> X'

    # __init__ have signature at first line of docstring
    directive.env.config.autoclass_content = 'both'

    class F2:
        '''some docstring for F2.'''
        def __init__(self, *args, **kw):
            '''
            __init__(a1, a2, kw1=True, kw2=False)

            some docstring for __init__.
            '''
    class G2(F2):
        pass

    assert formatsig('class', 'F2', F2, None, None) == \
        '(a1, a2, kw1=True, kw2=False)'
    assert formatsig('class', 'G2', G2, None, None) == \
        '(a1, a2, kw1=True, kw2=False)'

    # test for methods
    class H:
        def foo1(self, b, *c):
            pass

        def foo2(b, *c):
            pass

        def foo3(self, d='\n'):
            pass
    assert formatsig('method', 'H.foo', H.foo1, None, None) == '(b, *c)'
    assert formatsig('method', 'H.foo', H.foo1, 'a', None) == '(a)'
    assert formatsig('method', 'H.foo', H.foo2, None, None) == '(*c)'
    assert formatsig('method', 'H.foo', H.foo3, None, None) == r"(d='\\n')"

    # test bound methods interpreted as functions
    assert formatsig('function', 'foo', H().foo1, None, None) == '(b, *c)'
    assert formatsig('function', 'foo', H().foo2, None, None) == '(*c)'
    assert formatsig('function', 'foo', H().foo3, None, None) == r"(d='\\n')"

    # test exception handling (exception is caught and args is '')
    directive.env.config.autodoc_docstring_signature = False
    assert formatsig('function', 'int', int, None, None) == ''

    # test processing by event handler
    assert formatsig('method', 'bar', H.foo1, None, None) == '42'

    # test functions created via functools.partial
    from functools import partial
    curried1 = partial(lambda a, b, c: None, 'A')
    assert formatsig('function', 'curried1', curried1, None, None) == \
        '(b, c)'
    curried2 = partial(lambda a, b, c=42: None, 'A')
    assert formatsig('function', 'curried2', curried2, None, None) == \
        '(b, c=42)'
    curried3 = partial(lambda a, b, *c: None, 'A')
    assert formatsig('function', 'curried3', curried3, None, None) == \
        '(b, *c)'
    curried4 = partial(lambda a, b, c=42, *d, **e: None, 'A')
    assert formatsig('function', 'curried4', curried4, None, None) == \
        '(b, c=42, *d, **e)'


@pytest.mark.usefixtures('setup_test')
def test_get_doc():
    def getdocl(objtype, obj):
        inst = app.registry.documenters[objtype](directive, 'tmp')
        inst.object = obj
        inst.objpath = [obj.__name__]
        inst.doc_as_attr = False
        inst.format_signature()  # handle docstring signatures!
        ds = inst.get_doc()
        # for testing purposes, concat them and strip the empty line at the end
        res = sum(ds, [])[:-1]
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
        """
        Docstring
        """
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

    # already-unicode docstrings must be taken literally
    def f():
        """Döcstring"""
    assert getdocl('function', f) == ['Döcstring']

    # verify that method docstrings get extracted in both normal case
    # and in case of bound method posing as a function
    class J:  # NOQA
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

    options = {"members": 'integer'}
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
        '   '
    ]


@pytest.mark.usefixtures('setup_test')
def test_attrgetter_using():
    from target import Class
    from target.inheritance import Derived

    def assert_getter_works(objtype, name, obj, attrs=[], **kw):
        getattr_spy = []

        def special_getattr(obj, name, *defargs):
            if name in attrs:
                getattr_spy.append((obj, name))
                return None
            return getattr(obj, name, *defargs)
        app.add_autodoc_attrgetter(type, special_getattr)

        del getattr_spy[:]
        inst = app.registry.documenters[objtype](directive, name)
        inst.generate(**kw)

        hooked_members = [s[1] for s in getattr_spy]
        documented_members = [s[1] for s in processed_signatures]
        for attr in attrs:
            fullname = '.'.join((name, attr))
            assert attr in hooked_members
            assert fullname not in documented_members, \
                '%r was not hooked by special_attrgetter function' % fullname

    with catch_warnings(record=True):
        options.members = ALL
        options.inherited_members = False
        assert_getter_works('class', 'target.Class', Class, ['meth'])

        options.inherited_members = True
        assert_getter_works('class', 'target.inheritance.Derived', Derived, ['inheritedmeth'])


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_py_module(app, warning):
    # without py:module
    actual = do_autodoc(app, 'method', 'Class.meth')
    assert list(actual) == []
    assert ("don't know which module to import for autodocumenting 'Class.meth'"
            in warning.getvalue())

    # with py:module
    app.env.ref_context['py:module'] = 'target'
    warning.truncate(0)

    actual = do_autodoc(app, 'method', 'Class.meth')
    assert list(actual) == [
        '',
        '.. py:method:: Class.meth()',
        '   :module: target',
        '',
        '   Function.',
        '   '
    ]
    assert ("don't know which module to import for autodocumenting 'Class.meth'"
            not in warning.getvalue())


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_decorator(app):
    actual = do_autodoc(app, 'decorator', 'target.decorator.deco1')
    assert list(actual) == [
        '',
        '.. py:decorator:: deco1',
        '   :module: target.decorator',
        '',
        '   docstring for deco1',
        '   '
    ]

    actual = do_autodoc(app, 'decorator', 'target.decorator.deco2')
    assert list(actual) == [
        '',
        '.. py:decorator:: deco2(condition, message)',
        '   :module: target.decorator',
        '',
        '   docstring for deco2',
        '   '
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
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_warnings(app, warning):
    app.env.temp_data['docname'] = 'dummy'

    # can't import module
    do_autodoc(app, 'module', 'unknown')
    assert "failed to import module 'unknown'" in warning.getvalue()

    # missing function
    do_autodoc(app, 'function', 'unknown')
    assert "import for autodocumenting 'unknown'" in warning.getvalue()

    do_autodoc(app, 'function', 'target.unknown')
    assert "failed to import function 'unknown' from module 'target'" in warning.getvalue()

    # missing method
    do_autodoc(app, 'method', 'target.Class.unknown')
    assert "failed to import method 'Class.unknown' from module 'target'" in warning.getvalue()


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_attributes(app):
    options = {"synopsis": 'Synopsis',
               "platform": "Platform",
               "deprecated": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '   :synopsis: Synopsis',
        '   :platform: Platform',
        '   :deprecated:',
        ''
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_members(app):
    # default (no-members)
    actual = do_autodoc(app, 'class', 'target.inheritance.Base')
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
    ]

    # default ALL-members
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
        '   .. py:method:: Base.inheritedclassmeth()',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)'
    ]

    # default specific-members
    options = {"members": "inheritedmeth,inheritedstaticmeth"}
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
        '   .. py:method:: Base.inheritedmeth()',
        '   .. py:method:: Base.inheritedstaticmeth(cls)'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_exclude_members(app):
    options = {"members": None,
               "exclude-members": "inheritedmeth,inheritedstaticmeth"}
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
        '   .. py:method:: Base.inheritedclassmeth()'
    ]

    # members vs exclude-members
    options = {"members": "inheritedmeth",
               "exclude-members": "inheritedmeth"}
    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Base',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_undoc_members(app):
    options = {"members": None,
               "undoc-members": None}
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
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
        '   .. py:attribute:: Class.skipattr',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:method:: Class.undocmeth()'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherited_members(app):
    options = {"members": None,
               "inherited-members": None}
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert list(filter(lambda l: 'method::' in l, actual)) == [
        '   .. py:method:: Derived.inheritedclassmeth()',
        '   .. py:method:: Derived.inheritedmeth()',
        '   .. py:method:: Derived.inheritedstaticmeth(cls)',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherited_members_Base(app):
    options = {"members": None,
               "inherited-members": "Base",
               "special-members": None}

    # check methods for object class are shown
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert '   .. py:method:: Derived.inheritedmeth()' in actual
    assert '   .. py:method:: Derived.inheritedclassmeth' not in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherited_members_None(app):
    options = {"members": None,
               "inherited-members": "None",
               "special-members": None}

    # check methods for object class are shown
    actual = do_autodoc(app, 'class', 'target.inheritance.Derived', options)
    assert '   .. py:method:: Derived.__init__' in actual
    assert '   .. py:method:: Derived.__str__' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_imported_members(app):
    options = {"members": None,
               "imported-members": None,
               "ignore-module-all": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert '.. py:function:: save_traceback(app: Sphinx) -> str' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_special_members(app):
    # specific special methods
    options = {"undoc-members": None,
               "special-members": "__init__,__special1__"}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
    ]

    # combination with specific members
    options = {"members": "attr,docattr",
               "undoc-members": None,
               "special-members": "__init__,__special1__"}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:method:: Class.__special1__()',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
    ]

    # all special methods
    options = {"members": None,
               "undoc-members": None,
               "special-members": None}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class.__dict__',
        '   .. py:method:: Class.__init__(arg)',
        '   .. py:attribute:: Class.__module__',
        '   .. py:method:: Class.__special1__()',
        '   .. py:method:: Class.__special2__()',
        '   .. py:attribute:: Class.__weakref__',
        '   .. py:attribute:: Class.attr',
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
        '   .. py:method:: Class.undocmeth()'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_ignore_module_all(app):
    # default (no-ignore-module-all)
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(filter(lambda l: 'class::' in l, actual)) == [
        '.. py:class:: Class(arg)',
    ]

    # ignore-module-all
    options = {"members": None,
               "ignore-module-all": None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(filter(lambda l: 'class::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '.. py:class:: CustomDict',
        '.. py:class:: InnerChild',
        '.. py:class:: InstAttCls()',
        '.. py:class:: Outer',
        '   .. py:class:: Outer.Inner',
        '.. py:class:: StrRepr'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_noindex(app):
    options = {"noindex": True}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '   :noindex:',
        ''
    ]

    # TODO: :noindex: should be propagated to children of target item.

    actual = do_autodoc(app, 'class', 'target.inheritance.Base', options)
    assert list(actual) == [
        '',
        '.. py:class:: Base',
        '   :noindex:',
        '   :module: target.inheritance',
        ''
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_subclass_of_builtin_class(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.CustomDict', options)
    assert list(actual) == [
        '',
        '.. py:class:: CustomDict',
        '   :module: target',
        '',
        '   Docstring.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inner_class(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.Outer', options)
    assert list(actual) == [
        '',
        '.. py:class:: Outer',
        '   :module: target',
        '',
        '   Foo',
        '   ',
        '   ',
        '   .. py:class:: Outer.Inner',
        '      :module: target',
        '   ',
        '      Foo',
        '      ',
        '      ',
        '      .. py:method:: Outer.Inner.meth()',
        '         :module: target',
        '      ',
        '         Foo',
        '         ',
        '   ',
        '   .. py:attribute:: Outer.factory',
        '      :module: target',
        '   ',
        '      alias of :class:`builtins.dict`'
    ]

    actual = do_autodoc(app, 'class', 'target.Outer.Inner', options)
    assert list(actual) == [
        '',
        '.. py:class:: Inner',
        '   :module: target.Outer',
        '',
        '   Foo',
        '   ',
        '   ',
        '   .. py:method:: Inner.meth()',
        '      :module: target.Outer',
        '   ',
        '      Foo',
        '      ',
    ]

    options['show-inheritance'] = True
    actual = do_autodoc(app, 'class', 'target.InnerChild', options)
    assert list(actual) == [
        '',
        '.. py:class:: InnerChild',
        '   :module: target', '',
        '   Bases: :class:`target.Outer.Inner`',
        '',
        '   InnerChild docstring',
        '   '
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
        '   '
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
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_descriptor(app):
    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'class', 'target.descriptor.Class', options)
    assert list(actual) == [
        '',
        '.. py:class:: Class',
        '   :module: target.descriptor',
        '',
        '   ',
        '   .. py:attribute:: Class.descr',
        '      :module: target.descriptor',
        '   ',
        '      Descriptor instance docstring.',
        '      ',
        '   ',
        '   .. py:method:: Class.prop',
        '      :module: target.descriptor',
        '      :property:',
        '   ',
        '      Property.',
        '      '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_c_module(app):
    actual = do_autodoc(app, 'function', 'time.asctime')
    assert list(actual) == [
        '',
        '.. py:function:: asctime([tuple]) -> string',
        '   :module: time',
        '',
        "   Convert a time tuple to a string, e.g. 'Sat Jun 06 16:26:11 1998'.",
        '   When the time tuple is not present, current time as returned by localtime()',
        '   is used.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_member_order(app):
    # case member-order='bysource'
    options = {"members": None,
               'member-order': 'bysource',
               "undoc-members": True,
               'private-members': True}
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
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_string',
        '   .. py:attribute:: Class._private_inst_attr'
    ]

    # case member-order='groupwise'
    options = {"members": None,
               'member-order': 'groupwise',
               "undoc-members": True,
               'private-members': True}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:method:: Class.roger(a, *, b=2, c=3, d=4, e=5, f=6)',
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
        '   .. py:attribute:: Class.udocattr'
    ]

    # case member-order=None
    options = {"members": None,
               "undoc-members": True,
               'private-members': True}
    actual = do_autodoc(app, 'class', 'target.Class', options)
    assert list(filter(lambda l: '::' in l, actual)) == [
        '.. py:class:: Class(arg)',
        '   .. py:attribute:: Class._private_inst_attr',
        '   .. py:attribute:: Class.attr',
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
        '   .. py:method:: Class.undocmeth()'
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_module_scope(app):
    app.env.temp_data['autodoc:module'] = 'target'
    actual = do_autodoc(app, 'attribute', 'Class.mdocattr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.mdocattr',
        '   :module: target',
        '   :value: <_io.StringIO object>',
        '',
        '   should be documented as well - süß',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_scope(app):
    app.env.temp_data['autodoc:module'] = 'target'
    app.env.temp_data['autodoc:class'] = 'Class'
    actual = do_autodoc(app, 'attribute', 'mdocattr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.mdocattr',
        '   :module: target',
        '   :value: <_io.StringIO object>',
        '',
        '   should be documented as well - süß',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_attributes(app):
    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'class', 'target.AttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: AttCls',
        '   :module: target',
        '',
        '   ',
        '   .. py:attribute:: AttCls.a1',
        '      :module: target',
        '      :value: hello world',
        '   ',
        '   ',
        '   .. py:attribute:: AttCls.a2',
        '      :module: target',
        '      :value: None',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_instance_attributes(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.InstAttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '   ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :value: 'a'",
        '   ',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca2',
        '      :module: target',
        "      :value: 'b'",
        '   ',
        '      Doc comment for InstAttCls.ca2. One line only.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca3',
        '      :module: target',
        "      :value: 'c'",
        '   ',
        '      Docstring for class attribute InstAttCls.ca3.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '      :value: None',
        '   ',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ia2',
        '      :module: target',
        '      :value: None',
        '   ',
        '      Docstring for instance attribute InstAttCls.ia2.',
        '      '
    ]

    # pick up arbitrary attributes
    options = {"members": 'ca1,ia1'}
    actual = do_autodoc(app, 'class', 'target.InstAttCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: InstAttCls()',
        '   :module: target',
        '',
        '   Class with documented class and instance attributes.',
        '   ',
        '   ',
        '   .. py:attribute:: InstAttCls.ca1',
        '      :module: target',
        "      :value: 'a'",
        '   ',
        '      Doc comment for class attribute InstAttCls.ca1.',
        '      It can have multiple lines.',
        '      ',
        '   ',
        '   .. py:attribute:: InstAttCls.ia1',
        '      :module: target',
        '      :value: None',
        '   ',
        '      Doc comment for instance attribute InstAttCls.ia1',
        '      '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_slots(app):
    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'module', 'target.slots', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.slots',
        '',
        '',
        '.. py:class:: Bar()',
        '   :module: target.slots',
        '',
        '   ',
        '   .. py:attribute:: Bar.attr1',
        '      :module: target.slots',
        '   ',
        '      docstring of attr1',
        '      ',
        '   ',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.slots',
        '   ',
        '      docstring of instance attr2',
        '      ',
        '   ',
        '   .. py:attribute:: Bar.attr3',
        '      :module: target.slots',
        '   ',
        '',
        '.. py:class:: Foo',
        '   :module: target.slots',
        '',
        '   ',
        '   .. py:attribute:: Foo.attr',
        '      :module: target.slots',
        '   ',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_enum_class(app):
    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'class', 'target.enum.EnumCls', options)
    assert list(actual) == [
        '',
        '.. py:class:: EnumCls',
        '   :module: target.enum',
        '',
        '   this is enum class',
        '   ',
        '   ',
        '   .. py:method:: EnumCls.say_hello()',
        '      :module: target.enum',
        '   ',
        '      a method says hello to you.',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val1',
        '      :module: target.enum',
        '      :value: 12',
        '   ',
        '      doc for val1',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val2',
        '      :module: target.enum',
        '      :value: 23',
        '   ',
        '      doc for val2',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val3',
        '      :module: target.enum',
        '      :value: 34',
        '   ',
        '      doc for val3',
        '      ',
        '   ',
        '   .. py:attribute:: EnumCls.val4',
        '      :module: target.enum',
        '      :value: 34',
        '   '
    ]

    # checks for an attribute of EnumClass
    actual = do_autodoc(app, 'attribute', 'target.enum.EnumCls.val1')
    assert list(actual) == [
        '',
        '.. py:attribute:: EnumCls.val1',
        '   :module: target.enum',
        '   :value: 12',
        '',
        '   doc for val1',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_descriptor_class(app):
    options = {"members": 'CustomDataDescriptor,CustomDataDescriptor2'}
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
        '   ',
        '   ',
        '   .. py:method:: CustomDataDescriptor.meth()',
        '      :module: target.descriptor',
        '   ',
        '      Function.',
        '      ',
        '',
        '.. py:class:: CustomDataDescriptor2(doc)',
        '   :module: target.descriptor',
        '',
        '   Descriptor class with custom metaclass docstring.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autofunction_for_callable(app):
    actual = do_autodoc(app, 'function', 'target.callable.function')
    assert list(actual) == [
        '',
        '.. py:function:: function(arg1, arg2, **kwargs)',
        '   :module: target.callable',
        '',
        '   A callable object that behaves like a function.',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autofunction_for_method(app):
    actual = do_autodoc(app, 'function', 'target.callable.method')
    assert list(actual) == [
        '',
        '.. py:function:: method(arg1, arg2)',
        '   :module: target.callable',
        '',
        '   docstring of Callable.method().',
        '   '
    ]


@pytest.mark.usefixtures('setup_test')
def test_abstractmethods():
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'target.abstractmethods', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.abstractmethods',
        '',
        '',
        '.. py:class:: Base',
        '   :module: target.abstractmethods',
        '',
        '   ',
        '   .. py:method:: Base.abstractmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '   ',
        '   ',
        '   .. py:method:: Base.classmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :classmethod:',
        '   ',
        '   ',
        '   .. py:method:: Base.coroutinemeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :async:',
        '   ',
        '   ',
        '   .. py:method:: Base.meth()',
        '      :module: target.abstractmethods',
        '   ',
        '   ',
        '   .. py:method:: Base.prop',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :property:',
        '   ',
        '   ',
        '   .. py:method:: Base.staticmeth()',
        '      :module: target.abstractmethods',
        '      :abstractmethod:',
        '      :staticmethod:',
        '   '
    ]


@pytest.mark.usefixtures('setup_test')
def test_partialfunction():
    options = {"members": None}
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
        '   ',
        '',
        '.. py:function:: func2(b, c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func1',
        '   ',
        '',
        '.. py:function:: func3(c)',
        '   :module: target.partialfunction',
        '',
        '   docstring of func3',
        '   ',
        '',
        '.. py:function:: func4()',
        '   :module: target.partialfunction',
        '',
        '   docstring of func3',
        '   '
    ]


@pytest.mark.usefixtures('setup_test')
def test_imported_partialfunction_should_not_shown_without_imported_members():
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.imported_members', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.imported_members',
        ''
    ]


@pytest.mark.usefixtures('setup_test')
def test_bound_method():
    options = {"members": None}
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
        '   ',
    ]


@pytest.mark.usefixtures('setup_test')
def test_coroutine():
    actual = do_autodoc(app, 'function', 'target.functions.coroutinefunc')
    assert list(actual) == [
        '',
        '.. py:function:: coroutinefunc()',
        '   :module: target.functions',
        '   :async:',
        '',
    ]

    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.coroutine.AsyncClass', options)
    assert list(actual) == [
        '',
        '.. py:class:: AsyncClass',
        '   :module: target.coroutine',
        '',
        '   ',
        '   .. py:method:: AsyncClass.do_coroutine()',
        '      :module: target.coroutine',
        '      :async:',
        '   ',
        '      A documented coroutine function',
        '      ',
        '   ',
        '   .. py:method:: AsyncClass.do_coroutine2()',
        '      :module: target.coroutine',
        '      :async:',
        '      :classmethod:',
        '   ',
        '      A documented coroutine classmethod',
        '      ',
        '   ',
        '   .. py:method:: AsyncClass.do_coroutine3()',
        '      :module: target.coroutine',
        '      :async:',
        '      :staticmethod:',
        '   ',
        '      A documented coroutine staticmethod',
        '      ',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_partialmethod(app):
    expected = [
        '',
        '.. py:class:: Cell',
        '   :module: target.partialmethod',
        '',
        '   An example for partialmethod.',
        '   ',
        '   refs: https://docs.python.jp/3/library/functools.html#functools.partialmethod',
        '   ',
        '   ',
        '   .. py:method:: Cell.set_alive()',
        '      :module: target.partialmethod',
        '   ',
        '      Make a cell alive.',
        '      ',
        '   ',
        '   .. py:method:: Cell.set_state(state)',
        '      :module: target.partialmethod',
        '   ',
        '      Update state of cell to *state*.',
        '      ',
    ]

    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.partialmethod.Cell', options)
    assert list(actual) == expected


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_partialmethod_undoc_members(app):
    expected = [
        '',
        '.. py:class:: Cell',
        '   :module: target.partialmethod',
        '',
        '   An example for partialmethod.',
        '   ',
        '   refs: https://docs.python.jp/3/library/functools.html#functools.partialmethod',
        '   ',
        '   ',
        '   .. py:method:: Cell.set_alive()',
        '      :module: target.partialmethod',
        '   ',
        '      Make a cell alive.',
        '      ',
        '   ',
        '   .. py:method:: Cell.set_dead()',
        '      :module: target.partialmethod',
        '   ',
        '   ',
        '   .. py:method:: Cell.set_state(state)',
        '      :module: target.partialmethod',
        '   ',
        '      Update state of cell to *state*.',
        '      ',
    ]

    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'class', 'target.partialmethod.Cell', options)
    assert list(actual) == expected


@pytest.mark.skipif(sys.version_info < (3, 6), reason='py36+ is available since python3.6.')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_typed_instance_variables(app):
    options = {"members": None,
               "undoc-members": True}
    actual = do_autodoc(app, 'module', 'target.typed_vars', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typed_vars',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.typed_vars',
        '',
        '   ',
        '   .. py:attribute:: Class.attr1',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '   ',
        '   ',
        '   .. py:attribute:: Class.attr2',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: None',
        '   ',
        '   ',
        '   .. py:attribute:: Class.attr3',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: 0',
        '   ',
        '   ',
        '   .. py:attribute:: Class.attr4',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: None',
        '   ',
        '      attr4',
        '      ',
        '   ',
        '   .. py:attribute:: Class.attr5',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: None',
        '   ',
        '      attr5',
        '      ',
        '   ',
        '   .. py:attribute:: Class.attr6',
        '      :module: target.typed_vars',
        '      :type: int',
        '      :value: None',
        '   ',
        '      attr6',
        '      ',
        '',
        '.. py:data:: attr1',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr1',
        '   ',
        '',
        '.. py:data:: attr2',
        '   :module: target.typed_vars',
        '   :type: str',
        '   :value: None',
        '',
        '   attr2',
        '   ',
        '',
        '.. py:data:: attr3',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr3',
        '   '
    ]


@pytest.mark.sphinx('html', testroot='pycode-egg')
def test_autodoc_for_egged_code(app):
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'sample', options)
    assert list(actual) == [
        '',
        '.. py:module:: sample',
        '',
        '',
        '.. py:data:: CONSTANT',
        '   :module: sample',
        '   :value: 1',
        '',
        '   constant on sample.py',
        '   ',
        '',
        '.. py:function:: hello(s)',
        '   :module: sample',
        ''
    ]
