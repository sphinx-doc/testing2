"""Tests the Python Domain"""

from __future__ import annotations

import re
from unittest.mock import Mock

import docutils.utils
import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_annotation,
    desc_content,
    desc_name,
    desc_parameter,
    desc_parameterlist,
    desc_returns,
    desc_sig_keyword,
    desc_sig_literal_number,
    desc_sig_literal_string,
    desc_sig_name,
    desc_sig_operator,
    desc_sig_punctuation,
    desc_sig_space,
    desc_signature,
    desc_type_parameter,
    desc_type_parameter_list,
    pending_xref,
)
from sphinx.domains import IndexEntry
from sphinx.domains.python import PythonDomain, PythonModuleIndex
from sphinx.domains.python._annotations import _parse_annotation, _pseudo_parse_arglist
from sphinx.domains.python._object import py_sig_re
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node
from sphinx.writers.text import STDINDENT


def parse(sig):
    m = py_sig_re.match(sig)
    if m is None:
        raise ValueError
    name_prefix, tp_list, name, arglist, retann = m.groups()
    signode = addnodes.desc_signature(sig, '')
    _pseudo_parse_arglist(signode, arglist)
    return signode.astext()


def test_function_signatures():
    rv = parse("compile(source : string, filename, symbol='file')")
    assert rv == "(source : string, filename, symbol='file')"

    for params, expect in [
        ('(a=1)', '(a=1)'),
        ('(a: int = 1)', '(a: int = 1)'),
        ('(a=1, [b=None])', '(a=1, [b=None])'),
        ('(a=1[, b=None])', '(a=1, [b=None])'),
        ('(a=[], [b=None])', '(a=[], [b=None])'),
        ('(a=[][, b=None])', '(a=[], [b=None])'),
        ('(a: Foo[Bar]=[][, b=None])', '(a: Foo[Bar]=[], [b=None])'),
    ]:
        rv = parse(f'func{params}')
        assert rv == expect

        # Note: 'def f[Foo[Bar]]()' is not valid Python but people might write
        # it in a reST document to convene the intent of a higher-kinded type
        # variable.
        for tparams in ['', '[Foo]', '[Foo[Bar]]']:
            for retann in ['', '-> Foo', '-> Foo[Bar]', '-> anything else']:
                rv = parse(f'func{tparams}{params} {retann}'.rstrip())
                assert rv == expect


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_xrefs(app):
    """Domain objects have correct prefixes when looking up xrefs"""
    app.build(force_all=True)

    def assert_refnode(
        node, module_name, class_name, target, reftype=None, domain='py'
    ):
        attributes = {
            'refdomain': domain,
            'reftarget': target,
        }
        if reftype is not None:
            attributes['reftype'] = reftype
        if module_name is not False:
            attributes['py:module'] = module_name
        if class_name is not False:
            attributes['py:class'] = class_name
        assert_node(node, **attributes)

    doctree = app.env.get_doctree('roles')
    refnodes = list(doctree.findall(pending_xref))
    assert_refnode(refnodes[0], None, None, 'TopLevel', 'class')
    assert_refnode(refnodes[1], None, None, 'top_level', 'meth')
    assert_refnode(refnodes[2], None, None, 'TopLevelType', 'type')
    assert_refnode(refnodes[3], None, 'NestedParentA', 'child_1', 'meth')
    assert_refnode(
        refnodes[4], None, 'NestedParentA', 'NestedChildA.subchild_2', 'meth'
    )
    assert_refnode(refnodes[5], None, 'NestedParentA', 'child_2', 'meth')
    assert_refnode(refnodes[6], False, 'NestedParentA', 'any_child', domain='')
    assert_refnode(refnodes[7], None, 'NestedParentA', 'NestedChildA', 'class')
    assert_refnode(
        refnodes[8], None, 'NestedParentA.NestedChildA', 'subchild_2', 'meth'
    )
    assert_refnode(
        refnodes[9], None, 'NestedParentA.NestedChildA', 'NestedParentA.child_1', 'meth'
    )
    assert_refnode(
        refnodes[10], None, 'NestedParentA', 'NestedChildA.subchild_1', 'meth'
    )
    assert_refnode(refnodes[11], None, 'NestedParentB', 'child_1', 'meth')
    assert_refnode(refnodes[12], None, 'NestedParentB', 'NestedParentB', 'class')
    assert_refnode(refnodes[13], None, None, 'NestedParentA.NestedChildA', 'class')
    assert_refnode(refnodes[14], None, None, 'NestedParentA.NestedTypeA', 'type')
    assert len(refnodes) == 15

    doctree = app.env.get_doctree('module')
    refnodes = list(doctree.findall(pending_xref))
    assert_refnode(refnodes[0], 'module_a.submodule', None, 'ModTopLevel', 'class')
    assert_refnode(
        refnodes[1], 'module_a.submodule', 'ModTopLevel', 'mod_child_1', 'meth'
    )
    assert_refnode(
        refnodes[2],
        'module_a.submodule',
        'ModTopLevel',
        'ModTopLevel.mod_child_1',
        'meth',
    )
    assert_refnode(
        refnodes[3], 'module_a.submodule', 'ModTopLevel', 'mod_child_2', 'meth'
    )
    assert_refnode(
        refnodes[4],
        'module_a.submodule',
        'ModTopLevel',
        'module_a.submodule.ModTopLevel.mod_child_1',
        'meth',
    )
    assert_refnode(refnodes[5], 'module_a.submodule', 'ModTopLevel', 'prop', 'attr')
    assert_refnode(refnodes[6], 'module_a.submodule', 'ModTopLevel', 'prop', 'meth')
    assert_refnode(refnodes[7], 'module_b.submodule', None, 'ModTopLevel', 'class')
    assert_refnode(
        refnodes[8], 'module_b.submodule', 'ModTopLevel', 'ModNoModule', 'class'
    )
    assert_refnode(refnodes[9], False, False, 'int', 'class')
    assert_refnode(refnodes[10], False, False, 'tuple', 'class')
    assert_refnode(refnodes[11], False, False, 'str', 'class')
    assert_refnode(refnodes[12], False, False, 'float', 'class')
    assert_refnode(refnodes[13], False, False, 'list', 'class')
    assert_refnode(refnodes[14], False, False, 'ModTopLevel', 'class')
    assert_refnode(refnodes[15], False, False, 'index', 'doc', domain='std')
    assert_refnode(refnodes[16], False, False, 'typing.Literal', 'obj', domain='py')
    assert_refnode(refnodes[17], False, False, 'typing.Literal', 'obj', domain='py')
    assert_refnode(refnodes[18], False, False, 'list', 'class', domain='py')
    assert_refnode(refnodes[19], False, False, 'int', 'class', domain='py')
    assert_refnode(refnodes[20], False, False, 'str', 'class', domain='py')
    assert len(refnodes) == 21

    doctree = app.env.get_doctree('module_option')
    refnodes = list(doctree.findall(pending_xref))
    print(refnodes)
    print(refnodes[0])
    print(refnodes[1])
    assert_refnode(refnodes[0], 'test.extra', 'B', 'foo', 'meth')
    assert_refnode(refnodes[1], 'test.extra', 'B', 'foo', 'meth')
    assert len(refnodes) == 2


