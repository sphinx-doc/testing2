"""Test the doctest extension."""

from __future__ import annotations

import os
from collections import Counter

import pytest
from docutils import nodes
from packaging.specifiers import InvalidSpecifier
from packaging.version import InvalidVersion

from sphinx.ext.doctest import is_allowed_version

cleanup_called = 0


@pytest.mark.sphinx('doctest', testroot='ext-doctest')
def test_build(app):
    global cleanup_called  # NoQA: PLW0603
    cleanup_called = 0
    app.build(force_all=True)
    assert app.statuscode == 0, f'failures in doctests:\n{app.status.getvalue()}'
    # in doctest.txt, there are two named groups and the default group,
    # so the cleanup function must be called three times
    assert cleanup_called == 3, 'testcleanup did not get executed enough times'


@pytest.mark.sphinx('dummy', testroot='ext-doctest')
def test_highlight_language_default(app):
    app.build()
    doctree = app.env.get_doctree('doctest')
    for node in doctree.findall(nodes.literal_block):
        assert node['language'] in {'python', 'pycon', 'none'}


@pytest.mark.sphinx(
    'dummy',
    testroot='ext-doctest',
    confoverrides={'highlight_language': 'python'},
)
def test_highlight_language_python3(app):
    app.build()
    doctree = app.env.get_doctree('doctest')
    for node in doctree.findall(nodes.literal_block):
        assert node['language'] in {'python', 'pycon', 'none'}


def test_is_allowed_version():
    assert is_allowed_version('<3.4', '3.3') is True
    assert is_allowed_version('<3.4', '3.3') is True
    assert is_allowed_version('<3.2', '3.3') is False
    assert is_allowed_version('<=3.4', '3.3') is True
    assert is_allowed_version('<=3.2', '3.3') is False
    assert is_allowed_version('==3.3', '3.3') is True
    assert is_allowed_version('==3.4', '3.3') is False
    assert is_allowed_version('>=3.2', '3.3') is True
    assert is_allowed_version('>=3.4', '3.3') is False
    assert is_allowed_version('>3.2', '3.3') is True
    assert is_allowed_version('>3.4', '3.3') is False
    assert is_allowed_version('~=3.4', '3.4.5') is True
    assert is_allowed_version('~=3.4', '3.5.0') is True

    # invalid spec
    with pytest.raises(InvalidSpecifier):
        is_allowed_version('&3.4', '3.5')

    # invalid version
    with pytest.raises(InvalidVersion):
        is_allowed_version('>3.4', 'Sphinx')


def cleanup_call():
    global cleanup_called  # NoQA: PLW0603
    cleanup_called += 1


recorded_calls: Counter[tuple[str, str, int]] = Counter()


@pytest.mark.sphinx('doctest', testroot='ext-doctest-skipif')
def test_skipif(app):
    """Tests for the :skipif: option

    The tests are separated into a different test root directory since the
    ``app`` object only evaluates options once in its lifetime. If these tests
    were combined with the other doctest tests, the ``:skipif:`` evaluations
    would be recorded only on the first ``app.build(force_all=True)`` run, i.e.
    in ``test_build`` above, and the assertion below would fail.

    """
    global recorded_calls  # NoQA: PLW0603
    recorded_calls = Counter()
    app.build(force_all=True)
    if app.statuscode != 0:
        raise AssertionError('failures in doctests:' + app.status.getvalue())
    # The `:skipif:` expressions are always run.
    # Actual tests and setup/cleanup code is only run if the `:skipif:`
    # expression evaluates to a False value.
    # Global setup/cleanup are run before/after evaluating the `:skipif:`
    # option in each directive - thus 11 additional invocations for each on top
    # of the ones made for the whole test file.
    assert recorded_calls == {
        ('doctest_global_setup', 'body', True): 13,
        ('testsetup', ':skipif:', True): 1,
        ('testsetup', ':skipif:', False): 1,
        ('testsetup', 'body', False): 1,
        ('doctest', ':skipif:', True): 1,
        ('doctest', ':skipif:', False): 1,
        ('doctest', 'body', False): 1,
        ('testcode', ':skipif:', True): 1,
        ('testcode', ':skipif:', False): 1,
        ('testcode', 'body', False): 1,
        ('testoutput-1', ':skipif:', True): 1,
        ('testoutput-2', ':skipif:', True): 1,
        ('testoutput-2', ':skipif:', False): 1,
        ('testcleanup', ':skipif:', True): 1,
        ('testcleanup', ':skipif:', False): 1,
        ('testcleanup', 'body', False): 1,
        ('doctest_global_cleanup', 'body', True): 13,
    }


def record(directive, part, should_skip):
    recorded_calls[directive, part, should_skip] += 1
    return f'Recorded {directive} {part} {should_skip}'


@pytest.mark.sphinx('doctest', testroot='ext-doctest-with-autodoc')
def test_reporting_with_autodoc(app, capfd):
    # Patch builder to get a copy of the output
    written = []
    app.builder._warn_out = written.append
    app.build(force_all=True)

    failures = [
        line.replace(os.sep, '/')
        for line in '\n'.join(written).splitlines()
        if line.startswith('File')
    ]

    assert 'File "dir/inner.rst", line 1, in default' in failures
    assert 'File "dir/bar.py", line ?, in default' in failures
    assert 'File "foo.py", line ?, in default' in failures
    assert 'File "index.rst", line 4, in default' in failures


@pytest.mark.sphinx('doctest', testroot='ext-doctest-fail-fast')
@pytest.mark.parametrize('fail_fast', [False, True, None])
def test_fail_fast(app, fail_fast, capsys):
    if fail_fast is not None:
        app.config.doctest_fail_fast = fail_fast
    # Patch builder to get a copy of the output
    written = []
    app.builder._out = written.append
    app.build(force_all=True)
    assert app.statuscode

    written = ''.join(written)
    if fail_fast:
        assert 'Doctest summary (exiting after first failed test)' in written
        assert '1 failure in tests' in written
    else:
        assert 'Doctest summary\n' in written
        assert '2 failures in tests' in written
