# -*- coding: utf-8 -*-
"""
    test_coverage
    ~~~~~~~~~~~~~

    Test the coverage builder.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pickle

import pytest


@pytest.mark.sphinx('coverage')
def test_build(app, status, warning):
    app.builder.build_all()

    py_undoc = (app.outdir / 'python.txt').text()
    assert py_undoc.startswith('Undocumented Python objects\n'
                               '===========================\n')
    assert 'autodoc_target\n--------------\n' in py_undoc
    assert ' * Class -- missing methods:\n' in py_undoc
    assert ' * raises\n' in py_undoc
    assert ' * function\n' not in py_undoc  # these two are documented
    assert ' * Class\n' not in py_undoc     # in autodoc.txt

    assert ' * mod -- No module named mod'  # in the "failed import" section

    c_undoc = (app.outdir / 'c.txt').text()
    assert c_undoc.startswith('Undocumented C API elements\n'
                              '===========================\n')
    assert 'api.h' in c_undoc
    assert ' * Py_SphinxTest' in c_undoc

    undoc_py, undoc_c, py_undocumented, py_documented = pickle.loads((app.outdir / 'undoc.pickle').bytes())
    assert len(undoc_c) == 1
    # the key is the full path to the header file, which isn't testable
    assert list(undoc_c.values())[0] == set([('function', 'Py_SphinxTest')])

    assert 'autodoc_target' in undoc_py
    assert 'funcs' in undoc_py['autodoc_target']
    assert 'raises' in undoc_py['autodoc_target']['funcs']
    assert 'classes' in undoc_py['autodoc_target']
    assert 'Class' in undoc_py['autodoc_target']['classes']
    assert 'undocmeth' in undoc_py['autodoc_target']['classes']['Class']
