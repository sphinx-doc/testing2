"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import pytest

from tests.test_extensions.autodoc_util import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute(app):
    actual = do_autodoc(app, 'attribute', 'target.Class.attr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        "   :value: 'bar'",
        '',
        '   should be documented -- süß',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_novalue(app):
    options = {'no-value': None}
    actual = do_autodoc(app, 'attribute', 'target.Class.attr', options)
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        '',
        '   should be documented -- süß',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_typed_variable(app):
    actual = do_autodoc(app, 'attribute', 'target.typed_vars.Class.attr2')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr2',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_typed_variable_in_alias(app):
    actual = do_autodoc(app, 'attribute', 'target.typed_vars.Alias.attr2')
    assert list(actual) == [
        '',
        '.. py:attribute:: Alias.attr2',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_instance_variable(app):
    actual = do_autodoc(app, 'attribute', 'target.typed_vars.Class.attr4')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr4',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
        '   attr4',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_instance_variable_in_alias(app):
    actual = do_autodoc(app, 'attribute', 'target.typed_vars.Alias.attr4')
    assert list(actual) == [
        '',
        '.. py:attribute:: Alias.attr4',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
        '   attr4',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_instance_variable_without_comment(app):
    actual = do_autodoc(app, 'attribute', 'target.instance_variable.Bar.attr4')
    assert list(actual) == [
        '',
        '.. py:attribute:: Bar.attr4',
        '   :module: target.instance_variable',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_slots_variable_list(app):
    actual = do_autodoc(app, 'attribute', 'target.slots.Foo.attr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Foo.attr',
        '   :module: target.slots',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_slots_variable_dict(app):
    actual = do_autodoc(app, 'attribute', 'target.slots.Bar.attr1')
    assert list(actual) == [
        '',
        '.. py:attribute:: Bar.attr1',
        '   :module: target.slots',
        '   :type: int',
        '',
        '   docstring of attr1',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_slots_variable_str(app):
    actual = do_autodoc(app, 'attribute', 'target.slots.Baz.attr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Baz.attr',
        '   :module: target.slots',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_GenericAlias(app):
    actual = do_autodoc(app, 'attribute', 'target.genericalias.Class.T')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.T',
        '   :module: target.genericalias',
        '   :canonical: typing.List',
        '',
        '   A list of int',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_TypeVar(app):
    actual = do_autodoc(app, 'attribute', 'target.typevar.Class.T1')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.T1',
        '   :module: target.typevar',
        '   :canonical: target.typevar.T1',
        '   :value: ~T1',
        '',
        '   T1',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_hide_value(app):
    actual = do_autodoc(app, 'attribute', 'target.hide_value.Foo.SENTINEL1')
    assert list(actual) == [
        '',
        '.. py:attribute:: Foo.SENTINEL1',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '   :meta hide-value:',
        '',
    ]

    actual = do_autodoc(app, 'attribute', 'target.hide_value.Foo.SENTINEL2')
    assert list(actual) == [
        '',
        '.. py:attribute:: Foo.SENTINEL2',
        '   :module: target.hide_value',
        '',
        '   :meta hide-value:',
        '',
    ]
