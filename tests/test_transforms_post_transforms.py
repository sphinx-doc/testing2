"""Tests the post_transforms"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import SIG_ELEMENTS
from sphinx.testing.util import assert_node
from sphinx.transforms.post_transforms import SigElementFallbackTransform
from sphinx.util.docutils import new_document

if TYPE_CHECKING:
    from typing import Any, NoReturn  # noqa: F401

    from _pytest.fixtures import SubRequest  # noqa: F401

    from sphinx.testing.util import SphinxTestApp  # noqa: F401


@pytest.mark.sphinx('html', testroot='transforms-post_transforms-missing-reference')
def test_nitpicky_warning(app, status, warning):
    app.build()
    assert ('index.rst:4: WARNING: py:class reference target '
            'not found: io.StringIO' in warning.getvalue())

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<p><code class="xref py py-class docutils literal notranslate"><span class="pre">'
            'io.StringIO</span></code></p>' in content)


@pytest.mark.sphinx('html', testroot='transforms-post_transforms-missing-reference',
                    freshenv=True)
def test_missing_reference(app, status, warning):
    def missing_reference(app, env, node, contnode):
        assert app is app
        assert env is app.env
        assert node['reftarget'] == 'io.StringIO'
        assert contnode.astext() == 'io.StringIO'

        return nodes.inline('', 'missing-reference.StringIO')

    warning.truncate(0)
    app.connect('missing-reference', missing_reference)
    app.build()
    assert warning.getvalue() == ''

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p><span>missing-reference.StringIO</span></p>' in content


@pytest.mark.sphinx('html', testroot='domain-py-python_use_unqualified_type_names',
                    freshenv=True)
def test_missing_reference_conditional_pending_xref(app, status, warning):
    def missing_reference(app, env, node, contnode):
        return contnode

    warning.truncate(0)
    app.connect('missing-reference', missing_reference)
    app.build()
    assert warning.getvalue() == ''

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<span class="n"><span class="pre">Age</span></span>' in content


@pytest.mark.sphinx('html', testroot='transforms-post_transforms-keyboard',
                    freshenv=True)
def test_keyboard_hyphen_spaces(app):
    """Regression test for issue 10495, we want no crash."""
    app.build()
    assert "spanish" in (app.outdir / 'index.html').read_text(encoding='utf8')
    assert "inquisition" in (app.outdir / 'index.html').read_text(encoding='utf8')


class TestSigElementFallbackTransform:
    """Integration test for :class:`sphinx.transforms.post_transforms.SigElementFallbackTransform`."""
    # safe copy of the "built-in" desc_sig_* nodes
    _builtin_sig_elements: list[type[addnodes.desc_sig_element]] = SIG_ELEMENTS[:]

    @pytest.fixture(autouse=True)
    def builtin_sig_elements(self):
        # type: () -> list[type[addnodes.desc_sig_element]]
        """Fixture returning the original value of :data:`!sphinx.addnodes.SIG_ELEMENTS`."""
        return self._builtin_sig_elements[:]

    @pytest.fixture()
    def document(self, app, builtin_sig_elements):
        # type: (SphinxTestApp, list[type[addnodes.desc_sig_element]]) -> nodes.document
        """Fixture returning a new document with built-in ``desc_sig_*`` nodes and a final ``desc_inline`` node."""
        doc = new_document('')
        doc.settings.env = app.env
        # nodes that should be supported by a default custom translator class
        doc += [node_type('', '') for node_type in builtin_sig_elements]
        doc += addnodes.desc_inline('py')
        return doc

    @pytest.fixture()
    def with_desc_sig_elements(self, value):
        # type: (Any) -> bool
        """Dynamic fixture acting as the identity on booleans."""
        assert isinstance(value, bool)
        return value

    @pytest.fixture()
    def add_visitor_method_for(self, value):
        # type: (Any) -> list[str]
        """Dynamic fixture acting as the identity on list of strings."""
        assert isinstance(value, list)
        assert all(isinstance(item, str) for item in value)
        return value

    @pytest.fixture(autouse=True)
    def translator_class(self, request):
        # type: (SubRequest) -> type[nodes.NodeVisitor]
        """Minimal interface fixture similar to SphinxTranslator but orthogonal thereof."""
        logger = logging.getLogger(__name__)

        class BaseCustomTranslatorClass(nodes.NodeVisitor):
            """Base class for a custom translator class, orthogonal to ``SphinxTranslator``."""

            def __init__(self, document, *args):
                super().__init__(document)
                # ignore other arguments

            def dispatch_visit(self, node):
                for node_class in node.__class__.__mro__:
                    method = getattr(self, 'visit_%s' % node_class.__name__, None)
                    if method:
                        method(node)
                        break
                else:
                    logger.info('generic visit: %r', node.__class__.__name__)
                    super().dispatch_visit(node)

            def unknown_visit(self, node):
                logger.warning('unknown visit: %r', node.__class__.__name__)
                raise nodes.SkipDeparture  # ignore unknown departure

            def visit_document(self, node):
                raise nodes.SkipDeparture  # ignore departure

            @staticmethod
            def mark_node(self, node):
                # type: (BaseCustomTranslatorClass, nodes.Node) -> NoReturn
                logger.info('mark: %r', node.__class__.__name__)
                raise nodes.SkipDeparture  # ignore departure

        with_desc_sig_elements = request.getfixturevalue('with_desc_sig_elements')
        desc_sig_elements_list = request.getfixturevalue('builtin_sig_elements') if with_desc_sig_elements else []
        add_visitor_method_for = request.getfixturevalue('add_visitor_method_for')
        visitormethods = [f'visit_{tp.__name__}' for tp in desc_sig_elements_list]
        visitormethods.extend(f'visit_{name}' for name in add_visitor_method_for)
        class_dict = dict.fromkeys(visitormethods, BaseCustomTranslatorClass.mark_node)
        return type('CustomTranslatorClass', (BaseCustomTranslatorClass,), class_dict)

    @pytest.mark.parametrize('add_visitor_method_for',
                             [[], ['desc_inline']],
                             ids=[
                                 'no_explicit_visitor',
                                 'explicit_desc_inline_visitor',
                             ])
    @pytest.mark.parametrize('with_desc_sig_elements',
                             [True, False],
                             ids=[
                                 'with_default_visitors_for_desc_sig_elements',
                                 'without_default_visitors_for_desc_sig_elements',
                             ])
    @pytest.mark.sphinx('dummy')
    def test_support_desc_inline(self, app, document, with_desc_sig_elements, add_visitor_method_for, request):
        # type: (SphinxTestApp, nodes.document, bool, list[str], SubRequest) -> None
        document, _, _ = self._exec(request)
        # count the number of desc_inline nodes with the extra _sig_node_type field
        desc_inline_typename = addnodes.desc_inline.__name__
        visit_desc_inline = desc_inline_typename in add_visitor_method_for
        if visit_desc_inline:
            assert_node(document[-1], addnodes.desc_inline)
        else:
            assert_node(document[-1], nodes.inline, _sig_node_type=desc_inline_typename)

    @pytest.mark.parametrize('add_visitor_method_for',
                             [
                                 [],  # no support
                                 ['desc_sig_space'],  # enable desc_sig_space visitor
                                 ['desc_sig_element'],  # enable generic visitor
                                 ['desc_sig_space', 'desc_sig_element'],  # enable desc_sig_space and generic visitors
                             ],
                             ids=[
                                 'no_explicit_visitor',
                                 'explicit_desc_sig_space_visitor',
                                 'explicit_desc_sig_element_visitor',
                                 'explicit_desc_sig_space_and_desc_sig_element_visitors',
                             ])
    @pytest.mark.parametrize('with_desc_sig_elements',
                             [True, False],
                             ids=[
                                 'with_default_visitors_for_desc_sig_elements',
                                 'without_default_visitors_for_desc_sig_elements',
                             ])
    @pytest.mark.sphinx('dummy')
    def test_custom_implementation(self, app, document, with_desc_sig_elements, add_visitor_method_for, request):
        # type: (SphinxTestApp, nodes.document, bool, list[str], SubRequest) -> None
        document, stdout, stderr = self._exec(request)
        assert len(self._builtin_sig_elements) == len(document.children[:-1]) == len(stdout[:-1])

        visit_desc_sig_element = addnodes.desc_sig_element.__name__ in add_visitor_method_for
        ignore_sig_element_fallback_transform = visit_desc_sig_element or with_desc_sig_elements

        if ignore_sig_element_fallback_transform:
            # desc_sig_element is implemented or desc_sig_* nodes are properly handled (and left untouched)
            for node_type, node, mess in zip(self._builtin_sig_elements, document.children[:-1], stdout[:-1]):
                assert_node(node, node_type)
                assert not node.hasattr('_sig_node_type')
                assert mess == f'mark: {node_type.__name__!r}'
        else:
            # desc_sig_* nodes are converted into inline nodes
            for node_type, node, mess in zip(self._builtin_sig_elements, document.children[:-1], stdout[:-1]):
                assert_node(node, nodes.inline, _sig_node_type=node_type.__name__)
                assert mess == f'generic visit: {nodes.inline.__name__!r}'

        # desc_inline node is never handled and always transformed
        assert addnodes.desc_inline.__name__ not in add_visitor_method_for
        assert_node(document[-1], nodes.inline, _sig_node_type=addnodes.desc_inline.__name__)
        assert stdout[-1] == f'generic visit: {nodes.inline.__name__!r}'

        # nodes.inline are never handled
        assert len(stderr) == 1 if ignore_sig_element_fallback_transform else len(document.children)
        assert set(stderr) == {f'unknown visit: {nodes.inline.__name__!r}'}

    def _exec(self, request):
        # type: (SubRequest) -> tuple[nodes.document, list[str], list[str]]
        caplog = request.getfixturevalue('caplog')
        caplog.set_level(logging.INFO, logger=__name__)

        app = request.getfixturevalue('app')
        translator_class = request.getfixturevalue('translator_class')
        app.set_translator('dummy', translator_class)
        # run the post-transform directly [building phase]
        # document contains SIG_ELEMENTS nodes followed by a desc_inline node
        document = request.getfixturevalue('document')
        SigElementFallbackTransform(document).run()
        # run the translator [writing phase]
        translator = translator_class(document, app.builder)
        document.walkabout(translator)
        # extract messages
        messages = caplog.record_tuples
        stdout = [message for _, lvl, message in messages if lvl == logging.INFO]
        stderr = [message for _, lvl, message in messages if lvl == logging.WARN]
        return document, stdout, stderr
