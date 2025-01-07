"""Test the sphinx.apidoc module."""

from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING

import pytest

import sphinx.ext.apidoc._generate
from sphinx.ext.apidoc._cli import main as apidoc_main

if TYPE_CHECKING:
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp

_apidoc = namedtuple('_apidoc', 'coderoot,outdir')  # NoQA: PYI024


@pytest.fixture
def apidoc(rootdir, tmp_path, apidoc_params):
    _, kwargs = apidoc_params
    coderoot = rootdir / kwargs.get('coderoot', 'test-root')
    outdir = tmp_path / 'out'
    excludes = [str(coderoot / e) for e in kwargs.get('excludes', [])]
    args = [
        '-o',
        str(outdir),
        '-F',
        str(coderoot),
        *excludes,
        *kwargs.get('options', []),
    ]
    apidoc_main(args)
    return _apidoc(coderoot, outdir)


@pytest.fixture
def apidoc_params(request):
    pargs = {}
    kwargs = {}

    for info in reversed(list(request.node.iter_markers('apidoc'))):
        pargs |= dict(enumerate(info.args))
        kwargs.update(info.kwargs)

    args = [pargs[i] for i in sorted(pargs.keys())]
    return args, kwargs


@pytest.mark.apidoc(coderoot='test-root')
def test_simple(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'index.rst').is_file()

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-custom-templates',
    options=[
        '--separate',
        '--templatedir=tests/roots/test-ext-apidoc-custom-templates/_templates',
    ],
)
def test_custom_templates(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'index.rst').is_file()

    template_dir = apidoc.coderoot / '_templates'
    assert sorted(template_dir.iterdir()) == [
        template_dir / 'module.rst.jinja',
        template_dir / 'module.rst_t',
        template_dir / 'package.rst_t',
    ]

    app = make_app('text', srcdir=outdir)
    app.build()

    builddir = outdir / '_build' / 'text'

    # Assert that the legacy filename is discovered
    with open(builddir / 'mypackage.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'The legacy package template was found!' in txt

    # Assert that the new filename is preferred
    with open(builddir / 'mypackage.mymodule.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'The Jinja module template was found!' in txt


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-pep420/a',
    options=['--implicit-namespaces'],
)
def test_pep_0420_enabled(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'a.b.c.rst').is_file()
    assert (outdir / 'a.b.e.rst').is_file()
    assert (outdir / 'a.b.x.rst').is_file()

    with open(outdir / 'a.b.c.rst', encoding='utf-8') as f:
        rst = f.read()
    assert 'automodule:: a.b.c.d\n' in rst
    assert 'automodule:: a.b.c\n' in rst

    with open(outdir / 'a.b.e.rst', encoding='utf-8') as f:
        rst = f.read()
    assert 'automodule:: a.b.e.f\n' in rst

    with open(outdir / 'a.b.x.rst', encoding='utf-8') as f:
        rst = f.read()
    assert 'automodule:: a.b.x.y\n' in rst
    assert 'automodule:: a.b.x\n' not in rst

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())

    builddir = outdir / '_build' / 'text'
    assert (builddir / 'a.b.c.txt').is_file()
    assert (builddir / 'a.b.e.txt').is_file()
    assert (builddir / 'a.b.x.txt').is_file()

    with open(builddir / 'a.b.c.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'a.b.c package\n' in txt

    with open(builddir / 'a.b.e.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'a.b.e.f module\n' in txt

    with open(builddir / 'a.b.x.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'a.b.x namespace\n' in txt


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-pep420/a',
    options=['--implicit-namespaces', '--separate'],
)
def test_pep_0420_enabled_separate(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'a.b.c.rst').is_file()
    assert (outdir / 'a.b.e.rst').is_file()
    assert (outdir / 'a.b.e.f.rst').is_file()
    assert (outdir / 'a.b.x.rst').is_file()
    assert (outdir / 'a.b.x.y.rst').is_file()

    with open(outdir / 'a.b.c.rst', encoding='utf-8') as f:
        rst = f.read()
    assert '.. toctree::\n   :maxdepth: 4\n\n   a.b.c.d\n' in rst

    with open(outdir / 'a.b.e.rst', encoding='utf-8') as f:
        rst = f.read()
    assert '.. toctree::\n   :maxdepth: 4\n\n   a.b.e.f\n' in rst

    with open(outdir / 'a.b.x.rst', encoding='utf-8') as f:
        rst = f.read()
    assert '.. toctree::\n   :maxdepth: 4\n\n   a.b.x.y\n' in rst

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())

    builddir = outdir / '_build' / 'text'
    assert (builddir / 'a.b.c.txt').is_file()
    assert (builddir / 'a.b.e.txt').is_file()
    assert (builddir / 'a.b.e.f.txt').is_file()
    assert (builddir / 'a.b.x.txt').is_file()
    assert (builddir / 'a.b.x.y.txt').is_file()

    with open(builddir / 'a.b.c.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'a.b.c package\n' in txt

    with open(builddir / 'a.b.e.f.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'a.b.e.f module\n' in txt

    with open(builddir / 'a.b.x.txt', encoding='utf-8') as f:
        txt = f.read()
    assert 'a.b.x namespace\n' in txt


@pytest.mark.apidoc(coderoot='test-ext-apidoc-pep420/a')
def test_pep_0420_disabled(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert not (outdir / 'a.b.c.rst').exists()
    assert not (outdir / 'a.b.x.rst').exists()

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(coderoot='test-ext-apidoc-pep420/a/b')
def test_pep_0420_disabled_top_level_verify(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'c.rst').is_file()
    assert not (outdir / 'x.rst').exists()

    with open(outdir / 'c.rst', encoding='utf-8') as f:
        rst = f.read()
    assert 'c package\n' in rst
    assert 'automodule:: c.d\n' in rst
    assert 'automodule:: c\n' in rst

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(coderoot='test-ext-apidoc-trailing-underscore')
def test_trailing_underscore(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'package_.rst').is_file()

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())

    builddir = outdir / '_build' / 'text'
    with open(builddir / 'package_.txt', encoding='utf-8') as f:
        rst = f.read()
    assert 'package_ package\n' in rst
    assert 'package_.module_ module\n' in rst


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-pep420/a',
    excludes=['b/c/d.py', 'b/e/f.py', 'b/e/__init__.py'],
    options=['--implicit-namespaces', '--separate'],
)
def test_excludes(apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'a.rst').is_file()
    assert (outdir / 'a.b.rst').is_file()
    assert (outdir / 'a.b.c.rst').is_file()  # generated because not empty
    assert not (
        outdir / 'a.b.e.rst'
    ).is_file()  # skipped because of empty after excludes
    assert (outdir / 'a.b.x.rst').is_file()
    assert (outdir / 'a.b.x.y.rst').is_file()


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-pep420/a',
    excludes=['b/e'],
    options=['--implicit-namespaces', '--separate'],
)
def test_excludes_subpackage_should_be_skipped(apidoc):
    """Subpackage exclusion should work."""
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'a.rst').is_file()
    assert (outdir / 'a.b.rst').is_file()
    assert (outdir / 'a.b.c.rst').is_file()  # generated because not empty
    assert not (
        outdir / 'a.b.e.f.rst'
    ).is_file()  # skipped because 'b/e' subpackage is skipped


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-pep420/a',
    excludes=['b/e/f.py'],
    options=['--implicit-namespaces', '--separate'],
)
def test_excludes_module_should_be_skipped(apidoc):
    """Module exclusion should work."""
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'a.rst').is_file()
    assert (outdir / 'a.b.rst').is_file()
    assert (outdir / 'a.b.c.rst').is_file()  # generated because not empty
    assert not (
        outdir / 'a.b.e.f.rst'
    ).is_file()  # skipped because of empty after excludes


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-pep420/a',
    excludes=[],
    options=['--implicit-namespaces', '--separate'],
)
def test_excludes_module_should_not_be_skipped(apidoc):
    """Module should be included if no excludes are used."""
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'a.rst').is_file()
    assert (outdir / 'a.b.rst').is_file()
    assert (outdir / 'a.b.c.rst').is_file()  # generated because not empty
    assert (outdir / 'a.b.e.f.rst').is_file()  # skipped because of empty after excludes


