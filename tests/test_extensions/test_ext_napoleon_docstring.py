"""Tests for :py:mod:`sphinx.ext.napoleon.docstring` module."""

from __future__ import annotations

import re
import zlib
from collections import namedtuple
from inspect import cleandoc
from itertools import product
from textwrap import dedent
from unittest import mock

import pytest

from sphinx.ext.intersphinx._load import load_mappings, validate_intersphinx_mapping
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import (
    GoogleDocstring,
    NumpyDocstring,
    _convert_type_spec,
    _recombine_set_tokens,
    _token_type,
    _tokenize_type_spec,
)
from sphinx.testing.util import etree_parse

from tests.test_extensions.ext_napoleon_pep526_data_google import PEP526GoogleClass
from tests.test_extensions.ext_napoleon_pep526_data_numpy import (
    PEP526NumpyClass,
    PEP526NumpyDontUseAttrTypeForParam,
)


class NamedtupleSubclass(namedtuple('NamedtupleSubclass', ('attr1', 'attr2'))):  # NoQA: PYI024
    """Sample namedtuple subclass

    Attributes
    ----------
    attr1 : Arbitrary type
        Quick description of attr1
    attr2 : Another arbitrary type
        Quick description of attr2
    attr3 : Type

        Adds a newline after the type

    """

    # To avoid creating a dict, as a namedtuple doesn't have it:
    __slots__ = ()

    def __new__(cls, attr1, attr2=None):
        return super().__new__(cls, attr1, attr2)


class TestNamedtupleSubclass:
    def test_attributes_docstring(self):
        config = Config()
        actual = NumpyDocstring(
            cleandoc(NamedtupleSubclass.__doc__),
            config=config,
            app=None,
            what='class',
            name='NamedtupleSubclass',
            obj=NamedtupleSubclass,
        )
        expected = """\
Sample namedtuple subclass

.. attribute:: attr1

   Quick description of attr1

   :type: Arbitrary type

.. attribute:: attr2

   Quick description of attr2

   :type: Another arbitrary type

.. attribute:: attr3

   Adds a newline after the type

   :type: Type
"""

        assert str(actual) == expected


class TestInlineAttribute:
    inline_google_docstring = (
        'inline description with '
        '``a : in code``, '
        'a :ref:`reference`, '
        'a `link <https://foo.bar>`_, '
        'a :meta public:, '
        'a :meta field: value and '
        'an host:port and HH:MM strings.'
    )

    @staticmethod
    def _docstring(source):
        rst = GoogleDocstring(
            source, config=Config(), app=None, what='attribute', name='some_data', obj=0
        )
        return str(rst)

    def test_class_data_member(self):
        source = 'data member description:\n\n- a: b'
        actual = self._docstring(source).splitlines()
        assert actual == ['data member description:', '', '- a: b']

    def test_class_data_member_inline(self):
        source = f'CustomType: {self.inline_google_docstring}'
        actual = self._docstring(source).splitlines()
        assert actual == [self.inline_google_docstring, '', ':type: CustomType']

    def test_class_data_member_inline_no_type(self):
        source = self.inline_google_docstring
        actual = self._docstring(source).splitlines()
        assert actual == [source]

    def test_class_data_member_inline_ref_in_type(self):
        source = f':py:class:`int`: {self.inline_google_docstring}'
        actual = self._docstring(source).splitlines()
        assert actual == [self.inline_google_docstring, '', ':type: :py:class:`int`']


