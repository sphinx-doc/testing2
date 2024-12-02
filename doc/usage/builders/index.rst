.. _builders:

========
Builders
========

.. module:: sphinx.builders
   :synopsis: Available built-in builder classes.

These are the built-in Sphinx builders.  More builders can be added by
:doc:`extensions </usage/extensions/index>`.

The builder's "name" must be given to the **-M** or **-b** command-line options of
:program:`sphinx-build` to select a builder.

The most common builders are:

**html**
   Build HTML pages.  This is the default builder.

**dirhtml**
   Build HTML pages, but with a single directory per document.  Makes for
   prettier URLs (no ``.html``) if served from a webserver.

**singlehtml**
   Build a single HTML with the whole content.

**htmlhelp**, **qthelp**, **devhelp**, **epub**
   Build HTML files with additional information for building a documentation
   collection in one of these formats.

**applehelp**
   Build an Apple Help Book.  Requires :program:`hiutil` and
   :program:`codesign`, which are not Open Source and presently only
   available on Mac OS X 10.6 and higher.

**latex**
   Build LaTeX sources that can be compiled to a PDF document using
   :program:`pdflatex`.

**man**
   Build manual pages in groff format for UNIX systems.

**texinfo**
   Build Texinfo files that can be processed into Info files using
   :program:`makeinfo`.

**text**
   Build plain text files.

**gettext**
   Build gettext-style message catalogs (``.pot`` files).

**doctest**
   Run all doctests in the documentation, if the :mod:`~sphinx.ext.doctest`
   extension is enabled.

**linkcheck**
   Check the integrity of all external links.

**xml**
  Build Docutils-native XML files.

**pseudoxml**
  Build compact pretty-printed "pseudo-XML" files displaying the
  internal structure of the intermediate document trees.

--------------

.. module:: sphinx.builders.html
.. class:: StandaloneHTMLBuilder

   This is the standard HTML builder.  Its output is a directory with HTML
   files, complete with style sheets and optionally the reStructuredText sources.
   There are quite a few configuration values that customize
   the output of this builder, see the chapter :ref:`html-options` for details.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

.. module:: sphinx.builders.dirhtml
.. class:: DirectoryHTMLBuilder

   This is a subclass of the standard HTML builder.  Its output is a directory
   with HTML files, where each file is called ``index.html`` and placed in a
   subdirectory named like its page name.  For example, the document
   ``markup/rest.rst`` will not result in an output file ``markup/rest.html``,
   but ``markup/rest/index.html``.  When generating links between pages, the
   ``index.html`` is omitted, so that the URL would look like ``markup/rest/``.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 0.6

.. module:: sphinx.builders.singlehtml
.. class:: SingleFileHTMLBuilder

   This is an HTML builder that combines the whole project in one output file.
   (Obviously this only works with smaller projects.)  The file is named like
   the root document.  No indices will be generated.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.0

.. module:: sphinxcontrib.htmlhelp
.. class:: HTMLHelpBuilder

   This builder produces the same output as the standalone HTML builder, but
   also generates HTML Help support files that allow the Microsoft HTML Help
   Workshop to compile them into a CHM file.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

.. module:: sphinxcontrib.qthelp
.. class:: QtHelpBuilder

   This builder produces the same output as the standalone HTML builder, but
   also generates `Qt help`_ collection support files that allow the Qt
   collection generator to compile them.

   .. versionchanged:: 2.0

      Moved to sphinxcontrib.qthelp from sphinx.builders package.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. _Qt help: https://doc.qt.io/qt-4.8/qthelp-framework.html

.. module:: sphinxcontrib.applehelp
.. class:: AppleHelpBuilder

   This builder produces an Apple Help Book based on the same output as the
   standalone HTML builder.

   If the source directory contains any ``.lproj`` folders, the one
   corresponding to the selected language will have its contents merged with
   the generated output.  These folders will be ignored by all other
   documentation types.

   In order to generate a valid help book, this builder requires the command
   line tool :program:`hiutil`, which is only available on Mac OS X 10.6 and
   above.  You can disable the indexing step by setting
   :confval:`applehelp_disable_external_tools` to ``True``, in which case the
   output will not be valid until :program:`hiutil` has been run on all of the
   ``.lproj`` folders within the bundle.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.3

   .. versionchanged:: 2.0

      Moved to sphinxcontrib.applehelp from sphinx.builders package.