@pytest.mark.apidoc(
    coderoot='test-root',
    options=[
        '--doc-project',
        'プロジェクト名',
        '--doc-author',
        '著者名',
        '--doc-version',
        'バージョン',
        '--doc-release',
        'リリース',
    ],
)
def test_multibyte_parameters(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()
    assert (outdir / 'index.rst').is_file()

    conf_py = (outdir / 'conf.py').read_text(encoding='utf8')
    assert "project = 'プロジェクト名'" in conf_py
    assert "author = '著者名'" in conf_py
    assert "version = 'バージョン'" in conf_py
    assert "release = 'リリース'" in conf_py

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(
    coderoot='test-root',
    options=['--ext-mathjax'],
)
def test_extension_parsed(apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()

    with open(outdir / 'conf.py', encoding='utf-8') as f:
        rst = f.read()
    assert 'sphinx.ext.mathjax' in rst


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-toc/mypackage',
    options=['--implicit-namespaces'],
)
def test_toc_all_references_should_exist_pep420_enabled(apidoc):
    """All references in toc should exist. This test doesn't say if
    directories with empty __init__.py and and nothing else should be
    skipped, just ensures consistency between what's referenced in the toc
    and what is created. This is the variant with pep420 enabled.
    """
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()

    toc = extract_toc(outdir / 'mypackage.rst')

    refs = [l.strip() for l in toc.splitlines() if l.strip()]
    found_refs = []
    missing_files = []
    for ref in refs:
        if ref and ref[0] in {':', '#'}:
            continue
        found_refs.append(ref)
        filename = f'{ref}.rst'
        if not (outdir / filename).is_file():
            missing_files.append(filename)

    all_missing = ', '.join(missing_files)
    assert len(missing_files) == 0, (
        f'File(s) referenced in TOC not found: {all_missing}\nTOC:\n{toc}'
    )


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-toc/mypackage',
)
def test_toc_all_references_should_exist_pep420_disabled(apidoc):
    """All references in toc should exist. This test doesn't say if
    directories with empty __init__.py and and nothing else should be
    skipped, just ensures consistency between what's referenced in the toc
    and what is created. This is the variant with pep420 disabled.
    """
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()

    toc = extract_toc(outdir / 'mypackage.rst')

    refs = [l.strip() for l in toc.splitlines() if l.strip()]
    found_refs = []
    missing_files = []
    for ref in refs:
        if ref and ref[0] in {':', '#'}:
            continue
        filename = f'{ref}.rst'
        found_refs.append(ref)
        if not (outdir / filename).is_file():
            missing_files.append(filename)

    all_missing = ', '.join(missing_files)
    assert len(missing_files) == 0, (
        f'File(s) referenced in TOC not found: {all_missing}\nTOC:\n{toc}'
    )


