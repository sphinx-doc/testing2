.. highlight:: rst

==========
Directives
==========

:ref:`As previously discussed <rst-directives>`, a directive is a generic block
of explicit markup. While Docutils provides a number of directives, Sphinx
provides many more and uses directives as one of the primary extension
mechanisms.

See :doc:`/usage/domains/index` for roles added by domains.

.. seealso::

   Refer to the :ref:`reStructuredText Primer <rst-directives>` for an overview
   of the directives provided by Docutils.


.. _toctree-directive:

Table of contents
-----------------

.. index:: pair: table of; contents

Since reStructuredText does not have facilities to interconnect several documents,
or split documents into multiple output files,
Sphinx uses a custom directive to add relations between
the single files the documentation is made of, as well as tables of contents.
The ``toctree`` directive is the central element.

.. note::

   Simple "inclusion" of one file in another can be done with the
   :dudir:`include` directive.

.. note::

   To create table of contents for current document (.rst file), use the
   standard reStructuredText :dudir:`contents directive <table-of-contents>`.

.. rst:directive:: toctree

   This directive inserts a "TOC tree" at the current location, using the
   individual TOCs (including "sub-TOC trees") of the documents given in the
   directive body.  Relative document names (not beginning with a slash) are
   relative to the document the directive occurs in, absolute names are relative
   to the source directory.  A numeric ``maxdepth`` option may be given to
   indicate the depth of the tree; by default, all levels are included. [#]_

   The representation of "TOC tree" is changed in each output format.  The
   builders that output multiple files (e.g. HTML) treat it as a collection of
   hyperlinks.  On the other hand, the builders that output a single file (e.g.
   LaTeX, man page, etc.) replace it with the content of the documents on the
   TOC tree.

   Consider this example (taken from the Python docs' library reference index)::

      .. toctree::
         :maxdepth: 2

         intro
         strings
         datatypes
         numeric
         (many more documents listed here)

   This accomplishes two things:

   * Tables of contents from all those documents are inserted, with a maximum
     depth of two, that means one nested heading.  ``toctree`` directives in
     those documents are also taken into account.
   * Sphinx knows the relative order of the documents ``intro``,
     ``strings`` and so forth, and it knows that they are children of the shown
     document, the library index.  From this information it generates "next
     chapter", "previous chapter" and "parent chapter" links.

   **Entries**

   Document titles in the :rst:dir:`toctree` will be automatically read from the
   title of the referenced document. If that isn't what you want, you can
   specify an explicit title and target using a similar syntax to reStructuredText
   hyperlinks (and Sphinx's :ref:`cross-referencing syntax <xref-syntax>`). This
   looks like::

       .. toctree::

          intro
          All about strings <strings>
          datatypes

   The second line above will link to the ``strings`` document, but will use the
   title "All about strings" instead of the title of the ``strings`` document.

   You can also add external links, by giving an HTTP URL instead of a document
   name.

   The special entry name ``self`` stands for the document containing the
   toctree directive.  This is useful if you want to generate a "sitemap" from
   the toctree.

   In the end, all documents in the :term:`source directory` (or subdirectories)
   must occur in some ``toctree`` directive; Sphinx will emit a warning if it
   finds a file that is not included, because that means that this file will not
   be reachable through standard navigation.

   Use :confval:`exclude_patterns` to explicitly exclude documents or
   directories from building completely.  Use :ref:`the "orphan" metadata
   <metadata>` to let a document be built, but notify Sphinx that it is not
   reachable via a toctree.

   The "root document" (selected by :confval:`root_doc`) is the "root" of the TOC
   tree hierarchy.  It can be used as the documentation's main page, or as a
   "full table of contents" if you don't give a ``:maxdepth:`` option.

   .. versionchanged:: 0.6
      Added support for external links and "self" references.

   .. rubric:: Options

   .. rst:directive:option:: class: class names
      :type: a list of class names, separated by spaces

      Assign `class attributes`_.
      This is a :dudir:`common option <common-options>`.
      For example::

          .. toctree::
             :class: custom-toc

      .. _class attributes: https://docutils.sourceforge.io/docs/ref/doctree.html#classes

      .. versionadded:: 7.4

   .. rst:directive:option:: name: label
      :type: text

      An implicit target name that can be referenced using :rst:role:`ref`.
      This is a :dudir:`common option <common-options>`.
      For example::

          .. toctree::
             :name: mastertoc

             foo

      .. versionadded:: 1.3

   .. rst:directive:option:: caption
      :type: text

      Add a caption to the toctree.
      For example::

          .. toctree::
             :caption: Table of Contents

              foo

      .. versionadded:: 1.3

   .. rst:directive:option:: numbered
                             numbered: depth

      If you want to have section numbers even in HTML output,
      add the ``:numbered:`` option to the *top-level* toctree.
      For example::

         .. toctree::
            :numbered:

            foo
            bar

      Section numbering then starts at the heading of ``foo``.
      Sub-toctrees are automatically numbered
      (don't give the ``numbered`` flag to those).

      Numbering up to a specific depth is also possible,
      by giving the depth as a numeric argument to ``numbered``.

      .. versionadded:: 0.6

      .. versionchanged:: 1.1
         Added the numeric *depth* argument.

   .. rst:directive:option:: titlesonly

      Only list document titles, not other headings of the same level.
      For example::

          .. toctree::
             :titlesonly:

             foo
             bar

      .. versionadded:: 1.0

   .. rst:directive:option:: glob

      Parse glob wildcards in toctree entries.
      All entries are matched against the list of available documents,
      and matches are inserted into the list alphabetically.
      For example::

          .. toctree::
             :glob:

             intro*
             recipe/*
             *

      This includes first all documents whose names start with ``intro``,
      then all documents in the ``recipe`` folder, then all remaining documents
      (except the one containing the directive, of course.) [#]_

      .. versionadded:: 0.3

   .. rst:directive:option:: reversed

      Reverse the order of the entries in the list.
      This is particularly useful when using the ``:glob:`` option.

      .. versionadded:: 1.5

   .. rst:directive:option:: hidden

      A hidden toctree only defines the document hierarchy.
      It will not insert links into the document at the location of the directive.

      This makes sense if you have other means of navigation,
      e.g. through manual links, HTML sidebar navigation,
      or if you use the ``:includehidden:`` option on the top-level toctree.

      .. versionadded:: 0.6

   .. rst:directive:option:: includehidden

      If you want one global table of contents showing the complete document structure,
      you can add the ``:includehidden:`` option to the *top-level* toctree directive.
      All other toctrees on child pages can then be made invisible
      with the ``:hidden:`` option.
      The top-level toctree with ``:includehidden:`` will then include their entries.

      .. versionadded:: 1.2


Special names
^^^^^^^^^^^^^

.. index:: pair: genindex; toctree
           pair: modindex; toctree
           pair: search; toctree

Sphinx reserves some document names for its own use; you should not try to
create documents with these names -- it will cause problems.

The special document names (and pages generated for them) are:

* ``genindex``

  This is used for the general index,
  which is populated with entries from :rst:dir:`index` directives
  and all index-generating :ref:`object descriptions <basic-domain-markup>`.
  For example, see Sphinx's :ref:`genindex`.

* ``modindex``

  This is used for the Python module index,
  which contains one entry per :rst:dir:`py:module` directive.
  For example, see Sphinx's :ref:`py-modindex`.

* ``search``

  This is used for the search page,
  which contains a form that uses the generated JSON search index and JavaScript
  to full-text search the generated documents for search words;
  it works on every major browser.
  For example, see Sphinx's :ref:`search`.

* Every name beginning with ``_``

  Though few such names are currently used by Sphinx,
  you should not create documents or document-containing directories with such names.
  (Using ``_`` as a prefix for a custom template directory is fine.)

.. warning::

   Be careful with unusual characters in filenames.
   Some formats may interpret these characters in unexpected ways:

   * Do not use the colon ``:`` for HTML based formats.
     Links to other parts may not work.
   * Do not use the plus ``+`` for the ePub format.
     Some resources may not be found.


Paragraph-level markup
----------------------

These directives create short paragraphs and can be used inside information
units as well as normal text.


Admonitions, messages, and warnings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. index:: admonition, admonitions
           pair: attention; admonition
           pair: caution; admonition
           pair: danger; admonition
           pair: error; admonition
           pair: hint; admonition
           pair: important; admonition
           pair: note; admonition
           pair: tip; admonition
           pair: warning; admonition

The admonition directives create 'admonition' elements,
a standardised system of communicating different types of information,
from a helpful :rst:dir:`tip` to matters of paramount :rst:dir:`danger`.
These directives can be used anywhere an ordinary body element can,
and can contain arbitrary body elements.
There are nine specific named admonitions
and the generic :rst:dir:`admonition` directive.

.. rst:directive:: .. attention::

   Information that requires the reader's attention.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. attention::

      Please may I have your attention.

.. rst:directive:: .. caution::

   Information with regard to which the reader should exercise care.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. caution::

      Exercise due caution.

.. rst:directive:: .. danger::

   Information which may lead to near and present danger if not heeded.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. danger::

      Let none think to fly the danger for soon or late love is his own avenger.

.. rst:directive:: .. error::

   Information relating to failure modes of some description.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. error::

      ERROR 418: I'm a teapot.

.. rst:directive:: .. hint::

   Information that is helpful to the reader.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. hint::

      Look under the flowerpot.

.. rst:directive:: .. important::

   Information that is of paramount importance
   and which the reader must not ignore.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. important::

      This is a statement of paramount importance.

.. rst:directive:: .. note::

   An especially important bit of information that the reader should know.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. note::

      This function is not suitable for sending tins of spam.

.. rst:directive:: .. tip::

   Some useful tidbit of information for the reader.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. tip::

      Remember your sun cream!

.. rst:directive:: .. warning::

   An important bit of information that the reader should be very aware of.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. warning::

      Beware of the dog.

.. rst:directive:: .. admonition:: title

   A generic admonition, with an optional title.
   The content of the directive should be written in complete sentences
   and include all appropriate punctuation.

   Example:

   .. admonition:: This is a title

      This is the content of the admonition.


.. rst:directive:: seealso

   Many sections include a list of references to module documentation or
   external documents.
   These lists are created using the :rst:dir:`seealso` directive.

   The :rst:dir:`!seealso` directive is typically placed in a section
   just before any subsections.
   The content of the :rst:dir:`seealso` directive should be
   either a single line or a reStructuredText `definition list`_.

   .. _definition list: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#definition-lists

   Example::

      .. seealso::

         Python's :py:mod:`zipfile` module
            Documentation of Python's standard :py:mod:`zipfile` module.

         `GNU tar manual, Basic Tar Format <https://example.org>`_
            Documentation for tar archive files, including GNU tar extensions.

   .. seealso::

      Module :py:mod:`zipfile`
         Documentation of the :py:mod:`zipfile` standard module.

      `GNU tar manual, Basic Tar Format <https://example.org>`_
         Documentation for tar archive files, including GNU tar extensions.


.. _collapsible-admonitions:

.. rubric:: Collapsible text

.. versionadded:: 8.2

Each admonition directive supports a ``:collapsible:`` option,
to make the content of the admonition collapsible
(where supported by the output format).
This can be useful for content that is not always relevant.
By default, collapsible admonitions are initially open,
but this can be controlled with the ``open`` and ``closed`` arguments
to the ``:collapsible:`` option, which change the default state.
In output formats that don't support collapsible content,
the text is always included.
For example:

.. code-block:: rst

  .. note::
     :collapsible:

     This note is collapsible, and initially open by default.

  .. admonition:: Example
     :collapsible: open

     This example is collapsible, and initially open.

  .. hint::
     :collapsible: closed

     This hint is collapsible, but initially closed.

.. note::
  :collapsible:

  This note is collapsible, and initially open by default.

.. admonition:: Example
  :collapsible: open

  This example is collapsible, and initially open.

.. hint::
  :collapsible: closed

  This hint is collapsible, but initially closed.


Describing changes between versions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. index:: pair: added; in version
           pair: changes; in version
           pair: removed; in version

.. rst:directive:: .. versionadded:: version [brief explanation]

   This directive documents the version of the project
   which added the described feature.
   When this applies to an entire module or component,
   it should be placed at the top of the relevant section before any prose.

   The first argument must be given and is the version in question; you can add
   a second argument consisting of a *brief* explanation of the change.

   .. attention::
      There must be no blank line between the directive head and the explanation;
      this is to make these blocks visually continuous in the markup.

   Example::

      .. versionadded:: 2.5
         The *spam* parameter.

   .. versionadded:: 2.5
      The *spam* parameter.

.. rst:directive:: .. versionchanged:: version [brief explanation]

   Similar to :rst:dir:`versionadded`, but describes when and what changed in
   the named feature in some way (new parameters, changed side effects, etc.).

   Example::

      .. versionchanged:: 2.8
         The *spam* parameter is now of type *boson*.

   .. versionchanged:: 2.8
      The *spam* parameter is now of type *boson*.

.. rst:directive:: .. deprecated:: version [brief explanation]

   Similar to :rst:dir:`versionadded`, but describes when the feature was
   deprecated.
   A *brief* explanation can also be given,
   for example to tell the reader what to use instead.

   Example::

      .. deprecated:: 3.1
         Use :py:func:`spam` instead.

   .. deprecated:: 3.1
      Use :py:func:`!spam` instead.

.. rst:directive:: .. versionremoved:: version [brief explanation]

   Similar to :rst:dir:`versionadded`, but describes when the feature was removed.
   An explanation may be provided to tell the reader what to use instead,
   or why the feature was removed.

   .. versionadded:: 7.3

   Example::

      .. versionremoved:: 4.0
         The :py:func:`spam` function is more flexible, and should be used instead.

   .. versionremoved:: 4.0
      The :py:func:`!spam` function is more flexible, and should be used instead.


Presentational
^^^^^^^^^^^^^^

.. rst:directive:: .. rubric:: title

   A rubric is like an informal heading that doesn't correspond to the document's structure,
   i.e. it does not create a table of contents node.

   .. note::

      If the *title* of the rubric is "Footnotes" (or the selected language's
      equivalent), this rubric is ignored by the LaTeX writer, since it is
      assumed to only contain footnote definitions and therefore would create an
      empty heading.

   .. rubric:: Options

   .. rst:directive:option:: class: class names
      :type: a list of class names, separated by spaces

      Assign `class attributes`_.
      This is a :dudir:`common option <common-options>`.

   .. rst:directive:option:: name: label
      :type: text

      An implicit target name that can be referenced using :rst:role:`ref`.
      This is a :dudir:`common option <common-options>`.

   .. rst:directive:option:: heading-level: n
      :type: number from 1 to 6

      .. versionadded:: 7.4.1

      Use this option to specify the heading level of the rubric.
      In this case the rubric will be rendered as ``<h1>`` to ``<h6>`` for HTML output,
      or as the corresponding non-numbered sectioning command for LaTeX
      (see :confval:`latex_toplevel_sectioning`).


.. rst:directive:: centered

   This directive creates a centered boldfaced line of text.

   .. deprecated:: 1.1
      This presentation-only directive is a legacy from older versions.
      Use a :ref:`rst-class <rstclass>` directive instead and add an
      appropriate style.

.. rst:directive:: hlist

   This directive must contain a bullet list.  It will transform it into a more
   compact list by either distributing more than one item horizontally, or
   reducing spacing between items, depending on the builder.

   .. rubric:: Options

   .. rst:directive:option:: columns: n
      :type: int

      The number of columns; defaults to 2.
      For example::

         .. hlist::
            :columns: 3

            * A list of
            * short items
            * that should be
            * displayed
            * horizontally

   .. versionadded:: 0.6


.. _code-examples:

Showing code examples
---------------------

.. index:: pair: code; examples
           single: sourcecode

There are multiple ways to show syntax-highlighted literal code blocks in
Sphinx:

* using :ref:`reStructuredText doctest blocks <rst-doctest-blocks>`;
* using :ref:`reStructuredText literal blocks <rst-literal-blocks>`, optionally in
  combination with the :rst:dir:`highlight` directive;
* using the :rst:dir:`code-block` directive;
* and using the :rst:dir:`literalinclude` directive.

Doctest blocks can only be used
to show interactive Python sessions, while the remaining three can be used for
other languages. Of these three, literal blocks are useful when an entire
document, or at least large sections of it, use code blocks with the same
syntax and which should be styled in the same manner. On the other hand, the
:rst:dir:`code-block` directive makes more sense when you want more fine-tuned
control over the styling of each block or when you have a document containing
code blocks using multiple varied syntaxes. Finally, the
:rst:dir:`literalinclude` directive is useful for including entire code files
in your documentation.

In all cases, Syntax highlighting is provided by `Pygments
<https://pygments.org>`_. When using literal blocks, this is configured using
any :rst:dir:`highlight` directives in the source file. When a ``highlight``
directive is encountered, it is used until the next ``highlight`` directive is
encountered. If there is no ``highlight`` directive in the file, the global
highlighting language is used. This defaults to ``python`` but can be
configured using the :confval:`highlight_language` config value. The following
values are supported:

* ``none`` (no highlighting)
* ``default`` (similar to ``python3`` but with a fallback to ``none`` without
  warning highlighting fails; the default when :confval:`highlight_language`
  isn't set)
* ``guess`` (let Pygments guess the lexer based on contents, only works with
  certain well-recognizable languages)
* ``python``
* ``rest``
* ``c``
* ... and any other `lexer alias that Pygments supports`__

If highlighting with the selected language fails (i.e. Pygments emits an
"Error" token), the block is not highlighted in any way.

.. important::

   The list of lexer aliases supported is tied to the Pygment version. If you
   want to ensure consistent highlighting, you should fix your version of
   Pygments.

__ https://pygments.org/docs/lexers

.. rst:directive:: .. highlight:: language

   Example::

      .. highlight:: c

   This language is used until the next ``highlight`` directive is encountered.
   As discussed previously, *language* can be any lexer alias supported by
   Pygments.

   .. rubric:: Options

   .. rst:directive:option:: linenothreshold: threshold
      :type: number (optional)

      Enable to generate line numbers for code blocks.

      This option takes an optional number as threshold parameter.  If any
      threshold given, the directive will produce line numbers only for the code
      blocks longer than N lines.  If not given, line numbers will be produced
      for all of code blocks.

      Example::

         .. highlight:: python
            :linenothreshold: 5

   .. rst:directive:option:: force
      :type: no value

      If given, minor errors on highlighting are ignored.

      .. versionadded:: 2.1

.. rst:directive:: .. code-block:: [language]
                   .. sourcecode:: [language]
                   .. code:: [language]

   Example::

      .. code-block:: ruby

         Some Ruby code.

   The directive's alias name :rst:dir:`sourcecode` works as well.  This
   directive takes a language name as an argument.  It can be `any lexer alias
   supported by Pygments <https://pygments.org/docs/lexers/>`_.  If it is not
   given, the setting of :rst:dir:`highlight` directive will be used.  If not
   set, :confval:`highlight_language` will be used.  To display a code example
   *inline* within other text, rather than as a separate block, you can use the
   :rst:role:`code` role instead.

   .. versionchanged:: 2.0
      The ``language`` argument becomes optional.

   .. rubric:: Options

   .. rst:directive:option:: linenos
      :type: no value

      Enable to generate line numbers for the code block::

         .. code-block:: ruby
            :linenos:

            Some more Ruby code.

   .. rst:directive:option:: lineno-start: number
      :type: number

      Set the first line number of the code block.  If present, ``linenos``
      option is also automatically activated::

         .. code-block:: ruby
            :lineno-start: 10

            Some more Ruby code, with line numbering starting at 10.

      .. versionadded:: 1.3

   .. rst:directive:option:: emphasize-lines: line numbers
      :type: comma separated numbers

      Emphasize particular lines of the code block::

       .. code-block:: python
          :emphasize-lines: 3,5

          def some_function():
              interesting = False
              print('This line is highlighted.')
              print('This one is not...')
              print('...but this one is.')

      .. versionadded:: 1.1
      .. versionchanged:: 1.6.6
         LaTeX supports the ``emphasize-lines`` option.

   .. rst:directive:option:: force
      :type: no value

      Ignore minor errors on highlighting.

      .. versionadded:: 2.1

   .. rst:directive:option:: caption: caption of code block
      :type: text

      Set a caption to the code block.

      .. versionadded:: 1.3

   .. rst:directive:option:: name: a label for hyperlink
      :type: text

      Define implicit target name that can be referenced by using
      :rst:role:`ref`.  For example::

        .. code-block:: python
           :caption: this.py
           :name: this-py

           print('Explicit is better than implicit.')

      In order to cross-reference a code-block using either the
      :rst:role:`ref` or the :rst:role:`numref` role, it is necessary
      that both :strong:`name` and :strong:`caption` be defined. The
      argument of :strong:`name` can then be given to :rst:role:`numref`
      to generate the cross-reference. Example::

        See :numref:`this-py` for an example.

      When using :rst:role:`ref`, it is possible to generate a cross-reference
      with only :strong:`name` defined, provided an explicit title is
      given. Example::

        See :ref:`this code snippet <this-py>` for an example.

      .. versionadded:: 1.3

   .. rst:directive:option:: class: class names
      :type: a list of class names separated by spaces

      Assign `class attributes`_.
      This is a :dudir:`common option <common-options>`.

      .. versionadded:: 1.4

   .. rst:directive:option:: dedent: number
      :type: number or no value

      Strip indentation characters from the code block.  When number given,
      leading N characters are removed.  When no argument given, leading spaces
      are removed via :func:`textwrap.dedent`.  For example::

         .. code-block:: ruby
            :linenos:
            :dedent: 4

                some ruby code

      .. versionadded:: 1.3
      .. versionchanged:: 3.5
         Support automatic dedent.

.. rst:directive:: .. literalinclude:: filename

   Longer displays of verbatim text may be included by storing the example text
   in an external file containing only plain text.  The file may be included
   using the ``literalinclude`` directive. [#]_
   For example, to include the Python source file :file:`example.py`, use:

   .. code-block:: rst

      .. literalinclude:: example.py

   The file name is usually relative to the current file's path.  However, if
   it is absolute (starting with ``/``), it is relative to the top source
   directory.

   .. rubric:: General options

   .. rst:directive:option:: class: class names
      :type: a list of class names, separated by spaces

      Assign `class attributes`_.
      This is a :dudir:`common option <common-options>`.

      .. _class attributes: https://docutils.sourceforge.io/docs/ref/doctree.html#classes

      .. versionadded:: 1.4

   .. rst:directive:option:: name: label
      :type: text

      An implicit target name that can be referenced using :rst:role:`ref`.
      This is a :dudir:`common option <common-options>`.

      .. versionadded:: 1.3

   .. rst:directive:option:: caption: caption
      :type: text

      Add a caption above the included content.
      If no argument is given, the filename is used as the caption.

      .. versionadded:: 1.3

   .. rubric:: Options for formatting

   .. rst:directive:option:: dedent: number
      :type: number or no value

      Strip indentation characters from the included content.
      When a number is given, the leading N characters are removed.
      When no argument given, all common leading indentation is removed
      (using :func:`textwrap.dedent`).

      .. versionadded:: 1.3
      .. versionchanged:: 3.5
         Support automatic dedent.

   .. rst:directive:option:: tab-width: N
      :type: number

      Expand tabs to N spaces.

      .. versionadded:: 1.0

   .. rst:directive:option:: encoding
      :type: text

      Explicitly specify the encoding of the file.
      This overwrites the default encoding (:confval:`source_encoding`).
      For example:

      .. code-block:: rst

         .. literalinclude:: example.txt
            :encoding: latin-1

      .. versionadded:: 0.4.3

   .. rst:directive:option:: linenos
      :type: no value

      Show line numbers alongside the included content.
      By default, line numbers are counted from 1.
      This can be changed by the options ``:lineno-start:`` and ``:lineno-match:``.

   .. rst:directive:option:: lineno-start: number
      :type: number

      Set line number for the first line to show.
      If given, this automatically activates ``:linenos:``.

   .. rst:directive:option:: lineno-match

      When including only parts of a file and show the original line numbers.
      This is only allowed only when the selection consists of contiguous lines.

      .. versionadded:: 1.3

   .. rst:directive:option:: emphasize-lines: line numbers
      :type: comma separated numbers

      Emphasise particular lines of the included content.
      For example:

      .. code-block:: rst

         .. literalinclude:: example.txt
            :emphasize-lines: 1,2,4-6

   .. rst:directive:option:: language: language
      :type: text

      Select a highlighting language (`Pygments lexer`_) different from
      the current file's standard language
      (set by :rst:dir:`highlight` or :confval:`highlight_language`).

      .. _Pygments lexer: https://pygments.org/docs/lexers/

   .. rst:directive:option:: force
      :type: no value

      Ignore minor errors in highlighting.

      .. versionadded:: 2.1

   .. rubric:: Options for selecting the content to include

   .. rst:directive:option:: pyobject: object
      :type: text

      For Python files, only include the specified class, function or method:

      .. code-block:: rst

         .. literalinclude:: example.py
            :pyobject: Timer.start

      .. versionadded:: 0.6

   .. rst:directive:option:: lines: line numbers
      :type: comma separated numbers

      Specify exactly which lines to include::

         .. literalinclude:: example.py
            :lines: 1,3,5-10,20-

      This includes line 1, line 3, lines 5 to 10, and line 20 to the end.

      .. versionadded:: 0.6

   .. rst:directive:option:: start-at: text
                             start-after: text
                             end-before: text
                             end-at: text

      Another way to control which part of the file is included is to use
      the ``start-after`` and ``end-before`` options (or only one of them).
      If ``start-after`` is given as a string option,
      only lines that follow the first line containing that string are included.
      If ``end-before`` is given as a string option,
      only lines that precede the first lines containing that string are included.
      The ``start-at`` and ``end-at`` options behave in a similar way,
      but the lines containing the matched string are included.

      ``start-after``/``start-at`` and ``end-before``/``end-at`` can have same string.
      ``start-after``/``start-at`` filter lines before the line
      that contains the option string
      (``start-at`` will keep the line).
      Then ``end-before``/``end-at`` filter lines after the line
      that contains the option string
      (``end-at`` will keep the line and ``end-before`` skip the first line).

      .. versionadded:: 0.6
         Added the ``start-after`` and ``end-before`` options.
      .. versionadded:: 1.5
         Added the ``start-at``, and ``end-at`` options.

      .. tip::

         To only select ``[second-section]`` of an INI file such as the following,
         use ``:start-at: [second-section]`` and ``:end-before: [third-section]``:

         .. code-block:: ini

            [first-section]
            var_in_first=true

            [second-section]
            var_in_second=true

            [third-section]
            var_in_third=true

         These options can be useful when working with tag comments.
         Using ``:start-after: [initialise]`` and ``:end-before: [initialised]``
         keeps the lines between between the two comments below:

         .. code-block:: py

            if __name__ == "__main__":
                # [initialise]
                app.start(":8000")
                # [initialised]

         When lines have been selected in any of the ways described above,
         the line numbers in ``emphasize-lines`` refer to these selected lines,
         counted consecutively starting from 1.

   .. rst:directive:option:: prepend: line
      :type: text

      Prepend a line before the included code.
      This can be useful for example when highlighting
      PHP code that doesn't include the ``<?php`` or ``?>`` markers.

      .. versionadded:: 1.0

   .. rst:directive:option:: append: line
      :type: text

      Append a line after the included code.
      This can be useful for example when highlighting
      PHP code that doesn't include the ``<?php`` or ``?>`` markers.

      .. versionadded:: 1.0

   .. rst:directive:option:: diff: filename

      Show the diff of two files.
      For example:

      .. code-block:: rst

         .. literalinclude:: example.txt
            :diff: example.txt.orig

      This shows the diff between ``example.txt`` and ``example.txt.orig``
      with unified diff format.

      .. versionadded:: 1.3

   .. versionchanged:: 0.6
      Added support for absolute filenames.

   .. versionchanged:: 1.6
      With both ``start-after`` and ``lines`` in use,
      the first line as per ``start-after`` is considered to be
      with line number ``1`` for ``lines``.

.. _glossary-directive:

Glossary
--------

.. rst:directive:: .. glossary::

   This directive must contain a reStructuredText definition-list-like markup
   with terms and definitions.  The definitions will then be referenceable with the
   :rst:role:`term` role.  Example::

      .. glossary::

         environment
            A structure where information about all documents under the root is
            saved, and used for cross-referencing.  The environment is pickled
            after the parsing stage, so that successive runs only need to read
            and parse new and changed documents.

         source directory
            The directory which, including its subdirectories, contains all
            source files for one Sphinx project.

   In contrast to regular definition lists, *multiple* terms per entry are
   allowed, and inline markup is allowed in terms.  You can link to all of the
   terms.  For example::

      .. glossary::

         term 1
         term 2
            Definition of both terms.

   (When the glossary is sorted, the first term determines the sort order.)

   If you want to specify "grouping key" for general index entries, you can put
   a "key" as "term : key". For example::

      .. glossary::

         term 1 : A
         term 2 : B
            Definition of both terms.

   Note that "key" is used for grouping key as is.
   The "key" isn't normalized; key "A" and "a" become different groups.
   The whole characters in "key" is used instead of a first character; it is
   used for "Combining Character Sequence" and "Surrogate Pairs" grouping key.

   In i18n situation, you can specify "localized term : key" even if original
   text only have "term" part. In this case, translated "localized term" will be
   categorized in "key" group.


   .. versionchanged:: 1.1
      Now supports multiple terms and inline markup in terms.

   .. versionchanged:: 1.4
      Index key for glossary term should be considered *experimental*.


   .. rubric:: Options

   .. rst:directive:option:: sorted

      Sort the entries alphabetically.

      .. versionadded:: 0.6

      .. versionchanged:: 4.4
         In internationalized documentation, sort according to translated terms.



Meta-information markup
-----------------------

.. rst:directive:: .. sectionauthor:: name <email>

   Identifies the author of the current section.  The argument should include
   the author's name such that it can be used for presentation and email
   address.  The domain name portion of the address should be lower case.
   Example::

      .. sectionauthor:: Guido van Rossum <guido@python.org>

   By default, this markup isn't reflected in the output in any way (it helps
   keep track of contributions), but you can set the configuration value
   :confval:`show_authors` to ``True`` to make them produce a paragraph in the
   output.


.. rst:directive:: .. codeauthor:: name <email>

   The :rst:dir:`codeauthor` directive, which can appear multiple times, names
   the authors of the described code, just like :rst:dir:`sectionauthor` names
   the author(s) of a piece of documentation.  It too only produces output if
   the :confval:`show_authors` configuration value is ``True``.


Index-generating markup
-----------------------

Sphinx automatically creates index entries from all object descriptions (like
functions, classes or attributes) like discussed in
:doc:`/usage/domains/index`.

However, there is also explicit markup available, to make the index more
comprehensive and enable index entries in documents where information is not
mainly contained in information units, such as the language reference.

.. rst:directive:: .. index:: <entries>

   This directive contains one or more index entries.  Each entry consists of a
   type and a value, separated by a colon.

   For example::

      .. index::
         single: execution; context
         pair: module; __main__
         pair: module; sys
         triple: module; search; path
         seealso: scope

      The execution context
      ---------------------

      ...

   This directive contains five entries, which will be converted to entries in
   the generated index which link to the exact location of the index statement
   (or, in case of offline media, the corresponding page number).

   Since index directives generate cross-reference targets at their location in
   the source, it makes sense to put them *before* the thing they refer to --
   e.g. a heading, as in the example above.

   The possible entry types are:

   single
      Creates a single index entry.
      Can be made a sub-entry by separating the sub-entry text with a semicolon
      (this notation is also used below to describe what entries are created).
      Examples:

      .. code-block:: rst

         .. index:: single: execution
                    single: execution; context

      - ``single: execution`` creates an index entry labelled ``execution``.
      - ``single: execution; context`` creates an sub-entry of ``execution``
        labelled ``context``.
   pair
      A shortcut to create two index entries.
      The pair of values must be separated by a semicolon.
      Example:

      .. code-block:: rst

         .. index:: pair: loop; statement

      This would create two index entries; ``loop; statement`` and ``statement; loop``.
   triple
      A shortcut to create three index entries.
      All three values must be separated by a semicolon.
      Example:

      .. code-block:: rst

         .. index:: triple: module; search; path

      This would create three index entries; ``module; search path``,
      ``search; path, module``, and ``path; module search``.
   see
      A shortcut to create an index entry that refers to another entry.
      Example:

      .. code-block:: rst

         .. index:: see: entry; other

      This would create an index entry referring from ``entry`` to ``other``
      (i.e. 'entry': See 'other').
   seealso
      Like ``see``, but inserts 'see also' instead of 'see'.
   module, keyword, operator, object, exception, statement, builtin
      These **deprecated** shortcuts all create two index entries.
      For example, ``module: hashlib`` creates the entries ``module; hashlib``
      and ``hashlib; module``.

      .. deprecated:: 1.0
         These Python-specific entry types are deprecated.

      .. versionchanged:: 7.1
         Removal version set to Sphinx 9.0.
         Using these entry types will now emit warnings with the ``index`` category.

   You can mark up "main" index entries by prefixing them with an exclamation
   mark.  The references to "main" entries are emphasized in the generated
   index.  For example, if two pages contain ::

      .. index:: Python

   and one page contains ::

      .. index:: ! Python

   then the backlink to the latter page is emphasized among the three backlinks.

   For index directives containing only "single" entries, there is a shorthand
   notation::

      .. index:: BNF, grammar, syntax, notation

   This creates four index entries.

   .. versionchanged:: 1.1
      Added ``see`` and ``seealso`` types, as well as marking main entries.

   .. rubric:: Options

   .. rst:directive:option:: name: a label for hyperlink
      :type: text

      Define implicit target name that can be referenced by using
      :rst:role:`ref`.  For example::

        .. index:: Python
           :name: py-index

   .. versionadded:: 3.0

.. rst:role:: index

   While the :rst:dir:`index` directive is a block-level markup and links to the
   beginning of the next paragraph, there is also a corresponding role that sets
   the link target directly where it is used.

   The content of the role can be a simple phrase, which is then kept in the
   text and used as an index entry.  It can also be a combination of text and
   index entry, styled like with explicit targets of cross-references.  In that
   case, the "target" part can be a full entry as described for the directive
   above.  For example::

      This is a normal reStructuredText :index:`paragraph` that contains several
      :index:`index entries <pair: index; entry>`.

   .. versionadded:: 1.1


.. _tags:

Including content based on tags
-------------------------------

.. rst:directive:: .. only:: <expression>

   Include the content of the directive only if the *expression* is true.  The
   expression should consist of tags, like this::

      .. only:: html and draft

   Undefined tags are false, defined tags are true
   (tags can be defined via the :option:`--tag <sphinx-build --tag>`
   command-line option or within :file:`conf.py`, see :ref:`here <conf-tags>`).
   Boolean expressions (like ``(latex or html) and draft``) are supported
   and may use parentheses.

   The *format* and the *name* of the current builder (``html``, ``latex`` or
   ``text``) are always set as a tag [#]_.  To make the distinction between
   format and name explicit, they are also added with the prefix ``format_`` and
   ``builder_``, e.g. the epub builder defines the tags  ``html``, ``epub``,
   ``format_html`` and ``builder_epub``.

   These standard tags are set *after* the configuration file is read, so they
   are not available there.

   All tags must follow the standard Python identifier syntax as set out in
   the `Identifiers and keywords
   <https://docs.python.org/3/reference/lexical_analysis.html#identifiers>`_
   documentation.  That is, a tag expression may only consist of tags that
   conform to the syntax of Python variables.  In ASCII, this consists of the
   uppercase and lowercase letters ``A`` through ``Z``, the underscore ``_``
   and, except for the first character, the digits ``0`` through ``9``.

   .. versionadded:: 0.6
   .. versionchanged:: 1.2
      Added the name of the builder and the prefixes.

   .. warning::

      This directive is designed to control only content of document.  It could
      not control sections, labels and so on.

.. _table-directives:

Tables
------

Use :ref:`reStructuredText tables <rst-tables>`, i.e. either

- grid table syntax (:duref:`ref <grid-tables>`),
- simple table syntax (:duref:`ref <simple-tables>`),
- :dudir:`csv-table` syntax,
- or :dudir:`list-table` syntax.

The :dudir:`table` directive serves as optional wrapper of the *grid* and
*simple* syntaxes.

They work fine in HTML output, but rendering tables to LaTeX is complex.
Check the :confval:`latex_table_style`.

.. versionchanged:: 1.6
   Merged cells (multi-row, multi-column, both) from grid tables containing
   complex contents such as multiple paragraphs, blockquotes, lists, literal
   blocks, will render correctly to LaTeX output.

.. rst:directive:: .. tabularcolumns:: column spec

   This directive influences only the LaTeX output for the next table in
   source.  The mandatory argument is a column specification (known as an
   "alignment preamble" in LaTeX idiom).  Please refer to a LaTeX
   documentation, such as the `wiki page`_, for basics of such a column
   specification.

   .. _wiki page: https://en.wikibooks.org/wiki/LaTeX/Tables

   .. versionadded:: 0.3

   .. note::

      :rst:dir:`tabularcolumns` conflicts with ``:widths:`` option of table
      directives.  If both are specified, ``:widths:`` option will be ignored.

   Sphinx will render tables with more than 30 rows with ``longtable``.
   Besides the ``l``, ``r``, ``c`` and ``p{width}`` column specifiers, one can
   also use ``\X{a}{b}`` (new in version 1.5) which configures the column
   width to be a fraction ``a/b`` of the total line width and ``\Y{f}`` (new
   in version 1.6) where ``f`` is a decimal: for example ``\Y{0.2}`` means that
   the column will occupy ``0.2`` times the line width.

   When this directive is used for a table with at most 30 rows, Sphinx will
   render it with ``tabulary``.  One can then use specific column types ``L``
   (left), ``R`` (right), ``C`` (centered) and ``J`` (justified).  They have
   the effect of a ``p{width}`` (i.e. each cell is a LaTeX ``\parbox``) with
   the specified internal text alignment and an automatically computed
   ``width``.

   .. warning::

      - Cells that contain list-like elements such as object descriptions,
        blockquotes or any kind of lists are not compatible with the ``LRCJ``
        column types.  The column type must then be some ``p{width}`` with an
        explicit ``width`` (or ``\X{a}{b}`` or ``\Y{f}``).

      - Literal blocks do not work with ``tabulary`` at all.  Sphinx will
        fall back to ``tabular`` or ``longtable`` environments and generate a
        suitable column specification.

In absence of the :rst:dir:`tabularcolumns` directive, and for a table with at
most 30 rows and no problematic cells as described in the above warning,
Sphinx uses ``tabulary`` and the ``J`` column-type for every column.

.. versionchanged:: 1.6

   Formerly, the ``L`` column-type was used (text is flushed-left).  To revert
   to this, include ``\newcolumntype{T}{L}`` in the LaTeX preamble, as in fact
   Sphinx uses ``T`` and sets it by default to be an alias of ``J``.

.. hint::

   A frequent issue with ``tabulary`` is that columns with little contents
   appear to be "squeezed".  One can add to the LaTeX preamble for example
   ``\setlength{\tymin}{40pt}`` to ensure a minimal column width of ``40pt``,
   the ``tabulary`` default of ``10pt`` being too small.

.. hint::

   To force usage of the LaTeX ``longtable`` environment pass ``longtable`` as
   a ``:class:`` option to :dudir:`table`, :dudir:`csv-table`, or
   :dudir:`list-table`.  Use :ref:`rst-class <rstclass>` for other tables.

Math
----

The input language for mathematics is LaTeX markup.  This is the de-facto
standard for plain-text math notation and has the added advantage that no
further translation is necessary when building LaTeX output.

Keep in mind that when you put math markup in **Python docstrings** read by
:mod:`autodoc <sphinx.ext.autodoc>`, you either have to double all backslashes,
or use Python raw strings (``r"raw"``).

.. rst:directive:: math

   Directive for displayed math (math that takes the whole line for itself).

   The directive supports multiple equations, which should be separated by a
   blank line::

      .. math::

         (a + b)^2 = a^2 + 2ab + b^2

         (a - b)^2 = a^2 - 2ab + b^2

   In addition, each single equation is set within a ``split`` environment,
   which means that you can have multiple aligned lines in an equation,
   aligned at ``&`` and separated by ``\\``::

      .. math::

         (a + b)^2  &=  (a + b)(a + b) \\
                    &=  a^2 + 2ab + b^2

   For more details, look into the documentation of the `AmSMath LaTeX
   package`_.

   When the math is only one line of text, it can also be given as a directive
   argument::

      .. math:: (a + b)^2 = a^2 + 2ab + b^2

   .. rubric:: Options

   .. rst:directive:option:: class: class names
      :type: a list of class names, separated by spaces

      Assign `class attributes`_.
      This is a :dudir:`common option <common-options>`.

      .. _class attributes: https://docutils.sourceforge.io/docs/ref/doctree.html#classes

   .. rst:directive:option:: name: label
      :type: text

      An implicit target name that can be referenced using :rst:role:`ref`.
      This is a :dudir:`common option <common-options>`.

   .. rst:directive:option:: label: label
      :type: text

      Normally, equations are not numbered.  If you want your equation to get a
      number, use the ``label`` option.  When given, it selects an internal label
      for the equation, by which it can be cross-referenced, and causes an equation
      number to be issued.  See :rst:role:`eq` for an example.  The numbering
      style depends on the output format.

   .. rst:directive:option:: no-wrap

      Prevent wrapping of the given math in a math environment.
      When you give this option, you must make sure
      yourself that the math is properly set up.
      For example::

         .. math::
            :no-wrap:

            \begin{eqnarray}
               y    & = & ax^2 + bx + c \\
               f(x) & = & x^2 + 2xy + y^2
            \end{eqnarray}

      .. versionchanged:: 8.2

         The directive option ``:nowrap:`` was renamed to ``:no-wrap:``.

         The previous name has been retained as an alias,
         but will be deprecated and removed
         in a future version of Sphinx.

.. _AmSMath LaTeX package: https://www.ams.org/publications/authors/tex/amslatex

.. seealso::

   :ref:`math-support`
      Rendering options for math with HTML builders.

   :confval:`latex_engine`
      Explains how to configure LaTeX builder to support Unicode literals in
      math mark-up.


Grammar production displays
---------------------------

Special markup is available for displaying the productions of a formal grammar.
The markup is simple and does not attempt to model all aspects of BNF_
(or any derived forms), but provides enough to allow context-free grammars
to be displayed in a way that causes uses of a symbol to be rendered
as hyperlinks to the definition of the symbol.
There is this directive:

.. _BNF: https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form

.. rst:directive:: .. productionlist:: [production_group]

   This directive is used to enclose a group of productions.
   Each production is given on a single line and consists of a name,
   separated by a colon from the following definition.
   If the definition spans multiple lines, each continuation line
   must begin with a colon placed at the same column as in the first line.
   Blank lines are not allowed within ``productionlist`` directive arguments.

   The optional *production_group* directive argument serves to distinguish
   different sets of production lists that belong to different grammars.
   Multiple production lists with the same *production_group*
   thus define rules in the same scope.
   This can also be used to split the description of a long or complex grammar
   accross multiple ``productionlist`` directives with the same *production_group*.

   The definition can contain token names which are marked as interpreted text,
   (e.g. "``sum ::= `integer` "+" `integer```"),
   to generate cross-references to the productions of these tokens.
   Such cross-references implicitly refer to productions from the current group.
   To reference a production from another grammar, the token name
   must be prefixed with the group name and a colon, e.g. "``other-group:sum``".
   If the group of the token should not be shown in the production,
   it can be prefixed by a tilde, e.g., "``~other-group:sum``".
   To refer to a production from an unnamed grammar,
   the token should be prefixed by a colon, e.g., "``:sum``".
   No further reStructuredText parsing is done in the production,
   so that special characters (``*``, ``|``, etc) do not need to be escaped.

   Token productions can be cross-referenced outwith the production list
   by using the :rst:role:`token` role.
   If you have used a *production_group* argument,
   the token name must be prefixed with the group name and a colon,
   e.g., "``my_group:sum``" instead of just "``sum``".
   Standard :ref:`cross-referencing modifiers <xref-modifiers>`
   may be used with the ``:token:`` role,
   such as custom link text and suppressing the group name with a tilde (``~``).

The following is an example taken from the Python Reference Manual::

   .. productionlist::
      try_stmt: try1_stmt | try2_stmt
      try1_stmt: "try" ":" `suite`
               : ("except" [`expression` ["," `target`]] ":" `suite`)+
               : ["else" ":" `suite`]
               : ["finally" ":" `suite`]
      try2_stmt: "try" ":" `suite`
               : "finally" ":" `suite`


.. rubric:: Footnotes

.. [#] The LaTeX writer only refers the ``maxdepth`` option of first toctree
       directive in the document.

.. [#] A note on available globbing syntax: you can use the standard shell
       constructs ``*``, ``?``, ``[...]`` and ``[!...]`` with the feature that
       these all don't match slashes.  A double star ``**`` can be used to
       match any sequence of characters *including* slashes.

.. [#] There is a standard ``.. include`` directive, but it raises errors if the
       file is not found.  This one only emits a warning.

.. [#] For most builders name and format are the same. At the moment only
       builders derived from the html builder distinguish between the builder
       format and the builder name.

       Note that the current builder tag is not available in ``conf.py``, it is
       only available after the builder is initialized.
