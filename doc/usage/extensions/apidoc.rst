.. _ext-apidoc:

:mod:`sphinx.ext.apidoc` -- Generate API documentation from Python packages
===========================================================================

.. py:module:: sphinx.ext.apidoc
   :synopsis: Generate API documentation from Python modules

.. index:: pair: automatic; documentation
.. index:: pair: generation; documentation
.. index:: pair: generate; documentation

.. versionadded:: 8.2

.. role:: code-py(code)
   :language: Python

:mod:`sphinx.ext.apidoc` is a tool for automatic generation
of Sphinx sources from Python packages.
It provides the :program:`sphinx-apidoc` command-line tool as an extension,
allowing it to be run during the Sphinx build process.

The extension writes generated source files to a provided directory,
which are then read by Sphinx using the :mod:`sphinx.ext.autodoc` extension.

.. warning::

   :mod:`sphinx.ext.apidoc` generates source files that
   use :mod:`sphinx.ext.autodoc` to document all found modules.
   If any modules have side effects on import,
   these will be executed by ``autodoc`` when :program:`sphinx-build` is run.

   If you document scripts (as opposed to library modules),
   make sure their main routine is protected by
   an ``if __name__ == '__main__'`` condition.


Configuration
-------------

The apidoc extension uses the following configuration values:

.. confval:: apidoc_modules
   :no-index:
   :type: :code-py:`Sequence[dict[str, Any]]`
   :default: :code-py:`()`

   A list or sequence of dictionaries describing modules to document.

   For example:

   .. code-block:: python

      apidoc_modules = [
          {'destination': 'source/', 'path': 'path/to/module'},
          {
              'destination': 'source/',
              'path': 'path/to/another_module',
              'exclude_patterns': ['**/test*'],
              'maxdepth': 4,
              'followlinks': False,
              'separatemodules': False,
              'includeprivate': False,
              'noheadings': False,
              'modulefirst': False,
              'implicit_namespaces': False,
              'automodule_options': {
                  'members', 'show-inheritance', 'undoc-members'
              },
          },
      ]


   Valid keys are:

   :code-py:`'destination'`
     The output directory for generated files (**required**).
     This must be relative to the source directory,
     and will be created if it does not exist.

   :code-py:`'path'`
     The path to the module to document (**required**).
     This must be absolute or relative to the configuration directory.

   :code-py:`'exclude_patterns'`
     A sequence of patterns to exclude from generation.
     These may be literal paths or :py:mod:`fnmatch`-style patterns.
     Defaults to :code-py:`()`.

   :code-py:`'maxdepth'`
     The maximum depth of submodules to show in the generated table of contents.
     Defaults to :code-py:`4`.

   :code-py:`'followlinks'`
     Follow symbolic links.
     Defaults to :code-py:`False`.

   :code-py:`'separatemodules'`
     Put documentation for each module on an individual page.
     Defaults to :code-py:`False`.

   :code-py:`'includeprivate'`
     Generate documentation for '_private' modules with leading underscores.
     Defaults to :code-py:`False`.

   :code-py:`'noheadings'`
     Do not create headings for the modules/packages.
     Useful when source docstrings already contain headings.
     Defaults to :code-py:`False`.

   :code-py:`'modulefirst'`
     Place module documentation before submodule documentation.
     Defaults to :code-py:`False`.

   :code-py:`'implicit_namespaces'`
     By default sphinx-apidoc processes sys.path searching for modules only.
     Python 3.3 introduced :pep:`420` implicit namespaces that allow module path
     structures such as ``foo/bar/module.py`` or ``foo/bar/baz/__init__.py``
     (notice that ``bar`` and ``foo`` are namespaces, not modules).

     Interpret module paths using :pep:`420` implicit namespaces.
     Defaults to :code-py:`False`.

   :code-py:`'automodule_options'`
     Options to pass to generated :rst:dir:`automodule` directives.
     Defaults to :code-py:`{'members', 'show-inheritance', 'undoc-members'}`.
