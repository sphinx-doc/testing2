"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import typing

import pytest

from tests.test_extensions.autodoc_util import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_classes(app):
    actual = do_autodoc(app, 'function', 'target.classes.Foo')
    assert list(actual) == [
        '',
        '.. py:function:: Foo()',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc(app, 'function', 'target.classes.Bar')
    assert list(actual) == [
        '',
        '.. py:function:: Bar(x, y)',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc(app, 'function', 'target.classes.Baz')
    assert list(actual) == [
        '',
        '.. py:function:: Baz(x, y)',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc(app, 'function', 'target.classes.Qux')
    assert list(actual) == [
        '',
        '.. py:function:: Qux(foo, bar)',
        '   :module: target.classes',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_instance_variable(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.instance_variable.Bar', options)
    assert list(actual) == [
        '',
        '.. py:class:: Bar()',
        '   :module: target.instance_variable',
        '',
        '',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
        '',
        '   .. py:attribute:: Bar.attr3',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_inherited_instance_variable(app):
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.instance_variable.Bar', options)
    assert list(actual) == [
        '',
        '.. py:class:: Bar()',
        '   :module: target.instance_variable',
        '',
        '',
        '   .. py:attribute:: Bar.attr1',
        '      :module: target.instance_variable',
        '',
        '      docstring foo',
        '',
        '',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
        '',
        '   .. py:attribute:: Bar.attr3',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_uninitialized_attributes(app):
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc(
        app, 'class', 'target.uninitialized_attributes.Derived', options
    )
    assert list(actual) == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.uninitialized_attributes',
        '',
        '',
        '   .. py:attribute:: Derived.attr1',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Derived.attr3',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_undocumented_uninitialized_attributes(app):
    options = {
        'members': None,
        'inherited-members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(
        app, 'class', 'target.uninitialized_attributes.Derived', options
    )
    assert list(actual) == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.uninitialized_attributes',
        '',
        '',
        '   .. py:attribute:: Derived.attr1',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Derived.attr2',
        '      :module: target.uninitialized_attributes',
        '      :type: str',
        '',
        '',
        '   .. py:attribute:: Derived.attr3',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Derived.attr4',
        '      :module: target.uninitialized_attributes',
        '      :type: str',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_decorators(app):
    actual = do_autodoc(app, 'class', 'target.decorator.Baz')
    assert list(actual) == [
        '',
        '.. py:class:: Baz(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]

    actual = do_autodoc(app, 'class', 'target.decorator.Qux')
    assert list(actual) == [
        '',
        '.. py:class:: Qux(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]

    actual = do_autodoc(app, 'class', 'target.decorator.Quux')
    assert list(actual) == [
        '',
        '.. py:class:: Quux(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_properties(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.properties.Foo', options)
    assert list(actual) == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.properties',
        '',
        '   docstring',
        '',
        '',
        '   .. py:property:: Foo.prop1',
        '      :module: target.properties',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: Foo.prop1_with_type_comment',
        '      :module: target.properties',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: Foo.prop2',
        '      :module: target.properties',
        '      :classmethod:',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: Foo.prop2_with_type_comment',
        '      :module: target.properties',
        '      :classmethod:',
        '      :type: int',
        '',
        '      docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_slots_attribute(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.slots.Bar', options)
    assert list(actual) == [
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
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_show_inheritance_for_subclass_of_generic_type(app):
    options = {'show-inheritance': None}
    actual = do_autodoc(app, 'class', 'target.classes.Quux', options)
    assert list(actual) == [
        '',
        '.. py:class:: Quux(iterable=(), /)',
        '   :module: target.classes',
        '',
        '   Bases: :py:class:`~typing.List`\\ [:py:class:`int` | :py:class:`float`]',
        '',
        '   A subclass of List[Union[int, float]]',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_show_inheritance_for_decendants_of_generic_type(app):
    options = {'show-inheritance': None}
    actual = do_autodoc(app, 'class', 'target.classes.Corge', options)
    assert list(actual) == [
        '',
        '.. py:class:: Corge(iterable=(), /)',
        '   :module: target.classes',
        '',
        '   Bases: :py:class:`~target.classes.Quux`',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_process_bases(app):
    def autodoc_process_bases(app, name, obj, options, bases):
        assert name == 'target.classes.Quux'
        assert obj.__module__ == 'target.classes'
        assert obj.__name__ == 'Quux'
        assert options == {'show-inheritance': True, 'members': []}
        assert bases == [typing.List[typing.Union[int, float]]]  # NoQA: UP006, UP007

        bases.pop()
        bases.extend([int, str])

    app.connect('autodoc-process-bases', autodoc_process_bases)

    options = {'show-inheritance': None}
    actual = do_autodoc(app, 'class', 'target.classes.Quux', options)
    assert list(actual) == [
        '',
        '.. py:class:: Quux(iterable=(), /)',
        '   :module: target.classes',
        '',
        '   Bases: :py:class:`int`, :py:class:`str`',
        '',
        '   A subclass of List[Union[int, float]]',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_doc_from_class(app):
    options = {
        'members': None,
        'class-doc-from': 'class',
    }
    actual = do_autodoc(app, 'class', 'target.autoclass_content.C', options)
    assert list(actual) == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_doc_from_init(app):
    options = {
        'members': None,
        'class-doc-from': 'init',
    }
    actual = do_autodoc(app, 'class', 'target.autoclass_content.C', options)
    assert list(actual) == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_doc_from_both(app):
    options = {
        'members': None,
        'class-doc-from': 'both',
    }
    actual = do_autodoc(app, 'class', 'target.autoclass_content.C', options)
    assert list(actual) == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
        '   __init__ docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_alias(app):
    def autodoc_process_docstring(*args):
        """A handler always raises an error.
        This confirms this handler is never called for class aliases.
        """
        raise RuntimeError

    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    actual = do_autodoc(app, 'class', 'target.classes.Alias')
    assert list(actual) == [
        '',
        '.. py:attribute:: Alias',
        '   :module: target.classes',
        '',
        '   alias of :py:class:`~target.classes.Foo`',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_alias_having_doccomment(app):
    actual = do_autodoc(app, 'class', 'target.classes.OtherAlias')
    assert list(actual) == [
        '',
        '.. py:attribute:: OtherAlias',
        '   :module: target.classes',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_alias_for_imported_object_having_doccomment(app):
    actual = do_autodoc(app, 'class', 'target.classes.IntAlias')
    assert list(actual) == [
        '',
        '.. py:attribute:: IntAlias',
        '   :module: target.classes',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_coroutine(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.coroutine.AsyncClass', options)
    assert list(actual) == [
        '',
        '.. py:class:: AsyncClass()',
        '   :module: target.coroutine',
        '',
        '',
        '   .. py:method:: AsyncClass.do_asyncgen()',
        '      :module: target.coroutine',
        '      :async:',
        '',
        '      A documented async generator',
        '',
        '',
        '   .. py:method:: AsyncClass.do_coroutine()',
        '      :module: target.coroutine',
        '      :async:',
        '',
        '      A documented coroutine function',
        '',
        '',
        '   .. py:method:: AsyncClass.do_coroutine2()',
        '      :module: target.coroutine',
        '      :async:',
        '      :classmethod:',
        '',
        '      A documented coroutine classmethod',
        '',
        '',
        '   .. py:method:: AsyncClass.do_coroutine3()',
        '      :module: target.coroutine',
        '      :async:',
        '      :staticmethod:',
        '',
        '      A documented coroutine staticmethod',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata_NewType_module_level(app):
    actual = do_autodoc(app, 'class', 'target.typevar.T6')
    assert list(actual) == [
        '',
        '.. py:class:: T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`~datetime.date`',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_NewType_class_level(app):
    actual = do_autodoc(app, 'class', 'target.typevar.Class.T6')
    assert list(actual) == [
        '',
        '.. py:class:: Class.T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`~datetime.date`',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata_TypeVar_class_level(app):
    actual = do_autodoc(app, 'class', 'target.typevar.T1')
    assert list(actual) == [
        '',
        '.. py:class:: T1',
        '   :module: target.typevar',
        '',
        '   T1',
        '',
        "   alias of TypeVar('T1')",
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_TypeVar_module_level(app):
    actual = do_autodoc(app, 'class', 'target.typevar.Class.T1')
    assert list(actual) == [
        '',
        '.. py:class:: Class.T1',
        '   :module: target.typevar',
        '   :canonical: target.typevar.T1',
        '',
        '   T1',
        '',
        "   alias of TypeVar('T1')",
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_inherited_instance_variable_with_annotations(app):
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc(
        app, 'class', 'target.inherited_annotations.NoTypeAnnotation', options
    )
    assert list(actual) == [
        '',
        '.. py:class:: NoTypeAnnotation()',
        '   :module: target.inherited_annotations',
        '',
        '',
        '   .. py:attribute:: NoTypeAnnotation.a',
        '      :module: target.inherited_annotations',
        '      :value: 1',
        '',
        '      Local',
        '',
        '',
        '   .. py:attribute:: NoTypeAnnotation.inherit_me',
        '      :module: target.inherited_annotations',
        '      :type: int',
        '',
        '      Inherited',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_no_inherited_instance_variable_with_annotations(app):
    options = {'members': None}
    actual = do_autodoc(
        app, 'class', 'target.inherited_annotations.NoTypeAnnotation2', options
    )
    assert list(actual) == [
        '',
        '.. py:class:: NoTypeAnnotation2()',
        '   :module: target.inherited_annotations',
        '',
        '',
        '   .. py:attribute:: NoTypeAnnotation2.a',
        '      :module: target.inherited_annotations',
        '      :value: 1',
        '',
        '      Local',
        '',
    ]