class TestGoogleDocstring:
    docstrings = [
        (
            """Single line summary""",
            """Single line summary""",
        ),
        (
            """
        Single line summary

        Extended description

        """,
            """
        Single line summary

        Extended description
        """,
        ),
        (
            """
        Single line summary

        Args:
          arg1(str):Extended
            description of arg1
        """,
            """
        Single line summary

        :Parameters: **arg1** (*str*) -- Extended
                     description of arg1
        """,
        ),
        (
            """
        Single line summary

        Args:
          arg1(str):Extended
            description of arg1
          arg2 ( int ) : Extended
            description of arg2

        Keyword Args:
          kwarg1(str):Extended
            description of kwarg1
          kwarg2 ( int ) : Extended
            description of kwarg2""",
            """
        Single line summary

        :Parameters: * **arg1** (*str*) -- Extended
                       description of arg1
                     * **arg2** (*int*) -- Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (*str*) -- Extended
                              description of kwarg1
                            * **kwarg2** (*int*) -- Extended
                              description of kwarg2
        """,
        ),
        (
            """
        Single line summary

        Arguments:
          arg1(str):Extended
            description of arg1
          arg2 ( int ) : Extended
            description of arg2

        Keyword Arguments:
          kwarg1(str):Extended
            description of kwarg1
          kwarg2 ( int ) : Extended
            description of kwarg2""",
            """
        Single line summary

        :Parameters: * **arg1** (*str*) -- Extended
                       description of arg1
                     * **arg2** (*int*) -- Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (*str*) -- Extended
                              description of kwarg1
                            * **kwarg2** (*int*) -- Extended
                              description of kwarg2
        """,
        ),
        (
            """
        Single line summary

        Return:
          str:Extended
          description of return value
        """,
            """
        Single line summary

        :returns: *str* -- Extended
                  description of return value
        """,
        ),
        (
            """
        Single line summary

        Returns:
          str:Extended
          description of return value
        """,
            """
        Single line summary

        :returns: *str* -- Extended
                  description of return value
        """,
        ),
        (
            """
        Single line summary

        Returns:
          Extended
          description of return value
        """,
            """
        Single line summary

        :returns: Extended
                  description of return value
        """,
        ),
        (
            """
        Single line summary

        Returns:
          Extended
        """,
            """
        Single line summary

        :returns: Extended
        """,
        ),
        (
            """
        Single line summary

        Args:
          arg1(str):Extended
            description of arg1
          *args: Variable length argument list.
          **kwargs: Arbitrary keyword arguments.
        """,
            """
        Single line summary

        :Parameters: * **arg1** (*str*) -- Extended
                       description of arg1
                     * **\\*args** -- Variable length argument list.
                     * **\\*\\*kwargs** -- Arbitrary keyword arguments.
        """,
        ),
        (
            """
        Single line summary

        Args:
          arg1 (list(int)): Description
          arg2 (list[int]): Description
          arg3 (dict(str, int)): Description
          arg4 (dict[str, int]): Description
        """,
            """
        Single line summary

        :Parameters: * **arg1** (*list(int)*) -- Description
                     * **arg2** (*list[int]*) -- Description
                     * **arg3** (*dict(str, int)*) -- Description
                     * **arg4** (*dict[str, int]*) -- Description
        """,
        ),
        (
            """
        Single line summary

        Receive:
          arg1 (list(int)): Description
          arg2 (list[int]): Description
        """,
            """
        Single line summary

        :Receives: * **arg1** (*list(int)*) -- Description
                   * **arg2** (*list[int]*) -- Description
        """,
        ),
        (
            """
        Single line summary

        Receives:
          arg1 (list(int)): Description
          arg2 (list[int]): Description
        """,
            """
        Single line summary

        :Receives: * **arg1** (*list(int)*) -- Description
                   * **arg2** (*list[int]*) -- Description
        """,
        ),
        (
            """
        Single line summary

        Yield:
          str:Extended
          description of yielded value
        """,
            """
        Single line summary

        :Yields: *str* -- Extended
                 description of yielded value
        """,
        ),
        (
            """
        Single line summary

        Yields:
          Extended
          description of yielded value
        """,
            """
        Single line summary

        :Yields: Extended
                 description of yielded value
        """,
        ),
        (
            """
        Single line summary

        Args:

          arg1 (list of str): Extended
              description of arg1.
          arg2 (tuple of int): Extended
              description of arg2.
          arg3 (tuple of list of float): Extended
              description of arg3.
          arg4 (int, float, or list of bool): Extended
              description of arg4.
          arg5 (list of int, float, or bool): Extended
              description of arg5.
          arg6 (list of int or float): Extended
              description of arg6.
        """,
            """
        Single line summary

        :Parameters: * **arg1** (*list of str*) -- Extended
                       description of arg1.
                     * **arg2** (*tuple of int*) -- Extended
                       description of arg2.
                     * **arg3** (*tuple of list of float*) -- Extended
                       description of arg3.
                     * **arg4** (*int, float, or list of bool*) -- Extended
                       description of arg4.
                     * **arg5** (*list of int, float, or bool*) -- Extended
                       description of arg5.
                     * **arg6** (*list of int or float*) -- Extended
                       description of arg6.
        """,
        ),
    ]

    def test_sphinx_admonitions(self):
        admonition_map = {
            'Attention': 'attention',
            'Caution': 'caution',
            'Danger': 'danger',
            'Error': 'error',
            'Hint': 'hint',
            'Important': 'important',
            'Note': 'note',
            'Tip': 'tip',
            'Todo': 'todo',
            'Warning': 'warning',
            'Warnings': 'warning',
        }
        config = Config()
        for section, admonition in admonition_map.items():
            # Multiline
            actual = GoogleDocstring(
                f'{section}:\n'
                '    this is the first line\n'
                '\n'
                '    and this is the second line\n',
                config,
            )
            expect = (
                f'.. {admonition}::\n'
                '\n'
                '   this is the first line\n'
                '   \n'
                '   and this is the second line\n'
            )
            assert str(actual) == expect

            # Single line
            actual = GoogleDocstring(f'{section}:\n    this is a single line\n', config)
            expect = f'.. {admonition}:: this is a single line\n'
            assert str(actual) == expect

    def test_docstrings(self):
        config = Config(
            napoleon_use_param=False,
            napoleon_use_rtype=False,
            napoleon_use_keyword=False,
        )
        for docstring, expected in self.docstrings:
            actual = GoogleDocstring(dedent(docstring), config)
            expected = dedent(expected)
            assert str(actual) == expected

    def test_parameters_with_class_reference(self):
        docstring = """\
Construct a new XBlock.

This class should only be used by runtimes.

Arguments:
    runtime (:py:class:`~typing.Dict`\\[:py:class:`int`,:py:class:`str`\\]): Use it to
        access the environment. It is available in XBlock code
        as ``self.runtime``.

    field_data (:py:class:`FieldData`): Interface used by the XBlock
        fields to access their data from wherever it is persisted.

    scope_ids (:py:class:`ScopeIds`): Identifiers needed to resolve scopes.

"""

        actual = GoogleDocstring(docstring)
        expected = """\
Construct a new XBlock.

This class should only be used by runtimes.

:param runtime: Use it to
                access the environment. It is available in XBlock code
                as ``self.runtime``.
:type runtime: :py:class:`~typing.Dict`\\[:py:class:`int`,:py:class:`str`\\]
:param field_data: Interface used by the XBlock
                   fields to access their data from wherever it is persisted.
:type field_data: :py:class:`FieldData`
:param scope_ids: Identifiers needed to resolve scopes.
:type scope_ids: :py:class:`ScopeIds`
"""
        assert str(actual) == expected

    def test_attributes_with_class_reference(self):
        docstring = """\
Attributes:
    in_attr(:py:class:`numpy.ndarray`): super-dooper attribute
"""

        actual = GoogleDocstring(docstring)
        expected = """\
.. attribute:: in_attr

   super-dooper attribute

   :type: :py:class:`numpy.ndarray`
"""
        assert str(actual) == expected

        docstring = """\
Attributes:
    in_attr(numpy.ndarray): super-dooper attribute
"""

        actual = GoogleDocstring(docstring)
        expected = """\
.. attribute:: in_attr

   super-dooper attribute

   :type: numpy.ndarray
"""

    def test_attributes_with_use_ivar(self):
        docstring = """\
Attributes:
    foo (int): blah blah
    bar (str): blah blah
"""

        config = Config(napoleon_use_ivar=True)
        actual = GoogleDocstring(docstring, config, obj=self.__class__)
        expected = """\
:ivar foo: blah blah
:vartype foo: int
:ivar bar: blah blah
:vartype bar: str
"""
        assert str(actual) == expected

    def test_code_block_in_returns_section(self):
        docstring = """
Returns:
    foobar: foo::

        codecode
        codecode
"""
        expected = """
:returns:

          foo::

              codecode
              codecode
:rtype: foobar
"""
        actual = GoogleDocstring(docstring)
        assert str(actual) == expected

    def test_colon_in_return_type(self):
        docstring = """Example property.

Returns:
    :py:class:`~.module.submodule.SomeClass`: an example instance
    if available, None if not available.
"""
        expected = """Example property.

:returns: an example instance
          if available, None if not available.
:rtype: :py:class:`~.module.submodule.SomeClass`
"""
        actual = GoogleDocstring(docstring)
        assert str(actual) == expected

    def test_xrefs_in_return_type(self):
        docstring = """Example Function

Returns:
    :py:class:`numpy.ndarray`: A :math:`n \\times 2` array containing
    a bunch of math items
"""
        expected = """Example Function

:returns: A :math:`n \\times 2` array containing
          a bunch of math items
:rtype: :py:class:`numpy.ndarray`
"""
        actual = GoogleDocstring(docstring)
        assert str(actual) == expected

    def test_raises_types(self):
        docstrings = [
            (
                """
Example Function

Raises:
    RuntimeError:
        A setting wasn't specified, or was invalid.
    ValueError:
        Something something value error.
    :py:class:`AttributeError`
        errors for missing attributes.
    ~InvalidDimensionsError
        If the dimensions couldn't be parsed.
    `InvalidArgumentsError`
        If the arguments are invalid.
    :py:exc:`~ValueError`
        If the arguments are wrong.

""",
                """
Example Function

:raises RuntimeError: A setting wasn't specified, or was invalid.
:raises ValueError: Something something value error.
:raises AttributeError: errors for missing attributes.
:raises ~InvalidDimensionsError: If the dimensions couldn't be parsed.
:raises InvalidArgumentsError: If the arguments are invalid.
:raises ~ValueError: If the arguments are wrong.
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    InvalidDimensionsError

""",
                """
Example Function

:raises InvalidDimensionsError:
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    Invalid Dimensions Error

""",
                """
Example Function

:raises Invalid Dimensions Error:
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    Invalid Dimensions Error: With description

""",
                """
Example Function

:raises Invalid Dimensions Error: With description
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    InvalidDimensionsError: If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises InvalidDimensionsError: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    Invalid Dimensions Error: If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises Invalid Dimensions Error: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises If the dimensions couldn't be parsed.:
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    :py:class:`exc.InvalidDimensionsError`

""",
                """
Example Function

:raises exc.InvalidDimensionsError:
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    :py:class:`exc.InvalidDimensionsError`: If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    :py:class:`exc.InvalidDimensionsError`: If the dimensions couldn't be parsed,
       then a :py:class:`exc.InvalidDimensionsError` will be raised.

""",
                """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed,
    then a :py:class:`exc.InvalidDimensionsError` will be raised.
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    :py:class:`exc.InvalidDimensionsError`: If the dimensions couldn't be parsed.
    :py:class:`exc.InvalidArgumentsError`: If the arguments are invalid.

""",
                """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
:raises exc.InvalidArgumentsError: If the arguments are invalid.
""",
            ),
            ################################
            (
                """
Example Function

Raises:
    :py:class:`exc.InvalidDimensionsError`
    :py:class:`exc.InvalidArgumentsError`

""",
                """
Example Function

:raises exc.InvalidDimensionsError:
:raises exc.InvalidArgumentsError:
""",
            ),
        ]
        for docstring, expected in docstrings:
            actual = GoogleDocstring(docstring)
            assert str(actual) == expected

    def test_kwargs_in_arguments(self):
        docstring = """Allows to create attributes binded to this device.

Some other paragraph.

Code sample for usage::

  dev.bind(loopback=Loopback)
  dev.loopback.configure()

Arguments:
  **kwargs: name/class pairs that will create resource-managers
    bound as instance attributes to this instance. See code
    example above.
"""
        expected = """Allows to create attributes binded to this device.

Some other paragraph.

Code sample for usage::

  dev.bind(loopback=Loopback)
  dev.loopback.configure()

:param \\*\\*kwargs: name/class pairs that will create resource-managers
                   bound as instance attributes to this instance. See code
                   example above.
"""
        actual = GoogleDocstring(docstring)
        assert str(actual) == expected

    def test_section_header_formatting(self):
        docstrings = [
            (
                """
Summary line

Example:
    Multiline reStructuredText
    literal code block

""",
                """
Summary line

.. rubric:: Example

Multiline reStructuredText
literal code block
""",
            ),
            ################################
            (
                """
Summary line

Example::

    Multiline reStructuredText
    literal code block

""",
                """
Summary line

Example::

    Multiline reStructuredText
    literal code block
""",
            ),
            ################################
            (
                """
Summary line

:Example:

    Multiline reStructuredText
    literal code block

""",
                """
Summary line

:Example:

    Multiline reStructuredText
    literal code block
""",
            ),
        ]
        for docstring, expected in docstrings:
            actual = GoogleDocstring(docstring)
            assert str(actual) == expected

    def test_list_in_parameter_description(self):
        docstring = """One line summary.

Parameters:
    no_list (int):
    one_bullet_empty (int):
        *
    one_bullet_single_line (int):
        - first line
    one_bullet_two_lines (int):
        +   first line
            continued
    two_bullets_single_line (int):
        -  first line
        -  second line
    two_bullets_two_lines (int):
        * first line
          continued
        * second line
          continued
    one_enumeration_single_line (int):
        1.  first line
    one_enumeration_two_lines (int):
        1)   first line
             continued
    two_enumerations_one_line (int):
        (iii) first line
        (iv) second line
    two_enumerations_two_lines (int):
        a. first line
           continued
        b. second line
           continued
    one_definition_one_line (int):
        item 1
            first line
    one_definition_two_lines (int):
        item 1
            first line
            continued
    two_definitions_one_line (int):
        item 1
            first line
        item 2
            second line
    two_definitions_two_lines (int):
        item 1
            first line
            continued
        item 2
            second line
            continued
    one_definition_blank_line (int):
        item 1

            first line

            extra first line

    two_definitions_blank_lines (int):
        item 1

            first line

            extra first line

        item 2

            second line

            extra second line

    definition_after_inline_text (int): text line

        item 1
            first line

    definition_after_normal_text (int):
        text line

        item 1
            first line
"""

        expected = """One line summary.

:param no_list:
:type no_list: int
:param one_bullet_empty:
                         *
:type one_bullet_empty: int
:param one_bullet_single_line:
                               - first line
:type one_bullet_single_line: int
:param one_bullet_two_lines:
                             +   first line
                                 continued
:type one_bullet_two_lines: int
:param two_bullets_single_line:
                                -  first line
                                -  second line
:type two_bullets_single_line: int
:param two_bullets_two_lines:
                              * first line
                                continued
                              * second line
                                continued
:type two_bullets_two_lines: int
:param one_enumeration_single_line:
                                    1.  first line
:type one_enumeration_single_line: int
:param one_enumeration_two_lines:
                                  1)   first line
                                       continued
:type one_enumeration_two_lines: int
:param two_enumerations_one_line:
                                  (iii) first line
                                  (iv) second line
:type two_enumerations_one_line: int
:param two_enumerations_two_lines:
                                   a. first line
                                      continued
                                   b. second line
                                      continued
:type two_enumerations_two_lines: int
:param one_definition_one_line:
                                item 1
                                    first line
:type one_definition_one_line: int
:param one_definition_two_lines:
                                 item 1
                                     first line
                                     continued
:type one_definition_two_lines: int
:param two_definitions_one_line:
                                 item 1
                                     first line
                                 item 2
                                     second line
:type two_definitions_one_line: int
:param two_definitions_two_lines:
                                  item 1
                                      first line
                                      continued
                                  item 2
                                      second line
                                      continued
:type two_definitions_two_lines: int
:param one_definition_blank_line:
                                  item 1

                                      first line

                                      extra first line
:type one_definition_blank_line: int
:param two_definitions_blank_lines:
                                    item 1

                                        first line

                                        extra first line

                                    item 2

                                        second line

                                        extra second line
:type two_definitions_blank_lines: int
:param definition_after_inline_text: text line

                                     item 1
                                         first line
:type definition_after_inline_text: int
:param definition_after_normal_text: text line

                                     item 1
                                         first line
:type definition_after_normal_text: int
"""
        config = Config(napoleon_use_param=True)
        actual = GoogleDocstring(docstring, config)
        assert str(actual) == expected

        expected = """One line summary.

:Parameters: * **no_list** (*int*)
             * **one_bullet_empty** (*int*) --

               *
             * **one_bullet_single_line** (*int*) --

               - first line
             * **one_bullet_two_lines** (*int*) --

               +   first line
                   continued
             * **two_bullets_single_line** (*int*) --

               -  first line
               -  second line
             * **two_bullets_two_lines** (*int*) --

               * first line
                 continued
               * second line
                 continued
             * **one_enumeration_single_line** (*int*) --

               1.  first line
             * **one_enumeration_two_lines** (*int*) --

               1)   first line
                    continued
             * **two_enumerations_one_line** (*int*) --

               (iii) first line
               (iv) second line
             * **two_enumerations_two_lines** (*int*) --

               a. first line
                  continued
               b. second line
                  continued
             * **one_definition_one_line** (*int*) --

               item 1
                   first line
             * **one_definition_two_lines** (*int*) --

               item 1
                   first line
                   continued
             * **two_definitions_one_line** (*int*) --

               item 1
                   first line
               item 2
                   second line
             * **two_definitions_two_lines** (*int*) --

               item 1
                   first line
                   continued
               item 2
                   second line
                   continued
             * **one_definition_blank_line** (*int*) --

               item 1

                   first line

                   extra first line
             * **two_definitions_blank_lines** (*int*) --

               item 1

                   first line

                   extra first line

               item 2

                   second line

                   extra second line
             * **definition_after_inline_text** (*int*) -- text line

               item 1
                   first line
             * **definition_after_normal_text** (*int*) -- text line

               item 1
                   first line
"""
        config = Config(napoleon_use_param=False)
        actual = GoogleDocstring(docstring, config)
        assert str(actual) == expected

    def test_custom_generic_sections(self):
        docstrings = (
            (
                """\
Really Important Details:
    You should listen to me!
""",
                """.. rubric:: Really Important Details

You should listen to me!
""",
            ),
            (
                """\
Sooper Warning:
    Stop hitting yourself!
""",
                """:Warns: **Stop hitting yourself!**
""",
            ),
            (
                """\
Params Style:
    arg1 (int): Description of arg1
    arg2 (str): Description of arg2

""",
                """\
:Params Style: * **arg1** (*int*) -- Description of arg1
               * **arg2** (*str*) -- Description of arg2
""",
            ),
            (
                """\
Returns Style:
    description of custom section

""",
                """:Returns Style: description of custom section
""",
            ),
        )

        test_config = Config(
            napoleon_custom_sections=[
                'Really Important Details',
                ('Sooper Warning', 'warns'),
                ('Params Style', 'params_style'),
                ('Returns Style', 'returns_style'),
            ]
        )

        for docstring, expected in docstrings:
            actual = GoogleDocstring(docstring, test_config)
            assert str(actual) == expected

    def test_noindex(self):
        docstring = """
Attributes:
    arg
        description

Methods:
    func(i, j)
        description
"""

        expected = """
.. attribute:: arg
   :no-index:

   description

.. method:: func(i, j)
   :no-index:

   
   description
"""  # NoQA: W293
        config = Config()
        actual = GoogleDocstring(
            docstring,
            config=config,
            app=None,
            what='module',
            options={'no-index': True},
        )
        assert str(actual) == expected

    def test_keywords_with_types(self):
        docstring = """\
Do as you please

Keyword Args:
    gotham_is_yours (None): shall interfere.
"""
        actual = GoogleDocstring(docstring)
        expected = """\
Do as you please

:keyword gotham_is_yours: shall interfere.
:kwtype gotham_is_yours: None
"""
        assert str(actual) == expected

    def test_pep526_annotations(self):
        # Test class attributes annotations
        config = Config(
            napoleon_attr_annotations=True,
        )
        actual = GoogleDocstring(
            cleandoc(PEP526GoogleClass.__doc__),
            config,
            app=None,
            what='class',
            obj=PEP526GoogleClass,
        )
        expected = """\
Sample class with PEP 526 annotations and google docstring.

.. attribute:: attr1

   Attr1 description.

   :type: int

.. attribute:: attr2

   Attr2 description.

   :type: str
"""
        assert str(actual) == expected

    def test_preprocess_types(self):
        docstring = """\
Do as you please

Yield:
   str:Extended
"""
        actual = GoogleDocstring(docstring)
        expected = """\
Do as you please

:Yields: *str* -- Extended
"""
        assert str(actual) == expected

        config = Config(napoleon_preprocess_types=True)
        actual = GoogleDocstring(docstring, config)
        expected = """\
Do as you please

:Yields: :py:class:`str` -- Extended
"""
        assert str(actual) == expected