.. module:: sphinxcontrib.devhelp
.. class:: DevhelpBuilder

   This builder produces the same output as the standalone HTML builder, but
   also generates `GNOME Devhelp <https://wiki.gnome.org/Apps/Devhelp>`__
   support file that allows the GNOME Devhelp reader to view them.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionchanged:: 2.0

      Moved to sphinxcontrib.devhelp from sphinx.builders package.

.. module:: sphinx.builders.epub3
.. class:: Epub3Builder

   This builder produces the same output as the standalone HTML builder, but
   also generates an *epub* file for ebook readers.  See :ref:`epub-faq` for
   details about it.  For definition of the epub format, have a look at
   `<https://idpf.org/epub>`_ or `<https://en.wikipedia.org/wiki/EPUB>`_.
   The builder creates *EPUB 3* files.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.4

   .. versionchanged:: 1.5

      Since Sphinx 1.5, the epub3 builder is used as the default epub builder.

.. module:: sphinx.builders.latex
.. class:: LaTeXBuilder

   This builder produces LaTeX source files in the output directory.  The
   actual PDF builds happen inside this output directory and need to be
   triggered in a second step.  This can be done via
   :program:`make all-pdf` there.
   To combine the two steps into only one, use :option:`sphinx-build -M`
   (i.e. ``-M latexpdf`` not ``-b latexpdf``) or :program:`make latexpdf`
   at the project root.

   See :confval:`latex_documents` and the chapter :ref:`latex-options` for
   available options.

   PDF builds need a sufficiently complete LaTeX installation.
   The testing is currently (since 5.3.0) done on Ubuntu 22.04LTS,
   whose LaTeX distribution matches upstream TeXLive 2021 as of 2022/02/04,
   but PDF builds can be successfully done on much older LaTeX installations.

   At any rate, on Ubuntu for example, following packages must all be present:

   * ``texlive-latex-recommended``
   * ``texlive-fonts-recommended``
   * ``texlive-fonts-extra`` (needed for ``fontawesome5``, see the 7.4.0
     change notice below)
   * ``tex-gyre`` (if :confval:`latex_engine` left to default)
   * ``texlive-latex-extra``
   * ``latexmk``

   .. versionchanged:: 4.0.0
      TeX Gyre fonts now required for ``'pdflatex'`` engine (default).

   .. versionchanged:: 7.4.0
      LaTeX package ``xcolor`` is now required (it is part of Ubuntu
      ``texlive-latex-recommended`` anyhow).  The LaTeX package
      ``fontawesome5`` is recommended.  See the :ref:`'sphinxsetup'
      <latexsphinxsetup>` ``iconpackage`` key for more.

   Additional packages are needed in some circumstances:

   * ``texlive-lang-cyrillic`` for Cyrillic (and also then
     ``cm-super`` if using the default fonts),
   * ``texlive-lang-greek`` for Greek (and also then
     ``cm-super`` if using the default fonts),
   * ``texlive-xetex`` if :confval:`latex_engine` is ``'xelatex'``,
   * ``texlive-luatex`` if :confval:`latex_engine` is ``'lualatex'``,
   * ``fonts-freefont-otf`` if :confval:`latex_engine` is either
     ``'xelatex'`` or ``'lualatex'``.

   .. note::

      Since 1.6, ``make latexpdf`` uses on GNU/Linux and macOS
      :program:`latexmk`, as it
      makes sure the needed number of runs is automatically executed.
      On Windows the PDF builds execute a fix number of LaTeX runs
      (three, then ``makeindex``, then two more).

      One can pass to ``latexmk`` options via the ``LATEXMKOPTS``
      Makefile variable. For example:

      .. code-block:: console

         make latexpdf LATEXMKOPTS="-silent"

      reduces console output to a minimum.

      To pass options directly to the ``(pdf|xe|lua)latex`` binary, use
      variable ``LATEXOPTS``, for example:

      .. code-block:: console

         make latexpdf LATEXOPTS="--halt-on-error"

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

