.. highlight:: rst

:mod:`sphinx.ext.doctest` -- Test snippets in the documentation
===============================================================

.. module:: sphinx.ext.doctest
   :synopsis: Test snippets in the documentation.

.. index:: pair: automatic; testing
           single: doctest
           pair: testing; snippets

.. role:: code-py(code)
   :language: Python


It is often helpful to include snippets of code in your documentation and
demonstrate the results of executing them. But it is important to ensure that
the documentation stays up-to-date with the code.

This extension allows you to test such code snippets in the documentation in
a natural way.  If you mark the code blocks as shown here, the ``doctest``
builder will collect them and run them as doctest tests.

Within each document, you can assign each snippet to a *group*. Each group
consists of:

* zero or more *setup code* blocks (e.g. importing the module to test)
* one or more *test* blocks

When building the docs with the ``doctest`` builder, groups are collected for
each document and run one after the other, first executing setup code blocks,
then the test blocks in the order they appear in the file.

There are two kinds of test blocks:

* *doctest-style* blocks mimic interactive sessions by interleaving Python code
  (including the interpreter prompt) and output.

* *code-output-style* blocks consist of an ordinary piece of Python code, and
  optionally, a piece of output for that code.


Directives
----------

The *group* argument below is interpreted as follows: if it is empty, the block
is assigned to the group named ``default``.  If it is ``*``, the block is
assigned to all groups (including the ``default`` group).  Otherwise, it must be
a comma-separated list of group names.

.. rst:directive:: .. testsetup:: [group]

   A setup code block.  This code is not shown in the output for other builders,
   but executed before the doctests of the group(s) it belongs to.

   .. rubric:: Options

   .. rst:directive:option:: skipif: condition
      :type: text

      Skip the directive if the python expression *condition* is True.
      See :ref:`skipping tests conditionally <doctest-skipif>`.


.. rst:directive:: .. testcleanup:: [group]

   A cleanup code block.  This code is not shown in the output for other
   builders, but executed after the doctests of the group(s) it belongs to.

   .. versionadded:: 1.1

   .. rubric:: Options

   .. rst:directive:option:: skipif: condition
      :type: text

      Skip the directive if the python expression *condition* is True.
      See :ref:`skipping tests conditionally <doctest-skipif>`.