class TestNumpyDocstring:
    docstrings = [
        (
            """Single line summary""",
            """Single line summary""",
        ),
        (
            """
        Single line summary

        Extended description

        """,
            """
        Single line summary

        Extended description
        """,
        ),
        (
            """
        Single line summary

        Parameters
        ----------
        arg1:str
            Extended
            description of arg1
        """,
            """
        Single line summary

        :Parameters: **arg1** (:py:class:`str`) -- Extended
                     description of arg1
        """,
        ),
        (
            """
        Single line summary

        Parameters
        ----------
        arg1:str
            Extended
            description of arg1
        arg2 : int
            Extended
            description of arg2

        Keyword Arguments
        -----------------
          kwarg1:str
              Extended
              description of kwarg1
          kwarg2 : int
              Extended
              description of kwarg2
        """,
            """
        Single line summary

        :Parameters: * **arg1** (:py:class:`str`) -- Extended
                       description of arg1
                     * **arg2** (:py:class:`int`) -- Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (:py:class:`str`) -- Extended
                              description of kwarg1
                            * **kwarg2** (:py:class:`int`) -- Extended
                              description of kwarg2
        """,
        ),
        (
            """
        Single line summary

        Return
        ------
        str
            Extended
            description of return value
        """,
            """
        Single line summary

        :returns: :py:class:`str` -- Extended
                  description of return value
        """,
        ),
        (
            """
        Single line summary

        Returns
        -------
        str
            Extended
            description of return value
        """,
            """
        Single line summary

        :returns: :py:class:`str` -- Extended
                  description of return value
        """,
        ),
        (
            """
        Single line summary

        Parameters
        ----------
        arg1:str
             Extended description of arg1
        *args:
            Variable length argument list.
        **kwargs:
            Arbitrary keyword arguments.
        """,
            """
        Single line summary

        :Parameters: * **arg1** (:py:class:`str`) -- Extended description of arg1
                     * **\\*args** -- Variable length argument list.
                     * **\\*\\*kwargs** -- Arbitrary keyword arguments.
        """,
        ),
        (
            """
        Single line summary

        Parameters
        ----------
        arg1:str
             Extended description of arg1
        *args, **kwargs:
            Variable length argument list and arbitrary keyword arguments.
        """,
            """
        Single line summary

        :Parameters: * **arg1** (:py:class:`str`) -- Extended description of arg1
                     * **\\*args, \\*\\*kwargs** -- Variable length argument list and arbitrary keyword arguments.
        """,
        ),
        (
            """
        Single line summary

        Receive
        -------
        arg1:str
            Extended
            description of arg1
        arg2 : int
            Extended
            description of arg2
        """,
            """
        Single line summary

        :Receives: * **arg1** (:py:class:`str`) -- Extended
                     description of arg1
                   * **arg2** (:py:class:`int`) -- Extended
                     description of arg2
        """,
        ),
        (
            """
        Single line summary

        Receives
        --------
        arg1:str
            Extended
            description of arg1
        arg2 : int
            Extended
            description of arg2
        """,
            """
        Single line summary

        :Receives: * **arg1** (:py:class:`str`) -- Extended
                     description of arg1
                   * **arg2** (:py:class:`int`) -- Extended
                     description of arg2
        """,
        ),
        (
            """
        Single line summary

        Yield
        -----
        str
            Extended
            description of yielded value
        """,
            """
        Single line summary

        :Yields: :py:class:`str` -- Extended
                 description of yielded value
        """,
        ),
        (
            """
        Single line summary

        Yields
        ------
        str
            Extended
            description of yielded value
        """,
            """
        Single line summary

        :Yields: :py:class:`str` -- Extended
                 description of yielded value
        """,
        ),
    ]

    def test_sphinx_admonitions(self):
        admonition_map = {
            'Attention': 'attention',
            'Caution': 'caution',
            'Danger': 'danger',
            'Error': 'error',
            'Hint': 'hint',
            'Important': 'important',
            'Note': 'note',
            'Tip': 'tip',
            'Todo': 'todo',
            'Warning': 'warning',
            'Warnings': 'warning',
        }
        config = Config()
        for section, admonition in admonition_map.items():
            # Multiline
            underline = '-' * len(section)
            actual = NumpyDocstring(
                f'{section}\n'
                f'{underline}\n'
                '    this is the first line\n'
                '\n'
                '    and this is the second line\n',
                config,
            )
            expect = (
                f'.. {admonition}::\n'
                '\n'
                '   this is the first line\n'
                '   \n'
                '   and this is the second line\n'
            )
            assert str(actual) == expect

            # Single line
            actual = NumpyDocstring(
                f'{section}\n{"-" * len(section)}\n    this is a single line\n',
                config,
            )
            expect = f'.. {admonition}:: this is a single line\n'
            assert str(actual) == expect

    def test_docstrings(self):
        config = Config(
            napoleon_use_param=False,
            napoleon_use_rtype=False,
            napoleon_use_keyword=False,
            napoleon_preprocess_types=True,
        )
        for docstring, expected in self.docstrings:
            actual = NumpyDocstring(dedent(docstring), config)
            expected = dedent(expected)
            assert str(actual) == expected

    def test_type_preprocessor(self):
        docstring = dedent("""
        Single line summary

        Parameters
        ----------
        arg1:str
            Extended
            description of arg1
        """)

        config = Config(napoleon_preprocess_types=False, napoleon_use_param=False)
        actual = NumpyDocstring(docstring, config)
        expected = dedent("""
        Single line summary

        :Parameters: **arg1** (*str*) -- Extended
                     description of arg1
        """)
        assert str(actual) == expected

    def test_parameters_with_class_reference(self):
        docstring = """\
Parameters
----------
param1 : :class:`MyClass <name.space.MyClass>` instance

Other Parameters
----------------
param2 : :class:`MyClass <name.space.MyClass>` instance

"""

        config = Config(napoleon_use_param=False)
        actual = NumpyDocstring(docstring, config)
        expected = """\
:Parameters: **param1** (:class:`MyClass <name.space.MyClass>` instance)

:Other Parameters: **param2** (:class:`MyClass <name.space.MyClass>` instance)
"""
        assert str(actual) == expected

        config = Config(napoleon_use_param=True)
        actual = NumpyDocstring(docstring, config)
        expected = """\
:param param1:
:type param1: :class:`MyClass <name.space.MyClass>` instance

:param param2:
:type param2: :class:`MyClass <name.space.MyClass>` instance
"""
        assert str(actual) == expected

    def test_multiple_parameters(self):
        docstring = """\
Parameters
----------
x1, x2 : array_like
    Input arrays, description of ``x1``, ``x2``.

"""

        config = Config(napoleon_use_param=False)
        actual = NumpyDocstring(docstring, config)
        expected = """\
:Parameters: **x1, x2** (*array_like*) -- Input arrays, description of ``x1``, ``x2``.
"""
        assert str(actual) == expected

        config = Config(napoleon_use_param=True)
        actual = NumpyDocstring(dedent(docstring), config)
        expected = """\
:param x1: Input arrays, description of ``x1``, ``x2``.
:type x1: array_like
:param x2: Input arrays, description of ``x1``, ``x2``.
:type x2: array_like
"""
        assert str(actual) == expected

    def test_parameters_without_class_reference(self):
        docstring = """\
Parameters
----------
param1 : MyClass instance

"""

        config = Config(napoleon_use_param=False)
        actual = NumpyDocstring(docstring, config)
        expected = """\
:Parameters: **param1** (*MyClass instance*)
"""
        assert str(actual) == expected

        config = Config(napoleon_use_param=True)
        actual = NumpyDocstring(dedent(docstring), config)
        expected = """\
:param param1:
:type param1: MyClass instance
"""
        assert str(actual) == expected

    def test_see_also_refs(self):
        docstring = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