@pytest.mark.sphinx('html', testroot='domain-py')
def test_domain_py_xrefs_abbreviations(app):
    app.build(force_all=True)

    content = (app.outdir / 'abbr.html').read_text(encoding='utf8')
    assert re.search(
        r'normal: <a .* href="module.html#module_a.submodule.ModTopLevel.'
        r'mod_child_1" .*><.*>module_a.submodule.ModTopLevel.mod_child_1\(\)'
        r'<.*></a>',
        content,
    )
    assert re.search(
        r'relative: <a .* href="module.html#module_a.submodule.ModTopLevel.'
        r'mod_child_1" .*><.*>ModTopLevel.mod_child_1\(\)<.*></a>',
        content,
    )
    assert re.search(
        r'short name: <a .* href="module.html#module_a.submodule.ModTopLevel.'
        r'mod_child_1" .*><.*>mod_child_1\(\)<.*></a>',
        content,
    )
    assert re.search(
        r'relative \+ short name: <a .* href="module.html#module_a.submodule.'
        r'ModTopLevel.mod_child_1" .*><.*>mod_child_1\(\)<.*></a>',
        content,
    )
    assert re.search(
        r'short name \+ relative: <a .* href="module.html#module_a.submodule.'
        r'ModTopLevel.mod_child_1" .*><.*>mod_child_1\(\)<.*></a>',
        content,
    )


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_objects(app):
    app.build(force_all=True)

    modules = app.env.domains.python_domain.data['modules']
    objects = app.env.domains.python_domain.data['objects']

    assert 'module_a.submodule' in modules
    assert 'module_a.submodule' in objects
    assert 'module_b.submodule' in modules
    assert 'module_b.submodule' in objects

    assert objects['module_a.submodule.ModTopLevel'][2] == 'class'
    assert objects['module_a.submodule.ModTopLevel.mod_child_1'][2] == 'method'
    assert objects['module_a.submodule.ModTopLevel.mod_child_2'][2] == 'method'
    assert 'ModTopLevel.ModNoModule' not in objects
    assert objects['ModNoModule'][2] == 'class'
    assert objects['module_b.submodule.ModTopLevel'][2] == 'class'

    assert objects['TopLevel'][2] == 'class'
    assert objects['top_level'][2] == 'method'
    assert objects['TopLevelType'][2] == 'type'
    assert objects['NestedParentA'][2] == 'class'
    assert objects['NestedParentA.NestedTypeA'][2] == 'type'
    assert objects['NestedParentA.child_1'][2] == 'method'
    assert objects['NestedParentA.any_child'][2] == 'method'
    assert objects['NestedParentA.NestedChildA'][2] == 'class'
    assert objects['NestedParentA.NestedChildA.subchild_1'][2] == 'method'
    assert objects['NestedParentA.NestedChildA.subchild_2'][2] == 'method'
    assert objects['NestedParentA.child_2'][2] == 'method'
    assert objects['NestedParentB'][2] == 'class'
    assert objects['NestedParentB.child_1'][2] == 'method'


