"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

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
def test_callable(app):
    actual = do_autodoc(app, 'function', 'target.callable.function')
    assert list(actual) == [
        '',
        '.. py:function:: function(arg1, arg2, **kwargs)',
        '   :module: target.callable',
        '',
        '   A callable object that behaves like a function.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_method(app):
    actual = do_autodoc(app, 'function', 'target.callable.method')
    assert list(actual) == [
        '',
        '.. py:function:: method(arg1, arg2)',
        '   :module: target.callable',
        '   :canonical: target.callable.Callable.method',
        '',
        '   docstring of Callable.method().',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_builtin_function(app):
    import os

    actual = do_autodoc(app, 'function', 'os.umask')
    assert list(actual) == [
        '',
        '.. py:function:: umask(mask, /)',
        '   :module: os',
        f'   :canonical: {os.name}.umask',
        '',
        '   Set the current numeric umask and return the previous umask.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_methoddescriptor(app):
    actual = do_autodoc(app, 'function', 'builtins.int.__add__')
    assert list(actual) == [
        '',
        '.. py:function:: int.__add__(self, value, /)',
        '   :module: builtins',
        '',
        '   Return self+value.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_decorated(app):
    actual = do_autodoc(app, 'function', 'target.decorator.foo')
    assert list(actual) == [
        '',
        '.. py:function:: foo(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatch(app):
    options: dict[str, Any] = {}
    actual = do_autodoc(app, 'function', 'target.singledispatch.func', options)
    assert list(actual) == [
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
def test_cfunction(app):
    actual = do_autodoc(app, 'function', 'time.asctime')
    assert list(actual) == [
        '',
        '.. py:function:: asctime([tuple]) -> string',
        '   :module: time',
        '',
        "   Convert a time tuple to a string, e.g. 'Sat Jun 06 16:26:11 1998'.",
        '   When the time tuple is not present, current time as returned by localtime()',
        '   is used.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_wrapped_function(app):
    actual = do_autodoc(app, 'function', 'target.wrappedfunction.slow_function')
    assert list(actual) == [
        '',
        '.. py:function:: slow_function(message, timeout)',
        '   :module: target.wrappedfunction',
        '',
        '   This function is slow.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_wrapped_function_contextmanager(app):
    actual = do_autodoc(app, 'function', 'target.wrappedfunction.feeling_good')
    assert list(actual) == [
        '',
        '.. py:function:: feeling_good(x: int, y: int) -> ~typing.Generator',
        '   :module: target.wrappedfunction',
        '',
        "   You'll feel better in this context!",
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_coroutine(app):
    actual = do_autodoc(app, 'function', 'target.functions.coroutinefunc')
    assert list(actual) == [
        '',
        '.. py:function:: coroutinefunc()',
        '   :module: target.functions',
        '   :async:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_synchronized_coroutine(app):
    actual = do_autodoc(app, 'function', 'target.coroutine.sync_func')
    assert list(actual) == [
        '',
        '.. py:function:: sync_func()',
        '   :module: target.coroutine',
        '   :canonical: target.coroutine._other_coro_func',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_async_generator(app):
    actual = do_autodoc(app, 'function', 'target.functions.asyncgenerator')
    assert list(actual) == [
        '',
        '.. py:function:: asyncgenerator()',
        '   :module: target.functions',
        '   :async:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_slice_function_arg(app):
    actual = do_autodoc(app, 'function', 'target.functions.slice_arg_func')
    assert list(actual) == [
        '',
        '.. py:function:: slice_arg_func(arg: float64[:, :])',
        '   :module: target.functions',
        '',
    ]