See Also
--------
some, other, funcs
otherfunc : relationship

"""

        actual = NumpyDocstring(docstring)

        expected = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::

   :py:obj:`some`, :py:obj:`other`, :py:obj:`funcs`
   \n\
   :py:obj:`otherfunc`
       relationship
"""
        assert str(actual) == expected

        docstring = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

See Also
--------
some, other, funcs
otherfunc : relationship

"""

        config = Config()
        app = mock.Mock()
        actual = NumpyDocstring(docstring, config, app, 'method')

        expected = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::

   :py:obj:`some`, :py:obj:`other`, :py:obj:`funcs`
   \n\
   :py:obj:`otherfunc`
       relationship
"""
        assert str(actual) == expected

        docstring = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

See Also
--------
some, other, :func:`funcs`
otherfunc : relationship

"""
        translations = {
            'other': 'MyClass.other',
            'otherfunc': ':func:`~my_package.otherfunc`',
        }
        config = Config(napoleon_type_aliases=translations)
        app = mock.Mock()
        actual = NumpyDocstring(docstring, config, app, 'method')

        expected = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::

   :py:obj:`some`, :py:obj:`MyClass.other`, :func:`funcs`
   \n\
   :func:`~my_package.otherfunc`
       relationship
"""
        assert str(actual) == expected

    def test_colon_in_return_type(self):
        docstring = """
Summary

Returns
-------
:py:class:`~my_mod.my_class`
    an instance of :py:class:`~my_mod.my_class`
"""

        expected = """
Summary

:returns: an instance of :py:class:`~my_mod.my_class`
:rtype: :py:class:`~my_mod.my_class`
"""

        config = Config()
        app = mock.Mock()
        actual = NumpyDocstring(docstring, config, app, 'method')

        assert str(actual) == expected

    def test_underscore_in_attribute(self):
        docstring = """
Attributes
----------

arg_ : type
    some description
"""

        expected = """
:ivar arg_: some description
:vartype arg_: type
"""

        config = Config(napoleon_use_ivar=True)
        app = mock.Mock()
        actual = NumpyDocstring(docstring, config, app, 'class')

        assert str(actual) == expected

    def test_underscore_in_attribute_strip_signature_backslash(self):
        docstring = """
Attributes
----------

arg_ : type
    some description
"""

        expected = """
:ivar arg\\_: some description
:vartype arg\\_: type
"""

        config = Config(napoleon_use_ivar=True)
        config.strip_signature_backslash = True
        app = mock.Mock()
        actual = NumpyDocstring(docstring, config, app, 'class')

        assert str(actual) == expected

    def test_return_types(self):
        docstring = dedent("""
            Returns
            -------
            DataFrame
                a dataframe
        """)
        expected = dedent("""
           :returns: a dataframe
           :rtype: :py:class:`~pandas.DataFrame`
        """)
        translations = {
            'DataFrame': '~pandas.DataFrame',
        }
        config = Config(
            napoleon_use_param=True,
            napoleon_use_rtype=True,
            napoleon_preprocess_types=True,
            napoleon_type_aliases=translations,
        )
        actual = NumpyDocstring(docstring, config)
        assert str(actual) == expected

    def test_yield_types(self):
        docstring = dedent("""
            Example Function

            Yields
            ------
            scalar or array-like
                The result of the computation
        """)
        expected = dedent("""
            Example Function

            :Yields: :term:`scalar` or :py:class:`array-like <numpy.ndarray>` -- The result of the computation
        """)
        translations = {
            'scalar': ':term:`scalar`',
            'array-like': ':py:class:`array-like <numpy.ndarray>`',
        }
        config = Config(
            napoleon_type_aliases=translations, napoleon_preprocess_types=True
        )
        app = mock.Mock()
        actual = NumpyDocstring(docstring, config, app, 'method')
        assert str(actual) == expected

    def test_raises_types(self):
        docstrings = [
            (
                """
Example Function

Raises
------
  RuntimeError

      A setting wasn't specified, or was invalid.
  ValueError

      Something something value error.

""",
                """
Example Function

:raises RuntimeError: A setting wasn't specified, or was invalid.
:raises ValueError: Something something value error.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
InvalidDimensionsError

""",
                """
Example Function

:raises InvalidDimensionsError:
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
Invalid Dimensions Error

""",
                """
Example Function

:raises Invalid Dimensions Error:
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
Invalid Dimensions Error
    With description

""",
                """
Example Function

:raises Invalid Dimensions Error: With description
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
InvalidDimensionsError
    If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises InvalidDimensionsError: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
Invalid Dimensions Error
    If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises Invalid Dimensions Error: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises If the dimensions couldn't be parsed.:
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`

""",
                """
Example Function

:raises exc.InvalidDimensionsError:
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
    If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
    If the dimensions couldn't be parsed,
    then a :class:`exc.InvalidDimensionsError` will be raised.

""",
                """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed,
    then a :class:`exc.InvalidDimensionsError` will be raised.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
    If the dimensions couldn't be parsed.
:class:`exc.InvalidArgumentsError`
    If the arguments are invalid.

""",
                """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
:raises exc.InvalidArgumentsError: If the arguments are invalid.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
CustomError
    If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises package.CustomError: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
AnotherError
    If the dimensions couldn't be parsed.

""",
                """
Example Function

:raises ~package.AnotherError: If the dimensions couldn't be parsed.
""",
            ),
            ################################
            (
                """
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
:class:`exc.InvalidArgumentsError`

""",
                """
Example Function

:raises exc.InvalidDimensionsError:
:raises exc.InvalidArgumentsError:
""",
            ),
        ]
        for docstring, expected in docstrings:
            translations = {
                'CustomError': 'package.CustomError',
                'AnotherError': ':py:exc:`~package.AnotherError`',
            }
            config = Config(
                napoleon_type_aliases=translations, napoleon_preprocess_types=True
            )
            app = mock.Mock()
            actual = NumpyDocstring(docstring, config, app, 'method')
            assert str(actual) == expected

    def test_xrefs_in_return_type(self):
        docstring = """
Example Function

Returns
-------
:class:`numpy.ndarray`
    A :math:`n \\times 2` array containing
    a bunch of math items
"""
        expected = """
Example Function

:returns: A :math:`n \\times 2` array containing
          a bunch of math items
:rtype: :class:`numpy.ndarray`
"""
        config = Config()
        app = mock.Mock()
        actual = NumpyDocstring(docstring, config, app, 'method')
        assert str(actual) == expected

    def test_section_header_underline_length(self):
        docstrings = [
            (
                """
Summary line

Example
-
Multiline example
body

""",
                """
Summary line

Example
-
Multiline example
body
""",
            ),
            ################################
            (
                """
Summary line

Example
--
Multiline example
body

""",
                """
Summary line

.. rubric:: Example

Multiline example
body
""",
            ),
            ################################
            (
                """
Summary line

Example
-------
Multiline example
body

""",
                """
Summary line

.. rubric:: Example

Multiline example
body
""",
            ),
            ################################
            (
                """
Summary line

Example
------------
Multiline example
body

""",
                """
Summary line

.. rubric:: Example

Multiline example
body
""",
            ),
        ]
        for docstring, expected in docstrings:
            actual = NumpyDocstring(docstring)
            assert str(actual) == expected

    def test_list_in_parameter_description(self):
        docstring = """One line summary.

Parameters
----------
no_list : int
one_bullet_empty : int
    *
one_bullet_single_line : int
    - first line
one_bullet_two_lines : int
    +   first line
        continued
two_bullets_single_line : int
    -  first line
    -  second line
two_bullets_two_lines : int
    * first line
      continued
    * second line
      continued
one_enumeration_single_line : int
    1.  first line
one_enumeration_two_lines : int
    1)   first line
         continued
two_enumerations_one_line : int
    (iii) first line
    (iv) second line
two_enumerations_two_lines : int
    a. first line
       continued
    b. second line
       continued
one_definition_one_line : int
    item 1
        first line
one_definition_two_lines : int
    item 1
        first line
        continued
two_definitions_one_line : int
    item 1
        first line
    item 2
        second line
two_definitions_two_lines : int
    item 1
        first line
        continued
    item 2
        second line
        continued
one_definition_blank_line : int
    item 1

        first line

        extra first line

two_definitions_blank_lines : int
    item 1

        first line

        extra first line

    item 2

        second line

        extra second line

definition_after_normal_text : int
    text line

    item 1
        first line
"""

        expected = """One line summary.

:param no_list:
:type no_list: int
:param one_bullet_empty:
                         *
:type one_bullet_empty: int
:param one_bullet_single_line:
                               - first line
:type one_bullet_single_line: int
:param one_bullet_two_lines:
                             +   first line
                                 continued
:type one_bullet_two_lines: int
:param two_bullets_single_line:
                                -  first line
                                -  second line
:type two_bullets_single_line: int
:param two_bullets_two_lines:
                              * first line
                                continued
                              * second line
                                continued
:type two_bullets_two_lines: int
:param one_enumeration_single_line:
                                    1.  first line
:type one_enumeration_single_line: int
:param one_enumeration_two_lines:
                                  1)   first line
                                       continued
:type one_enumeration_two_lines: int
:param two_enumerations_one_line:
                                  (iii) first line
                                  (iv) second line
:type two_enumerations_one_line: int
:param two_enumerations_two_lines:
                                   a. first line
                                      continued
                                   b. second line
                                      continued
:type two_enumerations_two_lines: int
:param one_definition_one_line:
                                item 1
                                    first line
:type one_definition_one_line: int
:param one_definition_two_lines:
                                 item 1
                                     first line
                                     continued
:type one_definition_two_lines: int
:param two_definitions_one_line:
                                 item 1
                                     first line
                                 item 2
                                     second line
:type two_definitions_one_line: int
:param two_definitions_two_lines:
                                  item 1
                                      first line
                                      continued
                                  item 2
                                      second line
                                      continued
:type two_definitions_two_lines: int
:param one_definition_blank_line:
                                  item 1

                                      first line

                                      extra first line
:type one_definition_blank_line: int
:param two_definitions_blank_lines:
                                    item 1

                                        first line

                                        extra first line

                                    item 2

                                        second line

                                        extra second line
:type two_definitions_blank_lines: int
:param definition_after_normal_text: text line

                                     item 1
                                         first line
:type definition_after_normal_text: int
"""
        config = Config(napoleon_use_param=True)
        actual = NumpyDocstring(docstring, config)
        assert str(actual) == expected

        expected = """One line summary.

:Parameters: * **no_list** (:py:class:`int`)
             * **one_bullet_empty** (:py:class:`int`) --

               *
             * **one_bullet_single_line** (:py:class:`int`) --

               - first line
             * **one_bullet_two_lines** (:py:class:`int`) --

               +   first line
                   continued
             * **two_bullets_single_line** (:py:class:`int`) --

               -  first line
               -  second line
             * **two_bullets_two_lines** (:py:class:`int`) --

               * first line
                 continued
               * second line
                 continued
             * **one_enumeration_single_line** (:py:class:`int`) --

               1.  first line
             * **one_enumeration_two_lines** (:py:class:`int`) --

               1)   first line
                    continued
             * **two_enumerations_one_line** (:py:class:`int`) --

               (iii) first line
               (iv) second line
             * **two_enumerations_two_lines** (:py:class:`int`) --

               a. first line
                  continued
               b. second line
                  continued
             * **one_definition_one_line** (:py:class:`int`) --

               item 1
                   first line
             * **one_definition_two_lines** (:py:class:`int`) --

               item 1
                   first line
                   continued
             * **two_definitions_one_line** (:py:class:`int`) --

               item 1
                   first line
               item 2
                   second line
             * **two_definitions_two_lines** (:py:class:`int`) --

               item 1
                   first line
                   continued
               item 2
                   second line
                   continued
             * **one_definition_blank_line** (:py:class:`int`) --

               item 1

                   first line

                   extra first line
             * **two_definitions_blank_lines** (:py:class:`int`) --

               item 1

                   first line

                   extra first line

               item 2

                   second line

                   extra second line
             * **definition_after_normal_text** (:py:class:`int`) -- text line

               item 1
                   first line
"""
        config = Config(napoleon_use_param=False, napoleon_preprocess_types=True)
        actual = NumpyDocstring(docstring, config)
        assert str(actual) == expected

    def test_token_type(self):
        tokens = (
            ('1', 'literal'),
            ('-4.6', 'literal'),
            ('2j', 'literal'),
            ("'string'", 'literal'),
            ('"another_string"', 'literal'),
            ('{1, 2}', 'literal'),
            ("{'va{ue', 'set'}", 'literal'),
            ('optional', 'control'),
            ('default', 'control'),
            (', ', 'delimiter'),
            (' of ', 'delimiter'),
            (' or ', 'delimiter'),
            (': ', 'delimiter'),
            ('True', 'obj'),
            ('None', 'obj'),
            ('name', 'obj'),
            (':py:class:`Enum`', 'reference'),
        )

        for token, expected in tokens:
            actual = _token_type(token)
            assert actual == expected

    def test_tokenize_type_spec(self):
        specs = (
            'str',
            'defaultdict',
            'int, float, or complex',
            'int or float or None, optional',
            'list of list of int or float, optional',
            'tuple of list of str, float, or int',
            '{"F", "C", "N"}',
            "{'F', 'C', 'N'}, default: 'F'",
            "{'F', 'C', 'N or C'}, default 'F'",
            "str, default: 'F or C'",
            'int, default: None',
            'int, default None',
            'int, default :obj:`None`',
            '"ma{icious"',
            r"'with \'quotes\''",
        )

        tokens = (
            ['str'],
            ['defaultdict'],
            ['int', ', ', 'float', ', or ', 'complex'],
            ['int', ' or ', 'float', ' or ', 'None', ', ', 'optional'],
            ['list', ' of ', 'list', ' of ', 'int', ' or ', 'float', ', ', 'optional'],
            ['tuple', ' of ', 'list', ' of ', 'str', ', ', 'float', ', or ', 'int'],
            ['{', '"F"', ', ', '"C"', ', ', '"N"', '}'],
            ['{', "'F'", ', ', "'C'", ', ', "'N'", '}', ', ', 'default', ': ', "'F'"],
            ['{', "'F'", ', ', "'C'", ', ', "'N or C'", '}', ', ', 'default', ' ', "'F'"],
            ['str', ', ', 'default', ': ', "'F or C'"],
            ['int', ', ', 'default', ': ', 'None'],
            ['int', ', ', 'default', ' ', 'None'],
            ['int', ', ', 'default', ' ', ':obj:`None`'],
            ['"ma{icious"'],
            [r"'with \'quotes\''"],
        )  # fmt: skip

        for spec, expected in zip(specs, tokens, strict=True):
            actual = _tokenize_type_spec(spec)
            assert actual == expected

    def test_recombine_set_tokens(self):
        tokens = (
            ['{', '1', ', ', '2', '}'],
            ['{', '"F"', ', ', '"C"', ', ', '"N"', '}', ', ', 'optional'],
            ['{', "'F'", ', ', "'C'", ', ', "'N'", '}', ', ', 'default', ': ', 'None'],
            ['{', "'F'", ', ', "'C'", ', ', "'N'", '}', ', ', 'default', ' ', 'None'],
        )

        combined_tokens = (
            ['{1, 2}'],
            ['{"F", "C", "N"}', ', ', 'optional'],
            ["{'F', 'C', 'N'}", ', ', 'default', ': ', 'None'],
            ["{'F', 'C', 'N'}", ', ', 'default', ' ', 'None'],
        )

        for tokens_, expected in zip(tokens, combined_tokens, strict=True):
            actual = _recombine_set_tokens(tokens_)
            assert actual == expected

    def test_recombine_set_tokens_invalid(self):
        tokens = (
            ['{', '1', ', ', '2'],
            ['"F"', ', ', '"C"', ', ', '"N"', '}', ', ', 'optional'],
            ['{', '1', ', ', '2', ', ', 'default', ': ', 'None'],
        )
        combined_tokens = (
            ['{1, 2'],
            ['"F"', ', ', '"C"', ', ', '"N"', '}', ', ', 'optional'],
            ['{1, 2', ', ', 'default', ': ', 'None'],
        )

        for tokens_, expected in zip(tokens, combined_tokens, strict=True):
            actual = _recombine_set_tokens(tokens_)
            assert actual == expected

    def test_convert_numpy_type_spec(self):
        translations = {
            'DataFrame': 'pandas.DataFrame',
        }

        specs = (
            '',
            'optional',
            'str, optional',
            'int or float or None, default: None',
            'list of tuple of str, optional',
            'int, default None',
            '{"F", "C", "N"}',
            "{'F', 'C', 'N'}, default: 'N'",
            "{'F', 'C', 'N'}, default 'N'",
            'DataFrame, optional',
        )

        converted = (
            '',
            '*optional*',
            ':py:class:`str`, *optional*',
            ':py:class:`int` or :py:class:`float` or :py:obj:`None`, *default*: :py:obj:`None`',
            ':py:class:`list` of :py:class:`tuple` of :py:class:`str`, *optional*',
            ':py:class:`int`, *default* :py:obj:`None`',
            '``{"F", "C", "N"}``',
            "``{'F', 'C', 'N'}``, *default*: ``'N'``",
            "``{'F', 'C', 'N'}``, *default* ``'N'``",
            ':py:class:`pandas.DataFrame`, *optional*',
        )

        for spec, expected in zip(specs, converted, strict=True):
            actual = _convert_type_spec(spec, translations=translations)
            assert actual == expected

    def test_parameter_types(self):
        docstring = dedent("""\
            Parameters
            ----------
            param1 : DataFrame
                the data to work on
            param2 : int or float or None, optional
                a parameter with different types
            param3 : dict-like, optional
                a optional mapping
            param4 : int or float or None, optional
                a optional parameter with different types
            param5 : {"F", "C", "N"}, optional
                a optional parameter with fixed values
            param6 : int, default None
                different default format
            param7 : mapping of hashable to str, optional
                a optional mapping
            param8 : ... or Ellipsis
                ellipsis
            param9 : tuple of list of int
                a parameter with tuple of list of int
        """)
        expected = dedent("""\
            :param param1: the data to work on
            :type param1: :py:class:`DataFrame`
            :param param2: a parameter with different types
            :type param2: :py:class:`int` or :py:class:`float` or :py:obj:`None`, *optional*
            :param param3: a optional mapping
            :type param3: :term:`dict-like <mapping>`, *optional*
            :param param4: a optional parameter with different types
            :type param4: :py:class:`int` or :py:class:`float` or :py:obj:`None`, *optional*
            :param param5: a optional parameter with fixed values
            :type param5: ``{"F", "C", "N"}``, *optional*
            :param param6: different default format
            :type param6: :py:class:`int`, *default* :py:obj:`None`
            :param param7: a optional mapping
            :type param7: :term:`mapping` of :term:`hashable` to :py:class:`str`, *optional*
            :param param8: ellipsis
            :type param8: :py:obj:`... <Ellipsis>` or :py:obj:`Ellipsis`
            :param param9: a parameter with tuple of list of int
            :type param9: :py:class:`tuple` of :py:class:`list` of :py:class:`int`
        """)
        translations = {
            'dict-like': ':term:`dict-like <mapping>`',
            'mapping': ':term:`mapping`',
            'hashable': ':term:`hashable`',
        }
        config = Config(
            napoleon_use_param=True,
            napoleon_use_rtype=True,
            napoleon_preprocess_types=True,
            napoleon_type_aliases=translations,
        )
        actual = NumpyDocstring(docstring, config)
        assert str(actual) == expected

    @pytest.mark.sphinx('html', testroot='root')
    def test_token_type_invalid(self, app):
        tokens = (
            '{1, 2',
            '}',
            "'abc",
            "def'",
            '"ghi',
            'jkl"',
        )
        errors = (
            r'.+: invalid value set \(missing closing brace\):',
            r'.+: invalid value set \(missing opening brace\):',
            r'.+: malformed string literal \(missing closing quote\):',
            r'.+: malformed string literal \(missing opening quote\):',
            r'.+: malformed string literal \(missing closing quote\):',
            r'.+: malformed string literal \(missing opening quote\):',
        )
        for token, error in zip(tokens, errors, strict=True):
            try:
                _token_type(token)
            finally:
                raw_warnings = app.warning.getvalue()
                warnings = [w for w in raw_warnings.split('\n') if w.strip()]

                assert len(warnings) == 1
                assert re.compile(error).match(warnings[0])
                app.warning.truncate(0)

    @pytest.mark.parametrize(
        ('name', 'expected'),
        [
            ('x, y, z', 'x, y, z'),
            ('*args, **kwargs', r'\*args, \*\*kwargs'),
            ('*x, **y', r'\*x, \*\*y'),
        ],
    )
    def test_escape_args_and_kwargs(self, name, expected):
        numpy_docstring = NumpyDocstring('')
        actual = numpy_docstring._escape_args_and_kwargs(name)

        assert actual == expected

    def test_pep526_annotations(self):
        # test class attributes annotations
        config = Config(
            napoleon_attr_annotations=True,
        )
        actual = NumpyDocstring(
            cleandoc(PEP526NumpyClass.__doc__),
            config,
            app=None,
            what='class',
            obj=PEP526NumpyClass,
        )
        expected = """\
Sample class with PEP 526 annotations and numpy docstring

.. attribute:: attr1

   Attr1 description

   :type: int

.. attribute:: attr2

   Attr2 description

   :type: str
"""
        print(actual)
        assert str(actual) == expected

    def test_pep526_annotations_dont_use_attr_type_for_param(self):
        # test class attributes annotations
        config = Config(napoleon_attr_annotations=True)
        actual = str(
            NumpyDocstring(
                cleandoc(PEP526NumpyDontUseAttrTypeForParam.__doc__),
                config,
                app=None,
                what='class',
                obj=PEP526NumpyDontUseAttrTypeForParam,
            )
        )
        assert (
            actual
            == """\
A Class

:param blah: Description of parameter blah
:type blah: int
"""
        )


