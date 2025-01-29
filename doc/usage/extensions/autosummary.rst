.. highlight:: rst

:mod:`sphinx.ext.autosummary` -- Generate autodoc summaries
===========================================================

.. module:: sphinx.ext.autosummary
   :synopsis: Generate autodoc summaries

.. versionadded:: 0.6

.. role:: code-py(code)
   :language: Python

This extension generates function/method/attribute summary lists, similar to
those output e.g. by Epydoc and other API doc generation tools.  This is
especially useful when your docstrings are long and detailed, and putting each
one of them on a separate page makes them easier to read.

The :mod:`sphinx.ext.autosummary` extension does this in two parts:

1. There is an :rst:dir:`autosummary` directive for generating summary listings
   that contain links to the documented items, and short summary blurbs
   extracted from their docstrings.

2. A :rst:dir:`autosummary` directive also generates short "stub" files for the
   entries listed in its content.  These files by default contain only the
   corresponding :mod:`sphinx.ext.autodoc` directive, but can be customized with
   templates.

   The :program:`sphinx-autogen` script is also able to generate "stub" files
   from command line.

.. rst:directive:: autosummary

   Insert a table that contains links to documented items, and a short summary
   blurb (the first sentence of the docstring) for each of them.

   The :rst:dir:`autosummary` directive can also optionally serve as a
   :rst:dir:`toctree` entry for the included items. Optionally, stub
   ``.rst`` files for these items can also be automatically generated
   when :confval:`autosummary_generate` is `True`.

   For example, ::

       .. currentmodule:: sphinx

       .. autosummary::

          environment.BuildEnvironment
          util.relative_uri

   produces a table like this:

   .. currentmodule:: sphinx

   .. autosummary::

      environment.BuildEnvironment
      util.relative_uri

   .. currentmodule:: sphinx.ext.autosummary

   Autosummary preprocesses the docstrings and signatures with the same
   :event:`autodoc-process-docstring` and :event:`autodoc-process-signature`
   hooks as :mod:`~sphinx.ext.autodoc`.

   .. rubric:: Options

   .. rst:directive:option:: class: class names
      :type: a list of class names, separated by spaces

      Assign `class attributes`_ to the table.
      This is a :dudir:`common option <common-options>`.

      .. _class attributes: https://docutils.sourceforge.io/docs/ref/doctree.html#classes

      .. versionadded:: 8.2

   .. rst:directive:option:: toctree: optional directory name

      If you want the :rst:dir:`autosummary` table to also serve as a
      :rst:dir:`toctree` entry, use the ``toctree`` option, for example::

         .. autosummary::
            :toctree: DIRNAME

            sphinx.environment.BuildEnvironment
            sphinx.util.relative_uri

      The ``toctree`` option also signals to the :program:`sphinx-autogen` script
      that stub pages should be generated for the entries listed in this
      directive.  The option accepts a directory name as an argument;
      :program:`sphinx-autogen` will by default place its output in this
      directory. If no argument is given, output is placed in the same directory
      as the file that contains the directive.

      .. versionadded:: 0.6

   .. rst:directive:option:: caption: caption of ToC

      Add a caption to the toctree.

      .. versionadded:: 3.1

   .. rst:directive:option:: signatures: format

      How to display signatures. Valid values are

      - ``long`` (*default*): use a long signature. This is still cut off so that name
        plus signature do not exceeed a certain length.
      - ``short``: Function and class signatures are displayed as ``(…)`` if they have
        arguments and as ``()`` if they don't have arguments.
      - ``none``: do not show signatures.

      .. versionadded:: 8.2

   .. rst:directive:option:: nosignatures

      Do not show function signatures in the summary.

      This is equivalent to ``:signatures: none``.

      .. versionadded:: 0.6

      .. versionchanged:: 8.2

         The directive option is superseded by the more general ``:signatures: none``.

         It will be deprecated and removed
         in a future version of Sphinx.

   .. rst:directive:option:: template: filename

      Specify a custom template for rendering the summary.
      For example, ::

         .. autosummary::
            :template: mytemplate.rst

            sphinx.environment.BuildEnvironment

      would use the template :file:`mytemplate.rst` in your
      :confval:`templates_path` to generate the pages for all entries
      listed. See `Customizing templates`_ below.

      .. versionadded:: 1.0

   .. rst:directive:option:: recursive

      Generate documents for modules and sub-packages recursively.
      For example, ::

         .. autosummary::
            :recursive:

            sphinx.environment.BuildEnvironment

      .. versionadded:: 3.1