Note that a direct PDF builder is being provided by `rinohtype`_. The builder's
name is ``rinoh``. Refer to the `rinohtype manual`_ for details.

.. _rinohtype: https://github.com/brechtm/rinohtype
.. _rinohtype manual: https://www.mos6581.org/rinohtype/master/quickstart.html#sphinx-builder

.. module:: sphinx.builders.text
.. class:: TextBuilder

   This builder produces a text file for each reStructuredText file.
   This is almost the same as the reStructuredText source,
   but with much of the markup stripped for better readability.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 0.4

.. module:: sphinx.builders.manpage
.. class:: ManualPageBuilder

   This builder produces manual pages in the groff format.  You have to specify
   which documents are to be included in which manual pages via the
   :confval:`man_pages` configuration value.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.0


.. module:: sphinx.builders.texinfo
.. class:: TexinfoBuilder

   This builder produces Texinfo files that can be processed into Info files by
   the :program:`makeinfo` program.  You have to specify which documents are to
   be included in which Texinfo files via the :confval:`texinfo_documents`
   configuration value.

   The Info format is the basis of the on-line help system used by GNU Emacs and
   the terminal-based program :program:`info`.  See :ref:`texinfo-faq` for more
   details.  The Texinfo format is the official documentation system used by the
   GNU project.  More information on Texinfo can be found at
   `<https://www.gnu.org/software/texinfo/>`_.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.1


.. currentmodule:: sphinxcontrib.serializinghtml
.. class:: SerializingHTMLBuilder

   This builder uses a module that implements the Python serialization API
   (``pickle``, ``simplejson``, ``phpserialize``, and others) to dump the
   generated HTML documentation.  The pickle builder is a subclass of it.

   A concrete subclass of this builder serializing to the `PHP serialization`_
   format could look like this::

        import phpserialize

        class PHPSerializedBuilder(SerializingHTMLBuilder):
            name = 'phpserialized'
            implementation = phpserialize
            out_suffix = '.file.phpdump'
            globalcontext_filename = 'globalcontext.phpdump'
            searchindex_filename = 'searchindex.phpdump'

   .. _PHP serialization: https://pypi.org/project/phpserialize/

   .. attribute:: implementation

      A module that implements ``dump()``, ``load()``, ``dumps()`` and ``loads()``
      functions that conform to the functions with the same names from the
      pickle module.  Known modules implementing this interface are
      ``simplejson``, ``phpserialize``, ``plistlib``, and others.

   .. attribute:: out_suffix

      The suffix for all regular files.

   .. attribute:: globalcontext_filename

      The filename for the file that contains the "global context".  This
      is a dict with some general configuration values such as the name
      of the project.

   .. attribute:: searchindex_filename

      The filename for the search index Sphinx generates.

   See :ref:`serialization-details` for details about the output format.

   .. versionadded:: 0.5

.. class:: PickleHTMLBuilder

   This builder produces a directory with pickle files containing mostly HTML
   fragments and TOC information, for use of a web application (or custom
   postprocessing tool) that doesn't use the standard HTML templates.

   See :ref:`serialization-details` for details about the output format.

   .. autoattribute:: name

      The old name ``web`` still works as well.

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   The file suffix is ``.fpickle``.  The global context is called
   ``globalcontext.pickle``, the search index ``searchindex.pickle``.

.. class:: JSONHTMLBuilder

   This builder produces a directory with JSON files containing mostly HTML
   fragments and TOC information, for use of a web application (or custom
   postprocessing tool) that doesn't use the standard HTML templates.

   See :ref:`serialization-details` for details about the output format.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   The file suffix is ``.fjson``.  The global context is called
   ``globalcontext.json``, the search index ``searchindex.json``.

   .. versionadded:: 0.5

.. module:: sphinx.builders.gettext
.. class:: MessageCatalogBuilder

   This builder produces gettext-style message catalogs.  Each top-level file or
   subdirectory grows a single ``.pot`` catalog template.

   See the documentation on :ref:`intl` for further reference.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.1