.. rst:directive:: .. doctest:: [group]

   A doctest-style code block.  You can use standard :mod:`doctest` flags for
   controlling how actual output is compared with what you give as output.  The
   default set of flags is specified by the :confval:`doctest_default_flags`
   configuration variable.

   .. rubric:: Options

   .. rst:directive:option:: hide

     Hide the doctest block in other builders.
     By default it is shown as a highlighted doctest block.

   .. rst:directive:option:: options: doctest flags
      :type: comma separated list

      A comma-separated list of doctest flags that apply to each example in the
      tests.  (You still can give explicit flags per example, with doctest comments,
      but they will show up in other builders too.)

      Alternatively, you can give inline doctest options, like in doctest:

      .. code-block:: pycon

         >>> datetime.date.now()   # doctest: +SKIP
         datetime.date(2008, 1, 1)

      They will be respected when the test is run, but by default will be stripped from
      presentation output. You can prevent stripping using the option
      :rst:dir:`doctest:no-trim-doctest-flags`.

   .. rst:directive:option:: pyversion
      :type: text

      Specify the required Python version for the example to be tested. For instance,
      in the following case the example will be tested only for Python versions greater
      than 3.12::

         .. doctest::
            :pyversion: > 3.12

      The following operands are supported:

      * ``~=``: Compatible release clause
      * ``==``: Version matching clause
      * ``!=``: Version exclusion clause
      * ``<=``, ``>=``: Inclusive ordered comparison clause
      * ``<``, ``>``: Exclusive ordered comparison clause
      * ``===``: Arbitrary equality clause.

      ``pyversion`` option is followed :pep:`PEP-440: Version Specifiers
      <440#version-specifiers>`.

      .. versionadded:: 1.6

      .. versionchanged:: 1.7

         Supported PEP-440 operands and notations

   .. rst:directive:option:: trim-doctest-flags
                             no-trim-doctest-flags

      Whether to trim remove doctest flags (comments looking like
      ``# doctest: FLAG, ...``) at the ends of lines and ``<BLANKLINE>`` markers
      individually.  Default is ``trim-doctest-flags``.

      Note that like with standard doctests, you have to use ``<BLANKLINE>`` to
      signal a blank line in the expected output.  The ``<BLANKLINE>`` is removed
      when building presentation output (HTML, LaTeX etc.).

   .. rst:directive:option:: skipif: condition
      :type: text

      Skip the directive if the python expression *condition* is True.
      See :ref:`skipping tests conditionally <doctest-skipif>`.

.. rst:directive:: .. testcode:: [group]

   A code block for a code-output-style test.

   .. rubric:: Options

   .. rst:directive:option:: hide

      Hide the code block in other builders.
      By default it is shown as a highlighted code block.

   .. rst:directive:option:: trim-doctest-flags
                             no-trim-doctest-flags

      Whether to trim remove doctest flags (comments looking like
      ``# doctest: FLAG, ...``) at the ends of lines and ``<BLANKLINE>`` markers
      individually.  Default is ``trim-doctest-flags``.

   .. rst:directive:option:: skipif: condition
      :type: text

      Skip the directive if the python expression *condition* is True.
      See :ref:`skipping tests conditionally <doctest-skipif>`.

   .. note::

      Code in a ``testcode`` block is always executed all at once, no matter how
      many statements it contains.  Therefore, output will *not* be generated
      for bare expressions -- use ``print``.  Example::

          .. testcode::

             1+1         # this will give no output!
             print(2+2)  # this will give output

          .. testoutput::

             4

      Also, please be aware that since the doctest module does not support
      mixing regular output and an exception message in the same snippet, this
      applies to testcode/testoutput as well.


.. rst:directive:: .. testoutput:: [group]

   The corresponding output, or the exception message, for the last
   :rst:dir:`testcode` block.

   .. rst:directive:option:: hide

     Hide the doctest block in other builders.
     By default it is shown as a highlighted doctest block.

   .. rst:directive:option:: options: doctest flags
      :type: comma separated list

      A comma-separated list of doctest flags.

   .. rst:directive:option:: trim-doctest-flags
                             no-trim-doctest-flags

      Whether to trim remove doctest flags (comments looking like
      ``# doctest: FLAG, ...``) at the ends of lines and ``<BLANKLINE>`` markers
      individually.  Default is ``trim-doctest-flags``.

   .. rst:directive:option:: skipif: condition
      :type: text

      Skip the directive if the python expression *condition* is True.
      See :ref:`skipping tests conditionally <doctest-skipif>`.

   Example::

      .. testcode::

         print('Output     text.')

      .. testoutput::
         :hide:
         :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

         Output text.

The following is an example for the usage of the directives.  The test via
:rst:dir:`doctest` and the test via :rst:dir:`testcode` and
:rst:dir:`testoutput` are equivalent. ::

   The parrot module
   =================

   .. testsetup:: *

      import parrot

   The parrot module is a module about parrots.

   Doctest example:

   .. doctest::

      >>> parrot.voom(3000)
      This parrot wouldn't voom if you put 3000 volts through it!

   Test-Output example:

   .. testcode::

      parrot.voom(3000)

   This would output:

   .. testoutput::

      This parrot wouldn't voom if you put 3000 volts through it!


.. _doctest-skipif:

Skipping tests conditionally
----------------------------

``skipif``, a string option, can be used to skip directives conditionally. This
may be useful e.g. when a different set of tests should be run depending on the
environment (hardware, network/VPN, optional dependencies or different versions
of dependencies). The ``skipif`` option is supported by all of the doctest
directives. Below are typical use cases for ``skipif`` when used for different
directives:

- :rst:dir:`testsetup` and :rst:dir:`testcleanup`

  - conditionally skip test setup and/or cleanup
  - customize setup/cleanup code per environment

- :rst:dir:`doctest`

  - conditionally skip both a test and its output verification

- :rst:dir:`testcode`

  - conditionally skip a test
  - customize test code per environment

- :rst:dir:`testoutput`

  - conditionally skip output assertion for a skipped test
  - expect different output depending on the environment

The value of the ``skipif`` option is evaluated as a Python expression. If the
result is a true value, the directive is omitted from the test run just as if
it wasn't present in the file at all.

Instead of repeating an expression, the :confval:`doctest_global_setup`
configuration option can be used to assign it to a variable which can then be
used instead.

Here's an example which skips some tests if Pandas is not installed:

.. code-block:: py
   :caption: conf.py

   extensions = ['sphinx.ext.doctest']
   doctest_global_setup = '''
   try:
       import pandas as pd
   except ImportError:
       pd = None
   '''

.. code-block:: rst
   :caption: contents.rst

   .. testsetup::
      :skipif: pd is None

      data = pd.Series([42])

   .. doctest::
      :skipif: pd is None

      >>> data.iloc[0]
      42

   .. testcode::
      :skipif: pd is None

      print(data.iloc[-1])

   .. testoutput::
      :skipif: pd is None

      42


Configuration
-------------

The doctest extension uses the following configuration values:

.. confval:: doctest_default_flags
   :type: :code-py:`int`
   :default: :code-py:`ELLIPSIS | IGNORE_EXCEPTION_DETAIL | DONT_ACCEPT_TRUE_FOR_1`

   By default, these options are enabled:

   - ``ELLIPSIS``, allowing you to put ellipses in the expected output that
     match anything in the actual output;
   - ``IGNORE_EXCEPTION_DETAIL``, causing everything following the leftmost
     colon and any module information in the exception name to be ignored;
   - ``DONT_ACCEPT_TRUE_FOR_1``, rejecting "True" in the output where "1" is
     given -- the default behavior of accepting this substitution is a relic of
     pre-Python 2.2 times.

   .. versionadded:: 1.5

.. confval:: doctest_show_successes
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Controls whether successes are reported.

   For a project with many doctests,
   it may be useful to set this to ``False`` to only highlight failures.

   .. versionadded:: 7.2

.. confval:: doctest_path
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of directories that will be added to :data:`sys.path` when the doctest
   builder is used.  (Make sure it contains absolute paths.)

.. confval:: doctest_global_setup
   :type: :code-py:`str`
   :default: :code-py:`''`

   Python code that is treated like it were put in a ``testsetup`` directive for
   *every* file that is tested, and for every group.  You can use this to
   e.g. import modules you will always need in your doctests.

   .. versionadded:: 0.6

.. confval:: doctest_global_cleanup
   :type: :code-py:`str`
   :default: :code-py:`''`

   Python code that is treated like it were put in a ``testcleanup`` directive
   for *every* file that is tested, and for every group.  You can use this to
   e.g. remove any temporary files that the tests leave behind.

   .. versionadded:: 1.1

.. confval:: doctest_test_doctest_blocks
   :type: :code-py:`str`
   :default: :code-py:`'default'`

   If this is a nonempty string,
   standard reStructuredText doctest blocks will be tested too.
   They will be assigned to the group name given.

   reStructuredText doctest blocks are simply doctests
   put into a paragraph of their own, like so::

      Some documentation text.

      >>> print(1)
      1

      Some more documentation text.

   (Note that no special ``::`` is used to introduce a doctest block; docutils
   recognizes them from the leading ``>>>``.  Also, no additional indentation is
   used, though it doesn't hurt.)

   If this value is left at its default value, the above snippet is interpreted
   by the doctest builder exactly like the following::

      Some documentation text.

      .. doctest::

         >>> print(1)
         1

      Some more documentation text.

   This feature makes it easy for you to test doctests in docstrings included
   with the :mod:`~sphinx.ext.autodoc` extension without marking them up with a
   special directive.

   Note though that you can't have blank lines in reStructuredText doctest blocks.
   They will be interpreted as one block ending and another one starting.
   Also, removal of ``<BLANKLINE>`` and ``# doctest:`` options only works in
   :rst:dir:`doctest` blocks, though you may set :confval:`trim_doctest_flags`
   to achieve that in all code blocks with Python console content.

.. confval:: doctest_fail_fast
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Exit when the first failure is encountered.

   .. versionadded:: 8.2.0