:program:`sphinx-autogen` -- generate autodoc stub pages
--------------------------------------------------------

The :program:`sphinx-autogen` script can be used to conveniently generate stub
documentation pages for items included in :rst:dir:`autosummary` listings.

For example, the command ::

    $ sphinx-autogen -o generated *.rst

will read all :rst:dir:`autosummary` tables in the :file:`*.rst` files that have
the ``:toctree:`` option set, and output corresponding stub pages in directory
``generated`` for all documented items.  The generated pages by default contain
text of the form::

    sphinx.util.relative_uri
    ========================

    .. autofunction:: sphinx.util.relative_uri

If the ``-o`` option is not given, the script will place the output files in the
directories specified in the ``:toctree:`` options.

For more information, refer to the :doc:`sphinx-autogen documentation
</man/sphinx-autogen>`


Generating stub pages automatically
-----------------------------------

If you do not want to create stub pages with :program:`sphinx-autogen`, you can
also use these config values:

.. confval:: autosummary_context
   :type: :code-py:`dict[str, Any]`
   :default: :code-py:`{}`

   A dictionary of values to pass into the template engine's context for
   autosummary stubs files.

   .. versionadded:: 3.1

.. confval:: autosummary_generate
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Boolean indicating whether to scan all found documents for autosummary
   directives, and to generate stub pages for each.

   Can also be a list of documents for which stub pages should be generated.

   The new files will be placed in the directories specified in the
   ``:toctree:`` options of the directives.

   .. versionchanged:: 2.3

      Emits :event:`autodoc-skip-member` event as :mod:`~sphinx.ext.autodoc`
      does.

   .. versionchanged:: 4.0

      Enabled by default.

.. confval:: autosummary_generate_overwrite
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If true, autosummary overwrites existing files by generated stub pages.

   .. versionadded:: 3.0

.. confval:: autosummary_mock_imports
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   This value contains a list of modules to be mocked up.
   See :confval:`autodoc_mock_imports` for more details.
   It defaults to :confval:`autodoc_mock_imports`.

   .. versionadded:: 2.0

.. confval:: autosummary_imported_members
   :type: :code-py:`bool`
   :default: :code-py:`False`

   A boolean flag indicating whether to document classes and functions imported
   in modules.

   .. versionadded:: 2.1

   .. versionchanged:: 4.4

      If ``autosummary_ignore_module_all`` is ``False``, this configuration
      value is ignored for members listed in ``__all__``.

.. confval:: autosummary_ignore_module_all
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If ``False`` and a module has the ``__all__`` attribute set, autosummary
   documents every member listed in ``__all__`` and no others.

   Note that if an imported member is listed in ``__all__``, it will be
   documented regardless of the value of ``autosummary_imported_members``. To
   match the behaviour of ``from module import *``, set
   ``autosummary_ignore_module_all`` to False and
   ``autosummary_imported_members`` to True.

   .. versionadded:: 4.4

.. confval:: autosummary_filename_map
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   A dict mapping object names to filenames. This is necessary to avoid
   filename conflicts where multiple objects have names that are
   indistinguishable when case is ignored, on file systems where filenames
   are case-insensitive.

   .. versionadded:: 3.2

.. _autosummary-customizing-templates:

Customizing templates
---------------------

.. versionadded:: 1.0

You can customize the stub page templates, in a similar way as the HTML Jinja
templates, see :ref:`templating`. (:class:`~sphinx.application.TemplateBridge`
is not supported.)

.. note::

   If you find yourself spending much time tailoring the stub templates, this
   may indicate that it's a better idea to write custom narrative documentation
   instead.

Autosummary uses the following Jinja template files:

- :file:`autosummary/base.rst` -- fallback template
- :file:`autosummary/module.rst` -- template for modules
- :file:`autosummary/class.rst` -- template for classes
- :file:`autosummary/function.rst` -- template for functions
- :file:`autosummary/attribute.rst` -- template for class attributes
- :file:`autosummary/method.rst` -- template for class methods

The following variables are available in the templates:

.. currentmodule:: None

.. data:: name

   Name of the documented object, excluding the module and class parts.

.. data:: objname

   Name of the documented object, excluding the module parts.

.. data:: fullname

   Full name of the documented object, including module and class parts.

.. data:: objtype

   Type of the documented object, one of ``"module"``, ``"function"``,
   ``"class"``, ``"method"``, ``"attribute"``, ``"data"``, ``"object"``,
   ``"exception"``, ``"newvarattribute"``, ``"newtypedata"``, ``"property"``.

