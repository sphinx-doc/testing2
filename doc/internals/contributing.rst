======================
Contributing to Sphinx
======================

There are many ways you can contribute to Sphinx, be it filing bug reports or
feature requests, writing new documentation or submitting patches for new or
fixed behavior. This guide serves to illustrate how you can get started with
this.


Get help
--------

The Sphinx community maintains a number of mailing lists and IRC channels.

Stack Overflow with tag `python-sphinx`_
    Questions and answers about use and development.

`GitHub Discussions Q&A`__
    Question-and-answer style forum for discussions.

    __ https://github.com/orgs/sphinx-doc/discussions/categories/q-a

sphinx-users <sphinx-users@googlegroups.com>
    Mailing list for user support.

sphinx-dev <sphinx-dev@googlegroups.com>
    Mailing list for development related discussions.

#sphinx-doc on irc.libera.chat
    IRC channel for development questions and user support.

.. _python-sphinx: https://stackoverflow.com/questions/tagged/python-sphinx


Bug Reports and Feature Requests
--------------------------------

If you have encountered a problem with Sphinx or have an idea for a new
feature, please submit it to the `issue tracker`_ on GitHub.

For bug reports, please include the output produced during the build process
and also the log file Sphinx creates after it encounters an unhandled
exception.
The location of this file should be shown towards the end of the error message.
Please also include the output of :program:`sphinx-build --bug-report`.

Including or providing a link to the source files involved may help us fix the
issue.  If possible, try to create a minimal project that produces the error
and post that instead.

.. _`issue tracker`: https://github.com/sphinx-doc/sphinx/issues


Contribute code
---------------

The Sphinx source code is managed using Git and is `hosted on GitHub`_.  The
recommended way for new contributors to submit code to Sphinx is to fork this
repository and submit a pull request after committing changes to their fork.
The pull request will then need to be approved by one of the core developers
before it is merged into the main repository.

.. _hosted on GitHub: https://github.com/sphinx-doc/sphinx


.. _contribute-get-started:

Getting started
~~~~~~~~~~~~~~~

Before starting on a patch, we recommend checking for open issues
or opening a fresh issue to start a discussion around a feature idea or a bug.
If you feel uncomfortable or uncertain about an issue or your changes,
feel free to `start a discussion`_.

.. _start a discussion: https://github.com/orgs/sphinx-doc/discussions/

These are the basic steps needed to start developing on Sphinx.

#. Create an account on GitHub.

#. Fork_ the main Sphinx repository (`sphinx-doc/sphinx`_)
   using the GitHub interface.

   .. _Fork: https://github.com/sphinx-doc/sphinx/fork
   .. _sphinx-doc/sphinx: https://github.com/sphinx-doc/sphinx

#. Clone the forked repository to your machine.

   .. code-block:: shell

      git clone https://github.com/<USERNAME>/sphinx
      cd sphinx

