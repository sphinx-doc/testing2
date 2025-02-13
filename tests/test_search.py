"""Test the search index builder."""

from __future__ import annotations

import json
import warnings
from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from docutils import frontend, utils
from docutils.parsers import rst

from sphinx.search import IndexBuilder

from tests.utils import TESTS_ROOT

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path
    from typing import Any

    from sphinx.domains import ObjType

JAVASCRIPT_TEST_ROOTS = [
    directory
    for directory in (TESTS_ROOT / 'js' / 'roots').iterdir()
    if (directory / 'conf.py').exists()
]


class DummyDomainsContainer:
    def __init__(self, **domains: DummyDomain) -> None:
        self._domain_instances = domains

    def sorted(self) -> Iterator[DummyDomain]:
        for _domain_name, domain in sorted(self._domain_instances.items()):
            yield domain


class DummyEnvironment:
    def __init__(self, version: str, domains: DummyDomainsContainer) -> None:
        self.version = version
        self.domains = domains

    def __getattr__(self, name: str):
        if name.startswith('_search_index_'):
            setattr(self, name, {})
        return getattr(self, name, {})

    def __str__(self) -> str:
        return f'DummyEnvironment({self.version!r}, {self.domains!r})'


class DummyDomain:
    def __init__(
        self, name: str, data: Iterable[tuple[str, str, str, str, str, int]]
    ) -> None:
        self.name = name
        self.data = data
        self.object_types: dict[str, ObjType] = {}

    def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
        return self.data


def load_searchindex(path: Path) -> Any:
    searchindex = path.read_text(encoding='utf8')
    assert searchindex.startswith('Search.setIndex(')
    assert searchindex.endswith(')')

    return json.loads(searchindex[16:-1])


def is_registered_term(index: Any, keyword: str) -> bool:
    return index['terms'].get(keyword, []) != []


FILE_CONTENTS = """\
section_title
=============

.. test that comments are not indexed: boson

another_title
=============

test that non-comments are indexed: fermion
"""


@pytest.mark.sphinx('html', testroot='ext-viewcode')
def test_objects_are_escaped(app):
    app.build(force_all=True)
    index = load_searchindex(app.outdir / 'searchindex.js')
    for item in index.get('objects').get(''):
        if item[-1] == 'n::Array&lt;T, d&gt;':  # n::Array<T,d> is escaped
            break
    else:
        raise AssertionError(index.get('objects').get(''))


@pytest.mark.sphinx('html', testroot='search')
def test_meta_keys_are_handled_for_language_en(app):
    app.build(force_all=True)
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
    assert not is_registered_term(searchindex, 'thisnoteith')
    assert is_registered_term(searchindex, 'thisonetoo')
    assert is_registered_term(searchindex, 'findthiskei')
    assert is_registered_term(searchindex, 'thistoo')
    assert not is_registered_term(searchindex, 'onlygerman')
    assert is_registered_term(searchindex, 'notgerman')
    assert not is_registered_term(searchindex, 'onlytoogerman')


@pytest.mark.sphinx(
    'html',
    testroot='search',
    confoverrides={'html_search_language': 'de'},
    freshenv=True,
)
def test_meta_keys_are_handled_for_language_de(app):
    app.build(force_all=True)
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
    assert not is_registered_term(searchindex, 'thisnoteith')
    assert is_registered_term(searchindex, 'thisonetoo')
    assert not is_registered_term(searchindex, 'findthiskei')
    assert not is_registered_term(searchindex, 'thistoo')
    assert is_registered_term(searchindex, 'onlygerman')
    assert not is_registered_term(searchindex, 'notgerman')
    assert is_registered_term(searchindex, 'onlytoogerman')


@pytest.mark.sphinx('html', testroot='search')
def test_stemmer_does_not_remove_short_words(app):
    app.build(force_all=True)
    searchindex = (app.outdir / 'searchindex.js').read_text(encoding='utf8')
    assert 'bat' in searchindex


@pytest.mark.sphinx('html', testroot='search')
def test_stemmer(app):
    app.build(force_all=True)
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
    print(searchindex)
    assert is_registered_term(searchindex, 'findthisstemmedkei')
    assert is_registered_term(searchindex, 'intern')


