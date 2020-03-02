"""
    sphinx.ext.autosummary.generate
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Usable as a library or script to generate automatic RST source files for
    items referred to in autosummary:: directives.

    Each generated RST file contains a single auto*:: directive which
    extracts the docstring of the referred item.

    Example Makefile rule::

       generate:
               sphinx-autogen -o source/generated source/*.rst

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import argparse
import locale
import os
import pydoc
import re
import sys
import warnings
from typing import Any, Callable, Dict, List, Set, Tuple

from jinja2 import BaseLoader, FileSystemLoader, TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment

import sphinx.locale
from sphinx import __display_version__
from sphinx import package_dir
from sphinx.builders import Builder
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.ext.autodoc import Documenter
from sphinx.ext.autosummary import import_by_name, get_documenter
from sphinx.jinja2glue import BuiltinTemplateLoader
from sphinx.locale import __
from sphinx.registry import SphinxComponentRegistry
from sphinx.util import logging
from sphinx.util import rst
from sphinx.util.inspect import safe_getattr
from sphinx.util.osutil import ensuredir

if False:
    # For type annotation
    from typing import Type  # for python3.5.1


logger = logging.getLogger(__name__)


class DummyApplication:
    """Dummy Application class for sphinx-autogen command."""

    def __init__(self) -> None:
        self.registry = SphinxComponentRegistry()
        self.messagelog = []  # type: List[str]
        self.verbosity = 0
        self._warncount = 0
        self.warningiserror = False

    def emit_firstresult(self, *args: Any) -> None:
        pass


def setup_documenters(app: Any) -> None:
    from sphinx.ext.autodoc import (
        ModuleDocumenter, ClassDocumenter, ExceptionDocumenter, DataDocumenter,
        FunctionDocumenter, MethodDocumenter, AttributeDocumenter,
        InstanceAttributeDocumenter, DecoratorDocumenter, PropertyDocumenter,
        SlotsAttributeDocumenter, DataDeclarationDocumenter,
    )
    documenters = [
        ModuleDocumenter, ClassDocumenter, ExceptionDocumenter, DataDocumenter,
        FunctionDocumenter, MethodDocumenter, AttributeDocumenter,
        InstanceAttributeDocumenter, DecoratorDocumenter, PropertyDocumenter,
        SlotsAttributeDocumenter, DataDeclarationDocumenter,
    ]  # type: List[Type[Documenter]]
    for documenter in documenters:
        app.registry.add_documenter(documenter.objtype, documenter)


def _simple_info(msg: str) -> None:
    print(msg)


def _simple_warn(msg: str) -> None:
    print('WARNING: ' + msg, file=sys.stderr)


def _underline(title: str, line: str = '=') -> str:
    if '\n' in title:
        raise ValueError('Can only underline single lines')
    return title + '\n' + line * len(title)


class AutosummaryRenderer:
    """A helper class for rendering."""

    def __init__(self, builder: Builder, template_dir: str) -> None:
        loader = None  # type: BaseLoader
        template_dirs = [os.path.join(package_dir, 'ext', 'autosummary', 'templates')]
        if builder is None:
            if template_dir:
                template_dirs.insert(0, template_dir)
            loader = FileSystemLoader(template_dirs)
        else:
            # allow the user to override the templates
            loader = BuiltinTemplateLoader()
            loader.init(builder, dirs=template_dirs)

        self.env = SandboxedEnvironment(loader=loader)
        self.env.filters['escape'] = rst.escape
        self.env.filters['e'] = rst.escape
        self.env.filters['underline'] = _underline

    def exists(self, template_name: str) -> bool:
        """Check if template file exists."""
        try:
            self.env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False

    def render(self, template_name: str, context: Dict) -> str:
        """Render a template file."""
        return self.env.get_template(template_name).render(context)


# -- Generating output ---------------------------------------------------------


def generate_autosummary_content(name: str, obj: Any, parent: Any,
                                 template: AutosummaryRenderer, template_name: str,
                                 imported_members: bool, app: Any) -> str:
    doc = get_documenter(app, obj, parent)

    if template_name is None:
        template_name = 'autosummary/%s.rst' % doc.objtype
        if not template.exists(template_name):
            template_name = 'autosummary/base.rst'

    def skip_member(obj: Any, name: str, objtype: str, member_of: Any) -> bool:
        try:
            return app.emit_firstresult('autodoc-skip-member', objtype, name,
                                        obj, member_of, False, {})
        except Exception as exc:
            logger.warning(__('autosummary: failed to determine %r to be documented.'
                              'the following exception was raised:\n%s'),
                           name, exc, type='autosummary')
            return False

    def get_members(obj: Any, types: Set[str], include_public: List[str] = [],
                    imported: bool = True) -> Tuple[List[str], List[str]]:
        items = []  # type: List[str]
        public = []  # type: List[str]
        for name in dir(obj):
            try:
                value = safe_getattr(obj, name)
            except AttributeError:
                continue
            documenter = get_documenter(app, value, obj)
            if documenter.objtype in types:
                # skip imported members if expected
                if imported or getattr(value, '__module__', None) == obj.__name__:
                    skipped = skip_member(value, name, documenter.objtype, obj)
                    if skipped is True:
                        pass
                    elif skipped is False:
                        # show the member forcedly
                        items.append(name)
                        public.append(name)
                    else:
                        items.append(name)
                        if name in include_public or not name.startswith('_'):
                            # considers member as public
                            public.append(name)
        return public, items

    ns = {}  # type: Dict[str, Any]

    if doc.objtype == 'module':
        ns['members'] = dir(obj)
        ns['functions'], ns['all_functions'] = \
            get_members(obj, {'function'}, imported=imported_members)
        ns['classes'], ns['all_classes'] = \
            get_members(obj, {'class'}, imported=imported_members)
        ns['exceptions'], ns['all_exceptions'] = \
            get_members(obj, {'exception'}, imported=imported_members)
    elif doc.objtype == 'class':
        ns['members'] = dir(obj)
        ns['inherited_members'] = \
            set(dir(obj)) - set(obj.__dict__.keys())
        ns['methods'], ns['all_methods'] = \
            get_members(obj, {'method'}, ['__init__'])
        ns['attributes'], ns['all_attributes'] = \
            get_members(obj, {'attribute', 'property'})

    parts = name.split('.')
    if doc.objtype in ('method', 'attribute', 'property'):
        mod_name = '.'.join(parts[:-2])
        cls_name = parts[-2]
        obj_name = '.'.join(parts[-2:])
        ns['class'] = cls_name
    else:
        mod_name, obj_name = '.'.join(parts[:-1]), parts[-1]

    ns['fullname'] = name
    ns['module'] = mod_name
    ns['objname'] = obj_name
    ns['name'] = parts[-1]

    ns['objtype'] = doc.objtype
    ns['underline'] = len(name) * '='

    return template.render(template_name, ns)


def generate_autosummary_docs(sources: List[str], output_dir: str = None,
                              suffix: str = '.rst', warn: Callable = None,
                              info: Callable = None, base_path: str = None,
                              builder: Builder = None, template_dir: str = None,
                              imported_members: bool = False, app: Any = None,
                              overwrite: bool = True) -> None:
    if info:
        warnings.warn('info argument for generate_autosummary_docs() is deprecated.',
                      RemovedInSphinx40Warning)
        _info = info
    else:
        _info = logger.info

    if warn:
        warnings.warn('warn argument for generate_autosummary_docs() is deprecated.',
                      RemovedInSphinx40Warning)
        _warn = warn
    else:
        _warn = logger.warning

    showed_sources = list(sorted(sources))
    if len(showed_sources) > 20:
        showed_sources = showed_sources[:10] + ['...'] + showed_sources[-10:]
    _info(__('[autosummary] generating autosummary for: %s') %
          ', '.join(showed_sources))

    if output_dir:
        _info(__('[autosummary] writing to %s') % output_dir)

    if base_path is not None:
        sources = [os.path.join(base_path, filename) for filename in sources]

    template = AutosummaryRenderer(builder, template_dir)

    # read
    items = find_autosummary_in_files(sources)

    # keep track of new files
    new_files = []

    # write
    for name, path, template_name in sorted(set(items), key=str):
        if path is None:
            # The corresponding autosummary:: directive did not have
            # a :toctree: option
            continue

        path = output_dir or os.path.abspath(path)
        ensuredir(path)

        try:
            name, obj, parent, mod_name = import_by_name(name)
        except ImportError as e:
            _warn(__('[autosummary] failed to import %r: %s') % (name, e))
            continue

        content = generate_autosummary_content(name, obj, parent, template, template_name,
                                               imported_members, app)

        filename = os.path.join(path, name + suffix)
        if os.path.isfile(filename):
            with open(filename) as f:
                old_content = f.read()

            if content == old_content:
                continue
            elif overwrite:  # content has changed
                with open(filename, 'w') as f:
                    f.write(content)
                new_files.append(filename)
        else:
            with open(filename, 'w') as f:
                f.write(content)
            new_files.append(filename)

    # descend recursively to new files
    if new_files:
        generate_autosummary_docs(new_files, output_dir=output_dir,
                                  suffix=suffix, warn=warn, info=info,
                                  base_path=base_path, builder=builder,
                                  template_dir=template_dir,
                                  imported_members=imported_members, app=app,
                                  overwrite=overwrite)


# -- Finding documented entries in files ---------------------------------------

def find_autosummary_in_files(filenames: List[str]) -> List[Tuple[str, str, str]]:
    """Find out what items are documented in source/*.rst.

    See `find_autosummary_in_lines`.
    """
    documented = []  # type: List[Tuple[str, str, str]]
    for filename in filenames:
        with open(filename, encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
            documented.extend(find_autosummary_in_lines(lines, filename=filename))
    return documented


def find_autosummary_in_docstring(name: str, module: Any = None, filename: str = None
                                  ) -> List[Tuple[str, str, str]]:
    """Find out what items are documented in the given object's docstring.

    See `find_autosummary_in_lines`.
    """
    try:
        real_name, obj, parent, modname = import_by_name(name)
        lines = pydoc.getdoc(obj).splitlines()
        return find_autosummary_in_lines(lines, module=name, filename=filename)
    except AttributeError:
        pass
    except ImportError as e:
        print("Failed to import '%s': %s" % (name, e))
    except SystemExit:
        print("Failed to import '%s'; the module executes module level "
              "statement and it might call sys.exit()." % name)
    return []


def find_autosummary_in_lines(lines: List[str], module: Any = None, filename: str = None
                              ) -> List[Tuple[str, str, str]]:
    """Find out what items appear in autosummary:: directives in the
    given lines.

    Returns a list of (name, toctree, template) where *name* is a name
    of an object and *toctree* the :toctree: path of the corresponding
    autosummary directive (relative to the root of the file name), and
    *template* the value of the :template: option. *toctree* and
    *template* ``None`` if the directive does not have the
    corresponding options set.
    """
    autosummary_re = re.compile(r'^(\s*)\.\.\s+autosummary::\s*')
    automodule_re = re.compile(
        r'^\s*\.\.\s+automodule::\s*([A-Za-z0-9_.]+)\s*$')
    module_re = re.compile(
        r'^\s*\.\.\s+(current)?module::\s*([a-zA-Z0-9_.]+)\s*$')
    autosummary_item_re = re.compile(r'^\s+(~?[_a-zA-Z][a-zA-Z0-9_.]*)\s*.*?')
    toctree_arg_re = re.compile(r'^\s+:toctree:\s*(.*?)\s*$')
    template_arg_re = re.compile(r'^\s+:template:\s*(.*?)\s*$')

    documented = []  # type: List[Tuple[str, str, str]]

    toctree = None  # type: str
    template = None
    current_module = module
    in_autosummary = False
    base_indent = ""

    for line in lines:
        if in_autosummary:
            m = toctree_arg_re.match(line)
            if m:
                toctree = m.group(1)
                if filename:
                    toctree = os.path.join(os.path.dirname(filename),
                                           toctree)
                continue

            m = template_arg_re.match(line)
            if m:
                template = m.group(1).strip()
                continue

            if line.strip().startswith(':'):
                continue  # skip options

            m = autosummary_item_re.match(line)
            if m:
                name = m.group(1).strip()
                if name.startswith('~'):
                    name = name[1:]
                if current_module and \
                   not name.startswith(current_module + '.'):
                    name = "%s.%s" % (current_module, name)
                documented.append((name, toctree, template))
                continue

            if not line.strip() or line.startswith(base_indent + " "):
                continue

            in_autosummary = False

        m = autosummary_re.match(line)
        if m:
            in_autosummary = True
            base_indent = m.group(1)
            toctree = None
            template = None
            continue

        m = automodule_re.search(line)
        if m:
            current_module = m.group(1).strip()
            # recurse into the automodule docstring
            documented.extend(find_autosummary_in_docstring(
                current_module, filename=filename))
            continue

        m = module_re.match(line)
        if m:
            current_module = m.group(2)
            continue

    return documented


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS] <SOURCE_FILE>...',
        epilog=__('For more information, visit <http://sphinx-doc.org/>.'),
        description=__("""
Generate ReStructuredText using autosummary directives.

sphinx-autogen is a frontend to sphinx.ext.autosummary.generate. It generates
the reStructuredText files from the autosummary directives contained in the
given input files.

The format of the autosummary directive is documented in the
``sphinx.ext.autosummary`` Python module and can be read using::

  pydoc sphinx.ext.autosummary
"""))

    parser.add_argument('--version', action='version', dest='show_version',
                        version='%%(prog)s %s' % __display_version__)

    parser.add_argument('source_file', nargs='+',
                        help=__('source files to generate rST files for'))

    parser.add_argument('-o', '--output-dir', action='store',
                        dest='output_dir',
                        help=__('directory to place all output in'))
    parser.add_argument('-s', '--suffix', action='store', dest='suffix',
                        default='rst',
                        help=__('default suffix for files (default: '
                                '%(default)s)'))
    parser.add_argument('-t', '--templates', action='store', dest='templates',
                        default=None,
                        help=__('custom template directory (default: '
                                '%(default)s)'))
    parser.add_argument('-i', '--imported-members', action='store_true',
                        dest='imported_members', default=False,
                        help=__('document imported members (default: '
                                '%(default)s)'))

    return parser


def main(argv: List[str] = sys.argv[1:]) -> None:
    sphinx.locale.setlocale(locale.LC_ALL, '')
    sphinx.locale.init_console(os.path.join(package_dir, 'locale'), 'sphinx')

    app = DummyApplication()
    logging.setup(app, sys.stdout, sys.stderr)  # type: ignore
    setup_documenters(app)
    args = get_parser().parse_args(argv)
    generate_autosummary_docs(args.source_file, args.output_dir,
                              '.' + args.suffix,
                              template_dir=args.templates,
                              imported_members=args.imported_members,
                              app=app)


if __name__ == '__main__':
    main()
