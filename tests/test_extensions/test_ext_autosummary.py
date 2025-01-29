"""Test the autosummary extension."""

from __future__ import annotations

import sys
from contextlib import chdir
from io import StringIO
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.ext.autosummary import (
    autosummary_table,
    autosummary_toc,
    extract_summary,
    import_by_name,
    mangle_signature,
)
from sphinx.ext.autosummary.generate import (
    AutosummaryEntry,
    generate_autosummary_content,
    generate_autosummary_docs,
)
from sphinx.ext.autosummary.generate import main as autogen_main
from sphinx.testing.util import assert_node, etree_parse
from sphinx.util.docutils import new_document

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

html_warnfile = StringIO()


defaults = {
    'extensions': ['sphinx.ext.autosummary'],
    'autosummary_generate': True,
    'autosummary_generate_overwrite': False,
}


@pytest.fixture(autouse=True)
def _unload_target_module():
    sys.modules.pop('target', None)


def test_mangle_signature():
    TEST_SIGNATURE = """
    () :: ()
    (a, b, c, d, e) :: (a, b, c, d, e)
    (a, b, c=1, d=2, e=3) :: (a, b[, c, d, e])
    (a, b, aaa=1, bbb=1, ccc=1, eee=1, fff=1, ggg=1, hhh=1, iii=1, jjj=1)\
    :: (a, b[, aaa, bbb, ccc, ...])
    (a, b, c=(), d=<foo>) :: (a, b[, c, d])
    (a, b, c='foobar()', d=123) :: (a, b[, c, d])
    (a, b[, c]) :: (a, b[, c])
    (a, b[, cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx]) :: (a, b[, ...)
    (a, b='c=d, e=f, g=h', c=3) :: (a[, b, c])
    (a, b="c=d, e=f, g=h", c=3) :: (a[, b, c])
    (a, b='c=d, \\'e=f,\\' g=h', c=3) :: (a[, b, c])
    (a, b='c=d, ', e='\\\\' g=h, c=3) :: (a[, b, e, c])
    (a, b={'c=d, ': 3, '\\\\': 3}) :: (a[, b])
    (a=1, b=2, c=3) :: ([a, b, c])
    (a=1, b=<SomeClass: a, b, c>, c=3) :: ([a, b, c])
    (a=1, b=T(a=1, b=2), c=3) :: ([a, b, c])
    (a: Tuple[int, str], b: int) -> str :: (a, b)
    """

    TEST = [
        list(map(str.strip, x.split('::')))
        for x in TEST_SIGNATURE.split('\n')
        if '::' in x
    ]
    for inp, outp in TEST:
        res = mangle_signature(inp).strip().replace('\u00a0', ' ')
        assert res == outp, f"'{inp}' -> '{res}' != '{outp}'"


def test_extract_summary(capsys):
    settings = Mock(
        language_code='en',
        id_prefix='',
        auto_id_prefix='',
        pep_reference=False,
        rfc_reference=False,
    )
    document = new_document('', settings)

    # normal case
    doc = [
        '',
        'This is a first sentence. And second one.',
        '',
        'Second block is here',
    ]
    assert extract_summary(doc, document) == 'This is a first sentence.'

    # inliner case
    doc = [
        'This sentence contains *emphasis text having dots.*,',
        'it does not break sentence.',
    ]
    assert extract_summary(doc, document) == ' '.join(doc)

    # abbreviations
    doc = ['Blabla, i.e. bla.']
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, (i.e. bla).']
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, e.g. bla.']
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, (e.g. bla).']
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, et al. bla.']
    assert extract_summary(doc, document) == ' '.join(doc)

    # literal
    doc = ['blah blah::']
    assert extract_summary(doc, document) == 'blah blah.'

    # heading
    doc = [
        'blah blah',
        '=========',
    ]
    assert extract_summary(doc, document) == 'blah blah'

    doc = [
        '=========',
        'blah blah',
        '=========',
    ]
    assert extract_summary(doc, document) == 'blah blah'

    # hyperlink target
    doc = ['Do `this <https://www.sphinx-doc.org/>`_ and that. blah blah blah.']
    extracted = extract_summary(doc, document)
    assert extracted == 'Do `this <https://www.sphinx-doc.org/>`_ and that.'

    _, err = capsys.readouterr()
    assert err == ''