@pytest.mark.sphinx('html', testroot='domain-py')
def test_resolve_xref_for_properties(app):
    app.build(force_all=True)

    content = (app.outdir / 'module.html').read_text(encoding='utf8')
    assert (
        'Link to <a class="reference internal" href="#module_a.submodule.ModTopLevel.prop"'
        ' title="module_a.submodule.ModTopLevel.prop">'
        '<code class="xref py py-attr docutils literal notranslate"><span class="pre">'
        'prop</span> <span class="pre">attribute</span></code></a>'
    ) in content
    assert (
        'Link to <a class="reference internal" href="#module_a.submodule.ModTopLevel.prop"'
        ' title="module_a.submodule.ModTopLevel.prop">'
        '<code class="xref py py-meth docutils literal notranslate"><span class="pre">'
        'prop</span> <span class="pre">method</span></code></a>'
    ) in content
    assert (
        'Link to <a class="reference internal" href="#module_a.submodule.ModTopLevel.prop"'
        ' title="module_a.submodule.ModTopLevel.prop">'
        '<code class="xref py py-attr docutils literal notranslate"><span class="pre">'
        'prop</span> <span class="pre">attribute</span></code></a>'
    ) in content


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_find_obj(app):
    def find_obj(modname, prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains.python_domain.find_obj(
            app.env, modname, prefix, obj_name, obj_type, searchmode
        )

    app.build(force_all=True)

    assert find_obj(None, None, 'NONEXISTANT', 'class') == []
    assert find_obj(None, None, 'NestedParentA', 'class') == [
        (
            'NestedParentA',
            ('roles', 'NestedParentA', 'class', False),
        )
    ]
    assert find_obj(None, None, 'NestedParentA.NestedTypeA', 'type') == [
        (
            'NestedParentA.NestedTypeA',
            ('roles', 'NestedParentA.NestedTypeA', 'type', False),
        )
    ]
    assert find_obj(None, None, 'NestedParentA.NestedChildA', 'class') == [
        (
            'NestedParentA.NestedChildA',
            ('roles', 'NestedParentA.NestedChildA', 'class', False),
        )
    ]
    assert find_obj(None, 'NestedParentA', 'NestedChildA', 'class') == [
        (
            'NestedParentA.NestedChildA',
            ('roles', 'NestedParentA.NestedChildA', 'class', False),
        )
    ]
    assert find_obj(None, None, 'NestedParentA.NestedChildA.subchild_1', 'meth') == [
        (
            'NestedParentA.NestedChildA.subchild_1',
            ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method', False),
        )
    ]
    assert find_obj(None, 'NestedParentA', 'NestedChildA.subchild_1', 'meth') == [
        (
            'NestedParentA.NestedChildA.subchild_1',
            ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method', False),
        )
    ]
    assert find_obj(None, 'NestedParentA.NestedChildA', 'subchild_1', 'meth') == [
        (
            'NestedParentA.NestedChildA.subchild_1',
            ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method', False),
        )
    ]


@pytest.mark.sphinx('html', testroot='root')
def test_get_full_qualified_name():
    env = Mock(domaindata={})
    domain = PythonDomain(env)

    # non-python references
    node = nodes.reference()
    assert domain.get_full_qualified_name(node) is None

    # simple reference
    node = nodes.reference(reftarget='func')
    assert domain.get_full_qualified_name(node) == 'func'

    # with py:module context
    kwargs = {'py:module': 'module1'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.func'

    # with py:class context
    kwargs = {'py:class': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'Class.func'

    # with both py:module and py:class context
    kwargs = {'py:module': 'module1', 'py:class': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.Class.func'


@pytest.mark.sphinx('html', testroot='_blank')
def test_parse_annotation(app):
    doctree = _parse_annotation('int', app.env)
    assert_node(doctree, ([pending_xref, 'int'],))
    assert_node(
        doctree[0], pending_xref, refdomain='py', reftype='class', reftarget='int'
    )

    doctree = _parse_annotation('List[int]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'List'],
            [desc_sig_punctuation, '['],
            [pending_xref, 'int'],
            [desc_sig_punctuation, ']'],
        ),
    )

    doctree = _parse_annotation('Tuple[int, int]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Tuple'],
            [desc_sig_punctuation, '['],
            [pending_xref, 'int'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [pending_xref, 'int'],
            [desc_sig_punctuation, ']'],
        ),
    )

    doctree = _parse_annotation('Tuple[()]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Tuple'],
            [desc_sig_punctuation, '['],
            [desc_sig_punctuation, '('],
            [desc_sig_punctuation, ')'],
            [desc_sig_punctuation, ']'],
        ),
    )

    doctree = _parse_annotation('Tuple[int, ...]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Tuple'],
            [desc_sig_punctuation, '['],
            [pending_xref, 'int'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [desc_sig_punctuation, '...'],
            [desc_sig_punctuation, ']'],
        ),
    )

    doctree = _parse_annotation('Callable[[int, int], int]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Callable'],
            [desc_sig_punctuation, '['],
            [desc_sig_punctuation, '['],
            [pending_xref, 'int'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [pending_xref, 'int'],
            [desc_sig_punctuation, ']'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [pending_xref, 'int'],
            [desc_sig_punctuation, ']'],
        ),
    )

    doctree = _parse_annotation('Callable[[], int]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Callable'],
            [desc_sig_punctuation, '['],
            [desc_sig_punctuation, '['],
            [desc_sig_punctuation, ']'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [pending_xref, 'int'],
            [desc_sig_punctuation, ']'],
        ),
    )

    doctree = _parse_annotation('List[None]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'List'],
            [desc_sig_punctuation, '['],
            [pending_xref, 'None'],
            [desc_sig_punctuation, ']'],
        ),
    )

    # None type makes an object-reference (not a class reference)
    doctree = _parse_annotation('None', app.env)
    assert_node(doctree, ([pending_xref, 'None'],))
    assert_node(
        doctree[0], pending_xref, refdomain='py', reftype='obj', reftarget='None'
    )

    # Literal type makes an object-reference (not a class reference)
    doctree = _parse_annotation("typing.Literal['a', 'b']", app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Literal'],
            [desc_sig_punctuation, '['],
            [desc_sig_literal_string, "'a'"],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [desc_sig_literal_string, "'b'"],
            [desc_sig_punctuation, ']'],
        ),
    )
    assert_node(
        doctree[0],
        pending_xref,
        refdomain='py',
        reftype='obj',
        reftarget='typing.Literal',
    )

    # Annotated type with callable gets parsed
    doctree = _parse_annotation(
        'Annotated[Optional[str], annotated_types.MaxLen(max_length=10)]', app.env
    )
    assert_node(
        doctree,
        (
            [pending_xref, 'Annotated'],
            [desc_sig_punctuation, '['],
            [pending_xref, 'str'],
            [desc_sig_space, ' '],
            [desc_sig_punctuation, '|'],
            [desc_sig_space, ' '],
            [pending_xref, 'None'],
            [desc_sig_punctuation, ','],
            [desc_sig_space, ' '],
            [pending_xref, 'annotated_types.MaxLen'],
            [desc_sig_punctuation, '('],
            [desc_sig_name, 'max_length'],
            [desc_sig_operator, '='],
            [desc_sig_literal_number, '10'],
            [desc_sig_punctuation, ')'],
            [desc_sig_punctuation, ']'],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_parse_annotation_suppress(app):
    doctree = _parse_annotation('~typing.Dict[str, str]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Dict'],
            [desc_sig_punctuation, '['],
            [pending_xref, 'str'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [pending_xref, 'str'],
            [desc_sig_punctuation, ']'],
        ),
    )
    assert_node(
        doctree[0], pending_xref, refdomain='py', reftype='obj', reftarget='typing.Dict'
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_parse_annotation_Literal(app):
    doctree = _parse_annotation('Literal[True, False]', app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Literal'],
            [desc_sig_punctuation, '['],
            [desc_sig_keyword, 'True'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [desc_sig_keyword, 'False'],
            [desc_sig_punctuation, ']'],
        ),
    )

    doctree = _parse_annotation("typing.Literal[0, 1, 'abc']", app.env)
    assert_node(
        doctree,
        (
            [pending_xref, 'Literal'],
            [desc_sig_punctuation, '['],
            [desc_sig_literal_number, '0'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [desc_sig_literal_number, '1'],
            [desc_sig_punctuation, ','],
            desc_sig_space,
            [desc_sig_literal_string, "'abc'"],
            [desc_sig_punctuation, ']'],
        ),
    )


@pytest.mark.sphinx('html', testroot='root', freshenv=True)
def test_module_index(app):
    text = (
        '.. py:module:: docutils\n'
        '.. py:module:: sphinx\n'
        '.. py:module:: sphinx.config\n'
        '.. py:module:: sphinx.builders\n'
        '.. py:module:: sphinx.builders.html\n'
        '.. py:module:: sphinx_intl\n'
    )
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.domains.python_domain)
    assert index.generate() == (
        [
            (
                'd',
                [
                    IndexEntry(
                        name='docutils',
                        subtype=0,
                        docname='index',
                        anchor='module-docutils',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
            (
                's',
                [
                    IndexEntry(
                        name='sphinx',
                        subtype=1,
                        docname='index',
                        anchor='module-sphinx',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                    IndexEntry(
                        name='sphinx.builders',
                        subtype=2,
                        docname='index',
                        anchor='module-sphinx.builders',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                    IndexEntry(
                        name='sphinx.builders.html',
                        subtype=2,
                        docname='index',
                        anchor='module-sphinx.builders.html',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                    IndexEntry(
                        name='sphinx.config',
                        subtype=2,
                        docname='index',
                        anchor='module-sphinx.config',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                    IndexEntry(
                        name='sphinx_intl',
                        subtype=0,
                        docname='index',
                        anchor='module-sphinx_intl',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
        ],
        False,
    )


@pytest.mark.sphinx('html', testroot='root', freshenv=True)
def test_module_index_submodule(app):
    text = '.. py:module:: sphinx.config\n'
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.domains.python_domain)
    assert index.generate() == (
        [
            (
                's',
                [
                    IndexEntry(
                        name='sphinx',
                        subtype=1,
                        docname='',
                        anchor='',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                    IndexEntry(
                        name='sphinx.config',
                        subtype=2,
                        docname='index',
                        anchor='module-sphinx.config',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            )
        ],
        False,
    )


@pytest.mark.sphinx('html', testroot='root', freshenv=True)
def test_module_index_not_collapsed(app):
    text = '.. py:module:: docutils\n.. py:module:: sphinx\n'
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.domains.python_domain)
    assert index.generate() == (
        [
            (
                'd',
                [
                    IndexEntry(
                        name='docutils',
                        subtype=0,
                        docname='index',
                        anchor='module-docutils',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
            (
                's',
                [
                    IndexEntry(
                        name='sphinx',
                        subtype=0,
                        docname='index',
                        anchor='module-sphinx',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
        ],
        True,
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    freshenv=True,
    confoverrides={'modindex_common_prefix': ['sphinx.']},
)
def test_modindex_common_prefix(app):
    text = (
        '.. py:module:: docutils\n'
        '.. py:module:: sphinx\n'
        '.. py:module:: sphinx.config\n'
        '.. py:module:: sphinx.builders\n'
        '.. py:module:: sphinx.builders.html\n'
        '.. py:module:: sphinx_intl\n'
    )
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.domains.python_domain)
    assert index.generate() == (
        [
            (
                'b',
                [
                    IndexEntry(
                        name='sphinx.builders',
                        subtype=1,
                        docname='index',
                        anchor='module-sphinx.builders',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                    IndexEntry(
                        name='sphinx.builders.html',
                        subtype=2,
                        docname='index',
                        anchor='module-sphinx.builders.html',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
            (
                'c',
                [
                    IndexEntry(
                        name='sphinx.config',
                        subtype=0,
                        docname='index',
                        anchor='module-sphinx.config',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
            (
                'd',
                [
                    IndexEntry(
                        name='docutils',
                        subtype=0,
                        docname='index',
                        anchor='module-docutils',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
            (
                's',
                [
                    IndexEntry(
                        name='sphinx',
                        subtype=0,
                        docname='index',
                        anchor='module-sphinx',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                    IndexEntry(
                        name='sphinx_intl',
                        subtype=0,
                        docname='index',
                        anchor='module-sphinx_intl',
                        extra='',
                        qualifier='',
                        descr='',
                    ),
                ],
            ),
        ],
        True,
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_no_index_entry(app):
    text = '.. py:function:: f()\n.. py:function:: g()\n   :no-index-entry:\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('pair', 'built-in function; f()', 'f', '', None)],
    )
    assert_node(doctree[2], addnodes.index, entries=[])

    text = '.. py:class:: f\n.. py:class:: g\n   :no-index-entry:\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('single', 'f (built-in class)', 'f', '', None)],
    )
    assert_node(doctree[2], addnodes.index, entries=[])

    text = '.. py:module:: f\n.. py:module:: g\n   :no-index-entry:\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, nodes.target, nodes.target))
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('pair', 'module; f', 'module-f', '', None)],
    )


@pytest.mark.sphinx('html', testroot='domain-py-python_use_unqualified_type_names')
def test_python_python_use_unqualified_type_names(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<span class="n"><a class="reference internal" href="#foo.Name" title="foo.Name">'
        '<span class="pre">Name</span></a></span>'
    ) in content
    assert '<span class="n"><span class="pre">foo.Age</span></span>' in content
    assert (
        '<p><strong>name</strong> (<a class="reference internal" href="#foo.Name" '
        'title="foo.Name"><em>Name</em></a>) – blah blah</p>'
    ) in content
    assert '<p><strong>age</strong> (<em>foo.Age</em>) – blah blah</p>' in content


@pytest.mark.sphinx(
    'html',
    testroot='domain-py-python_use_unqualified_type_names',
    confoverrides={'python_use_unqualified_type_names': False},
)
def test_python_python_use_unqualified_type_names_disabled(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<span class="n"><a class="reference internal" href="#foo.Name" title="foo.Name">'
        '<span class="pre">foo.Name</span></a></span>'
    ) in content
    assert '<span class="n"><span class="pre">foo.Age</span></span>' in content
    assert (
        '<p><strong>name</strong> (<a class="reference internal" href="#foo.Name" '
        'title="foo.Name"><em>foo.Name</em></a>) – blah blah</p>'
    ) in content
    assert '<p><strong>age</strong> (<em>foo.Age</em>) – blah blah</p>' in content


@pytest.mark.sphinx('dummy', testroot='domain-py-xref-warning')
def test_warn_missing_reference(app):
    app.build()
    assert "index.rst:6: WARNING: undefined label: 'no-label'" in app.warning.getvalue()
    assert (
        'index.rst:6: WARNING: Failed to create a cross reference. '
        "A title or caption not found: 'existing-label'"
    ) in app.warning.getvalue()


@pytest.mark.parametrize('include_options', [True, False])
@pytest.mark.sphinx('html', testroot='root', confoverrides={'nitpicky': True})
def test_signature_line_number(app, include_options):
    text = '.. py:function:: foo(bar : string)\n' + (
        '   :no-index-entry:\n' if include_options else ''
    )
    doc = restructuredtext.parse(app, text)
    xrefs = list(doc.findall(condition=addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert 'index.rst' in source
    assert line == 1


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'python_maximum_signature_line_length': len('hello(name: str) -> str'),
        'maximum_signature_line_length': 1,
    },
)
def test_python_maximum_signature_line_length_overrides_global(app):
    text = '.. py:function:: hello(name: str) -> str'
    doctree = restructuredtext.parse(app, text)
    expected_doctree = (
        addnodes.index,
        [
            desc,
            (
                [
                    desc_signature,
                    (
                        [desc_name, 'hello'],
                        desc_parameterlist,
                        [desc_returns, pending_xref, 'str'],
                    ),
                ],
                desc_content,
            ),
        ],
    )
    assert_node(doctree, expected_doctree)
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    signame_node = [desc_sig_name, 'name']
    expected_sig = [
        desc_parameterlist,
        desc_parameter,
        (
            signame_node,
            [desc_sig_punctuation, ':'],
            desc_sig_space,
            [nodes.inline, pending_xref, 'str'],
        ),
    ]
    assert_node(doctree[1][0][1], expected_sig)
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=False)


@pytest.mark.sphinx(
    'html',
    testroot='domain-py-python_maximum_signature_line_length',
)
def test_domain_py_python_maximum_signature_line_length_in_html(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    expected_parameter_list_hello = """\

<dl>
<dd>\
<em class="sig-param">\
<span class="n"><span class="pre">name</span></span>\
<span class="p"><span class="pre">:</span></span>\
<span class="w"> </span>\
<span class="n"><span class="pre">str</span></span>\
</em>,\
</dd>
</dl>

<span class="sig-paren">)</span> \
<span class="sig-return">\
<span class="sig-return-icon">&#x2192;</span> \
<span class="sig-return-typehint"><span class="pre">str</span></span>\
</span>\
<a class="headerlink" href="#hello" title="Link to this definition">¶</a>\
</dt>\
"""
    assert expected_parameter_list_hello in content

    param_line_fmt = '<dd>{}</dd>\n'
    param_name_fmt = (
        '<em class="sig-param"><span class="n"><span class="pre">{}</span></span></em>'
    )
    optional_fmt = '<span class="optional">{}</span>'

    expected_a = param_line_fmt.format(
        optional_fmt.format('[')
        + param_name_fmt.format('a')
        + ','
        + optional_fmt.format('['),
    )
    assert expected_a in content

    expected_b = param_line_fmt.format(
        param_name_fmt.format('b')
        + ','
        + optional_fmt.format(']')
        + optional_fmt.format(']'),
    )
    assert expected_b in content

    expected_c = param_line_fmt.format(param_name_fmt.format('c') + ',')
    assert expected_c in content

    expected_d = param_line_fmt.format(
        param_name_fmt.format('d') + optional_fmt.format('[') + ','
    )
    assert expected_d in content

    expected_e = param_line_fmt.format(param_name_fmt.format('e') + ',')
    assert expected_e in content

    expected_f = param_line_fmt.format(
        param_name_fmt.format('f') + ',' + optional_fmt.format(']')
    )
    assert expected_f in content

    expected_parameter_list_foo = """\

<dl>
{}{}{}{}{}{}</dl>

<span class="sig-paren">)</span>\
<a class="headerlink" href="#foo" title="Link to this definition">¶</a>\
</dt>\
""".format(expected_a, expected_b, expected_c, expected_d, expected_e, expected_f)
    assert expected_parameter_list_foo in content


@pytest.mark.sphinx(
    'text',
    testroot='domain-py-python_maximum_signature_line_length',
)
def test_domain_py_python_maximum_signature_line_length_in_text(app):
    app.build()
    content = (app.outdir / 'index.txt').read_text(encoding='utf8')
    param_line_fmt = STDINDENT * ' ' + '{}\n'

    expected_parameter_list_hello = '(\n{}) -> str'.format(
        param_line_fmt.format('name: str,')
    )

    assert expected_parameter_list_hello in content

    expected_a = param_line_fmt.format('[a,[')
    assert expected_a in content

    expected_b = param_line_fmt.format('b,]]')
    assert expected_b in content

    expected_c = param_line_fmt.format('c,')
    assert expected_c in content

    expected_d = param_line_fmt.format('d[,')
    assert expected_d in content

    expected_e = param_line_fmt.format('e,')
    assert expected_e in content

    expected_f = param_line_fmt.format('f,]')
    assert expected_f in content

    expected_parameter_list_foo = '(\n{}{}{}{}{}{})'.format(
        expected_a,
        expected_b,
        expected_c,
        expected_d,
        expected_e,
        expected_f,
    )
    assert expected_parameter_list_foo in content


@pytest.mark.sphinx(
    'html',
    testroot='domain-py-python_maximum_signature_line_length',
    confoverrides={'python_trailing_comma_in_multi_line_signatures': False},
)
def test_domain_py_python_trailing_comma_in_multi_line_signatures_in_html(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    expected_parameter_list_hello = """\

<dl>
<dd>\
<em class="sig-param">\
<span class="n"><span class="pre">name</span></span>\
<span class="p"><span class="pre">:</span></span>\
<span class="w"> </span>\
<span class="n"><span class="pre">str</span></span>\
</em>\
</dd>
</dl>

<span class="sig-paren">)</span> \
<span class="sig-return">\
<span class="sig-return-icon">&#x2192;</span> \
<span class="sig-return-typehint"><span class="pre">str</span></span>\
</span>\
<a class="headerlink" href="#hello" title="Link to this definition">¶</a>\
</dt>\
"""
    assert expected_parameter_list_hello in content

    param_line_fmt = '<dd>{}</dd>\n'
    param_name_fmt = (
        '<em class="sig-param"><span class="n"><span class="pre">{}</span></span></em>'
    )
    optional_fmt = '<span class="optional">{}</span>'

    expected_a = param_line_fmt.format(
        optional_fmt.format('[')
        + param_name_fmt.format('a')
        + ','
        + optional_fmt.format('['),
    )
    assert expected_a in content

    expected_b = param_line_fmt.format(
        param_name_fmt.format('b')
        + ','
        + optional_fmt.format(']')
        + optional_fmt.format(']'),
    )
    assert expected_b in content

    expected_c = param_line_fmt.format(param_name_fmt.format('c') + ',')
    assert expected_c in content

    expected_d = param_line_fmt.format(
        param_name_fmt.format('d') + optional_fmt.format('[') + ','
    )
    assert expected_d in content

    expected_e = param_line_fmt.format(param_name_fmt.format('e') + ',')
    assert expected_e in content

    expected_f = param_line_fmt.format(
        param_name_fmt.format('f') + optional_fmt.format(']')
    )
    assert expected_f in content

    expected_parameter_list_foo = """\

<dl>
{}{}{}{}{}{}</dl>

<span class="sig-paren">)</span>\
<a class="headerlink" href="#foo" title="Link to this definition">¶</a>\
</dt>\
""".format(expected_a, expected_b, expected_c, expected_d, expected_e, expected_f)
    assert expected_parameter_list_foo in content


@pytest.mark.sphinx(
    'text',
    testroot='domain-py-python_maximum_signature_line_length',
    freshenv=True,
    confoverrides={'python_trailing_comma_in_multi_line_signatures': False},
)
def test_domain_py_python_trailing_comma_in_multi_line_signatures_in_text(app):
    app.build()
    content = (app.outdir / 'index.txt').read_text(encoding='utf8')
    param_line_fmt = STDINDENT * ' ' + '{}\n'

    expected_parameter_list_hello = '(\n{}) -> str'.format(
        param_line_fmt.format('name: str')
    )

    assert expected_parameter_list_hello in content

    expected_a = param_line_fmt.format('[a,[')
    assert expected_a in content

    expected_b = param_line_fmt.format('b,]]')
    assert expected_b in content

    expected_c = param_line_fmt.format('c,')
    assert expected_c in content

    expected_d = param_line_fmt.format('d[,')
    assert expected_d in content

    expected_e = param_line_fmt.format('e,')
    assert expected_e in content

    expected_f = param_line_fmt.format('f]')
    assert expected_f in content

    expected_parameter_list_foo = '(\n{}{}{}{}{}{})'.format(
        expected_a,
        expected_b,
        expected_c,
        expected_d,
        expected_e,
        expected_f,
    )
    assert expected_parameter_list_foo in content


@pytest.mark.sphinx('html', testroot='_blank')
def test_module_content_line_number(app):
    text = '.. py:module:: foo\n\n   Some link here: :ref:`abc`\n'
    doc = restructuredtext.parse(app, text)
    xrefs = list(doc.findall(condition=addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert 'index.rst' in source
    assert line == 3


@pytest.mark.sphinx(
    'html',
    testroot='root',
    freshenv=True,
    confoverrides={'python_display_short_literal_types': True},
)
def test_short_literal_types(app):
    text = """\
.. py:function:: literal_ints(x: Literal[1, 2, 3] = 1) -> None
.. py:function:: literal_union(x: Union[Literal["a"], Literal["b"], Literal["c"]]) -> None
"""
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [desc_name, 'literal_ints'],
                            [
                                desc_parameterlist,
                                (
                                    [
                                        desc_parameter,
                                        (
                                            [desc_sig_name, 'x'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [
                                                desc_sig_name,
                                                (
                                                    [desc_sig_literal_number, '1'],
                                                    desc_sig_space,
                                                    [desc_sig_punctuation, '|'],
                                                    desc_sig_space,
                                                    [desc_sig_literal_number, '2'],
                                                    desc_sig_space,
                                                    [desc_sig_punctuation, '|'],
                                                    desc_sig_space,
                                                    [desc_sig_literal_number, '3'],
                                                ),
                                            ],
                                            desc_sig_space,
                                            [desc_sig_operator, '='],
                                            desc_sig_space,
                                            [nodes.inline, '1'],
                                        ),
                                    ],
                                ),
                            ],
                            [desc_returns, pending_xref, 'None'],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [desc_name, 'literal_union'],
                            [
                                desc_parameterlist,
                                (
                                    [
                                        desc_parameter,
                                        (
                                            [desc_sig_name, 'x'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [
                                                desc_sig_name,
                                                (
                                                    [desc_sig_literal_string, "'a'"],
                                                    desc_sig_space,
                                                    [desc_sig_punctuation, '|'],
                                                    desc_sig_space,
                                                    [desc_sig_literal_string, "'b'"],
                                                    desc_sig_space,
                                                    [desc_sig_punctuation, '|'],
                                                    desc_sig_space,
                                                    [desc_sig_literal_string, "'c'"],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            [desc_returns, pending_xref, 'None'],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_function_pep_695(app):
    text = """.. py:function:: func[\
        S,\
        T: int,\
        U: (int, str),\
        R: int | str,\
        A: int | Annotated[int, ctype("char")],\
        *V,\
        **P\
    ]
    """
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [desc_name, 'func'],
                            [
                                desc_type_parameter_list,
                                (
                                    [desc_type_parameter, ([desc_sig_name, 'S'])],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'T'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [desc_sig_name, ([pending_xref, 'int'])],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'U'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [desc_sig_punctuation, '('],
                                            [
                                                desc_sig_name,
                                                (
                                                    [pending_xref, 'int'],
                                                    [desc_sig_punctuation, ','],
                                                    desc_sig_space,
                                                    [pending_xref, 'str'],
                                                ),
                                            ],
                                            [desc_sig_punctuation, ')'],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'R'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [
                                                desc_sig_name,
                                                (
                                                    [pending_xref, 'int'],
                                                    desc_sig_space,
                                                    [desc_sig_punctuation, '|'],
                                                    desc_sig_space,
                                                    [pending_xref, 'str'],
                                                ),
                                            ],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'A'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [
                                                desc_sig_name,
                                                (
                                                    [pending_xref, 'int'],
                                                    [desc_sig_space, ' '],
                                                    [desc_sig_punctuation, '|'],
                                                    [desc_sig_space, ' '],
                                                    [pending_xref, 'Annotated'],
                                                    [desc_sig_punctuation, '['],
                                                    [pending_xref, 'int'],
                                                    [desc_sig_punctuation, ','],
                                                    [desc_sig_space, ' '],
                                                    [pending_xref, 'ctype'],
                                                    [desc_sig_punctuation, '('],
                                                    [desc_sig_literal_string, "'char'"],
                                                    [desc_sig_punctuation, ')'],
                                                    [desc_sig_punctuation, ']'],
                                                ),
                                            ],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_operator, '*'],
                                            [desc_sig_name, 'V'],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_operator, '**'],
                                            [desc_sig_name, 'P'],
                                        ),
                                    ],
                                ),
                            ],
                            [desc_parameterlist, ()],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_class_def_pep_695(app):
    # Non-concrete unbound generics are allowed at runtime but type checkers
    # should fail (https://peps.python.org/pep-0695/#type-parameter-scopes)
    text = """.. py:class:: Class[S: Sequence[T], T, KT, VT](Dict[KT, VT])"""
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class'],
                            [
                                desc_type_parameter_list,
                                (
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'S'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [
                                                desc_sig_name,
                                                (
                                                    [pending_xref, 'Sequence'],
                                                    [desc_sig_punctuation, '['],
                                                    [pending_xref, 'T'],
                                                    [desc_sig_punctuation, ']'],
                                                ),
                                            ],
                                        ),
                                    ],
                                    [desc_type_parameter, ([desc_sig_name, 'T'])],
                                    [desc_type_parameter, ([desc_sig_name, 'KT'])],
                                    [desc_type_parameter, ([desc_sig_name, 'VT'])],
                                ),
                            ],
                            [desc_parameterlist, ([desc_parameter, 'Dict[KT, VT]'])],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_class_def_pep_696(app):
    # test default values for type variables without using PEP 696 AST parser
    text = """.. py:class:: Class[\
        T, KT, VT,\
        J: int,\
        K = list,\
        S: str = str,\
        L: (T, tuple[T, ...], collections.abc.Iterable[T]) = set[T],\
        Q: collections.abc.Mapping[KT, VT] = dict[KT, VT],\
        *V = *tuple[*Ts, bool],\
        **P = [int, Annotated[int, ValueRange(3, 10), ctype("char")]]\
    ](Other[T, KT, VT, J, S, L, Q, *V, **P])
    """
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class'],
                            [
                                desc_type_parameter_list,
                                (
                                    [desc_type_parameter, ([desc_sig_name, 'T'])],
                                    [desc_type_parameter, ([desc_sig_name, 'KT'])],
                                    [desc_type_parameter, ([desc_sig_name, 'VT'])],
                                    # J: int
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'J'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [desc_sig_name, ([pending_xref, 'int'])],
                                        ),
                                    ],
                                    # K = list
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'K'],
                                            desc_sig_space,
                                            [desc_sig_operator, '='],
                                            desc_sig_space,
                                            [nodes.inline, 'list'],
                                        ),
                                    ],
                                    # S: str = str
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'S'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [desc_sig_name, ([pending_xref, 'str'])],
                                            desc_sig_space,
                                            [desc_sig_operator, '='],
                                            desc_sig_space,
                                            [nodes.inline, 'str'],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'L'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [desc_sig_punctuation, '('],
                                            [
                                                desc_sig_name,
                                                (
                                                    # T
                                                    [pending_xref, 'T'],
                                                    [desc_sig_punctuation, ','],
                                                    desc_sig_space,
                                                    # tuple[T, ...]
                                                    [pending_xref, 'tuple'],
                                                    [desc_sig_punctuation, '['],
                                                    [pending_xref, 'T'],
                                                    [desc_sig_punctuation, ','],
                                                    desc_sig_space,
                                                    [desc_sig_punctuation, '...'],
                                                    [desc_sig_punctuation, ']'],
                                                    [desc_sig_punctuation, ','],
                                                    desc_sig_space,
                                                    # collections.abc.Iterable[T]
                                                    [
                                                        pending_xref,
                                                        'collections.abc.Iterable',
                                                    ],
                                                    [desc_sig_punctuation, '['],
                                                    [pending_xref, 'T'],
                                                    [desc_sig_punctuation, ']'],
                                                ),
                                            ],
                                            [desc_sig_punctuation, ')'],
                                            desc_sig_space,
                                            [desc_sig_operator, '='],
                                            desc_sig_space,
                                            [nodes.inline, 'set[T]'],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_name, 'Q'],
                                            [desc_sig_punctuation, ':'],
                                            desc_sig_space,
                                            [
                                                desc_sig_name,
                                                (
                                                    [
                                                        pending_xref,
                                                        'collections.abc.Mapping',
                                                    ],
                                                    [desc_sig_punctuation, '['],
                                                    [pending_xref, 'KT'],
                                                    [desc_sig_punctuation, ','],
                                                    desc_sig_space,
                                                    [pending_xref, 'VT'],
                                                    [desc_sig_punctuation, ']'],
                                                ),
                                            ],
                                            desc_sig_space,
                                            [desc_sig_operator, '='],
                                            desc_sig_space,
                                            [nodes.inline, 'dict[KT, VT]'],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_operator, '*'],
                                            [desc_sig_name, 'V'],
                                            desc_sig_space,
                                            [desc_sig_operator, '='],
                                            desc_sig_space,
                                            [nodes.inline, '*tuple[*Ts, bool]'],
                                        ),
                                    ],
                                    [
                                        desc_type_parameter,
                                        (
                                            [desc_sig_operator, '**'],
                                            [desc_sig_name, 'P'],
                                            desc_sig_space,
                                            [desc_sig_operator, '='],
                                            desc_sig_space,
                                            [
                                                nodes.inline,
                                                '[int, Annotated[int, ValueRange(3, 10), ctype("char")]]',
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            [
                                desc_parameterlist,
                                (
                                    [
                                        desc_parameter,
                                        'Other[T, KT, VT, J, S, L, Q, *V, **P]',
                                    ],
                                ),
                            ],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )


@pytest.mark.parametrize(
    ('tp_list', 'tptext'),
    [
        ('[T:int]', '[T: int]'),
        ('[T:*Ts]', '[T: *Ts]'),
        ('[T:int|(*Ts)]', '[T: int | (*Ts)]'),
        ('[T:(*Ts)|int]', '[T: (*Ts) | int]'),
        ('[T:(int|(*Ts))]', '[T: (int | (*Ts))]'),
        ('[T:((*Ts)|int)]', '[T: ((*Ts) | int)]'),
        ("[T:Annotated[int,ctype('char')]]", "[T: Annotated[int, ctype('char')]]"),
    ],
)
@pytest.mark.sphinx('html', testroot='root')
def test_pep_695_and_pep_696_whitespaces_in_bound(app, tp_list, tptext):
    text = f'.. py:function:: f{tp_list}()'
    doctree = restructuredtext.parse(app, text)
    assert doctree.astext() == f'\n\nf{tptext}()\n\n'

    text = f'.. py:function:: f{tp_list}() -> Annotated[T, Qux[int]()]'
    doctree = restructuredtext.parse(app, text)
    assert doctree.astext() == f'\n\nf{tptext}() -> Annotated[T, Qux[int]()]\n\n'


@pytest.mark.parametrize(
    ('tp_list', 'tptext'),
    [
        ('[T:(int,str)]', '[T: (int, str)]'),
        ('[T:(int|str,*Ts)]', '[T: (int | str, *Ts)]'),
    ],
)
@pytest.mark.sphinx('html', testroot='root')
def test_pep_695_and_pep_696_whitespaces_in_constraints(app, tp_list, tptext):
    text = f'.. py:function:: f{tp_list}()'
    doctree = restructuredtext.parse(app, text)
    assert doctree.astext() == f'\n\nf{tptext}()\n\n'

    text = f'.. py:function:: f{tp_list}() -> Annotated[T, Qux[int]()]'
    doctree = restructuredtext.parse(app, text)
    assert doctree.astext() == f'\n\nf{tptext}() -> Annotated[T, Qux[int]()]\n\n'


@pytest.mark.parametrize(
    ('tp_list', 'tptext'),
    [
        ('[T=int]', '[T = int]'),
        ('[T:int=int]', '[T: int = int]'),
        ('[*V=*Ts]', '[*V = *Ts]'),
        ('[*V=(*Ts)]', '[*V = (*Ts)]'),
        ('[*V=*tuple[str,...]]', '[*V = *tuple[str, ...]]'),
        ('[*V=*tuple[*Ts,...]]', '[*V = *tuple[*Ts, ...]]'),
        ('[*V=*tuple[int,*Ts]]', '[*V = *tuple[int, *Ts]]'),
        ('[*V=*tuple[*Ts,int]]', '[*V = *tuple[*Ts, int]]'),
        ('[**P=[int,*Ts]]', '[**P = [int, *Ts]]'),
        ('[**P=[int, int*3]]', '[**P = [int, int * 3]]'),
        ('[**P=[int, *Ts*3]]', '[**P = [int, *Ts * 3]]'),
        ('[**P=[int,A[int,ctype("char")]]]', '[**P = [int, A[int, ctype("char")]]]'),
    ],
)
@pytest.mark.sphinx('html', testroot='root')
def test_pep_695_and_pep_696_whitespaces_in_default(app, tp_list, tptext):
    text = f'.. py:function:: f{tp_list}()'
    doctree = restructuredtext.parse(app, text)
    assert doctree.astext() == f'\n\nf{tptext}()\n\n'

    text = f'.. py:function:: f{tp_list}() -> Annotated[T, Qux[int]()]'
    doctree = restructuredtext.parse(app, text)
    assert doctree.astext() == f'\n\nf{tptext}() -> Annotated[T, Qux[int]()]\n\n'
