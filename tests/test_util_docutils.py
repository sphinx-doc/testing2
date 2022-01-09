"""
    test_util_docutils
    ~~~~~~~~~~~~~~~~~~

    Tests util.utils functions.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

from docutils import nodes

from sphinx.util.docutils import (
    SphinxFileOutput,
    SphinxTranslator,
    docutils_namespace,
    new_document,
    register_node,
)


def test_register_node():
    class custom_node(nodes.Element):
        pass

    with docutils_namespace():
        register_node(custom_node)

        # check registered
        assert hasattr(nodes.GenericNodeVisitor, 'visit_custom_node')
        assert hasattr(nodes.GenericNodeVisitor, 'depart_custom_node')
        assert hasattr(nodes.SparseNodeVisitor, 'visit_custom_node')
        assert hasattr(nodes.SparseNodeVisitor, 'depart_custom_node')

    # check unregistered outside namespace
    assert not hasattr(nodes.GenericNodeVisitor, 'visit_custom_node')
    assert not hasattr(nodes.GenericNodeVisitor, 'depart_custom_node')
    assert not hasattr(nodes.SparseNodeVisitor, 'visit_custom_node')
    assert not hasattr(nodes.SparseNodeVisitor, 'depart_custom_node')


def test_SphinxFileOutput(tmpdir):
    content = 'Hello Sphinx World'

    # write test.txt at first
    filename = str(tmpdir / 'test.txt')
    output = SphinxFileOutput(destination_path=filename)
    output.write(content)
    os.utime(filename, (0, 0))

    # overwrite it again
    output.write(content)
    assert os.stat(filename).st_mtime != 0  # updated

    # write test2.txt at first
    filename = str(tmpdir / 'test2.txt')
    output = SphinxFileOutput(destination_path=filename, overwrite_if_changed=True)
    output.write(content)
    os.utime(filename, (0, 0))

    # overwrite it again
    output.write(content)
    assert os.stat(filename).st_mtime == 0  # not updated

    # overwrite it again (content changed)
    output.write(content + "; content change")
    assert os.stat(filename).st_mtime != 0  # updated


def test_SphinxTranslator(app):
    class CustomNode(nodes.inline):
        pass

    class MyTranslator(SphinxTranslator):
        def __init__(self, *args):
            self.called = []
            super().__init__(*args)

        def visit_document(self, node):
            pass

        def depart_document(self, node):
            pass

        def visit_inline(self, node):
            self.called.append('visit_inline')

        def depart_inline(self, node):
            self.called.append('depart_inline')

    document = new_document('')
    document += CustomNode()

    translator = MyTranslator(document, app.builder)
    document.walkabout(translator)

    # MyTranslator does not have visit_CustomNode. But it calls visit_inline instead.
    assert translator.called == ['visit_inline', 'depart_inline']