@pytest.mark.sphinx(
    'dummy',
    testroot='ext-autosummary-ext',
    confoverrides=defaults.copy(),
)
def test_get_items_summary(make_app, app_params):
    import sphinx.ext.autosummary
    import sphinx.ext.autosummary.generate

    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    sphinx.ext.autosummary.generate.setup_documenters(app)
    # monkey-patch Autosummary.get_items so we can easily get access to it's
    # results..
    orig_get_items = sphinx.ext.autosummary.Autosummary.get_items

    autosummary_items = {}

    def new_get_items(self, names, *args, **kwargs):
        results = orig_get_items(self, names, *args, **kwargs)
        for name, result in zip(names, results, strict=True):
            autosummary_items[name] = result  # NoQA: PERF403
        return results

    def handler(app, what, name, obj, options, lines):
        assert isinstance(lines, list)

        # ensure no docstring is processed twice:
        assert 'THIS HAS BEEN HANDLED' not in lines
        lines.append('THIS HAS BEEN HANDLED')

    app.connect('autodoc-process-docstring', handler)

    sphinx.ext.autosummary.Autosummary.get_items = new_get_items
    try:
        app.build(force_all=True)
    finally:
        sphinx.ext.autosummary.Autosummary.get_items = orig_get_items

    html_warnings = app._warning.getvalue()
    assert html_warnings == ''

    expected_values = {
        'with_sentence': 'I have a sentence which spans multiple lines.',
        'no_sentence': "this doesn't start with a capital.",
        'empty_line': 'This is the real summary',
        'module_attr': 'This is a module attribute',
        'C.class_attr': 'This is a class attribute',
        'C.instance_attr': 'This is an instance attribute',
        'C.prop_attr1': 'This is a function docstring',
        'C.prop_attr2': 'This is a attribute docstring',
        'C.C2': 'This is a nested inner class docstring',
    }
    for key, expected in expected_values.items():
        assert autosummary_items[key][2] == expected, (
            f'Summary for {key} was {autosummary_items[key]!r} - expected {expected!r}'
        )

    # check an item in detail
    assert 'func' in autosummary_items
    func_attrs = (
        'func',
        '(arg_, *args, **kwargs)',
        'Test function take an argument ended with underscore.',
        'dummy_module.func',
    )
    assert autosummary_items['func'] == func_attrs


def str_content(elem: Element) -> str:
    if elem.text is not None:
        return elem.text
    else:
        return ''.join(str_content(e) for e in elem)


@pytest.mark.sphinx(
    'xml',
    testroot='ext-autosummary-ext',
    confoverrides=defaults.copy(),
)
def test_escaping(app):
    app.build(force_all=True)

    docpage = app.builder.outdir / 'underscore_module_.xml'
    assert docpage.exists()

    title = etree_parse(docpage).find('section/title')
    assert str_content(title) == 'underscore_module_'


@pytest.mark.sphinx('html', testroot='ext-autosummary')
def test_autosummary_generate_content_for_module(app):
    import autosummary_dummy_module  # type: ignore[import-not-found]

    template = Mock()

    generate_autosummary_content(
        'autosummary_dummy_module',
        autosummary_dummy_module,
        None,
        template,
        None,
        False,
        app,
        False,
        {},
    )
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == [
        'CONSTANT1',
        'CONSTANT2',
        'Exc',
        'Foo',
        '_Baz',
        '_Exc',
        '__all__',
        '__builtins__',
        '__cached__',
        '__doc__',
        '__file__',
        '__name__',
        '__package__',
        '_quux',
        'bar',
        'non_imported_member',
        'quuz',
        'qux',
    ]
    assert context['functions'] == ['bar']
    assert context['all_functions'] == ['_quux', 'bar']
    assert context['classes'] == ['Foo']
    assert context['all_classes'] == ['Foo', '_Baz']
    assert context['exceptions'] == ['Exc']
    assert context['all_exceptions'] == ['Exc', '_Exc']
    assert context['attributes'] == ['CONSTANT1', 'qux', 'quuz', 'non_imported_member']
    assert context['all_attributes'] == [
        'CONSTANT1',
        'qux',
        'quuz',
        'non_imported_member',
    ]
    assert context['fullname'] == 'autosummary_dummy_module'
    assert context['module'] == 'autosummary_dummy_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx('html', testroot='ext-autosummary')
def test_autosummary_generate_content_for_module___all__(app):
    import autosummary_dummy_module

    template = Mock()
    app.config.autosummary_ignore_module_all = False

    generate_autosummary_content(
        'autosummary_dummy_module',
        autosummary_dummy_module,
        None,
        template,
        None,
        False,
        app,
        False,
        {},
    )
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == [
        'CONSTANT1',
        'Exc',
        'Foo',
        '_Baz',
        'bar',
        'qux',
        'path',
    ]
    assert context['functions'] == ['bar']
    assert context['all_functions'] == ['bar']
    assert context['classes'] == ['Foo']
    assert context['all_classes'] == ['Foo', '_Baz']
    assert context['exceptions'] == ['Exc']
    assert context['all_exceptions'] == ['Exc']
    assert context['attributes'] == ['CONSTANT1', 'qux']
    assert context['all_attributes'] == ['CONSTANT1', 'qux']
    assert context['fullname'] == 'autosummary_dummy_module'
    assert context['module'] == 'autosummary_dummy_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx('html', testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_skipped(app):
    import autosummary_dummy_module

    template = Mock()

    def skip_member(app, what, name, obj, skip, options):
        if name in {'Foo', 'bar', 'Exc'}:
            return True
        return None

    app.connect('autodoc-skip-member', skip_member)
    generate_autosummary_content(
        'autosummary_dummy_module',
        autosummary_dummy_module,
        None,
        template,
        None,
        False,
        app,
        False,
        {},
    )
    context = template.render.call_args[0][1]
    assert context['members'] == [
        'CONSTANT1',
        'CONSTANT2',
        '_Baz',
        '_Exc',
        '__all__',
        '__builtins__',
        '__cached__',
        '__doc__',
        '__file__',
        '__name__',
        '__package__',
        '_quux',
        'non_imported_member',
        'quuz',
        'qux',
    ]
    assert context['functions'] == []
    assert context['classes'] == []
    assert context['exceptions'] == []