@pytest.mark.sphinx('html', testroot='search')
def test_term_in_heading_and_section(app):
    app.build(force_all=True)
    searchindex = (app.outdir / 'searchindex.js').read_text(encoding='utf8')
    # if search term is in the title of one doc and in the text of another
    # both documents should be a hit in the search index as a title,
    # respectively text hit
    assert '"textinhead":2' in searchindex
    assert '"textinhead":0' in searchindex


@pytest.mark.sphinx('html', testroot='search')
def test_term_in_raw_directive(app):
    app.build(force_all=True)
    searchindex = load_searchindex(app.outdir / 'searchindex.js')
    assert not is_registered_term(searchindex, 'raw')
    assert is_registered_term(searchindex, 'rawword')
    assert not is_registered_term(searchindex, 'latex_keyword')


def test_IndexBuilder():
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        # DeprecationWarning: The frontend.OptionParser class will be replaced
        # by a subclass of argparse.ArgumentParser in Docutils 0.21 or later.
        optparser = frontend.OptionParser(components=(rst.Parser,))
    settings = optparser.get_default_values()
    parser = rst.Parser()

    domain1 = DummyDomain(
        'dummy1',
        [
            ('objname1', 'objdispname1', 'objtype1', 'docname1_1', '#anchor', 1),
            ('objname2', 'objdispname2', 'objtype2', 'docname1_2', '', -1),
        ],
    )
    domain2 = DummyDomain(
        'dummy2',
        [
            ('objname1', 'objdispname1', 'objtype1', 'docname2_1', '#anchor', 1),
            ('objname2', 'objdispname2', 'objtype2', 'docname2_2', '', -1),
        ],
    )
    env = DummyEnvironment('1.0', DummyDomainsContainer(dummy1=domain1, dummy2=domain2))
    doc = utils.new_document('test data', settings)
    doc['file'] = 'dummy'
    parser.parse(FILE_CONTENTS, doc)

    # feed
    index = IndexBuilder(env, 'en', {}, '')
    index.feed('docname1_1', 'filename1_1', 'title1_1', doc)
    index.feed('docname1_2', 'filename1_2', 'title1_2', doc)
    index.feed('docname2_2', 'filename2_2', 'title2_2', doc)
    index.feed('docname2_1', 'filename2_1', 'title2_1', doc)
    assert index._titles == {
        'docname1_1': 'title1_1',
        'docname1_2': 'title1_2',
        'docname2_1': 'title2_1',
        'docname2_2': 'title2_2',
    }
    assert index._filenames == {
        'docname1_1': 'filename1_1',
        'docname1_2': 'filename1_2',
        'docname2_1': 'filename2_1',
        'docname2_2': 'filename2_2',
    }
    # note: element iteration order (sort order) is important when the index
    # is frozen (serialized) during build -- however, the _mapping-related
    # dictionaries below may be iterated in arbitrary order by Python at
    # runtime.
    assert index._mapping == {
        'ar': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'fermion': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'comment': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'non': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'index': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'test': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
    }
    assert index._title_mapping == {
        'another_titl': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
        'section_titl': {'docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'},
    }
    assert index._objtypes == {}
    assert index._objnames == {}

    # freeze
    assert index.freeze() == {
        'docnames': ('docname1_1', 'docname1_2', 'docname2_1', 'docname2_2'),
        'envversion': '1.0',
        'filenames': ['filename1_1', 'filename1_2', 'filename2_1', 'filename2_2'],
        'objects': {
            '': [
                (0, 0, 1, '#anchor', 'objdispname1'),
                (2, 1, 1, '#anchor', 'objdispname1'),
            ]
        },
        'objnames': {
            0: ('dummy1', 'objtype1', 'objtype1'),
            1: ('dummy2', 'objtype1', 'objtype1'),
        },
        'objtypes': {0: 'dummy1:objtype1', 1: 'dummy2:objtype1'},
        'terms': {
            'ar': [0, 1, 2, 3],
            'comment': [0, 1, 2, 3],
            'fermion': [0, 1, 2, 3],
            'index': [0, 1, 2, 3],
            'non': [0, 1, 2, 3],
            'test': [0, 1, 2, 3],
        },
        'titles': ('title1_1', 'title1_2', 'title2_1', 'title2_2'),
        'titleterms': {
            'another_titl': [0, 1, 2, 3],
            'section_titl': [0, 1, 2, 3],
        },
        'alltitles': {
            'another_title': [
                (0, 'another-title'),
                (1, 'another-title'),
                (2, 'another-title'),
                (3, 'another-title'),
            ],
            'section_title': [(0, None), (1, None), (2, None), (3, None)],
        },
        'indexentries': {},
    }
    assert index._objtypes == {('dummy1', 'objtype1'): 0, ('dummy2', 'objtype1'): 1}
    assert index._objnames == {
        0: ('dummy1', 'objtype1', 'objtype1'),
        1: ('dummy2', 'objtype1', 'objtype1'),
    }

    env = DummyEnvironment('1.0', DummyDomainsContainer(dummy1=domain1, dummy2=domain2))

    # dump / load
    stream = BytesIO()
    index.dump(stream, 'pickle')
    stream.seek(0)

    index2 = IndexBuilder(env, 'en', {}, '')
    index2.load(stream, 'pickle')

    assert index2._titles == index._titles
    assert index2._filenames == index._filenames
    assert index2._mapping == index._mapping
    assert index2._title_mapping == index._title_mapping
    assert index2._objtypes == {}
    assert index2._objnames == {}

    # freeze after load
    assert index2.freeze() == index.freeze()
    assert index2._objtypes == index._objtypes
    assert index2._objnames == index._objnames

    # prune
    index.prune(['docname1_2', 'docname2_2'])
    assert index._titles == {'docname1_2': 'title1_2', 'docname2_2': 'title2_2'}
    assert index._filenames == {
        'docname1_2': 'filename1_2',
        'docname2_2': 'filename2_2',
    }
    assert index._mapping == {
        'ar': {'docname1_2', 'docname2_2'},
        'fermion': {'docname1_2', 'docname2_2'},
        'comment': {'docname1_2', 'docname2_2'},
        'non': {'docname1_2', 'docname2_2'},
        'index': {'docname1_2', 'docname2_2'},
        'test': {'docname1_2', 'docname2_2'},
    }
    assert index._title_mapping == {
        'another_titl': {'docname1_2', 'docname2_2'},
        'section_titl': {'docname1_2', 'docname2_2'},
    }
    assert index._objtypes == {('dummy1', 'objtype1'): 0, ('dummy2', 'objtype1'): 1}
    assert index._objnames == {
        0: ('dummy1', 'objtype1', 'objtype1'),
        1: ('dummy2', 'objtype1', 'objtype1'),
    }

    # freeze after prune
    assert index.freeze() == {
        'docnames': ('docname1_2', 'docname2_2'),
        'envversion': '1.0',
        'filenames': ['filename1_2', 'filename2_2'],
        'objects': {},
        'objnames': {
            0: ('dummy1', 'objtype1', 'objtype1'),
            1: ('dummy2', 'objtype1', 'objtype1'),
        },
        'objtypes': {0: 'dummy1:objtype1', 1: 'dummy2:objtype1'},
        'terms': {
            'ar': [0, 1],
            'comment': [0, 1],
            'fermion': [0, 1],
            'index': [0, 1],
            'non': [0, 1],
            'test': [0, 1],
        },
        'titles': ('title1_2', 'title2_2'),
        'titleterms': {
            'another_titl': [0, 1],
            'section_titl': [0, 1],
        },
        'alltitles': {
            'another_title': [(0, 'another-title'), (1, 'another-title')],
            'section_title': [(0, None), (1, None)],
        },
        'indexentries': {},
    }
    assert index._objtypes == {('dummy1', 'objtype1'): 0, ('dummy2', 'objtype1'): 1}
    assert index._objnames == {
        0: ('dummy1', 'objtype1', 'objtype1'),
        1: ('dummy2', 'objtype1', 'objtype1'),
    }