.. data:: module

   Name of the module the documented object belongs to.

.. data:: class

   Name of the class the documented object belongs to.  Only available for
   methods and attributes.

.. data:: underline

   A string containing ``len(full_name) * '='``. Use the ``underline`` filter
   instead.

.. data:: members

   List containing names of all members of the module or class including private
   ones. Only available for modules and classes.

.. data:: inherited_members

   List containing names of all inherited members of class including private ones.
   Only available for classes.

   .. versionadded:: 1.8.0

.. data:: inherited_qualnames

   List containing the fully qualified names of each inherited member including
   private ones. Will return just the closest parent from which this class was
   inherited. Only available for classes.

   The following example assumes that this code block has been written as
   part of a module ``mypackage.test``

   .. code-block:: python

      class foo():
          foo_attr = "I'm an attribute"
          def __init__(self):
              print("object initialised")

          def do_something(self):
              print("Foo something")

          def _i_am_private(self):
              print("I'm a private method")

      class bar(foo):
          def do_something_else(self):
              print("Bar something")

   Some available parameters for the autosummary of class ``bar`` in the above
   example are:

   * ``name`` returns ``'bar'``
   * ``objname`` returns ``'bar'``
   * ``fullname`` returns ``'mypackage.test.bar'``
   * ``methods`` returns ``['__init__', 'do_something', 'do_something_else']``
   * ``attributes`` returns ``['foo_attr']``
   * ``members`` returns a list with many built in methods/attributes and
     ``['__init__', '_i_am_private', 'do_something', 'do_something_else',
     'foo_attr']``
   * ``inherited_members`` returns a list with many built in methods/attributes
     and ``['__init__', '_i_am_private','do_something', 'foo_attr']``
   * ``inherited_qualnames`` returns a list with many built in methods/
     attributes and ``['mypackage.test.foo.__init__',
     'mypackage.test.foo._i_am_private', 'mypackage.test.foo.do_something',
     'mypackage.test.foo.foo_attr']``
   * ``inherited_methods`` returns ``['mypackage.test.foo.__init__',
     'mypackage.test.foo.do_something']``
   * ``inherited_attributes`` returns ``['mypackage.test.foo.foo_attr']``

   These parameters could then be used in a Sphinx template ``class.rst`` like
   the following

   .. code-block:: RST
      :dedent: 0

      .. currentmodule:: {{ module }}

      .. autoclass:: {{ objname }}
         :show-inheritance:

      .. rubric:: Methods
      .. autosummary::
         :toctree:
         :nosignatures:
      {% for item in methods %}
      {% if item not in inherited_members %}
         {{objname}}.{{ item }}
      {%- endif %}
      {%- endfor %}

      .. rubric:: Inherited Methods
      .. autosummary::
      {% for item in inherited_methods %}
         {{item}}
      {%- endfor %}

   .. versionadded:: 7.3.0

.. data:: inherited_methods

   List containing fully qualified names of "public" inherited methods only.
   ``__init__`` is still included. Only available for classes.

   .. versionadded:: 7.3.0

.. data:: inherited_attributes

   List containing qualified names of "public" inherited attributes only.
   Only available for classes.

   .. versionadded:: 7.3.0

.. data:: functions

   List containing names of "public" functions in the module.  Here, "public"
   means that the name does not start with an underscore. Only available
   for modules.

.. data:: classes

   List containing names of "public" classes in the module.  Only available for
   modules.

.. data:: exceptions

   List containing names of "public" exceptions in the module.  Only available
   for modules.

.. data:: methods

   List containing names of "public" methods in the class.  Only available for
   classes.

.. data:: attributes

   List containing names of "public" attributes in the class/module.  Only
   available for classes and modules.

   .. versionchanged:: 3.1

      Attributes of modules are supported.

.. data:: modules

   List containing names of "public" modules in the package.  Only available for
   modules that are packages and the ``recursive`` option is on.

   .. versionadded:: 3.1

Additionally, the following filters are available

.. function:: escape(s)

   Escape any special characters in the text to be used in formatting RST
   contexts. For instance, this prevents asterisks making things bold. This
   replaces the builtin Jinja `escape filter`_ that does html-escaping.

.. function:: underline(s, line='=')
   :no-index:

   Add a title underline to a piece of text.

For instance, ``{{ fullname | escape | underline }}`` should be used to produce
the title of a page.

.. note::

   You can use the :rst:dir:`autosummary` directive in the stub pages.
   Stub pages are generated also based on these directives.

.. _`escape filter`: https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.escape