@pytest.mark.sphinx(
    'text',
    testroot='ext-napoleon',
    confoverrides={
        'autodoc_typehints': 'description',
        'autodoc_typehints_description_target': 'all',
    },
)
def test_napoleon_and_autodoc_typehints_description_all(app):
    app.build()
    content = (app.outdir / 'typehints.txt').read_text(encoding='utf-8')
    assert content == (
        'typehints\n'
        '*********\n'
        '\n'
        'mypackage.typehints.hello(x, *args, **kwargs)\n'
        '\n'
        '   Parameters:\n'
        '      * **x** (*int*) -- X\n'
        '\n'
        '      * ***args** (*int*) -- Additional arguments.\n'
        '\n'
        '      * ****kwargs** (*int*) -- Extra arguments.\n'
        '\n'
        '   Return type:\n'
        '      None\n'
    )


@pytest.mark.sphinx(
    'text',
    testroot='ext-napoleon',
    confoverrides={
        'autodoc_typehints': 'description',
        'autodoc_typehints_description_target': 'documented_params',
    },
)
def test_napoleon_and_autodoc_typehints_description_documented_params(app):
    app.build()
    content = (app.outdir / 'typehints.txt').read_text(encoding='utf-8')
    assert content == (
        'typehints\n'
        '*********\n'
        '\n'
        'mypackage.typehints.hello(x, *args, **kwargs)\n'
        '\n'
        '   Parameters:\n'
        '      * **x** (*int*) -- X\n'
        '\n'
        '      * ***args** (*int*) -- Additional arguments.\n'
        '\n'
        '      * ****kwargs** (*int*) -- Extra arguments.\n'
    )