def test_IndexBuilder_lookup():
    env = DummyEnvironment('1.0', {})

    # zh
    index = IndexBuilder(env, 'zh', {}, '')
    assert index.lang.lang == 'zh'

    # zh_CN
    index = IndexBuilder(env, 'zh_CN', {}, '')
    assert index.lang.lang == 'zh'


@pytest.mark.sphinx(
    'html',
    testroot='search',
    confoverrides={'html_search_language': 'zh'},
    srcdir='search_zh',
)
def test_search_index_gen_zh(app):
    app.build(force_all=True)
    index = load_searchindex(app.outdir / 'searchindex.js')
    assert 'chinesetest ' not in index['terms']
    assert 'chinesetest' in index['terms']
    assert 'chinesetesttwo' in index['terms']
    assert 'cas' in index['terms']


@pytest.mark.sphinx(
    'html',
    testroot='search',
    freshenv=True,
)
def test_nosearch(app):
    app.build()
    index = load_searchindex(app.outdir / 'searchindex.js')
    assert index['docnames'] == ['index', 'nosearch', 'tocitem']
    # latex is in 'nosearch.rst', and nowhere else
    assert 'latex' not in index['terms']
    # cat is in 'index.rst' but is marked with the 'no-search' class
    assert 'cat' not in index['terms']
    # bat is indexed from 'index.rst' and 'tocitem.rst' (document IDs 0, 2), and
    # not from 'nosearch.rst' (document ID 1)
    assert 'bat' in index['terms']
    assert index['terms']['bat'] == [0, 2]