def extract_toc(path):
    """Helper: Extract toc section from package rst file"""
    with open(path, encoding='utf-8') as f:
        rst = f.read()

    # Read out the part containing the toctree
    toctree_start = '\n.. toctree::\n'
    toctree_end = '\nSubmodules'

    start_idx = rst.index(toctree_start)
    end_idx = rst.index(toctree_end, start_idx)
    toctree = rst[start_idx + len(toctree_start) : end_idx]

    return toctree


@pytest.mark.apidoc(
    coderoot='test-ext-apidoc-subpackage-in-toc',
    options=['--separate'],
)
def test_subpackage_in_toc(apidoc):
    """Make sure that empty subpackages with non-empty subpackages in them
    are not skipped (issue #4520)
    """
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').is_file()

    assert (outdir / 'parent.rst').is_file()
    with open(outdir / 'parent.rst', encoding='utf-8') as f:
        parent = f.read()
    assert 'parent.child' in parent

    assert (outdir / 'parent.child.rst').is_file()
    with open(outdir / 'parent.child.rst', encoding='utf-8') as f:
        parent_child = f.read()
    assert 'parent.child.foo' in parent_child

    assert (outdir / 'parent.child.foo.rst').is_file()


def test_private(tmp_path):
    (tmp_path / 'hello.py').touch()
    (tmp_path / '_world.py').touch()

    # without --private option
    apidoc_main(['-o', str(tmp_path), str(tmp_path)])
    assert (tmp_path / 'hello.rst').exists()
    assert ':private-members:' not in (tmp_path / 'hello.rst').read_text(
        encoding='utf8'
    )
    assert not (tmp_path / '_world.rst').exists()

    # with --private option
    apidoc_main(['--private', '-f', '-o', str(tmp_path), str(tmp_path)])
    assert (tmp_path / 'hello.rst').exists()
    assert ':private-members:' in (tmp_path / 'hello.rst').read_text(encoding='utf8')
    assert (tmp_path / '_world.rst').exists()


def test_toc_file(tmp_path):
    outdir = tmp_path
    (outdir / 'module').mkdir(parents=True, exist_ok=True)
    (outdir / 'example.py').touch()
    (outdir / 'module' / 'example.py').touch()
    apidoc_main(['-o', str(tmp_path), str(tmp_path)])
    assert (outdir / 'modules.rst').exists()

    content = (outdir / 'modules.rst').read_text(encoding='utf8')
    assert content == (
        'test_toc_file0\n'
        '==============\n'
        '\n'
        '.. toctree::\n'
        '   :maxdepth: 4\n'
        '\n'
        '   example\n'
    )


