==========
Extensions
==========

Since many projects will need special features in their documentation, Sphinx
allows adding "extensions" to the build process, each of which can modify
almost any aspect of document processing.

This chapter describes the extensions bundled with Sphinx.  For the API
documentation on writing your own extension, refer to :ref:`dev-extensions`.


.. _builtin-extensions:

Built-in extensions
-------------------

These extensions are built in and can be activated by respective entries in the
:confval:`extensions` configuration value:

.. toctree::
   :maxdepth: 1

   apidoc
   autodoc
   autosectionlabel
   autosummary
   coverage
   doctest
   duration
   extlinks
   githubpages
   graphviz
   ifconfig
   imgconverter
   inheritance
   intersphinx
   linkcode
   math
   napoleon
   todo
   viewcode


.. _third-party-extensions:

Third-party extensions
----------------------

You can find several extensions contributed by users in the `sphinx-contrib`__
organization. If you wish to include your extension in this organization,
simply follow the instructions provided in the `github-administration`__
project. This is optional and there are several extensions hosted elsewhere.
The `awesome-sphinxdoc`__ and `sphinx-extensions`__ projects are both curated
lists of Sphinx packages, and many packages use the
`Framework :: Sphinx :: Extension`__ and
`Framework :: Sphinx :: Theme`__ trove classifiers for Sphinx extensions and
themes, respectively.

.. __: https://github.com/sphinx-contrib/
.. __: https://github.com/sphinx-contrib/github-administration
.. __: https://github.com/yoloseem/awesome-sphinxdoc
.. __: https://sphinx-extensions.readthedocs.io/en/latest/
.. __: https://pypi.org/search/?c=Framework+%3A%3A+Sphinx+%3A%3A+Extension
.. __: https://pypi.org/search/?c=Framework+%3A%3A+Sphinx+%3A%3A+Theme

Where to put your own extensions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extensions local to a project should be put within the project's directory
structure.  Set Python's module search path, ``sys.path``, accordingly so that
Sphinx can find them.  For example, if your extension ``foo.py`` lies in the
``exts`` subdirectory of the project root, put into :file:`conf.py`:

.. code-block:: python

   import sys
   from pathlib import Path

   sys.path.append(str(Path('exts').resolve()))

   extensions = ['foo']

You can also install extensions anywhere else on ``sys.path``, e.g. in the
``site-packages`` directory.