#. Install the [UV package manager](https://docs.astral.sh/uv/).

   See <https://docs.astral.sh/uv/getting-started/installation/>

   UV will manage your development environment for you. You can run commands inside your development environment by prefixing them with `uv run`.

   See the [UV documentation](https://docs.astral.sh/uv/guides/) for more tips.

   .. tip::

      You can avoid prefixing with `uv run` by 'activating' your virtual environment:

      .. code-block:: shell

         uv sync # create the virtualenv (if it doesn't already exist)
         . ./.venv/bin/activate

#. Create a new working branch. Choose any name you like.

   .. code-block:: shell

      git switch -c feature-xyz

#. Hack, hack, hack.

   Write your code along with tests that shows that the bug was fixed or that
   the feature works as expected.

#. Add a bullet point to :file:`CHANGES.rst` if the fix or feature is not trivial
   (small doc updates, typo fixes), then commit:

   .. code-block:: shell

      git commit -m '#42: Add useful new feature that does this.'

   GitHub recognizes certain phrases that can be used to automatically
   update the issue tracker. For example:

   .. code-block:: shell

      git commit -m 'Closes #42: Fix invalid markup in docstring of Foo.bar.'

   would close issue #42.

#. Push changes in the branch to your forked repository on GitHub:

   .. code-block:: shell

      git push origin feature-xyz

#. Submit a pull request from your branch to the ``master`` branch.

#. Wait for a core developer or contributor to review your changes.


Coding style
~~~~~~~~~~~~

Please follow these guidelines when writing code for Sphinx:

* Try to use the same code style as used in the rest of the project.

* For non-trivial changes, please update the :file:`CHANGES.rst` file.
  If your changes alter existing behavior, please document this.

* New features should be documented.
  Include examples and use cases where appropriate.
  If possible, include a sample that is displayed in the generated output.

* When adding a new configuration variable,
  be sure to :doc:`document it </usage/configuration>`
  and update :file:`sphinx/cmd/quickstart.py` if it's important enough.

* Add appropriate unit tests.

Style and type checks can be run as follows:

.. code-block:: shell

   uv run ruff check .
   uv run mypy


Unit tests
~~~~~~~~~~

Sphinx is tested using pytest_ for Python code and Jasmine_ for JavaScript.

.. _pytest: https://docs.pytest.org/en/latest/
.. _Jasmine: https://jasmine.github.io/

* To run unit tests for a specific Python version, such as Python 3.13:

  .. code-block:: shell

     uv run --python 3.13 pytest

* Arguments to :program:`pytest` can be passed,
  e.g., in order to run a particular test:

  .. code-block:: shell

     uv run pytest tests/test_module.py::test_new_feature

To run JavaScript tests, use :program:`npm`:

.. code-block:: shell

   npm install
   npm run test

.. tip::

   :program:`jasmine` requires a Firefox binary to use as a test browser.

   On Unix systems, you can check the presence and location of the ``firefox``
   binary at the command-line by running ``command -v firefox``.

New unit tests should be included in the :file:`tests/` directory where necessary:

* For bug fixes, first add a test that fails without your changes and passes
  after they are applied.

* Tests that need a :program:`sphinx-build` run should be integrated in one of the
  existing test modules if possible.

* Tests should be quick and only test the relevant components, as we aim that
  *the test suite should not take more than a minute to run*.
  In general, avoid using the ``app`` fixture and ``app.build()``
  unless a full integration test is required.

.. versionadded:: 1.8

   Sphinx also runs JavaScript tests.

.. versionchanged:: 1.5.2
   Sphinx was switched from nose to pytest.


Contribute documentation
------------------------

Contributing to documentation involves modifying the source files
found in the :file:`doc/` folder.
To get started, you should first follow :ref:`contribute-get-started`,
and then take the steps below to work with the documentation.

The following sections describe how to get started with contributing
documentation, as well as key aspects of a few different tools that we use.

.. todo:: Add a more extensive documentation contribution guide.


Build the documentation
~~~~~~~~~~~~~~~~~~~~~~~

To build the documentation, run the following command:

.. code-block:: shell

   uv run sphinx-build -M html ./doc ./build/sphinx --fail-on-warning

This will parse the Sphinx documentation's source files and generate HTML for
you to preview in :file:`build/sphinx/html`.

You can also build a **live version of the documentation** that you can preview
in the browser. It will detect changes and reload the page any time you make
edits.
To do so, use `sphinx-autobuild`_ to run the following command:

.. code-block:: shell

   uv run sphinx-autobuild ./doc ./build/sphinx/

.. _sphinx-autobuild: https://github.com/sphinx-doc/sphinx-autobuild

Translations
~~~~~~~~~~~~

The parts of messages in Sphinx that go into builds are translated into several
locales.  The translations are kept as gettext ``.po`` files translated from the
master template :file:`sphinx/locale/sphinx.pot`.

Sphinx uses `Babel <https://babel.pocoo.org/en/latest/>`_ to extract messages
and maintain the catalog files.  The :file:`utils` directory contains a helper
script, ``babel_runner.py``.

* Use ``python babel_runner.py extract`` to update the ``.pot`` template.
* Use ``python babel_runner.py update`` to update all existing language
  catalogs in ``sphinx/locale/*/LC_MESSAGES`` with the current messages in the
  template file.
* Use ``python babel_runner.py compile`` to compile the ``.po`` files to binary
  ``.mo`` files and ``.js`` files.

When an updated ``.po`` file is submitted, run
``python babel_runner.py compile`` to commit both the source and the compiled
catalogs.

When a new locale is submitted, add a new directory with the ISO 639-1 language
identifier and put ``sphinx.po`` in there.  Don't forget to update the possible
values for :confval:`language` in :file:`doc/usage/configuration.rst`.

The Sphinx core messages can also be translated on `Transifex
<https://www.transifex.com/sphinx-doc/sphinx-1/>`_.  There ``tx`` client tool,
which is provided by the ``transifex_client`` Python package, can be used to
pull translations in ``.po`` format from Transifex.  To do this, go to
:file:`sphinx/locale` and then run ``tx pull -f -l LANG`` where ``LANG`` is an
existing language identifier.  It is good practice to run
``python babel_runner.py update`` afterwards to make sure the ``.po`` file has the
canonical Babel formatting.


Debugging tips
--------------

* Delete the build cache before building documents if you make changes in the
  code by running the command ``make clean`` or using the
  :option:`sphinx-build --fresh-env` option.

* Use the :option:`sphinx-build --pdb` option to run ``pdb`` on exceptions.

* Use ``node.pformat()`` and ``node.asdom().toxml()`` to generate a printable
  representation of the document structure.

* Set the configuration variable :confval:`keep_warnings` to ``True`` so
  warnings will be displayed in the generated output.

* Set the configuration variable :confval:`nitpicky` to ``True`` so that Sphinx
  will complain about references without a known target.

* Set the debugging options in the `Docutils configuration file
  <https://docutils.sourceforge.io/docs/user/config.html>`_.


Updating generated files
------------------------

* JavaScript stemming algorithms in :file:`sphinx/search/non-minified-js/*.js`
  are generated using `snowball <https://github.com/snowballstem/snowball>`_
  by cloning the repository, executing ``make dist_libstemmer_js`` and then
  unpacking the tarball which is generated in :file:`dist` directory.

  Minified files in :file:`sphinx/search/minified-js/*.js` are generated from
  non-minified ones using :program:`uglifyjs` (installed via npm), with ``-m``
  option to enable mangling.

* The :file:`searchindex.js` files found in
  the :file:`tests/js/fixtures/*` directories
  are generated by using the standard Sphinx HTML builder
  on the corresponding input projects found in :file:`tests/js/roots/*`.
  The fixtures provide test data used by the Sphinx JavaScript unit tests,
  and can be regenerated by running
  the :file:`utils/generate_js_fixtures.py` script.