def test_module_file(tmp_path):
    outdir = tmp_path
    (outdir / 'example.py').touch()
    apidoc_main(['-o', str(tmp_path), str(tmp_path)])
    assert (outdir / 'example.rst').exists()

    content = (outdir / 'example.rst').read_text(encoding='utf8')
    assert content == (
        'example module\n'
        '==============\n'
        '\n'
        '.. automodule:: example\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )


def test_module_file_noheadings(tmp_path):
    outdir = tmp_path
    (outdir / 'example.py').touch()
    apidoc_main(['--no-headings', '-o', str(tmp_path), str(tmp_path)])
    assert (outdir / 'example.rst').exists()

    content = (outdir / 'example.rst').read_text(encoding='utf8')
    assert content == (
        '.. automodule:: example\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )


def test_package_file(tmp_path):
    outdir = tmp_path
    (outdir / 'testpkg').mkdir(parents=True, exist_ok=True)
    (outdir / 'testpkg' / '__init__.py').touch()
    (outdir / 'testpkg' / 'hello.py').touch()
    (outdir / 'testpkg' / 'world.py').touch()
    (outdir / 'testpkg' / 'subpkg').mkdir(parents=True, exist_ok=True)
    (outdir / 'testpkg' / 'subpkg' / '__init__.py').touch()
    apidoc_main(['-o', str(outdir), str(outdir / 'testpkg')])
    assert (outdir / 'testpkg.rst').exists()
    assert (outdir / 'testpkg.subpkg.rst').exists()

    content = (outdir / 'testpkg.rst').read_text(encoding='utf8')
    assert content == (
        'testpkg package\n'
        '===============\n'
        '\n'
        'Subpackages\n'
        '-----------\n'
        '\n'
        '.. toctree::\n'
        '   :maxdepth: 4\n'
        '\n'
        '   testpkg.subpkg\n'
        '\n'
        'Submodules\n'
        '----------\n'
        '\n'
        'testpkg.hello module\n'
        '--------------------\n'
        '\n'
        '.. automodule:: testpkg.hello\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
        '\n'
        'testpkg.world module\n'
        '--------------------\n'
        '\n'
        '.. automodule:: testpkg.world\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
        '\n'
        'Module contents\n'
        '---------------\n'
        '\n'
        '.. automodule:: testpkg\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )

    content = (outdir / 'testpkg.subpkg.rst').read_text(encoding='utf8')
    assert content == (
        'testpkg.subpkg package\n'
        '======================\n'
        '\n'
        'Module contents\n'
        '---------------\n'
        '\n'
        '.. automodule:: testpkg.subpkg\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )


def test_package_file_separate(tmp_path):
    outdir = tmp_path
    (outdir / 'testpkg').mkdir(parents=True, exist_ok=True)
    (outdir / 'testpkg' / '__init__.py').touch()
    (outdir / 'testpkg' / 'example.py').touch()
    apidoc_main(['--separate', '-o', str(tmp_path), str(tmp_path / 'testpkg')])
    assert (outdir / 'testpkg.rst').exists()
    assert (outdir / 'testpkg.example.rst').exists()

    content = (outdir / 'testpkg.rst').read_text(encoding='utf8')
    assert content == (
        'testpkg package\n'
        '===============\n'
        '\n'
        'Submodules\n'
        '----------\n'
        '\n'
        '.. toctree::\n'
        '   :maxdepth: 4\n'
        '\n'
        '   testpkg.example\n'
        '\n'
        'Module contents\n'
        '---------------\n'
        '\n'
        '.. automodule:: testpkg\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )

    content = (outdir / 'testpkg.example.rst').read_text(encoding='utf8')
    assert content == (
        'testpkg.example module\n'
        '======================\n'
        '\n'
        '.. automodule:: testpkg.example\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )


def test_package_file_module_first(tmp_path):
    outdir = tmp_path
    (outdir / 'testpkg').mkdir(parents=True, exist_ok=True)
    (outdir / 'testpkg' / '__init__.py').touch()
    (outdir / 'testpkg' / 'example.py').touch()
    apidoc_main(['--module-first', '-o', str(tmp_path), str(tmp_path)])

    content = (outdir / 'testpkg.rst').read_text(encoding='utf8')
    assert content == (
        'testpkg package\n'
        '===============\n'
        '\n'
        '.. automodule:: testpkg\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
        '\n'
        'Submodules\n'
        '----------\n'
        '\n'
        'testpkg.example module\n'
        '----------------------\n'
        '\n'
        '.. automodule:: testpkg.example\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )


def test_package_file_without_submodules(tmp_path):
    outdir = tmp_path
    (outdir / 'testpkg').mkdir(parents=True, exist_ok=True)
    (outdir / 'testpkg' / '__init__.py').touch()
    apidoc_main(['-o', str(tmp_path), str(tmp_path / 'testpkg')])
    assert (outdir / 'testpkg.rst').exists()

    content = (outdir / 'testpkg.rst').read_text(encoding='utf8')
    assert content == (
        'testpkg package\n'
        '===============\n'
        '\n'
        'Module contents\n'
        '---------------\n'
        '\n'
        '.. automodule:: testpkg\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )


def test_namespace_package_file(tmp_path):
    outdir = tmp_path
    (outdir / 'testpkg').mkdir(parents=True, exist_ok=True)
    (outdir / 'testpkg' / 'example.py').touch()
    apidoc_main([
        '--implicit-namespace',
        '-o',
        str(tmp_path),
        str(tmp_path / 'testpkg'),
    ])
    assert (outdir / 'testpkg.rst').exists()

    content = (outdir / 'testpkg.rst').read_text(encoding='utf8')
    assert content == (
        'testpkg namespace\n'
        '=================\n'
        '\n'
        '.. py:module:: testpkg\n'
        '\n'
        'Submodules\n'
        '----------\n'
        '\n'
        'testpkg.example module\n'
        '----------------------\n'
        '\n'
        '.. automodule:: testpkg.example\n'
        '   :members:\n'
        '   :show-inheritance:\n'
        '   :undoc-members:\n'
    )


def test_no_duplicates(rootdir, tmp_path):
    """Make sure that a ".pyx" and ".so" don't cause duplicate listings.

    We can't use pytest.mark.apidoc here as we use a different set of arguments
    to apidoc_main
    """
    original_suffixes = sphinx.ext.apidoc._generate.PY_SUFFIXES
    try:
        # Ensure test works on Windows
        sphinx.ext.apidoc._generate.PY_SUFFIXES += ('.so',)

        package = rootdir / 'test-ext-apidoc-duplicates' / 'fish_licence'
        outdir = tmp_path / 'out'
        apidoc_main(['-o', str(outdir), '-T', str(package), '--implicit-namespaces'])

        # Ensure the module has been documented
        assert (outdir / 'fish_licence.rst').is_file()

        # Ensure the submodule only appears once
        text = (outdir / 'fish_licence.rst').read_text(encoding='utf-8')
        count_submodules = text.count(r'fish\_licence.halibut module')
        assert count_submodules == 1

    finally:
        sphinx.ext.apidoc._generate.PY_SUFFIXES = original_suffixes


def test_remove_old_files(tmp_path: Path):
    """Test that old files are removed when using the -r option.

    Also ensure that pre-existing files are not re-written, if unchanged.
    This is required to avoid unnecessary rebuilds.
    """
    module_dir = tmp_path / 'module'
    module_dir.mkdir()
    (module_dir / 'example.py').touch()
    gen_dir = tmp_path / 'gen'
    gen_dir.mkdir()
    (gen_dir / 'other.rst').touch()
    apidoc_main(['-o', str(gen_dir), str(module_dir)])
    assert set(gen_dir.iterdir()) == {
        gen_dir / 'modules.rst',
        gen_dir / 'example.rst',
        gen_dir / 'other.rst',
    }
    example_mtime = (gen_dir / 'example.rst').stat().st_mtime_ns
    apidoc_main(['--remove-old', '-o', str(gen_dir), str(module_dir)])
    assert set(gen_dir.iterdir()) == {gen_dir / 'modules.rst', gen_dir / 'example.rst'}
    assert (gen_dir / 'example.rst').stat().st_mtime_ns == example_mtime


@pytest.mark.sphinx(testroot='ext-apidoc')
def test_sphinx_extension(app: SphinxTestApp):
    """Test running apidoc as an extension."""
    app.build()
    assert app.warning.getvalue() == ''

    assert set((app.srcdir / 'generated').iterdir()) == {
        app.srcdir / 'generated' / 'modules.rst',
        app.srcdir / 'generated' / 'my_package.rst',
    }
    assert 'show-inheritance' not in (
        app.srcdir / 'generated' / 'my_package.rst'
    ).read_text(encoding='utf8')
    assert (app.outdir / 'generated' / 'my_package.html').is_file()

    # test a re-build
    app.build()
    assert app.warning.getvalue() == ''

    # TODO check nothing got re-built
    # TODO test that old files are removed