@pytest.mark.sphinx(
    'html',
    testroot='search',
    parallel=3,
    freshenv=True,
)
def test_parallel(app):
    app.build()
    index = load_searchindex(app.outdir / 'searchindex.js')
    assert index['docnames'] == ['index', 'nosearch', 'tocitem']


@pytest.mark.sphinx('html', testroot='search')
def test_search_index_is_deterministic(app):
    app.build(force_all=True)
    index = load_searchindex(app.outdir / 'searchindex.js')
    # Pretty print the index. Only shown by pytest on failure.
    print(f'searchindex.js contents:\n\n{json.dumps(index, indent=2)}')
    assert_is_sorted(index, '')


def is_title_tuple_type(item: list[int | str]) -> bool:
    """In the search index, titles inside .alltitles are stored as a tuple of
    (document_idx, title_anchor). Tuples are represented as lists in JSON,
    but their contents must not be sorted. We cannot sort them anyway, as
    document_idx is an int and title_anchor is a str.
    """
    return len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], str)


def assert_is_sorted(
    item: dict[str, str] | list[int | str] | int | str, path: str
) -> None:
    lists_not_to_sort = {
        # Each element of .titles is related to the element of .docnames in the same position.
        # The ordering is deterministic because .docnames is sorted.
        '.titles',
        # Each element of .filenames is related to the element of .docnames in the same position.
        # The ordering is deterministic because .docnames is sorted.
        '.filenames',
    }

    err_path = path or '<root>'
    if isinstance(item, dict):
        assert list(item.keys()) == sorted(item.keys()), f'{err_path} is not sorted'
        for key, value in item.items():
            assert_is_sorted(value, f'{path}.{key}')
    elif isinstance(item, list):
        if not is_title_tuple_type(item) and path not in lists_not_to_sort:
            # sort nulls last; http://stackoverflow.com/questions/19868767/
            assert item == sorted(item, key=lambda x: (x is None, x)), (
                f'{err_path} is not sorted'
            )
        for i, child in enumerate(item):
            assert_is_sorted(child, f'{path}[{i}]')


@pytest.mark.parametrize('directory', JAVASCRIPT_TEST_ROOTS)
def test_check_js_search_indexes(make_app, sphinx_test_tempdir, directory):
    app = make_app(
        'html',
        srcdir=directory,
        builddir=sphinx_test_tempdir / directory.name,
    )
    app.build()

    fresh_searchindex = app.outdir / 'searchindex.js'
    existing_searchindex = (
        TESTS_ROOT / 'js' / 'fixtures' / directory.name / 'searchindex.js'
    )

    msg = (
        f'Search index fixture {existing_searchindex} does not match regenerated copy.'
    )
    assert fresh_searchindex.read_bytes() == existing_searchindex.read_bytes(), msg