@pytest.mark.sphinx('html', testroot='ext-napoleon-paramtype', freshenv=True)
def test_napoleon_keyword_and_paramtype(app, tmp_path):
    inv_file = tmp_path / 'objects.inv'
    inv_file.write_bytes(
        b"""\
# Sphinx inventory version 2
# Project: Intersphinx Test
# Version: 42
# The remainder of this file is compressed using zlib.
"""
        + zlib.compress(b"""\
None py:data 1 none.html -
list py:class 1 list.html -
int py:class 1 int.html -
""")
    )
    app.config.intersphinx_mapping = {'python': ('127.0.0.1:5555', str(inv_file))}
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    app.build(force_all=True)

    etree = etree_parse(app.outdir / 'index.html')

    for name, typename in product(
        ('keyword', 'kwarg', 'kwparam'),
        ('paramtype', 'kwtype'),
    ):
        param = f'{name}_{typename}'
        li_ = list(etree.findall(f'.//li/p/strong[.="{param}"]/../..'))
        assert len(li_) == 1
        li = li_[0]

        text = li.text or ''.join(li.itertext())
        assert text == f'{param} (list[int]) \u2013 some param'

        a_ = list(li.findall('.//a[@class="reference external"]'))

        assert len(a_) == 2
        for a, uri in zip(a_, ('list.html', 'int.html'), strict=True):
            assert a.attrib['href'] == f'127.0.0.1:5555/{uri}'
            assert a.attrib['title'] == '(in Intersphinx Test v42)'