.. module:: sphinx.builders.changes
.. class:: ChangesBuilder

   This builder produces an HTML overview of all :rst:dir:`versionadded`,
   :rst:dir:`versionchanged`, :rst:dir:`deprecated` and :rst:dir:`versionremoved`
   directives for the current :confval:`version`.  This is useful to generate a
   changelog file, for example.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

.. module:: sphinx.builders.dummy
.. class:: DummyBuilder

   This builder produces no output.  The input is only parsed and checked for
   consistency.  This is useful for linting purposes.

   .. autoattribute:: name

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.4

.. module:: sphinx.builders.linkcheck
.. class:: CheckExternalLinksBuilder

   This builder scans all documents for external links, tries to open them with
   ``requests``, and writes an overview which ones are broken and redirected to
   standard output and to :file:`output.txt` in the output directory.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionchanged:: 1.5

      Since Sphinx 1.5, the linkcheck builder uses the requests module.

   .. versionchanged:: 3.4

      The linkcheck builder retries links when servers apply rate limits.

.. module:: sphinx.builders.xml
.. class:: XMLBuilder

   This builder produces Docutils-native XML files.  The output can be
   transformed with standard XML tools such as XSLT processors into arbitrary
   final forms.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.2

.. class:: PseudoXMLBuilder

   This builder is used for debugging the Sphinx/Docutils "Reader to Transform
   to Writer" pipeline. It produces compact pretty-printed "pseudo-XML", files
   where nesting is indicated by indentation (no end-tags). External
   attributes for all elements are output, and internal attributes for any
   leftover "pending" elements are also given.

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types

   .. versionadded:: 1.2


Built-in Sphinx extensions that offer more builders are:

* :mod:`~sphinx.ext.doctest`
* :mod:`~sphinx.ext.coverage`


.. _serialization-details:

Serialization builder details
-----------------------------

All serialization builders outputs one file per source file and a few special
files.  They also copy the reStructuredText source files
to the ``_sources`` directory under the output directory.

The :class:`.PickleHTMLBuilder` is a builtin subclass that implements the pickle
serialization interface.

The files per source file have the extensions of
:attr:`~.SerializingHTMLBuilder.out_suffix`, and are arranged in directories
just as the source files are.  They unserialize to a dictionary (or dictionary
like structure) with these keys:

``body``
   The HTML "body" (that is, the HTML rendering of the source file), as rendered
   by the HTML translator.

``title``
   The title of the document, as HTML (may contain markup).

``toc``
   The table of contents for the file, rendered as an HTML ``<ul>``.

``display_toc``
   A boolean that is ``True`` if the ``toc`` contains more than one entry.

``current_page_name``
   The document name of the current file.

``parents``, ``prev`` and ``next``
   Information about related chapters in the TOC tree.  Each relation is a
   dictionary with the keys ``link`` (HREF for the relation) and ``title``
   (title of the related document, as HTML).  ``parents`` is a list of
   relations, while ``prev`` and ``next`` are a single relation.

``sourcename``
   The name of the source file under ``_sources``.

The special files are located in the root output directory.  They are:

:attr:`.SerializingHTMLBuilder.globalcontext_filename`
   A pickled dict with these keys:

   ``project``, ``copyright``, ``release``, ``version``
      The same values as given in the configuration file.

   ``style``
      :confval:`html_style`.

   ``last_updated``
      Date of last build.

   ``builder``
      Name of the used builder, in the case of pickles this is always
      ``'pickle'``.

   ``titles``
      A dictionary of all documents' titles, as HTML strings.

:attr:`.SerializingHTMLBuilder.searchindex_filename`
   An index that can be used for searching the documentation.  It is a pickled
   list with these entries:

   * A list of indexed docnames.
   * A list of document titles, as HTML strings, in the same order as the first
     list.
   * A dict mapping word roots (processed by an English-language stemmer) to a
     list of integers, which are indices into the first list.

``environment.pickle``
   The build environment.  This is always a pickle file, independent of the
   builder and a copy of the environment that was used when the builder was
   started.

   .. todo:: Document common members.

   Unlike the other pickle files this pickle file requires that the ``sphinx``
   package is available on unpickling.
