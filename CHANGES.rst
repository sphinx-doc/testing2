Release 8.1.0 (in development)
==============================

Dependencies
------------

* #12756: Add lower-bounds to the ``sphinxcontrib-*`` dependencies.
  Patch by Adam Turner.

Incompatible changes
--------------------

* #12763: Remove unused internal class ``sphinx.util.Tee``.
  Patch by Adam Turner.
* #12822: LaTeX: for Unicode engines, the :ref:`fvset` default is changed to
  ``'\\fvset{fontsize=auto}'`` from ``'\\fvset{fontsize=\\small}'``.
  Code-blokcs are unchanged as FreeMono is now loaded with ``Scale=0.9``.
  An adjustement to existing projects is needed only if they used a custom
  :ref:`fontpkg` configuration and did not set :ref:`fvset`.

Deprecated
----------

* #12762: Deprecate ``sphinx.util.import_object``.
  Use :py:func:`importlib.import_module` instead.
  Patch by Adam Turner.
* #12766: Deprecate ``sphinx.util.FilenameUniqDict``
  and ``sphinx.util.DownloadFiles``.
  Patch by Adam Turner.

Features added
--------------

* #11328: Mention evaluation of templated content during production of static
  output files.
* #12704: LaTeX: make :dudir:`contents <table-of-contents>`, :dudir:`topic`,
  and :dudir:`sidebar` directives separately customizable for PDF output.
  Patch by Jean-François B. and Bénédikt Tran.
* #12474: Support type-dependent search result highlighting via CSS.
  Patch by Tim Hoffmann.
* #12652: LaTeX: Add :confval:`math_numsep` support to latex builder.
  Patch by Thomas Fanning and Jean-François B.
* #12743: No longer exit on the first warning when
  :option:`--fail-on-warning <sphinx-build --fail-on-warning>` is used.
  Instead, exit with a non-zero status if any warnings were generated
  during the build.
  Patch by Adam Turner.
* #12743: Add :option:`sphinx-build --exception-on-warning`,
  to raise an exception when warnings are emitted during the build.
  Patch by Adam Turner and Jeremy Maitin-Shepard.

Bugs fixed
----------

* #12514: intersphinx: fix the meaning of a negative value for
  :confval:`intersphinx_cache_limit`.
  Patch by Shengyu Zhang.
* #12722: LaTeX: avoid TeX reporting ``Overfull \hbox`` from too long
  strings in a codeline when the problem has actually been solved thanks
  to :ref:`latexsphinxsetupforcewraps`.
  Patch by Jean-François B.
* #12730: The ``UnreferencedFootnotesDetector`` transform has been improved
  to more consistently detect unreferenced footnotes.
  Note, the priority of the transform has been changed from 200 to 622,
  so that it now runs after the docutils ``Footnotes`` resolution transform.
  Patch by Chris Sewell.
* #12778: LaTeX: let :ref:`'sphinxsetup' <latexsphinxsetup>`
  ``div.topic_box-shadow`` key if used with only one dimension set both
  x-offset and y-offset as per documentation.
* #12587: Do not warn when potential ambiguity detected during Intersphinx
  resolution occurs due to duplicate targets that differ case-insensitively.
  Patch by James Addison.
* #12639: Fix singular and plural search results text.
  Patch by Hugo van Kemenade.
* #12645: Correctly support custom gettext output templates.
  Patch by Jeremy Bowman.
* #12717: LaTeX: let :option:`-q <sphinx-build -q>` (quiet) option for
  :program:`sphinx-build -M latexpdf` or :program:`make latexpdf` (``O=-q``)
  get passed to :program:`latexmk`.  Let :option:`-Q <sphinx-build -Q>`
  (silent) apply as well to the PDF build phase.
  Patch by Jean-François B.
* #12744: LaTeX: Classes injected by a custom interpreted text role now give
  rise to nested ``\DUrole``'s, rather than a single one with comma separated
  classes.
  Patch by Jean-François B.
* #12831: LaTeX: avoid large voids sometimes occurring at page bottoms.
  Patch by Jean-François B.
* #11970, #12551: singlehtml builder: make target URIs to be same-document
  references in the sense of :rfc:`RFC 3986, §4.4 <3986#section-4.4>`,
  e.g., ``index.html#foo`` becomes ``#foo``.
  (note: continuation of a partial fix added in Sphinx 7.3.0)
  Patch by James Addison (with reference to prior work by Eric Norige)
* #12735: Fix :pep:`695` generic classes LaTeX output formatting.
  Patch by Jean-François B. and Bénédikt Tran.
* #12782: intersphinx: fix double forward slashes when generating the inventory
  file URL (user-defined base URL of an intersphinx project are left untouched
  even if they end with double forward slashes).
  Patch by Bénédikt Tran.
* #12797: Fix
  ``TypeError: Some type variables (...) are not listed in Generic[...]``
  when inheriting from both Generic and autodoc mocked class.

Testing
-------

* #12141: Migrate from the deprecated ``karma`` JavaScript test framework to
  the actively-maintained ``jasmine`` framework.  Test coverage is unaffected.
  Patch by James Addison.