@pytest.mark.sphinx('html', testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_imported_members(app):
    import autosummary_dummy_module

    template = Mock()

    generate_autosummary_content(
        'autosummary_dummy_module',
        autosummary_dummy_module,
        None,
        template,
        None,
        True,
        app,
        False,
        {},
    )
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == [
        'CONSTANT1',
        'CONSTANT2',
        'Class',
        'Exc',
        'Foo',
        'Union',
        '_Baz',
        '_Exc',
        '__all__',
        '__builtins__',
        '__cached__',
        '__doc__',
        '__file__',
        '__loader__',
        '__name__',
        '__package__',
        '__spec__',
        '_quux',
        'bar',
        'considered_as_imported',
        'non_imported_member',
        'path',
        'quuz',
        'qux',
    ]
    assert context['functions'] == ['bar']
    assert context['all_functions'] == ['_quux', 'bar']
    assert context['classes'] == ['Class', 'Foo']
    assert context['all_classes'] == ['Class', 'Foo', '_Baz']
    assert context['exceptions'] == ['Exc']
    assert context['all_exceptions'] == ['Exc', '_Exc']
    assert context['attributes'] == ['CONSTANT1', 'qux', 'quuz', 'non_imported_member']
    assert context['all_attributes'] == [
        'CONSTANT1',
        'qux',
        'quuz',
        'non_imported_member',
    ]
    assert context['fullname'] == 'autosummary_dummy_module'
    assert context['module'] == 'autosummary_dummy_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx('html', testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_imported_members_inherited_module(app):
    import autosummary_dummy_inherited_module  # type: ignore[import-not-found]

    template = Mock()

    generate_autosummary_content(
        'autosummary_dummy_inherited_module',
        autosummary_dummy_inherited_module,
        None,
        template,
        None,
        True,
        app,
        False,
        {},
    )
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == [
        'Foo',
        'InheritedAttrClass',
        '__all__',
        '__builtins__',
        '__cached__',
        '__doc__',
        '__file__',
        '__loader__',
        '__name__',
        '__package__',
        '__spec__',
    ]
    assert context['functions'] == []
    assert context['classes'] == ['Foo', 'InheritedAttrClass']
    assert context['exceptions'] == []
    assert context['all_exceptions'] == []
    assert context['attributes'] == []
    assert context['all_attributes'] == []
    assert context['fullname'] == 'autosummary_dummy_inherited_module'
    assert context['module'] == 'autosummary_dummy_inherited_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx(testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_imported_members_inherited_class(app):
    import autosummary_dummy_inherited_module

    template = Mock()

    generate_autosummary_content(
        'autosummary_dummy_inherited_module.InheritedAttrClass',
        autosummary_dummy_inherited_module.InheritedAttrClass,
        None,
        template,
        None,
        True,
        app,
        False,
        {},
    )
    assert template.render.call_args[0][0] == 'class'

    context = template.render.call_args[0][1]

    def assert_all_a_in_b(a, b):
        assert all(x in b for x in a)

    assert_all_a_in_b(
        [
            'Bar',
            'CONSTANT3',
            'CONSTANT4',
            '__init__',
            'bar',
            'baz',
            'subclassattr',
            'value',
        ],
        context['members'],
    )
    assert_all_a_in_b(
        ['Bar', 'CONSTANT3', 'CONSTANT4', 'bar', 'baz', 'value'],
        context['inherited_members'],
    )
    assert '__init__' not in context['inherited_members']
    assert 'subclassattr' not in context['inherited_members']

    assert context['methods'] == ['__init__', 'bar']
    assert context['attributes'] == [
        'CONSTANT3',
        'CONSTANT4',
        'baz',
        'subclassattr',
        'value',
    ]
    assert_all_a_in_b(
        [
            'autosummary_dummy_module.Foo.Bar',
            'autosummary_dummy_module.Foo.CONSTANT3',
            'autosummary_dummy_module.Foo.CONSTANT4',
            'autosummary_dummy_module.Foo.bar',
            'autosummary_dummy_module.Foo.baz',
            'autosummary_dummy_module.Foo.value',
        ],
        context['inherited_qualnames'],
    )
    assert context['inherited_methods'] == ['autosummary_dummy_module.Foo.bar']
    assert context['inherited_attributes'] == [
        'autosummary_dummy_module.Foo.CONSTANT3',
        'autosummary_dummy_module.Foo.CONSTANT4',
        'autosummary_dummy_module.Foo.baz',
        'autosummary_dummy_module.Foo.value',
    ]
    assert (
        context['fullname'] == 'autosummary_dummy_inherited_module.InheritedAttrClass'
    )
    assert context['module'] == 'autosummary_dummy_inherited_module'
    assert context['objname'] == 'InheritedAttrClass'
    assert context['name'] == 'InheritedAttrClass'
    assert context['objtype'] == 'class'


@pytest.mark.sphinx(testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_imported_members_complex_inheritance(
    app,
):
    import autosummary_dummy_complex_inheritance_module

    built_in_attr = autosummary_dummy_complex_inheritance_module.built_in_attr
    built_in_members = autosummary_dummy_complex_inheritance_module.built_in_members
    built_in_members2 = autosummary_dummy_complex_inheritance_module.built_in_members2

    template_jerry = Mock()

    generate_autosummary_content(
        name='autosummary_dummy_complex_inheritance_module.Jerry',
        obj=autosummary_dummy_complex_inheritance_module.Jerry,
        parent=None,
        template=template_jerry,
        template_name=None,
        imported_members=True,
        app=app,
        recursive=False,
        context={},
    )
    assert template_jerry.render.call_args[0][0] == 'class'

    context = template_jerry.render.call_args[0][1]

    assert context['name'] == 'Jerry'
    assert context['module'] == 'autosummary_dummy_complex_inheritance_module'
    assert context['fullname'] == 'autosummary_dummy_complex_inheritance_module.Jerry'

    assert context['attributes'] == ['relation']
    assert context['methods'] == [
        '__init__',
        'addition',
        'get_age',
        'get_name',
        'get_salary',
    ]

    assert context['all_attributes'] == [
        *built_in_attr,
        'relation',
    ]
    assert context['all_methods'] == [
        '__delattr__',
        '__dir__',
        '__eq__',
        '__format__',
        '__ge__',
        '__getattribute__',
        '__getstate__',
        '__gt__',
        '__hash__',
        '__init__',
        '__init_subclass__',
        '__le__',
        '__lt__',
        '__ne__',
        '__new__',
        '__reduce__',
        '__reduce_ex__',
        '__repr__',
        '__setattr__',
        '__sizeof__',
        '__str__',
        '__subclasshook__',
        'addition',
        'get_age',
        'get_name',
        'get_salary',
    ]

    assert context['inherited_attributes'] == [
        'autosummary_dummy_complex_inheritance_module.Parent.relation'
    ]
    assert context['inherited_methods'] == [
        'autosummary_dummy_complex_inheritance_module.Architect.get_age',
        'autosummary_dummy_complex_inheritance_module.Job.get_salary',
        'autosummary_dummy_complex_inheritance_module.Child.addition',
        'autosummary_dummy_complex_inheritance_module.Child.get_name',
    ]

    assert context['inherited_qualnames'] == [
        'autosummary_dummy_complex_inheritance_module.Architect.get_age',
        'autosummary_dummy_complex_inheritance_module.Job.__dict__',
        'autosummary_dummy_complex_inheritance_module.Job.__weakref__',
        'autosummary_dummy_complex_inheritance_module.Job.get_salary',
        'autosummary_dummy_complex_inheritance_module.Child.addition',
        'autosummary_dummy_complex_inheritance_module.Child.get_name',
        'autosummary_dummy_complex_inheritance_module.Parent.relation',
        'builtins.object.__class__',
        'builtins.object.__delattr__',
        'builtins.object.__dir__',
        'builtins.object.__eq__',
        'builtins.object.__format__',
        'builtins.object.__ge__',
        'builtins.object.__getattribute__',
        'builtins.object.__getstate__',
        'builtins.object.__gt__',
        'builtins.object.__hash__',
        'builtins.object.__init_subclass__',
        'builtins.object.__le__',
        'builtins.object.__lt__',
        'builtins.object.__ne__',
        'builtins.object.__new__',
        'builtins.object.__reduce__',
        'builtins.object.__reduce_ex__',
        'builtins.object.__repr__',
        'builtins.object.__setattr__',
        'builtins.object.__sizeof__',
        'builtins.object.__str__',
        'builtins.object.__subclasshook__',
    ]

    assert context['inherited_members'] == [
        '__class__',
        '__delattr__',
        '__dict__',
        '__dir__',
        '__eq__',
        '__format__',
        '__ge__',
        '__getattribute__',
        '__getstate__',
        '__gt__',
        '__hash__',
        '__init_subclass__',
        '__le__',
        '__lt__',
        '__ne__',
        '__new__',
        '__reduce__',
        '__reduce_ex__',
        '__repr__',
        '__setattr__',
        '__sizeof__',
        '__str__',
        '__subclasshook__',
        '__weakref__',
        'addition',
        'get_age',
        'get_name',
        'get_salary',
        'relation',
    ]

    assert context['members'] == [
        *built_in_members,
        'addition',
        'get_age',
        'get_name',
        'get_salary',
        'relation',
    ]

    template_baby = Mock()

    generate_autosummary_content(
        name='autosummary_dummy_complex_inheritance_module.Baby',
        obj=autosummary_dummy_complex_inheritance_module.Baby,
        parent=None,
        template=template_baby,
        template_name=None,
        imported_members=True,
        app=app,
        recursive=False,
        context={},
    )

    context2 = template_baby.render.call_args[0][1]

    assert context2['name'] == 'Baby'
    assert context2['module'] == 'autosummary_dummy_complex_inheritance_module'
    assert context2['fullname'] == 'autosummary_dummy_complex_inheritance_module.Baby'

    assert context2['attributes'] == ['relation']
    assert context2['methods'] == ['__init__', 'addition', 'get_age', 'get_name']

    assert context2['all_attributes'] == [
        '__private_baby_name',
        *built_in_attr,
        'relation',
    ]
    assert context2['all_methods'] == [
        '__delattr__',
        '__dir__',
        '__eq__',
        '__format__',
        '__ge__',
        '__getattribute__',
        '__getstate__',
        '__gt__',
        '__hash__',
        '__init__',
        '__init_subclass__',
        '__le__',
        '__lt__',
        '__ne__',
        '__new__',
        '__reduce__',
        '__reduce_ex__',
        '__repr__',
        '__setattr__',
        '__sizeof__',
        '__str__',
        '__subclasshook__',
        'addition',
        'get_age',
        'get_name',
    ]

    assert context2['inherited_attributes'] == [
        'autosummary_dummy_complex_inheritance_module.Parent.relation'
    ]
    assert context2['inherited_methods'] == [
        'autosummary_dummy_complex_inheritance_module.Child.addition',
        'autosummary_dummy_complex_inheritance_module.Child.get_name',
    ]

    assert context2['inherited_qualnames'] == [
        'autosummary_dummy_complex_inheritance_module.Child.addition',
        'autosummary_dummy_complex_inheritance_module.Child.get_name',
        'autosummary_dummy_complex_inheritance_module.Parent.__dict__',
        'autosummary_dummy_complex_inheritance_module.Parent.__weakref__',
        'autosummary_dummy_complex_inheritance_module.Parent.relation',
        'builtins.object.__class__',
        'builtins.object.__delattr__',
        'builtins.object.__dir__',
        'builtins.object.__eq__',
        'builtins.object.__format__',
        'builtins.object.__ge__',
        'builtins.object.__getattribute__',
        'builtins.object.__getstate__',
        'builtins.object.__gt__',
        'builtins.object.__hash__',
        'builtins.object.__init_subclass__',
        'builtins.object.__le__',
        'builtins.object.__lt__',
        'builtins.object.__ne__',
        'builtins.object.__new__',
        'builtins.object.__reduce__',
        'builtins.object.__reduce_ex__',
        'builtins.object.__repr__',
        'builtins.object.__setattr__',
        'builtins.object.__sizeof__',
        'builtins.object.__str__',
        'builtins.object.__subclasshook__',
    ]

    assert context2['inherited_members'] == [
        '__class__',
        '__delattr__',
        '__dict__',
        '__dir__',
        '__eq__',
        '__format__',
        '__ge__',
        '__getattribute__',
        '__getstate__',
        '__gt__',
        '__hash__',
        '__init_subclass__',
        '__le__',
        '__lt__',
        '__ne__',
        '__new__',
        '__reduce__',
        '__reduce_ex__',
        '__repr__',
        '__setattr__',
        '__sizeof__',
        '__str__',
        '__subclasshook__',
        '__weakref__',
        'addition',
        'get_name',
        'relation',
    ]

    assert context2['members'] == [
        'BabyInnerClass',
        '__private_baby_name',
        *built_in_members2,
        'addition',
        'get_age',
        'get_name',
        'relation',
    ]


@pytest.mark.sphinx('dummy', testroot='ext-autosummary')
def test_autosummary_generate(app):
    app.build(force_all=True)

    doctree = app.env.get_doctree('index')
    assert_node(
        doctree,
        (
            nodes.paragraph,
            nodes.paragraph,
            addnodes.tabular_col_spec,
            autosummary_table,
            [autosummary_toc, addnodes.toctree],
        ),
    )
    assert_node(
        doctree[3],
        [
            autosummary_table,
            nodes.table,
            nodes.tgroup,
            (
                nodes.colspec,
                nodes.colspec,
                [
                    nodes.tbody,
                    (
                        nodes.row,
                        nodes.row,
                        nodes.row,
                        nodes.row,
                        nodes.row,
                        nodes.row,
                        nodes.row,
                        nodes.row,
                    ),
                ],
            ),
        ],
    )
    assert_node(doctree[4][0], addnodes.toctree, caption='An autosummary')

    assert len(doctree[3][0][0][2]) == 8
    assert doctree[3][0][0][2][0].astext() == 'autosummary_dummy_module\n\n'
    assert doctree[3][0][0][2][1].astext() == 'autosummary_dummy_module.Foo()\n\n'
    assert doctree[3][0][0][2][2].astext() == 'autosummary_dummy_module.Foo.Bar()\n\n'
    assert doctree[3][0][0][2][3].astext() == (
        'autosummary_dummy_module.Foo.value\n\ndocstring'
    )
    assert doctree[3][0][0][2][4].astext() == 'autosummary_dummy_module.bar(x[, y])\n\n'
    assert doctree[3][0][0][2][5].astext() == (
        'autosummary_dummy_module.qux\n\na module-level attribute'
    )
    assert doctree[3][0][0][2][6].astext() == (
        'autosummary_dummy_inherited_module.InheritedAttrClass()\n\n'
    )
    assert doctree[3][0][0][2][7].astext() == (
        'autosummary_dummy_inherited_module.InheritedAttrClass.subclassattr\n\nother docstring'
    )

    path = app.srcdir / 'generated' / 'autosummary_dummy_module.rst'
    module = path.read_text(encoding='utf8')

    assert '   .. autosummary::\n   \n      Foo\n   \n' in module
    assert (
        '   .. autosummary::\n'
        '   \n'
        '      CONSTANT1\n'
        '      qux\n'
        '      quuz\n'
        '      non_imported_member\n'
        '   \n'
    ) in module

    path = app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.rst'
    Foo = path.read_text(encoding='utf8')
    assert '.. automethod:: __init__' in Foo
    assert (
        '   .. autosummary::\n   \n      ~Foo.__init__\n      ~Foo.bar\n   \n'
    ) in Foo
    assert (
        '   .. autosummary::\n'
        '   \n'
        '      ~Foo.CONSTANT3\n'
        '      ~Foo.CONSTANT4\n'
        '      ~Foo.baz\n'
        '      ~Foo.value\n'
        '   \n'
    ) in Foo

    path = app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.Bar.rst'
    FooBar = path.read_text(encoding='utf8')
    assert (
        '.. currentmodule:: autosummary_dummy_module\n\n.. autoclass:: Foo.Bar\n'
    ) in FooBar

    path = app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.value.rst'
    Foo_value = path.read_text(encoding='utf8')
    assert (
        '.. currentmodule:: autosummary_dummy_module\n\n.. autoattribute:: Foo.value'
    ) in Foo_value

    path = app.srcdir / 'generated' / 'autosummary_dummy_module.qux.rst'
    qux = path.read_text(encoding='utf8')
    assert '.. currentmodule:: autosummary_dummy_module\n\n.. autodata:: qux' in qux

    path = (
        app.srcdir
        / 'generated'
        / 'autosummary_dummy_inherited_module.InheritedAttrClass.rst'
    )
    InheritedAttrClass = path.read_text(encoding='utf8')
    print(InheritedAttrClass)
    assert '.. automethod:: __init__' in Foo
    assert (
        '   .. autosummary::\n'
        '   \n'
        '      ~InheritedAttrClass.__init__\n'
        '      ~InheritedAttrClass.bar\n'
        '   \n'
    ) in InheritedAttrClass
    assert (
        '   .. autosummary::\n'
        '   \n'
        '      ~InheritedAttrClass.CONSTANT3\n'
        '      ~InheritedAttrClass.CONSTANT4\n'
        '      ~InheritedAttrClass.baz\n'
        '      ~InheritedAttrClass.subclassattr\n'
        '      ~InheritedAttrClass.value\n'
        '   \n'
    ) in InheritedAttrClass

    path = (
        app.srcdir
        / 'generated'
        / 'autosummary_dummy_inherited_module.InheritedAttrClass.subclassattr.rst'
    )
    InheritedAttrClass_subclassattr = path.read_text(encoding='utf8')
    assert (
        '.. currentmodule:: autosummary_dummy_inherited_module\n'
        '\n'
        '.. autoattribute:: InheritedAttrClass.subclassattr'
    ) in InheritedAttrClass_subclassattr


@pytest.mark.sphinx(
    'dummy',
    testroot='ext-autosummary',
    confoverrides={'autosummary_generate_overwrite': False},
)
def test_autosummary_generate_overwrite1(app_params, make_app):
    args, kwargs = app_params
    srcdir = kwargs.get('srcdir')

    (srcdir / 'generated').mkdir(parents=True, exist_ok=True)
    (srcdir / 'generated' / 'autosummary_dummy_module.rst').write_text('', encoding='utf8')  # fmt: skip

    app = make_app(*args, **kwargs)
    path = srcdir / 'generated' / 'autosummary_dummy_module.rst'
    content = path.read_text(encoding='utf8')
    assert content == ''
    assert 'autosummary_dummy_module.rst' not in app._warning.getvalue()


@pytest.mark.sphinx(
    'dummy',
    testroot='ext-autosummary',
    confoverrides={'autosummary_generate_overwrite': True},
)
def test_autosummary_generate_overwrite2(app_params, make_app):
    args, kwargs = app_params
    srcdir = kwargs.get('srcdir')

    (srcdir / 'generated').mkdir(parents=True, exist_ok=True)
    (srcdir / 'generated' / 'autosummary_dummy_module.rst').write_text('', encoding='utf8')  # fmt: skip

    app = make_app(*args, **kwargs)
    path = srcdir / 'generated' / 'autosummary_dummy_module.rst'
    content = path.read_text(encoding='utf8')
    assert content != ''
    assert 'autosummary_dummy_module.rst' not in app._warning.getvalue()


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-recursive')
@pytest.mark.usefixtures('rollback_sysmodules')
def test_autosummary_recursive(app):
    sys.modules.pop('package', None)  # unload target module to clear the module cache

    app.build()

    # autosummary having :recursive: option
    assert (app.srcdir / 'generated' / 'package.rst').exists()
    assert (app.srcdir / 'generated' / 'package.module.rst').exists()
    assert not (app.srcdir / 'generated' / 'package.module_importfail.rst').exists()
    assert (app.srcdir / 'generated' / 'package.package.rst').exists()
    assert (app.srcdir / 'generated' / 'package.package.module.rst').exists()

    # autosummary not having :recursive: option
    assert (app.srcdir / 'generated' / 'package2.rst').exists()
    assert not (app.srcdir / 'generated' / 'package2.module.rst').exists()

    # Check content of recursively generated stub-files
    content = (app.srcdir / 'generated' / 'package.rst').read_text(encoding='utf8')
    assert 'module' in content
    assert 'package' in content
    assert 'module_importfail' in content
    # we no longer generate fully-qualified module names.
    assert 'package.module' not in content
    assert 'package.package' not in content
    assert 'package.module_importfail' not in content

    path = app.srcdir / 'generated' / 'package.package.rst'
    content = path.read_text(encoding='utf8')
    assert 'module' in content
    assert 'package.package.module' not in content

    warnings = app.warning.getvalue()
    assert 'Summarised items should not include the current module.' not in warnings


@pytest.mark.sphinx(
    'dummy',
    testroot='ext-autosummary-recursive',
    srcdir='test_autosummary_recursive_skips_mocked_modules',
    confoverrides={'autosummary_mock_imports': ['package.package']},
)
@pytest.mark.usefixtures('rollback_sysmodules')
def test_autosummary_recursive_skips_mocked_modules(app):
    sys.modules.pop('package', None)  # unload target module to clear the module cache
    app.build()

    assert (app.srcdir / 'generated' / 'package.rst').exists()
    assert (app.srcdir / 'generated' / 'package.module.rst').exists()
    assert not (app.srcdir / 'generated' / 'package.package.rst').exists()
    assert not (app.srcdir / 'generated' / 'package.package.module.rst').exists()


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-filename-map')
def test_autosummary_filename_map(app):
    app.build()

    assert (app.srcdir / 'generated' / 'module_mangled.rst').exists()
    assert not (app.srcdir / 'generated' / 'autosummary_dummy_module.rst').exists()
    assert (app.srcdir / 'generated' / 'bar.rst').exists()
    assert not (app.srcdir / 'generated' / 'autosummary_dummy_module.bar.rst').exists()
    assert (app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.rst').exists()

    html_warnings = app._warning.getvalue()
    assert html_warnings == ''


@pytest.mark.sphinx(
    'latex',
    testroot='ext-autosummary-ext',
    confoverrides=defaults.copy(),
)
def test_autosummary_latex_table_colspec(app):
    app.build(force_all=True)
    result = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    print(app.status.getvalue())
    print(app.warning.getvalue())
    assert r'\begin{longtable}{\X{1}{2}\X{1}{2}}' in result
    assert r'p{0.5\linewidth}' not in result


def test_import_by_name():
    import sphinx
    import sphinx.ext.autosummary

    prefixed_name, obj, parent, modname = import_by_name('sphinx')
    assert prefixed_name == 'sphinx'
    assert obj is sphinx
    assert parent is None
    assert modname == 'sphinx'

    prefixed_name, obj, parent, modname = import_by_name(
        'sphinx.ext.autosummary.__name__'
    )
    assert prefixed_name == 'sphinx.ext.autosummary.__name__'
    assert obj is sphinx.ext.autosummary.__name__
    assert parent is sphinx.ext.autosummary
    assert modname == 'sphinx.ext.autosummary'

    prefixed_name, obj, parent, modname = import_by_name(
        'sphinx.ext.autosummary.Autosummary.get_items'
    )
    assert prefixed_name == 'sphinx.ext.autosummary.Autosummary.get_items'
    assert obj == sphinx.ext.autosummary.Autosummary.get_items
    assert parent is sphinx.ext.autosummary.Autosummary
    assert modname == 'sphinx.ext.autosummary'


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-mock_imports')
def test_autosummary_mock_imports(app):
    try:
        app.build()
        assert app.warning.getvalue() == ''

        # generated/foo is generated successfully
        assert app.env.get_doctree('generated/foo')
    finally:
        sys.modules.pop('foo', None)  # unload foo module


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-imported_members')
def test_autosummary_imported_members(app):
    try:
        app.build()
        # generated/foo is generated successfully
        assert app.env.get_doctree('generated/autosummary_dummy_package')

        path = app.srcdir / 'generated' / 'autosummary_dummy_package.rst'
        module = path.read_text(encoding='utf8')
        assert '   .. autosummary::\n   \n      Bar\n   ' in module
        assert '   .. autosummary::\n   \n      foo\n   ' in module
    finally:
        sys.modules.pop('autosummary_dummy_package', None)


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-module_all')
def test_autosummary_module_all(app):
    try:
        app.build()
        # generated/foo is generated successfully
        assert app.env.get_doctree('generated/autosummary_dummy_package_all')
        path = app.srcdir / 'generated' / 'autosummary_dummy_package_all.rst'
        module = path.read_text(encoding='utf8')
        assert '   .. autosummary::\n   \n      PublicBar\n   \n' in module
        assert (
            '   .. autosummary::\n   \n      public_foo\n      public_baz\n   \n'
        ) in module
        assert (
            '.. autosummary::\n   :toctree:\n   :recursive:\n\n   extra_dummy_module\n'
        ) in module
    finally:
        sys.modules.pop('autosummary_dummy_package_all', None)


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-module_empty_all')
def test_autosummary_module_empty_all(app):
    try:
        app.build()
        # generated/foo is generated successfully
        assert app.env.get_doctree('generated/autosummary_dummy_package_empty_all')
        path = app.srcdir / 'generated' / 'autosummary_dummy_package_empty_all.rst'
        module = path.read_text(encoding='utf8')
        assert '.. automodule:: autosummary_dummy_package_empty_all' in module
        # for __all__ = (), the output should not contain any variables
        assert '__all__' not in module
        assert '__builtins__' not in module
        assert '__cached__' not in module
        assert '__doc__' not in module
        assert '__file__' not in module
        assert '__loader__' not in module
        assert '__name__' not in module
        assert '__package__' not in module
        assert '__path__' not in module
        assert '__spec__' not in module
    finally:
        sys.modules.pop('autosummary_dummy_package_all', None)


@pytest.mark.sphinx(
    'html',
    testroot='ext-autodoc',
    confoverrides={'extensions': ['sphinx.ext.autosummary']},
)
def test_generate_autosummary_docs_property(app):
    with patch('sphinx.ext.autosummary.generate.find_autosummary_in_files') as mock:
        mock.return_value = [
            AutosummaryEntry('target.methods.Base.prop', 'prop', None, False)
        ]
        generate_autosummary_docs([], output_dir=app.srcdir, app=app)

    content = (app.srcdir / 'target.methods.Base.prop.rst').read_text(encoding='utf8')
    assert content == (
        'target.methods.Base.prop\n'
        '========================\n'
        '\n'
        '.. currentmodule:: target.methods\n'
        '\n'
        '.. autoproperty:: Base.prop'
    )


@pytest.mark.sphinx('html', testroot='ext-autosummary-skip-member')
def test_autosummary_skip_member(app):
    app.build()

    content = (app.srcdir / 'generate' / 'target.Foo.rst').read_text(encoding='utf8')
    assert 'Foo.skipmeth' not in content
    assert 'Foo._privatemeth' in content


@pytest.mark.sphinx('html', testroot='ext-autosummary-template')
def test_autosummary_template(app):
    app.build()

    content = (app.srcdir / 'generate' / 'target.Foo.rst').read_text(encoding='utf8')
    assert 'EMPTY' in content


@pytest.mark.sphinx(
    'dummy',
    testroot='ext-autosummary',
    confoverrides={'autosummary_generate': []},
)
def test_empty_autosummary_generate(app):
    app.build()
    assert (
        'WARNING: autosummary: failed to import autosummary_importfail'
    ) in app.warning.getvalue()


@pytest.mark.sphinx(
    'dummy',
    testroot='ext-autosummary',
    confoverrides={'autosummary_generate': ['unknown']},
)
def test_invalid_autosummary_generate(app):
    assert (
        'WARNING: autosummary_generate: file not found: unknown.rst'
    ) in app.warning.getvalue()


def test_autogen(rootdir, tmp_path):
    with chdir(rootdir / 'test-templating'):
        args = ['-o', str(tmp_path), '-t', '.', 'autosummary_templating.txt']
        autogen_main(args)
        assert (tmp_path / 'sphinx.application.TemplateBridge.rst').exists()


def test_autogen_remove_old(rootdir, tmp_path):
    """Test the ``--remove-old`` option."""
    tmp_path.joinpath('other.rst').write_text('old content', encoding='utf-8')
    with chdir(rootdir / 'test-templating'):
        args = ['-o', str(tmp_path), '-t', '.', 'autosummary_templating.txt']
        autogen_main(args)
        assert set(tmp_path.iterdir()) == {
            tmp_path / 'sphinx.application.TemplateBridge.rst',
            tmp_path / 'other.rst',
        }
        autogen_main([*args, '--remove-old'])
        assert set(tmp_path.iterdir()) == {
            tmp_path / 'sphinx.application.TemplateBridge.rst'
        }
