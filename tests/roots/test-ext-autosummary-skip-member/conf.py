import os
import sys

sys.path.insert(0, os.path.abspath('.'))


extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autodoc_default_options = {'members': True}


def skip_member(app, what, name, obj, member_of, skip, options):
    if name == 'skipmeth':
        return True
    elif name == '_privatemeth':
        return False


def setup(app):
    app.connect('autodoc-skip-member', skip_member)
