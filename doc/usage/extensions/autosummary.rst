.. highlight:: rest

:mod:`sphinx.ext.autosummary` -- Generate autodoc summaries
===========================================================

.. module:: sphinx.ext.autosummary
   :synopsis: Generate autodoc summaries

.. versionadded:: 0.6

This extension generates function/method/attribute summary lists, similar to
those output e.g. by Epydoc and other API doc generation tools.  This is
especially useful when your docstrings are long and detailed, and putting each
one of them on a separate page makes them easier to read.

The :mod:`sphinx.ext.autosummary` extension does this in two parts:

1. There is an :rst:dir:`autosummary` directive for generating summary listings
   that contain links to the documented items, and short summary blurbs
   extracted from their docstrings.

2. Optionally, the convenience script :program:`sphinx-autogen` or the new
   :confval:`autosummary_generate` config value can be used to generate short
   "stub" files for the entries listed in the :rst:dir:`autosummary` directives.
   These files by default contain only the corresponding
   :mod:`sphinx.ext.autodoc` directive, but can be customized with templates.

.. rst:directive:: autosummary

   Insert a table that contains links to documented items, and a short summary
   blurb (the first sentence of the docstring) for each of them.

   The :rst:dir:`autosummary` directive can also optionally serve as a
   :rst:dir:`toctree` entry for the included items. Optionally, stub
   ``.rst`` files for these items can also be automatically generated.

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

   **Options**

   * If you want the :rst:dir:`autosummary` table to also serve as a
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

   * If you don't want the :rst:dir:`autosummary` to show function signatures in
     the listing, include the ``nosignatures`` option::

         .. autosummary::
            :nosignatures:

            sphinx.environment.BuildEnvironment
            sphinx.util.relative_uri

   * You can specify a custom template with the ``template`` option.
     For example, ::

         .. autosummary::
            :template: mytemplate.rst

            sphinx.environment.BuildEnvironment

     would use the template :file:`mytemplate.rst` in your
     :confval:`templates_path` to generate the pages for all entries
     listed. See `Customizing templates`_ below.

     .. versionadded:: 1.0


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

.. confval:: autosummary_generate

   Boolean indicating whether to scan all found documents for autosummary
   directives, and to generate stub pages for each.

   Can also be a list of documents for which stub pages should be generated.

   The new files will be placed in the directories specified in the
   ``:toctree:`` options of the directives.

   .. versionchanged:: 2.3

      Emits :event:`autodoc-skip-member` event as :mod:`~sphinx.ext.autodoc`
      does.

   .. versionchanged:: 3.0

      Emitted :event:`autodoc-skip-member` event has parameter ``member_of``
      as :mod:`~sphinx.ext.autodoc` does.

.. confval:: autosummary_generate_overwrite

   If true, autosummary already overwrites stub files by generated contents.
   Defaults to true (enabled).

   .. versionadded:: 3.0

.. confval:: autosummary_mock_imports

   This value contains a list of modules to be mocked up.  See
   :confval:`autodoc_mock_imports` for more details.  It defaults to
   :confval:`autodoc_mock_imports`.

   .. versionadded:: 2.0

.. confval:: autosummary_imported_members

   A boolean flag indicating whether to document classes and functions imported
   in modules. Default is ``False``

   .. versionadded:: 2.1


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

The following variables available in the templates:

.. currentmodule:: None

.. data:: name

   Name of the documented object, excluding the module and class parts.

.. data:: objname

   Name of the documented object, excluding the module parts.

.. data:: fullname

   Full name of the documented object, including module and class parts.

.. data:: module

   Name of the module the documented object belongs to.

.. data:: class

   Name of the class the documented object belongs to.  Only available for
   methods and attributes.

.. data:: underline

   A string containing ``len(full_name) * '='``. Use the ``underline`` filter
   instead.

.. data:: members

   List containing names of all members of the module or class.  Only available
   for modules and classes.

.. data:: inherited_members

   List containing names of all inherited members of class.  Only available for
   classes.

   .. versionadded:: 1.8.0

.. data:: functions

   List containing names of "public" functions in the module.  Here, "public"
   here means that the name does not start with an underscore. Only available
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

   List containing names of "public" attributes in the class.  Only available
   for classes.


Additionally, the following filters are available

.. function:: escape(s)

   Escape any special characters in the text to be used in formatting RST
   contexts. For instance, this prevents asterisks making things bold. This
   replaces the builtin Jinja `escape filter`_ that does html-escaping.

.. function:: underline(s, line='=')

   Add a title underline to a piece of text.

For instance, ``{{ fullname | escape | underline }}`` should be used to produce
the title of a page.

.. note::

   You can use the :rst:dir:`autosummary` directive in the stub pages.
   Stub pages are generated also based on these directives.

.. _`escape filter`: http://jinja.pocoo.org/docs/2.9/templates/#escape
