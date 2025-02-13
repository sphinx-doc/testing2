Release 8.2.0 (in development)
==============================

Dependencies
------------

* #13000: Drop Python 3.10 support.

Incompatible changes
--------------------

* #13044: Remove the internal and undocumented ``has_equations`` data
  from the :py:class:`!MathDomain`` domain.
  The undocumented :py:meth:`!MathDomain.has_equations` method
  now unconditionally returns ``True``.
  These are replaced by the ``has_maths_elements`` key of the page context dict.
  Patch by Adam Turner.
* #13227: HTML output for sequences of keys in the :rst:role:`kbd` role
  no longer uses a ``<kbd class="kbd compound">`` element to wrap
  the keys and separators, but places them directly in the relevant parent node.
  This means that CSS rulesets targeting ``kbd.compound`` or ``.kbd.compound``
  will no longer have any effect.
  Patch by Adam Turner.

Deprecated
----------

* #13037: Deprecate the ``SingleHTMLBuilder.fix_refuris`` method.
  Patch by James Addison.
* #13083, #13330: Un-deprecate ``sphinx.util.import_object``.
  Patch by Matthias Geier.

Features added
--------------

* #13173: Add a new ``duplicate_declaration`` warning type,
  with ``duplicate_declaration.c`` and ``duplicate_declaration.cpp`` subtypes.
  Patch by Julien Lecomte and Adam Turner.
* #11824: linkcode: Allow extensions to add support for a domain by defining
  the keys that should be present.
  Patch by Nicolas Peugnet.
* #13144: Add a ``class`` option to the :rst:dir:`autosummary` directive.
  Patch by Tim Hoffmann.
* #13146: Napoleon: Unify the type preprocessing logic to allow
  Google-style docstrings to use the optional and default keywords.
  Patch by Chris Barrick.
* #13227: Implement the :rst:role:`kbd` role as a ``SphinxRole``.
  Patch by Adam Turner.
* #13065: Enable colour by default in when running on CI.
  Patch by Adam Turner.
* #13230: Allow supressing warnings from the :rst:dir:`toctree` directive
  when a glob pattern doesn't match any documents,
  via the new ``toc.empty_glob`` warning sub-type.
  Patch by Slawek Figiel.
* #9732: Add the new ``autodoc.mocked_object`` warnings sub-type.
  Patch by Cyril Roelandt.
* #7630, #4824: autodoc: Use :file:`.pyi` type stub files
  to auto-document native modules.
  Patch by Adam Turner, partially based on work by Allie Fitter.
* #12975: Enable configuration of trailing commas in multi-line signatures
  in the Python and Javascript domains, via the new
  :confval:`python_trailing_comma_in_multi_line_signatures` and
  :confval:`javascript_trailing_comma_in_multi_line_signatures`
  configuration options.
* #13264: Rename the :rst:dir:`math` directive's ``nowrap``option
  to :rst:dir:`no-wrap``,
  and rename the :rst:dir:`autosummary` directive's ``nosignatures``option
  to :rst:dir:`no-signatures``.
  Patch by Adam Turner.
* #13269: Added the option to disable the use of type comments in
  via the new :confval:`autodoc_use_type_comments` option,
  which defaults to ``True`` for backwards compatibility.
  The default will change to ``False`` in Sphinx 10.
  Patch by Adam Turner.
* #9732: Add the new ``ref.any`` warnings sub-type
  to allow suppressing the ambiguous 'any' cross-reference warning.
  Patch by Simão Afonso and Adam Turner.
* #13272: The Python and JavaScript module directives now support
  the ``:no-index-entry:`` option.
  Patch by Adam Turner.
* #12233: autodoc: Allow directives to use ``:no-index-entry:``
  and include the ``:no-index:`` and ``:no-index-entry:`` options within
  :confval:`autodoc_default_options`.
  Patch by Jonny Saunders and Adam Turner.
* #13172: Add support for short signatures in autosummary.
  Patch by Tim Hoffmann.
* #13271: Change the signature prefix for abstract methods
  in the Python domain to *abstractmethod* from *abstract*.
  Patch by Adam Turner.
* #13271: Support the ``:abstract:`` option for
  classes, methods, and properties in the Python domain.
  Patch by Adam Turner.
* #12507: Add the :ref:`collapsible <collapsible-admonitions>` option
  to admonition directives.
  Patch by Chris Sewell.
* #8191, #8159: Add :rst:dir:`inheritance-diagram:include-subclasses` option to
  the :rst:dir:`inheritance-diagram` directive.
  Patch by Walter Dörwald.
* #11995: autodoc: Add support for :confval:`python_display_short_literal_types`.
  Patch by Bénédikt Tran and Adam Turner.
* #13163: Always print the full context when Sphinx encounters an internal error.
  Patch by Kevin Deldycke and Adam Turner.
* #13105: Introduce the :rst:role:`py:deco` role to cross-reference decorator
  functions and methods in the Python domain.
  Patch by Adam Turner.
* #9169: Add the :confval:`intersphinx_resolve_self` option
  to resolve an intersphinx reference to the current project.
  Patch by Jakob Lykke Andersen and Adam Turner.
* #11280: Add ability to skip a particular section using the ``no-search`` class.
  Patch by Will Lachance.
* #13326: Remove hardcoding from handling :class:`~sphinx.addnodes.productionlist`
  nodes in all writers, to improve flexibility.
  Patch by Adam Turner.

Bugs fixed
----------

* #12463: autosummary: Respect an empty module ``__all__``.
  Patch by Valentin Pratz
* #13060: HTML Search: use ``Map`` to store per-file term scores.
  Patch by James Addison
* #13130: LaTeX docs: ``pdflatex`` index creation may fail for index entries
  in French.  See :confval:`latex_use_xindy`.
  Patch by Jean-François B.
* #13152: LaTeX: fix a typo from v7.4.0 in a default for ``\sphinxboxsetup``.
  Patch by Jean-François B.
* #13096: HTML Search: check that query terms exist as properties in
  term indices before accessing them.
* #11233: linkcheck: match redirect URIs against :confval:`linkcheck_ignore` by
  overriding session-level ``requests.get_redirect_target``.
* #13195: viewcode: Fix issue where import paths differ from the directory
  structure.
  Patch by Ben Egan and Adam Turner.
* #13188: autodoc: fix detection of class methods implemented in C.
  Patch by Bénédikt Tran.
* #1810: Always copy static files when building, regardless of whether
  any documents have changed since the previous build.
  Patch by Adam Turner.
* #13201: autodoc: fix ordering of members when using ``groupwise``
  for :confval:`autodoc_member_order`. Class methods are now rendered
  before static methods, which themselves are rendered before regular
  methods and attributes.
  Patch by Bénédikt Tran.
* #12975: Avoid rendering a trailing comma in C and C++ multi-line signatures.
* #13178: autodoc: Fix resolution for ``pathlib`` types.
  Patch by Adam Turner.
* #13136: autodoc: Correctly handle multiple inheritance.
  Patch by Pavel Holica
* #13273, #13318: Properly convert command-line overrides for Boolean types.
  Patch by Adam Turner.
* #13302, #13319: Use the correct indentation for continuation lines
  in :rst:dir:`productionlist` directives.
  Patch by Adam Turner.
* #13328: Fix parsing of PEP 695 functions with return annotations.
  Patch by Bénédikt Tran. Initial work by Arash Badie-Modiri.

Testing
-------

* #13224: Correctness fixup for ``test_html_multi_line_copyright``.
  Patch by Colin Watson, applied by James Addison.
