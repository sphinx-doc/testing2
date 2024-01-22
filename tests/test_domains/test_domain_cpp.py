"""Tests the C++ Domain"""

from __future__ import annotations

import itertools
import re
import textwrap
import zlib
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

import sphinx.domains.cpp
from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_content,
    desc_name,
    desc_parameter,
    desc_parameterlist,
    desc_sig_name,
    desc_sig_space,
    desc_signature,
    desc_signature_line,
    pending_xref,
)
from sphinx.domains.cpp._ids import _id_prefix, _max_id
from sphinx.domains.cpp._parser import DefinitionParser
from sphinx.domains.cpp._symbol import Symbol
from sphinx.ext.intersphinx import load_mappings, validate_intersphinx_mapping
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node
from sphinx.util.cfamily import DefinitionError, NoOldIdError
from sphinx.writers.text import STDINDENT

if TYPE_CHECKING:
    from io import StringIO


def parse(name, string):
    class Config:
        cpp_id_attributes = ['id_attr']
        cpp_paren_attributes = ['paren_attr']

    parser = DefinitionParser(string, location=None, config=Config())
    parser.allowFallbackExpressionParsing = False
    ast = parser.parse_declaration(name, name)
    parser.assert_end()
    # The scopedness would usually have been set by CPPEnumObject
    if name == 'enum':
        ast.scoped = None  # simulate unscoped enum
    return ast


def _check(name, input, id_dict, output, key, as_text_output):
    if key is None:
        key = name
    key += ' '
    if name in {'function', 'member'}:
        input_actual = input
        output_ast = output
        output_as_text = output
    else:
        input_actual = input.format(key='')
        output_ast = output.format(key='')
        output_as_text = output.format(key=key)
    if as_text_output is not None:
        output_as_text = as_text_output

    # first a simple check of the AST
    ast = parse(name, input_actual)
    res = str(ast)
    if res != output_ast:
        print()
        print('Input:    ', input)
        print('Result:   ', res)
        print('Expected: ', output_ast)
        raise DefinitionError
    root_symbol = Symbol(None, None, None, None, None, None, None)
    symbol = root_symbol.add_declaration(ast, docname='TestDoc', line=42)
    parent_node = addnodes.desc()
    signode = addnodes.desc_signature(input, '')
    parent_node += signode
    ast.describe_signature(signode, 'lastIsName', symbol, options={})
    res_as_text = parent_node.astext()
    if res_as_text != output_as_text:
        print()
        print('Input:    ', input)
        print('astext(): ', res_as_text)
        print('Expected: ', output_as_text)
        print('Node:', parent_node)
        raise DefinitionError

    id_expected = [None]
    for i in range(1, _max_id + 1):
        if i in id_dict:
            id_expected.append(id_dict[i])
        else:
            id_expected.append(id_expected[i - 1])
    id_actual = [None]
    for i in range(1, _max_id + 1):
        try:
            id = ast.get_id(version=i)
            assert id is not None
            id_actual.append(id[len(_id_prefix[i]) :])
        except NoOldIdError:
            id_actual.append(None)

    res = [True]
    for i in range(1, _max_id + 1):
        res.append(id_expected[i] == id_actual[i])

    if not all(res):
        print('input:    %s' % input.rjust(20))
        for i in range(1, _max_id + 1):
            if res[i]:
                continue
            print('Error in id version %d.' % i)
            print('result:   %s' % id_actual[i])
            print('expected: %s' % id_expected[i])
        print(root_symbol.dump(0))
        raise DefinitionError


def check(name, input, id_dict, output=None, key=None, as_text_output=None):
    if output is None:
        output = input
    # First, check without semicolon
    _check(name, input, id_dict, output, key, as_text_output)
    # Second, check with semicolon
    _check(
        name,
        input + ' ;',
        id_dict,
        output + ';',
        key,
        as_text_output + ';' if as_text_output is not None else None,
    )


@pytest.mark.parametrize(
    ('type_', 'id_v2'),
    sphinx.domains.cpp._ids._id_fundamental_v2.items(),
)
def test_domain_cpp_ast_fundamental_types(type_, id_v2):
    # see https://en.cppreference.com/w/cpp/language/types
    def make_id_v1():
        if type_ == 'decltype(auto)':
            return None
        id_ = type_.replace(' ', '-').replace('long', 'l')
        if '__int' not in type_:
            id_ = id_.replace('int', 'i')
        id_ = id_.replace('bool', 'b').replace('char', 'c')
        id_ = id_.replace('wc_t', 'wchar_t').replace('c16_t', 'char16_t')
        id_ = id_.replace('c8_t', 'char8_t')
        id_ = id_.replace('c32_t', 'char32_t')
        return f'f__{id_}'

    def make_id_v2():
        id_ = id_v2
        if type_ == 'std::nullptr_t':
            id_ = 'NSt9nullptr_tE'
        return f'1f{id_}'

    id1 = make_id_v1()
    id2 = make_id_v2()

    input = f'void f({type_.replace(" ", "  ")} arg)'
    output = f'void f({type_} arg)'

    check('function', input, {1: id1, 2: id2}, output=output)
    if ' ' in type_:
        # try permutations of all components
        tcs = type_.split()
        for p in itertools.permutations(tcs):
            input = f'void f({" ".join(p)} arg)'
            check('function', input, {1: id1, 2: id2})


def test_domain_cpp_ast_expressions():
    def expr_check(expr, id, id4=None):
        ids = 'IE1CIA%s_1aE'
        # call .format() on the expr to unescape double curly braces
        id_dict = {2: ids % expr.format(), 3: ids % id}
        if id4 is not None:
            id_dict[4] = ids % id4
        check('class', 'template<> {key}C<a[%s]>' % expr, id_dict)

        class Config:
            cpp_id_attributes = ['id_attr']
            cpp_paren_attributes = ['paren_attr']

        parser = DefinitionParser(expr, location=None, config=Config())
        parser.allowFallbackExpressionParsing = False
        ast = parser.parse_expression()
        res = str(ast)
        if res != expr:
            print()
            print('Input:    ', expr)
            print('Result:   ', res)
            raise DefinitionError
        display_string = ast.get_display_string()
        if res != display_string:
            # note: if the expression contains an anon name then this will trigger a falsely
            print()
            print('Input:    ', expr)
            print('Result:   ', res)
            print('Display:  ', display_string)
            raise DefinitionError

    # primary
    expr_check('nullptr', 'LDnE')
    expr_check('true', 'L1E')
    expr_check('false', 'L0E')
    ints = [
        '5',
        '0',
        '075',
        '0x0123456789ABCDEF',
        '0XF',
        '0b1',
        '0B1',
        "0b0'1'0",
        "00'1'2",
        "0x0'1'2",
        "1'2'3",
    ]
    unsigned_suffix = ['', 'u', 'U']
    long_suffix = ['', 'l', 'L', 'll', 'LL']
    for i in ints:
        for u in unsigned_suffix:
            for l in long_suffix:
                expr = i + u + l
                expr_check(expr, 'L' + expr.replace("'", '') + 'E')
                expr = i + l + u
                expr_check(expr, 'L' + expr.replace("'", '') + 'E')
    decimal_floats = [
        '5e42',
        '5e+42',
        '5e-42',
        '5.',
        '5.e42',
        '5.e+42',
        '5.e-42',
        '.5',
        '.5e42',
        '.5e+42',
        '.5e-42',
        '5.0',
        '5.0e42',
        '5.0e+42',
        '5.0e-42',
        "1'2'3e7'8'9",
        "1'2'3.e7'8'9",
        ".4'5'6e7'8'9",
        "1'2'3.4'5'6e7'8'9",
    ]
    hex_floats = [
        'ApF',
        'Ap+F',
        'Ap-F',
        'A.',
        'A.pF',
        'A.p+F',
        'A.p-F',
        '.A',
        '.ApF',
        '.Ap+F',
        '.Ap-F',
        'A.B',
        'A.BpF',
        'A.Bp+F',
        'A.Bp-F',
        "A'B'Cp1'2'3",
        "A'B'C.p1'2'3",
        ".D'E'Fp1'2'3",
        "A'B'C.D'E'Fp1'2'3",
    ]
    for suffix in ('', 'f', 'F', 'l', 'L'):
        for e in decimal_floats:
            expr = e + suffix
            expr_check(expr, 'L' + expr.replace("'", '') + 'E')
        for e in hex_floats:
            expr = '0x' + e + suffix
            expr_check(expr, 'L' + expr.replace("'", '') + 'E')
    expr_check('"abc\\"cba"', 'LA8_KcE')  # string
    expr_check('this', 'fpT')
    # character literals
    char_prefix_and_ids = [('', 'c'), ('u8', 'c'), ('u', 'Ds'), ('U', 'Di'), ('L', 'w')]
    chars = [
        ('a', '97'),
        ('\\n', '10'),
        ('\\012', '10'),
        ('\\0', '0'),
        ('\\x0a', '10'),
        ('\\x0A', '10'),
        ('\\u0a42', '2626'),
        ('\\u0A42', '2626'),
        ('\\U0001f34c', '127820'),
        ('\\U0001F34C', '127820'),
    ]
    for p, t in char_prefix_and_ids:
        for c, val in chars:
            expr_check(f"{p}'{c}'", t + val)
    # user-defined literals
    for i in ints:
        expr_check(i + '_udl', 'clL_Zli4_udlEL' + i.replace("'", '') + 'EE')
        expr_check(i + 'uludl', 'clL_Zli5uludlEL' + i.replace("'", '') + 'EE')
    for f in decimal_floats:
        expr_check(f + '_udl', 'clL_Zli4_udlEL' + f.replace("'", '') + 'EE')
        expr_check(f + 'fudl', 'clL_Zli4fudlEL' + f.replace("'", '') + 'EE')
    for f in hex_floats:
        expr_check('0x' + f + '_udl', 'clL_Zli4_udlEL0x' + f.replace("'", '') + 'EE')
    for p, t in char_prefix_and_ids:
        for c, val in chars:
            expr_check(f"{p}'{c}'_udl", 'clL_Zli4_udlE' + t + val + 'E')
    expr_check('"abc"_udl', 'clL_Zli4_udlELA3_KcEE')
    # from issue #7294
    expr_check('6.62607015e-34q_J', 'clL_Zli3q_JEL6.62607015e-34EE')

    # fold expressions, paren, name
    expr_check('(... + Ns)', '(... + Ns)', id4='flpl2Ns')
    expr_check('(Ns + ...)', '(Ns + ...)', id4='frpl2Ns')
    expr_check('(Ns + ... + 0)', '(Ns + ... + 0)', id4='fLpl2NsL0E')
    expr_check('(5)', 'L5E')
    expr_check('C', '1C')
    # postfix
    expr_check('A(2)', 'cl1AL2EE')
    expr_check('A[2]', 'ix1AL2E')
    expr_check('a.b.c', 'dtdt1a1b1c')
    expr_check('a->b->c', 'ptpt1a1b1c')
    expr_check('i++', 'pp1i')
    expr_check('i--', 'mm1i')
    expr_check('dynamic_cast<T&>(i)++', 'ppdcR1T1i')
    expr_check('static_cast<T&>(i)++', 'ppscR1T1i')
    expr_check('reinterpret_cast<T&>(i)++', 'pprcR1T1i')
    expr_check('const_cast<T&>(i)++', 'ppccR1T1i')
    expr_check('typeid(T).name', 'dtti1T4name')
    expr_check('typeid(a + b).name', 'dttepl1a1b4name')
    # unary
    expr_check('++5', 'pp_L5E')
    expr_check('--5', 'mm_L5E')
    expr_check('*5', 'deL5E')
    expr_check('&5', 'adL5E')
    expr_check('+5', 'psL5E')
    expr_check('-5', 'ngL5E')
    expr_check('!5', 'ntL5E')
    expr_check('not 5', 'ntL5E')
    expr_check('~5', 'coL5E')
    expr_check('compl 5', 'coL5E')
    expr_check('sizeof...(a)', 'sZ1a')
    expr_check('sizeof(T)', 'st1T')
    expr_check('sizeof -42', 'szngL42E')
    expr_check('alignof(T)', 'at1T')
    expr_check('noexcept(-42)', 'nxngL42E')
    # new-expression
    expr_check('new int', 'nw_iE')
    expr_check('new volatile int', 'nw_ViE')
    expr_check('new int[42]', 'nw_AL42E_iE')
    expr_check('new int()', 'nw_ipiE')
    expr_check('new int(5, 42)', 'nw_ipiL5EL42EE')
    expr_check('::new int', 'nw_iE')
    expr_check('new int{{}}', 'nw_iilE')
    expr_check('new int{{5, 42}}', 'nw_iilL5EL42EE')
    # delete-expression
    expr_check('delete p', 'dl1p')
    expr_check('delete [] p', 'da1p')
    expr_check('::delete p', 'dl1p')
    expr_check('::delete [] p', 'da1p')
    # cast
    expr_check('(int)2', 'cviL2E')
    # binary op
    expr_check('5 || 42', 'ooL5EL42E')
    expr_check('5 or 42', 'ooL5EL42E')
    expr_check('5 && 42', 'aaL5EL42E')
    expr_check('5 and 42', 'aaL5EL42E')
    expr_check('5 | 42', 'orL5EL42E')
    expr_check('5 bitor 42', 'orL5EL42E')
    expr_check('5 ^ 42', 'eoL5EL42E')
    expr_check('5 xor 42', 'eoL5EL42E')
    expr_check('5 & 42', 'anL5EL42E')
    expr_check('5 bitand 42', 'anL5EL42E')
    # ['==', '!=']
    expr_check('5 == 42', 'eqL5EL42E')
    expr_check('5 != 42', 'neL5EL42E')
    expr_check('5 not_eq 42', 'neL5EL42E')
    # ['<=', '>=', '<', '>', '<=>']
    expr_check('5 <= 42', 'leL5EL42E')
    expr_check('A <= 42', 'le1AL42E')
    expr_check('5 >= 42', 'geL5EL42E')
    expr_check('5 < 42', 'ltL5EL42E')
    expr_check('A < 42', 'lt1AL42E')
    expr_check('5 > 42', 'gtL5EL42E')
    expr_check('A > 42', 'gt1AL42E')
    expr_check('5 <=> 42', 'ssL5EL42E')
    expr_check('A <=> 42', 'ss1AL42E')
    # ['<<', '>>']
    expr_check('5 << 42', 'lsL5EL42E')
    expr_check('A << 42', 'ls1AL42E')
    expr_check('5 >> 42', 'rsL5EL42E')
    # ['+', '-']
    expr_check('5 + 42', 'plL5EL42E')
    expr_check('5 - 42', 'miL5EL42E')
    # ['*', '/', '%']
    expr_check('5 * 42', 'mlL5EL42E')
    expr_check('5 / 42', 'dvL5EL42E')
    expr_check('5 % 42', 'rmL5EL42E')
    # ['.*', '->*']
    expr_check('5 .* 42', 'dsL5EL42E')
    expr_check('5 ->* 42', 'pmL5EL42E')
    # conditional
    expr_check('5 ? 7 : 3', 'quL5EL7EL3E')
    # assignment
    expr_check('a = 5', 'aS1aL5E')
    expr_check('a *= 5', 'mL1aL5E')
    expr_check('a /= 5', 'dV1aL5E')
    expr_check('a %= 5', 'rM1aL5E')
    expr_check('a += 5', 'pL1aL5E')
    expr_check('a -= 5', 'mI1aL5E')
    expr_check('a >>= 5', 'rS1aL5E')
    expr_check('a <<= 5', 'lS1aL5E')
    expr_check('a &= 5', 'aN1aL5E')
    expr_check('a and_eq 5', 'aN1aL5E')
    expr_check('a ^= 5', 'eO1aL5E')
    expr_check('a xor_eq 5', 'eO1aL5E')
    expr_check('a |= 5', 'oR1aL5E')
    expr_check('a or_eq 5', 'oR1aL5E')
    expr_check('a = {{1, 2, 3}}', 'aS1ailL1EL2EL3EE')
    # complex assignment and conditional
    expr_check('5 = 6 = 7', 'aSL5EaSL6EL7E')
    expr_check('5 = 6 ? 7 = 8 : 3', 'aSL5EquL6EaSL7EL8EL3E')
    # comma operator
    expr_check('a, 5', 'cm1aL5E')

    # Additional tests
    # a < expression that starts with something that could be a template
    expr_check('A < 42', 'lt1AL42E')
    check(
        'function',
        'template<> void f(A<B, 2> &v)',
        {2: 'IE1fR1AI1BX2EE', 3: 'IE1fR1AI1BXL2EEE', 4: 'IE1fvR1AI1BXL2EEE'},
    )
    expr_check('A<1>::value', 'N1AIXL1EEE5valueE')
    check('class', 'template<int T = 42> {key}A', {2: 'I_iE1A'})
    check('enumerator', '{key}A = std::numeric_limits<unsigned long>::max()', {2: '1A'})

    expr_check('operator()()', 'clclE')
    expr_check('operator()<int>()', 'clclIiEE')

    # pack expansion
    expr_check('a(b(c, 1 + d...)..., e(f..., g))', 'cl1aspcl1b1cspplL1E1dEcl1esp1f1gEE')


def test_domain_cpp_ast_type_definitions():
    check('type', 'public bool b', {1: 'b', 2: '1b'}, '{key}bool b', key='typedef')
    check('type', '{key}bool A::b', {1: 'A::b', 2: 'N1A1bE'}, key='typedef')
    check('type', '{key}bool *b', {1: 'b', 2: '1b'}, key='typedef')
    check('type', '{key}bool *const b', {1: 'b', 2: '1b'}, key='typedef')
    check('type', '{key}bool *volatile const b', {1: 'b', 2: '1b'}, key='typedef')
    check('type', '{key}bool *volatile const b', {1: 'b', 2: '1b'}, key='typedef')
    check('type', '{key}bool *volatile const *b', {1: 'b', 2: '1b'}, key='typedef')
    check('type', '{key}bool &b', {1: 'b', 2: '1b'}, key='typedef')
    check('type', '{key}bool b[]', {1: 'b', 2: '1b'}, key='typedef')
    check(
        'type',
        '{key}std::pair<int, int> coord',
        {1: 'coord', 2: '5coord'},
        key='typedef',
    )
    check('type', '{key}long long int foo', {1: 'foo', 2: '3foo'}, key='typedef')
    check(
        'type',
        '{key}std::vector<std::pair<std::string, long long>> module::blah',
        {1: 'module::blah', 2: 'N6module4blahE'},
        key='typedef',
    )
    check('type', '{key}std::function<void()> F', {1: 'F', 2: '1F'}, key='typedef')
    check('type', '{key}std::function<R(A1, A2)> F', {1: 'F', 2: '1F'}, key='typedef')
    check(
        'type', '{key}std::function<R(A1, A2, A3)> F', {1: 'F', 2: '1F'}, key='typedef'
    )
    check(
        'type',
        '{key}std::function<R(A1, A2, A3, As...)> F',
        {1: 'F', 2: '1F'},
        key='typedef',
    )
    check(
        'type',
        '{key}MyContainer::const_iterator',
        {1: 'MyContainer::const_iterator', 2: 'N11MyContainer14const_iteratorE'},
    )
    check(
        'type',
        'public MyContainer::const_iterator',
        {1: 'MyContainer::const_iterator', 2: 'N11MyContainer14const_iteratorE'},
        output='{key}MyContainer::const_iterator',
    )
    # test decl specs on right
    check('type', '{key}bool const b', {1: 'b', 2: '1b'}, key='typedef')
    # test name in global scope
    check('type', '{key}bool ::B::b', {1: 'B::b', 2: 'N1B1bE'}, key='typedef')

    check('type', '{key}A = B', {2: '1A'}, key='using')
    check('type', '{key}A = decltype(b)', {2: '1A'}, key='using')

    # from breathe#267 (named function parameters for function pointers
    check(
        'type',
        '{key}void (*gpio_callback_t)(struct device *port, uint32_t pin)',
        {1: 'gpio_callback_t', 2: '15gpio_callback_t'},
        key='typedef',
    )
    check(
        'type',
        '{key}void (*f)(std::function<void(int i)> g)',
        {1: 'f', 2: '1f'},
        key='typedef',
    )

    check(
        'type',
        '{key}T = A::template B<int>::template C<double>',
        {2: '1T'},
        key='using',
    )

    check('type', '{key}T = Q<A::operator()>', {2: '1T'}, key='using')
    check('type', '{key}T = Q<A::operator()<int>>', {2: '1T'}, key='using')
    check('type', '{key}T = Q<A::operator bool>', {2: '1T'}, key='using')


def test_domain_cpp_ast_concept_definitions():
    check(
        'concept',
        'template<typename Param> {key}A::B::Concept',
        {2: 'I0EN1A1B7ConceptE'},
    )
    check(
        'concept',
        'template<typename A, typename B, typename ...C> {key}Foo',
        {2: 'I00DpE3Foo'},
    )
    with pytest.raises(DefinitionError):
        parse('concept', '{key}Foo')
    with pytest.raises(DefinitionError):
        parse('concept', 'template<typename T> template<typename U> {key}Foo')


def test_domain_cpp_ast_member_definitions():
    check(
        'member',
        '  const  std::string  &  name = 42',
        {1: 'name__ssCR', 2: '4name'},
        output='const std::string &name = 42',
    )
    check(
        'member',
        '  const  std::string  &  name',
        {1: 'name__ssCR', 2: '4name'},
        output='const std::string &name',
    )
    check(
        'member',
        '  const  std::string  &  name [ n ]',
        {1: 'name__ssCRA', 2: '4name'},
        output='const std::string &name[n]',
    )
    check(
        'member',
        'const std::vector< unsigned int, long> &name',
        {1: 'name__std::vector:unsigned-i.l:CR', 2: '4name'},
        output='const std::vector<unsigned int, long> &name',
    )
    check('member', 'module::myclass foo[n]', {1: 'foo__module::myclassA', 2: '3foo'})
    check('member', 'int *const p', {1: 'p__iPC', 2: '1p'})
    check('member', 'extern int myInt', {1: 'myInt__i', 2: '5myInt'})
    check('member', 'thread_local int myInt', {1: 'myInt__i', 2: '5myInt'})
    check('member', 'extern thread_local int myInt', {1: 'myInt__i', 2: '5myInt'})
    check(
        'member',
        'thread_local extern int myInt',
        {1: 'myInt__i', 2: '5myInt'},
        'extern thread_local int myInt',
    )

    # tests based on https://en.cppreference.com/w/cpp/language/bit_field
    check('member', 'int b : 3', {1: 'b__i', 2: '1b'})
    check('member', 'int b : 8 = 42', {1: 'b__i', 2: '1b'})
    check('member', 'int b : 8{42}', {1: 'b__i', 2: '1b'})
    # TODO: enable once the ternary operator is supported
    # check('member', 'int b : true ? 8 : a = 42', {1: 'b__i', 2: '1b'})
    # TODO: enable once the ternary operator is supported
    # check('member', 'int b : (true ? 8 : a) = 42', {1: 'b__i', 2: '1b'})
    check('member', 'int b : 1 || new int{0}', {1: 'b__i', 2: '1b'})

    check('member', 'inline int n', {1: 'n__i', 2: '1n'})
    check('member', 'constinit int n', {1: 'n__i', 2: '1n'})


def test_domain_cpp_ast_function_definitions():
    check('function', 'void f(volatile int)', {1: 'f__iV', 2: '1fVi'})
    check('function', 'void f(std::size_t)', {1: 'f__std::s', 2: '1fNSt6size_tE'})
    check('function', 'operator bool() const', {1: 'castto-b-operatorC', 2: 'NKcvbEv'})
    check(
        'function',
        'A::operator bool() const',
        {1: 'A::castto-b-operatorC', 2: 'NK1AcvbEv'},
    )
    check(
        'function',
        'A::operator bool() volatile const &',
        {1: 'A::castto-b-operatorVCR', 2: 'NVKR1AcvbEv'},
    )
    check(
        'function',
        'A::operator bool() volatile const &&',
        {1: 'A::castto-b-operatorVCO', 2: 'NVKO1AcvbEv'},
    )
    check(
        'function',
        'bool namespaced::theclass::method(arg1, arg2)',
        {
            1: 'namespaced::theclass::method__arg1.arg2',
            2: 'N10namespaced8theclass6methodE4arg14arg2',
        },
    )
    x = (
        'std::vector<std::pair<std::string, int>> &module::test(register int '
        'foo, bar, std::string baz = "foobar, blah, bleh") const = 0'
    )
    check(
        'function',
        x,
        {1: 'module::test__i.bar.ssC', 2: 'NK6module4testEi3barNSt6stringE'},
    )
    check(
        'function',
        'void f(std::pair<A, B>)',
        {1: 'f__std::pair:A.B:', 2: '1fNSt4pairI1A1BEE'},
    )
    check(
        'function',
        'explicit module::myclass::foo::foo()',
        {1: 'module::myclass::foo::foo', 2: 'N6module7myclass3foo3fooEv'},
    )
    check(
        'function',
        'module::myclass::foo::~foo()',
        {1: 'module::myclass::foo::~foo', 2: 'N6module7myclass3fooD0Ev'},
    )
    check(
        'function',
        'int printf(const char *fmt, ...)',
        {1: 'printf__cCP.z', 2: '6printfPKcz'},
    )
    check(
        'function',
        'int foo(const unsigned int j)',
        {1: 'foo__unsigned-iC', 2: '3fooKj'},
    )
    check('function', 'int foo(const int *const ptr)', {1: 'foo__iCPC', 2: '3fooPCKi'})
    check(
        'function',
        'module::myclass::operator std::vector<std::string>()',
        {
            1: 'module::myclass::castto-std::vector:ss:-operator',
            2: 'N6module7myclasscvNSt6vectorINSt6stringEEEEv',
        },
    )
    check(
        'function',
        'void operator()(const boost::array<VertexID, 2> &v) const',
        {
            1: 'call-operator__boost::array:VertexID.2:CRC',
            2: 'NKclERKN5boost5arrayI8VertexIDX2EEE',
            3: 'NKclERKN5boost5arrayI8VertexIDXL2EEEE',
        },
    )
    check(
        'function',
        'void operator()(const boost::array<VertexID, 2, "foo,  bar"> &v) const',
        {
            1: 'call-operator__boost::array:VertexID.2."foo,--bar":CRC',
            2: 'NKclERKN5boost5arrayI8VertexIDX2EX"foo,  bar"EEE',
            3: 'NKclERKN5boost5arrayI8VertexIDXL2EEXLA9_KcEEEE',
        },
    )
    check(
        'function',
        'MyClass::MyClass(MyClass::MyClass&&)',
        {
            1: 'MyClass::MyClass__MyClass::MyClassRR',
            2: 'N7MyClass7MyClassERRN7MyClass7MyClassE',
        },
    )
    check('function', 'constexpr int get_value()', {1: 'get_valueCE', 2: '9get_valuev'})
    check(
        'function',
        'static constexpr int get_value()',
        {1: 'get_valueCE', 2: '9get_valuev'},
    )
    check(
        'function',
        'int get_value() const noexcept',
        {1: 'get_valueC', 2: 'NK9get_valueEv'},
    )
    check(
        'function',
        'int get_value() const noexcept(std::is_nothrow_move_constructible<T>::value)',
        {1: 'get_valueC', 2: 'NK9get_valueEv'},
    )
    check(
        'function',
        'int get_value() const noexcept("see below")',
        {1: 'get_valueC', 2: 'NK9get_valueEv'},
    )
    check(
        'function',
        'int get_value() const noexcept = delete',
        {1: 'get_valueC', 2: 'NK9get_valueEv'},
    )
    check(
        'function',
        'int get_value() volatile const',
        {1: 'get_valueVC', 2: 'NVK9get_valueEv'},
    )
    check(
        'function',
        'MyClass::MyClass(MyClass::MyClass&&) = default',
        {
            1: 'MyClass::MyClass__MyClass::MyClassRR',
            2: 'N7MyClass7MyClassERRN7MyClass7MyClassE',
        },
    )
    check(
        'function',
        'virtual MyClass::a_virtual_function() const override',
        {1: 'MyClass::a_virtual_functionC', 2: 'NK7MyClass18a_virtual_functionEv'},
    )
    check('function', 'A B() override', {1: 'B', 2: '1Bv'})
    check('function', 'A B() final', {1: 'B', 2: '1Bv'})
    check('function', 'A B() final override', {1: 'B', 2: '1Bv'})
    check(
        'function',
        'A B() override final',
        {1: 'B', 2: '1Bv'},
        output='A B() final override',
    )
    check(
        'function',
        'MyClass::a_member_function() volatile',
        {1: 'MyClass::a_member_functionV', 2: 'NV7MyClass17a_member_functionEv'},
    )
    check(
        'function',
        'MyClass::a_member_function() volatile const',
        {1: 'MyClass::a_member_functionVC', 2: 'NVK7MyClass17a_member_functionEv'},
    )
    check(
        'function',
        'MyClass::a_member_function() &&',
        {1: 'MyClass::a_member_functionO', 2: 'NO7MyClass17a_member_functionEv'},
    )
    check(
        'function',
        'MyClass::a_member_function() &',
        {1: 'MyClass::a_member_functionR', 2: 'NR7MyClass17a_member_functionEv'},
    )
    check(
        'function',
        'MyClass::a_member_function() const &',
        {1: 'MyClass::a_member_functionCR', 2: 'NKR7MyClass17a_member_functionEv'},
    )
    check(
        'function',
        'int main(int argc, char *argv[])',
        {1: 'main__i.cPA', 2: '4mainiA_Pc'},
    )
    check(
        'function',
        'MyClass &MyClass::operator++()',
        {1: 'MyClass::inc-operator', 2: 'N7MyClassppEv'},
    )
    check(
        'function',
        'MyClass::pointer MyClass::operator->()',
        {1: 'MyClass::pointer-operator', 2: 'N7MyClassptEv'},
    )

    x = (
        'std::vector<std::pair<std::string, int>> &module::test(register int '
        'foo, bar[n], std::string baz = "foobar, blah, bleh") const = 0'
    )
    check(
        'function',
        x,
        {
            1: 'module::test__i.barA.ssC',
            2: 'NK6module4testEiAn_3barNSt6stringE',
            3: 'NK6module4testEiA1n_3barNSt6stringE',
        },
    )
    check(
        'function',
        'int foo(Foo f = Foo(double(), std::make_pair(int(2), double(3.4))))',
        {1: 'foo__Foo', 2: '3foo3Foo'},
    )
    check('function', 'int foo(A a = x(a))', {1: 'foo__A', 2: '3foo1A'})
    with pytest.raises(DefinitionError):
        parse('function', 'int foo(B b=x(a)')
    with pytest.raises(DefinitionError):
        parse('function', 'int foo)C c=x(a))')
    with pytest.raises(DefinitionError):
        parse('function', 'int foo(D d=x(a')
    check('function', 'int foo(const A&... a)', {1: 'foo__ACRDp', 2: '3fooDpRK1A'})
    check('function', 'int foo(const A&...)', {1: 'foo__ACRDp', 2: '3fooDpRK1A'})
    check('function', 'int foo(const A*... a)', {1: 'foo__ACPDp', 2: '3fooDpPK1A'})
    check('function', 'int foo(const A*...)', {1: 'foo__ACPDp', 2: '3fooDpPK1A'})
    check('function', 'int foo(const int A::*... a)', {2: '3fooDpM1AKi'})
    check('function', 'int foo(const int A::*...)', {2: '3fooDpM1AKi'})
    # check('function', 'int foo(int (*a)(A)...)', {1: "foo__ACRDp", 2: "3fooDpPK1A"})
    # check('function', 'int foo(int (*)(A)...)', {1: "foo__ACRDp", 2: "3fooDpPK1A"})
    check('function', 'virtual void f()', {1: 'f', 2: '1fv'})
    # test for ::nestedName, from issue 1738
    check(
        'function',
        'result(int val, ::std::error_category const &cat)',
        {1: 'result__i.std::error_categoryCR', 2: '6resultiRKNSt14error_categoryE'},
    )
    check('function', 'int *f()', {1: 'f', 2: '1fv'})
    # tests derived from issue #1753 (skip to keep sanity)
    check('function', 'f(int (&array)[10])', {2: '1fRA10_i', 3: '1fRAL10E_i'})
    check('function', 'void f(int (&array)[10])', {2: '1fRA10_i', 3: '1fRAL10E_i'})
    check('function', 'void f(float *q(double))', {2: '1fFPfdE'})
    check('function', 'void f(float *(*q)(double))', {2: '1fPFPfdE'})
    check('function', 'void f(float (*q)(double))', {2: '1fPFfdE'})
    check('function', 'int (*f(double d))(float)', {1: 'f__double', 2: '1fd'})
    check('function', 'int (*f(bool b))[5]', {1: 'f__b', 2: '1fb'})
    check(
        'function',
        'int (*A::f(double d) const)(float)',
        {1: 'A::f__doubleC', 2: 'NK1A1fEd'},
    )
    check(
        'function',
        'void f(std::shared_ptr<int(double)> ptr)',
        {2: '1fNSt10shared_ptrIFidEEE'},
    )
    check('function', 'void f(int *const p)', {1: 'f__iPC', 2: '1fPCi'})
    check('function', 'void f(int *volatile const p)', {1: 'f__iPVC', 2: '1fPVCi'})

    check('function', 'extern int f()', {1: 'f', 2: '1fv'})
    check('function', 'consteval int f()', {1: 'f', 2: '1fv'})

    check('function', 'explicit(true) void f()', {1: 'f', 2: '1fv'})

    check('function', 'decltype(auto) f()', {1: 'f', 2: '1fv'})

    # TODO: make tests for functions in a template, e.g., Test<int&&()>
    # such that the id generation for function type types is correct.

    check(
        'function',
        'friend std::ostream &f(std::ostream &s, int i)',
        {1: 'f__osR.i', 2: '1fRNSt7ostreamEi'},
    )

    # from breathe#223
    check('function', 'void f(struct E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(class E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(typename E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(enum E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(union E e)', {1: 'f__E', 2: '1f1E'})

    # pointer to member (function)
    check('function', 'void f(int C::*)', {2: '1fM1Ci'})
    check('function', 'void f(int C::* p)', {2: '1fM1Ci'})
    check('function', 'void f(int ::C::* p)', {2: '1fM1Ci'})
    check('function', 'void f(int C::*const)', {2: '1fKM1Ci'})
    check('function', 'void f(int C::*const&)', {2: '1fRKM1Ci'})
    check('function', 'void f(int C::*volatile)', {2: '1fVM1Ci'})
    check(
        'function',
        'void f(int C::*const volatile)',
        {2: '1fVKM1Ci'},
        output='void f(int C::*volatile const)',
    )
    check('function', 'void f(int C::*volatile const)', {2: '1fVKM1Ci'})
    check('function', 'void f(int (C::*)(float, double))', {2: '1fM1CFifdE'})
    check('function', 'void f(int (C::* p)(float, double))', {2: '1fM1CFifdE'})
    check('function', 'void f(int (::C::* p)(float, double))', {2: '1fM1CFifdE'})
    check('function', 'void f(void (C::*)() const &)', {2: '1fM1CKRFvvE'})
    check('function', 'int C::* f(int, double)', {2: '1fid'})
    check('function', 'void f(int C::* *p)', {2: '1fPM1Ci'})
    check('function', 'void f(int C::**)', {2: '1fPM1Ci'})
    check('function', 'void f(int C::*const *p)', {2: '1fPKM1Ci'})
    check('function', 'void f(int C::*const*)', {2: '1fPKM1Ci'})

    # exceptions from return type mangling
    check('function', 'template<typename T> C()', {2: 'I0E1Cv'})
    check('function', 'template<typename T> operator int()', {2: 'I0Ecviv'})

    # trailing return types
    ids = {1: 'f', 2: '1fv'}
    check('function', 'int f()', ids)
    check('function', 'auto f() -> int', ids)
    check('function', 'virtual auto f() -> int = 0', ids)
    check('function', 'virtual auto f() -> int final', ids)
    check('function', 'virtual auto f() -> int override', ids)

    ids = {2: 'I0E1fv', 4: 'I0E1fiv'}
    check('function', 'template<typename T> int f()', ids)
    check('function', 'template<typename T> f() -> int', ids)

    # from breathe#441
    check(
        'function',
        'auto MakeThingy() -> Thingy*',
        {1: 'MakeThingy', 2: '10MakeThingyv'},
    )

    # from #8960
    check('function', 'void f(void (*p)(int, double), int i)', {2: '1fPFvidEi'})

    # from #9535 comment
    check('function', 'void f(void (*p)(int) = &foo)', {2: '1fPFviE'})


def test_domain_cpp_ast_operators():
    check('function', 'void operator new()', {1: 'new-operator', 2: 'nwv'})
    check('function', 'void operator new[]()', {1: 'new-array-operator', 2: 'nav'})
    check('function', 'void operator delete()', {1: 'delete-operator', 2: 'dlv'})
    check(
        'function', 'void operator delete[]()', {1: 'delete-array-operator', 2: 'dav'}
    )
    check('function', 'operator bool() const', {1: 'castto-b-operatorC', 2: 'NKcvbEv'})
    check('function', 'void operator""_udl()', {2: 'li4_udlv'})

    check('function', 'void operator~()', {1: 'inv-operator', 2: 'cov'})
    check('function', 'void operator compl()', {2: 'cov'})
    check('function', 'void operator+()', {1: 'add-operator', 2: 'plv'})
    check('function', 'void operator-()', {1: 'sub-operator', 2: 'miv'})
    check('function', 'void operator*()', {1: 'mul-operator', 2: 'mlv'})
    check('function', 'void operator/()', {1: 'div-operator', 2: 'dvv'})
    check('function', 'void operator%()', {1: 'mod-operator', 2: 'rmv'})
    check('function', 'void operator&()', {1: 'and-operator', 2: 'anv'})
    check('function', 'void operator bitand()', {2: 'anv'})
    check('function', 'void operator|()', {1: 'or-operator', 2: 'orv'})
    check('function', 'void operator bitor()', {2: 'orv'})
    check('function', 'void operator^()', {1: 'xor-operator', 2: 'eov'})
    check('function', 'void operator xor()', {2: 'eov'})
    check('function', 'void operator=()', {1: 'assign-operator', 2: 'aSv'})
    check('function', 'void operator+=()', {1: 'add-assign-operator', 2: 'pLv'})
    check('function', 'void operator-=()', {1: 'sub-assign-operator', 2: 'mIv'})
    check('function', 'void operator*=()', {1: 'mul-assign-operator', 2: 'mLv'})
    check('function', 'void operator/=()', {1: 'div-assign-operator', 2: 'dVv'})
    check('function', 'void operator%=()', {1: 'mod-assign-operator', 2: 'rMv'})
    check('function', 'void operator&=()', {1: 'and-assign-operator', 2: 'aNv'})
    check('function', 'void operator and_eq()', {2: 'aNv'})
    check('function', 'void operator|=()', {1: 'or-assign-operator', 2: 'oRv'})
    check('function', 'void operator or_eq()', {2: 'oRv'})
    check('function', 'void operator^=()', {1: 'xor-assign-operator', 2: 'eOv'})
    check('function', 'void operator xor_eq()', {2: 'eOv'})
    check('function', 'void operator<<()', {1: 'lshift-operator', 2: 'lsv'})
    check('function', 'void operator>>()', {1: 'rshift-operator', 2: 'rsv'})
    check('function', 'void operator<<=()', {1: 'lshift-assign-operator', 2: 'lSv'})
    check('function', 'void operator>>=()', {1: 'rshift-assign-operator', 2: 'rSv'})
    check('function', 'void operator==()', {1: 'eq-operator', 2: 'eqv'})
    check('function', 'void operator!=()', {1: 'neq-operator', 2: 'nev'})
    check('function', 'void operator not_eq()', {2: 'nev'})
    check('function', 'void operator<()', {1: 'lt-operator', 2: 'ltv'})
    check('function', 'void operator>()', {1: 'gt-operator', 2: 'gtv'})
    check('function', 'void operator<=()', {1: 'lte-operator', 2: 'lev'})
    check('function', 'void operator>=()', {1: 'gte-operator', 2: 'gev'})
    check('function', 'void operator<=>()', {2: 'ssv'})
    check('function', 'void operator!()', {1: 'not-operator', 2: 'ntv'})
    check('function', 'void operator not()', {2: 'ntv'})
    check('function', 'void operator&&()', {1: 'sand-operator', 2: 'aav'})
    check('function', 'void operator and()', {2: 'aav'})
    check('function', 'void operator||()', {1: 'sor-operator', 2: 'oov'})
    check('function', 'void operator or()', {2: 'oov'})
    check('function', 'void operator++()', {1: 'inc-operator', 2: 'ppv'})
    check('function', 'void operator--()', {1: 'dec-operator', 2: 'mmv'})
    check('function', 'void operator,()', {1: 'comma-operator', 2: 'cmv'})
    check(
        'function', 'void operator->*()', {1: 'pointer-by-pointer-operator', 2: 'pmv'}
    )
    check('function', 'void operator->()', {1: 'pointer-operator', 2: 'ptv'})
    check('function', 'void operator()()', {1: 'call-operator', 2: 'clv'})
    check('function', 'void operator[]()', {1: 'subscript-operator', 2: 'ixv'})


def test_domain_cpp_ast_nested_name():
    check('class', '{key}::A', {1: 'A', 2: '1A'})
    check('class', '{key}::A::B', {1: 'A::B', 2: 'N1A1BE'})
    check('function', 'void f(::A a)', {1: 'f__A', 2: '1f1A'})
    check('function', 'void f(::A::B a)', {1: 'f__A::B', 2: '1fN1A1BE'})


def test_domain_cpp_ast_class_definitions():
    check('class', 'public A', {1: 'A', 2: '1A'}, output='{key}A')
    check('class', 'private {key}A', {1: 'A', 2: '1A'})
    check('class', '{key}A final', {1: 'A', 2: '1A'})

    # test bases
    check('class', '{key}A', {1: 'A', 2: '1A'})
    check('class', '{key}A::B::C', {1: 'A::B::C', 2: 'N1A1B1CE'})
    check('class', '{key}A : B', {1: 'A', 2: '1A'})
    check('class', '{key}A : private B', {1: 'A', 2: '1A'})
    check('class', '{key}A : public B', {1: 'A', 2: '1A'})
    check('class', '{key}A : B, C', {1: 'A', 2: '1A'})
    check('class', '{key}A : B, protected C, D', {1: 'A', 2: '1A'})
    check(
        'class',
        'A : virtual private B',
        {1: 'A', 2: '1A'},
        output='{key}A : private virtual B',
    )
    check('class', '{key}A : private virtual B', {1: 'A', 2: '1A'})
    check('class', '{key}A : B, virtual C', {1: 'A', 2: '1A'})
    check('class', '{key}A : public virtual B', {1: 'A', 2: '1A'})
    check('class', '{key}A : B, C...', {1: 'A', 2: '1A'})
    check('class', '{key}A : B..., C', {1: 'A', 2: '1A'})

    # from #4094
    check(
        'class',
        'template<class, class = std::void_t<>> {key}has_var',
        {2: 'I00E7has_var'},
    )
    check(
        'class',
        'template<class T> {key}has_var<T, std::void_t<decltype(&T::var)>>',
        {2: 'I0E7has_varI1TNSt6void_tIDTadN1T3varEEEEE'},
    )

    check(
        'class',
        'template<typename ...Ts> {key}T<int (*)(Ts)...>',
        {2: 'IDpE1TIJPFi2TsEEE'},
    )
    check(
        'class',
        'template<int... Is> {key}T<(Is)...>',
        {2: 'I_DpiE1TIJX(Is)EEE', 3: 'I_DpiE1TIJX2IsEEE'},
    )


def test_domain_cpp_ast_union_definitions():
    check('union', '{key}A', {2: '1A'})


def test_domain_cpp_ast_enum_definitions():
    check('enum', '{key}A', {2: '1A'})
    check('enum', '{key}A : std::underlying_type<B>::type', {2: '1A'})
    check('enum', '{key}A : unsigned int', {2: '1A'})
    check('enum', 'public A', {2: '1A'}, output='{key}A')
    check('enum', 'private {key}A', {2: '1A'})

    check('enumerator', '{key}A', {2: '1A'})
    check('enumerator', '{key}A = std::numeric_limits<unsigned long>::max()', {2: '1A'})


def test_domain_cpp_ast_anon_definitions():
    check('class', '@a', {3: 'Ut1_a'}, as_text_output='class [anonymous]')
    check('union', '@a', {3: 'Ut1_a'}, as_text_output='union [anonymous]')
    check('enum', '@a', {3: 'Ut1_a'}, as_text_output='enum [anonymous]')
    check('class', '@1', {3: 'Ut1_1'}, as_text_output='class [anonymous]')
    check('class', '@a::A', {3: 'NUt1_a1AE'}, as_text_output='class [anonymous]::A')

    check(
        'function',
        'int f(int @a)',
        {1: 'f__i', 2: '1fi'},
        as_text_output='int f(int [anonymous])',
    )


def test_domain_cpp_ast_templates():
    check('class', 'A<T>', {2: 'IE1AI1TE'}, output='template<> {key}A<T>')
    # first just check which objects support templating
    check('class', 'template<> {key}A', {2: 'IE1A'})
    check('function', 'template<> void A()', {2: 'IE1Av', 4: 'IE1Avv'})
    check('member', 'template<> A a', {2: 'IE1a'})
    check('type', 'template<> {key}a = A', {2: 'IE1a'}, key='using')
    with pytest.raises(DefinitionError):
        parse('enum', 'template<> A')
    with pytest.raises(DefinitionError):
        parse('enumerator', 'template<> A')
    # then all the real tests
    check('class', 'template<typename T1, typename T2> {key}A', {2: 'I00E1A'})
    check('type', 'template<> {key}a', {2: 'IE1a'}, key='using')

    check('class', 'template<typename T> {key}A', {2: 'I0E1A'})
    check('class', 'template<class T> {key}A', {2: 'I0E1A'})
    check('class', 'template<typename ...T> {key}A', {2: 'IDpE1A'})
    check('class', 'template<typename...> {key}A', {2: 'IDpE1A'})
    check('class', 'template<typename = Test> {key}A', {2: 'I0E1A'})
    check('class', 'template<typename T = Test> {key}A', {2: 'I0E1A'})

    check('class', 'template<template<typename> typename T> {key}A', {2: 'II0E0E1A'})
    check('class', 'template<template<typename> class T> {key}A', {2: 'II0E0E1A'})
    check('class', 'template<template<typename> typename> {key}A', {2: 'II0E0E1A'})
    check(
        'class',
        'template<template<typename> typename ...T> {key}A',
        {2: 'II0EDpE1A'},
    )
    check('class', 'template<template<typename> typename...> {key}A', {2: 'II0EDpE1A'})
    check(
        'class',
        'template<typename T, template<typename> typename...> {key}A',
        {2: 'I0I0EDpE1A'},
    )

    check('class', 'template<int> {key}A', {2: 'I_iE1A'})
    check('class', 'template<int T> {key}A', {2: 'I_iE1A'})
    check('class', 'template<int... T> {key}A', {2: 'I_DpiE1A'})
    check('class', 'template<int T = 42> {key}A', {2: 'I_iE1A'})
    check('class', 'template<int = 42> {key}A', {2: 'I_iE1A'})

    check('class', 'template<typename A<B>::C> {key}A', {2: 'I_N1AI1BE1CEE1A'})
    check('class', 'template<typename A<B>::C = 42> {key}A', {2: 'I_N1AI1BE1CEE1A'})
    # from #7944
    check(
        'function',
        'template<typename T, '
        'typename std::enable_if<!has_overloaded_addressof<T>::value, bool>::type = false'
        '> constexpr T *static_addressof(T &ref)',
        {
            2: 'I0_NSt9enable_ifIX!has_overloaded_addressof<T>::valueEbE4typeEE16static_addressofR1T',
            3: 'I0_NSt9enable_ifIXntN24has_overloaded_addressofI1TE5valueEEbE4typeEE16static_addressofR1T',
            4: 'I0_NSt9enable_ifIXntN24has_overloaded_addressofI1TE5valueEEbE4typeEE16static_addressofP1TR1T',
        },
    )

    check('class', 'template<> {key}A<NS::B<>>', {2: 'IE1AIN2NS1BIEEE'})

    # from #2058
    check(
        'function',
        'template<typename Char, typename Traits> '
        'inline std::basic_ostream<Char, Traits> &operator<<('
        'std::basic_ostream<Char, Traits> &os, '
        'const c_string_view_base<const Char, Traits> &str)',
        {
            2: 'I00ElsRNSt13basic_ostreamI4Char6TraitsEE'
            'RK18c_string_view_baseIK4Char6TraitsE',
            4: 'I00Els'
            'RNSt13basic_ostreamI4Char6TraitsEE'
            'RNSt13basic_ostreamI4Char6TraitsEE'
            'RK18c_string_view_baseIK4Char6TraitsE',
        },
    )

    # template introductions
    with pytest.raises(DefinitionError):
        parse('enum', 'abc::ns::foo{id_0, id_1, id_2} A')
    with pytest.raises(DefinitionError):
        parse('enumerator', 'abc::ns::foo{id_0, id_1, id_2} A')
    check(
        'class',
        'abc::ns::foo{{id_0, id_1, id_2}} {key}xyz::bar',
        {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE'},
    )
    check(
        'class',
        'abc::ns::foo{{id_0, id_1, ...id_2}} {key}xyz::bar',
        {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE'},
    )
    check(
        'class',
        'abc::ns::foo{{id_0, id_1, id_2}} {key}xyz::bar<id_0, id_1, id_2>',
        {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE'},
    )
    check(
        'class',
        'abc::ns::foo{{id_0, id_1, ...id_2}} {key}xyz::bar<id_0, id_1, id_2...>',
        {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE'},
    )

    check(
        'class',
        'template<> Concept{{U}} {key}A<int>::B',
        {2: 'IEI0EX7ConceptI1UEEN1AIiE1BE'},
    )

    check(
        'type',
        'abc::ns::foo{{id_0, id_1, id_2}} {key}xyz::bar = ghi::qux',
        {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE'},
        key='using',
    )
    check(
        'type',
        'abc::ns::foo{{id_0, id_1, ...id_2}} {key}xyz::bar = ghi::qux',
        {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE'},
        key='using',
    )
    check(
        'function',
        'abc::ns::foo{id_0, id_1, id_2} void xyz::bar()',
        {
            2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barEv',
            4: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barEvv',
        },
    )
    check(
        'function',
        'abc::ns::foo{id_0, id_1, ...id_2} void xyz::bar()',
        {
            2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barEv',
            4: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barEvv',
        },
    )
    check(
        'member',
        'abc::ns::foo{id_0, id_1, id_2} ghi::qux xyz::bar',
        {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE'},
    )
    check(
        'member',
        'abc::ns::foo{id_0, id_1, ...id_2} ghi::qux xyz::bar',
        {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE'},
    )
    check(
        'concept', 'Iterator{{T, U}} {key}Another', {2: 'I00EX8IteratorI1T1UEE7Another'}
    )
    check(
        'concept',
        'template<typename ...Pack> {key}Numerics = (... && Numeric<Pack>)',
        {2: 'IDpE8Numerics'},
    )

    # explicit specializations of members
    check('member', 'template<> int A<int>::a', {2: 'IEN1AIiE1aE'})
    # same as above
    check(
        'member',
        'template int A<int>::a',
        {2: 'IEN1AIiE1aE'},
        output='template<> int A<int>::a',
    )
    check(
        'member',
        'template<> template<> int A<int>::B<int>::b',
        {2: 'IEIEN1AIiE1BIiE1bE'},
    )
    # same as above
    check(
        'member',
        'template int A<int>::B<int>::b',
        {2: 'IEIEN1AIiE1BIiE1bE'},
        output='template<> template<> int A<int>::B<int>::b',
    )

    # defaulted constrained type parameters
    check('type', 'template<C T = int&> {key}A', {2: 'I_1CE1A'}, key='using')

    # pack expansion after non-type template parameter
    check(
        'type',
        'template<int (X::*)(bool)...> {key}A',
        {2: 'I_DpM1XFibEE1A'},
        key='using',
    )


def test_domain_cpp_ast_placeholder_types():
    check(
        'function', 'void f(Sortable auto &v)', {1: 'f__SortableR', 2: '1fR8Sortable'}
    )
    check(
        'function',
        'void f(const Sortable auto &v)',
        {1: 'f__SortableCR', 2: '1fRK8Sortable'},
    )
    check(
        'function',
        'void f(Sortable decltype(auto) &v)',
        {1: 'f__SortableR', 2: '1fR8Sortable'},
    )
    check(
        'function',
        'void f(const Sortable decltype(auto) &v)',
        {1: 'f__SortableCR', 2: '1fRK8Sortable'},
    )
    check(
        'function',
        'void f(Sortable decltype ( auto ) &v)',
        {1: 'f__SortableR', 2: '1fR8Sortable'},
        output='void f(Sortable decltype(auto) &v)',
    )


def test_domain_cpp_ast_requires_clauses():
    check(
        'function',
        'template<typename T> requires A auto f() -> void requires B',
        {4: 'I0EIQaa1A1BE1fvv'},
    )
    check(
        'function',
        'template<typename T> requires A || B or C void f()',
        {4: 'I0EIQoo1Aoo1B1CE1fvv'},
    )
    check('function', 'void f() requires A || B || C', {4: 'IQoo1Aoo1B1CE1fv'})
    check('function', 'Foo() requires A || B || C', {4: 'IQoo1Aoo1B1CE3Foov'})
    check(
        'function',
        'template<typename T> requires A && B || C and D void f()',
        {4: 'I0EIQooaa1A1Baa1C1DE1fvv'},
    )
    check(
        'function',
        'template<typename T> requires R<T> '
        'template<typename U> requires S<T> '
        'void A<T>::f() requires B',
        {4: 'I0EIQ1RI1TEEI0EIQaa1SI1TE1BEN1A1fEvv'},
    )
    check(
        'function',
        'template<template<typename T> requires R<T> typename X> void f()',
        {2: 'II0EIQ1RI1TEE0E1fv', 4: 'II0EIQ1RI1TEE0E1fvv'},
    )
    check(
        'type',
        'template<typename T> requires IsValid<T> {key}T = true_type',
        {4: 'I0EIQ7IsValidI1TEE1T'},
        key='using',
    )
    check(
        'class',
        'template<typename T> requires IsValid<T> {key}T : Base',
        {4: 'I0EIQ7IsValidI1TEE1T'},
        key='class',
    )
    check(
        'union',
        'template<typename T> requires IsValid<T> {key}T',
        {4: 'I0EIQ7IsValidI1TEE1T'},
        key='union',
    )
    check(
        'member',
        'template<typename T> requires IsValid<T> int Val = 7',
        {4: 'I0EIQ7IsValidI1TEE3Val'},
    )


def test_domain_cpp_ast_template_args():
    # from breathe#218
    check(
        'function',
        'template<typename F> void allow(F *f, typename func<F, B, G != 1>::type tt)',
        {
            2: 'I0E5allowP1FN4funcI1F1BXG != 1EE4typeE',
            3: 'I0E5allowP1FN4funcI1F1BXne1GL1EEE4typeE',
            4: 'I0E5allowvP1FN4funcI1F1BXne1GL1EEE4typeE',
        },
    )
    # from #3542
    check(
        'type',
        'template<typename T> {key}'
        'enable_if_not_array_t = std::enable_if_t<!is_array<T>::value, int>',
        {2: 'I0E21enable_if_not_array_t'},
        key='using',
    )


def test_domain_cpp_ast_initializers():
    ids_member = {1: 'v__T', 2: '1v'}
    ids_function = {1: 'f__T', 2: '1f1T'}
    ids_template = {2: 'I_1TE1fv', 4: 'I_1TE1fvv'}
    # no init
    check('member', 'T v', ids_member)
    check('function', 'void f(T v)', ids_function)
    check('function', 'template<T v> void f()', ids_template)
    # with '=', assignment-expression
    check('member', 'T v = 42', ids_member)
    check('function', 'void f(T v = 42)', ids_function)
    check('function', 'template<T v = 42> void f()', ids_template)
    # with '=', braced-init
    check('member', 'T v = {}', ids_member)
    check('function', 'void f(T v = {})', ids_function)
    check('function', 'template<T v = {}> void f()', ids_template)
    check('member', 'T v = {42, 42, 42}', ids_member)
    check('function', 'void f(T v = {42, 42, 42})', ids_function)
    check('function', 'template<T v = {42, 42, 42}> void f()', ids_template)
    check('member', 'T v = {42, 42, 42,}', ids_member)
    check('function', 'void f(T v = {42, 42, 42,})', ids_function)
    check('function', 'template<T v = {42, 42, 42,}> void f()', ids_template)
    check('member', 'T v = {42, 42, args...}', ids_member)
    check('function', 'void f(T v = {42, 42, args...})', ids_function)
    check('function', 'template<T v = {42, 42, args...}> void f()', ids_template)
    # without '=', braced-init
    check('member', 'T v{}', ids_member)
    check('member', 'T v{42, 42, 42}', ids_member)
    check('member', 'T v{42, 42, 42,}', ids_member)
    check('member', 'T v{42, 42, args...}', ids_member)
    # other
    check('member', 'T v = T{}', ids_member)


def test_domain_cpp_ast_attributes():
    # style: C++
    check('member', '[[]] int f', {1: 'f__i', 2: '1f'})
    check(
        'member',
        '[ [ ] ] int f',
        {1: 'f__i', 2: '1f'},
        # this will fail when the proper grammar is implemented
        output='[[ ]] int f',
    )
    check('member', '[[a]] int f', {1: 'f__i', 2: '1f'})
    # style: GNU
    check('member', '__attribute__(()) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((a)) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((a, b)) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((optimize(3))) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((format(printf, 1, 2))) int f', {1: 'f__i', 2: '1f'})
    # style: user-defined id
    check('member', 'id_attr int f', {1: 'f__i', 2: '1f'})
    # style: user-defined paren
    check('member', 'paren_attr() int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr(a) int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr("") int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr(()[{}][]{}) int f', {1: 'f__i', 2: '1f'})
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr(() int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr([) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr({) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr([)]) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr((])) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr({]}) int f')

    # position: decl specs
    check(
        'function',
        'static inline __attribute__(()) void f()',
        {1: 'f', 2: '1fv'},
        output='__attribute__(()) static inline void f()',
    )
    check('function', '[[attr1]] [[attr2]] void f()', {1: 'f', 2: '1fv'})
    # position: declarator
    check('member', 'int *[[attr1]] [[attr2]] i', {1: 'i__iP', 2: '1i'})
    check(
        'member',
        'int *const [[attr1]] [[attr2]] volatile i',
        {1: 'i__iPVC', 2: '1i'},
        output='int *[[attr1]] [[attr2]] volatile const i',
    )
    check('member', 'int &[[attr1]] [[attr2]] i', {1: 'i__iR', 2: '1i'})
    check('member', 'int *[[attr1]] [[attr2]] *i', {1: 'i__iPP', 2: '1i'})
    # position: parameters and qualifiers
    check('function', 'void f() [[attr1]] [[attr2]]', {1: 'f', 2: '1fv'})

    # position: class, union, enum
    check('class', '{key}[[attr1]] [[attr2]] Foo', {1: 'Foo', 2: '3Foo'}, key='class')
    check('union', '{key}[[attr1]] [[attr2]] Foo', {2: '3Foo'}, key='union')
    check('enum', '{key}[[attr1]] [[attr2]] Foo', {2: '3Foo'}, key='enum')
    # position: enumerator
    check('enumerator', '{key}Foo [[attr1]] [[attr2]]', {2: '3Foo'})
    check('enumerator', '{key}Foo [[attr1]] [[attr2]] = 42', {2: '3Foo'})


def check_ast_xref_parsing(target):
    class Config:
        cpp_id_attributes = ['id_attr']
        cpp_paren_attributes = ['paren_attr']

    parser = DefinitionParser(target, location='', config=Config())
    parser.parse_xref_object()
    parser.assert_end()


def test_domain_cpp_ast_xref_parsing():
    check_ast_xref_parsing('f')
    check_ast_xref_parsing('f()')
    check_ast_xref_parsing('void f()')
    check_ast_xref_parsing('T f()')


@pytest.mark.parametrize(
    ('param', 'is_pack'),
    [
        ('typename', False),
        ('typename T', False),
        ('typename...', True),
        ('typename... T', True),
        ('int', False),
        ('int N', False),
        ('int* N', False),
        ('int& N', False),
        ('int&... N', True),
        ('int*... N', True),
        ('int...', True),
        ('int... N', True),
        ('auto', False),
        ('auto...', True),
        ('int X::*', False),
        ('int X::*...', True),
        ('int (X::*)(bool)', False),
        ('int (X::*x)(bool)', False),
        ('int (X::*)(bool)...', True),
        ('template<typename> class', False),
        ('template<typename> class...', True),
    ],
)
def test_domain_cpp_template_parameters_is_pack(param: str, is_pack: bool):
    def parse_template_parameter(param: str):
        ast = parse('type', 'template<' + param + '> X')
        return ast.templatePrefix.templates[0].params[0]

    ast = parse_template_parameter(param)
    assert ast.isPack == is_pack


# def test_print():
#     # used for getting all the ids out for checking
#     for a in ids:
#         print(a)
#     raise DefinitionError


def filter_warnings(warning: StringIO, file):
    lines = warning.getvalue().split('\n')
    res = [
        l
        for l in lines
        if 'domain-cpp' in l
        and f'{file}.rst' in l
        and "WARNING: document isn't included in any toctree" not in l
    ]
    print(f"Filtered warnings for file '{file}':")
    for w in res:
        print(w)
    return res


@pytest.mark.sphinx('html', testroot='domain-cpp', confoverrides={'nitpicky': True})
def test_domain_cpp_build_multi_decl_lookup(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'lookup-key-overload')
    assert len(ws) == 0

    ws = filter_warnings(app.warning, 'multi-decl-lookup')
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='domain-cpp', confoverrides={'nitpicky': True})
def test_domain_cpp_build_warn_template_param_qualified_name(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'warn-template-param-qualified-name')
    assert len(ws) == 2
    assert 'WARNING: cpp:type reference target not found: T::typeWarn' in ws[0]
    assert 'WARNING: cpp:type reference target not found: T::U::typeWarn' in ws[1]


@pytest.mark.sphinx('html', testroot='domain-cpp', confoverrides={'nitpicky': True})
def test_domain_cpp_build_backslash_ok_true(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'backslash')
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='domain-cpp', confoverrides={'nitpicky': True})
def test_domain_cpp_build_semicolon(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'semicolon')
    assert len(ws) == 0


@pytest.mark.sphinx(
    'html',
    testroot='domain-cpp',
    confoverrides={'nitpicky': True, 'strip_signature_backslash': True},
)
def test_domain_cpp_build_backslash_ok_false(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'backslash')
    assert len(ws) == 1
    assert 'WARNING: Parsing of expression failed. Using fallback parser.' in ws[0]


@pytest.mark.sphinx('html', testroot='domain-cpp', confoverrides={'nitpicky': True})
def test_domain_cpp_build_anon_dup_decl(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'anon-dup-decl')
    assert len(ws) == 2
    assert 'WARNING: cpp:identifier reference target not found: @a' in ws[0]
    assert 'WARNING: cpp:identifier reference target not found: @b' in ws[1]


@pytest.mark.sphinx('html', testroot='domain-cpp')
def test_domain_cpp_build_misuse_of_roles(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'roles-targets-ok')
    assert len(ws) == 0

    ws = filter_warnings(app.warning, 'roles-targets-warn')
    # the roles that should be able to generate warnings:
    all_roles = [
        'class',
        'struct',
        'union',
        'func',
        'member',
        'var',
        'type',
        'concept',
        'enum',
        'enumerator',
    ]
    ok = [  # target_type, ok_roles
        ('class', ['class', 'struct', 'type']),
        ('union', ['union', 'type']),
        ('func', ['func', 'type']),
        ('member', ['member', 'var']),
        ('type', ['type']),
        ('concept', ['concept']),
        ('enum', ['type', 'enum']),
        ('enumerator', ['enumerator']),
        ('functionParam', ['member', 'var']),
        ('templateParam', ['class', 'struct', 'union', 'member', 'var', 'type']),
    ]
    warn = []
    for target_type, roles in ok:
        txt_target_type = 'function' if target_type == 'func' else target_type
        for r in all_roles:
            if r not in roles:
                warn.append(f'WARNING: cpp:{r} targets a {txt_target_type} (')
                if target_type == 'templateParam':
                    warn.extend((
                        f'WARNING: cpp:{r} targets a {txt_target_type} (',
                        f'WARNING: cpp:{r} targets a {txt_target_type} (',
                    ))
    warn = sorted(warn)
    for w in ws:
        assert 'targets a' in w
    ws = [w[w.index('WARNING:') :] for w in ws]
    ws = sorted(ws)
    print('Expected warnings:')
    for w in warn:
        print(w)
    print('Actual warnings:')
    for w in ws:
        print(w)

    for i in range(min(len(warn), len(ws))):
        assert ws[i].startswith(warn[i])

    assert len(ws) == len(warn)


@pytest.mark.sphinx(
    'html',
    testroot='domain-cpp',
    confoverrides={'add_function_parentheses': True},
)
def test_domain_cpp_build_with_add_function_parentheses_is_True(app):
    app.build(force_all=True)

    role_patterns = [
        'Sphinx',
        'Sphinx::version',
        'version',
        'List',
        'MyEnum',
    ]
    paren_patterns = [
        ('ref function without parens ', r'paren_1\(\)'),
        ('ref function with parens ', r'paren_2\(\)'),
        ('ref function without parens, explicit title ', 'paren_3_title'),
        ('ref function with parens, explicit title ', 'paren_4_title'),
        ('ref op call without parens ', r'paren_5::operator\(\)\(\)'),
        ('ref op call with parens ', r'paren_6::operator\(\)\(\)'),
        ('ref op call without parens, explicit title ', 'paren_7_title'),
        ('ref op call with parens, explicit title ', 'paren_8_title'),
    ]

    text = (app.outdir / 'roles.html').read_text(encoding='utf8')
    for ref_text in role_patterns:
        pattern = (
            f'<li><p><a .*?><code .*?><span .*?>{ref_text}</span></code></a></p></li>'
        )
        match = re.search(pattern, text)
        assert match is not None, f'Pattern not found in roles.html:\n\t{pattern}'
    for desc_text, ref_text in paren_patterns:
        pattern = f'<li><p>{desc_text}<a .*?><code .*?><span .*?>{ref_text}</span></code></a></p></li>'
        match = re.search(pattern, text)
        assert match is not None, f'Pattern not found in roles.html:\n\t{pattern}'

    text = (app.outdir / 'any-role.html').read_text(encoding='utf8')
    for desc_text, ref_text in paren_patterns:
        pattern = f'<li><p>{desc_text}<a .*?><code .*?><span .*?>{ref_text}</span></code></a></p></li>'
        match = re.search(pattern, text)
        assert match is not None, f'Pattern not found in any-role.html:\n\t{pattern}'


@pytest.mark.sphinx(
    'html',
    testroot='domain-cpp',
    confoverrides={'add_function_parentheses': False},
)
def test_domain_cpp_build_with_add_function_parentheses_is_False(app):
    app.build(force_all=True)

    role_patterns = [
        'Sphinx',
        'Sphinx::version',
        'version',
        'List',
        'MyEnum',
    ]
    paren_patterns = [
        ('ref function without parens ', 'paren_1'),
        ('ref function with parens ', 'paren_2'),
        ('ref function without parens, explicit title ', 'paren_3_title'),
        ('ref function with parens, explicit title ', 'paren_4_title'),
        ('ref op call without parens ', r'paren_5::operator\(\)'),
        ('ref op call with parens ', r'paren_6::operator\(\)'),
        ('ref op call without parens, explicit title ', 'paren_7_title'),
        ('ref op call with parens, explicit title ', 'paren_8_title'),
    ]

    text = (app.outdir / 'roles.html').read_text(encoding='utf8')
    for ref_text in role_patterns:
        pattern = (
            f'<li><p><a .*?><code .*?><span .*?>{ref_text}</span></code></a></p></li>'
        )
        match = re.search(pattern, text)
        assert match is not None, f'Pattern not found in roles.html:\n\t{pattern}'
    for desc_text, ref_text in paren_patterns:
        pattern = f'<li><p>{desc_text}<a .*?><code .*?><span .*?>{ref_text}</span></code></a></p></li>'
        match = re.search(pattern, text)
        assert match is not None, f'Pattern not found in roles.html:\n\t{pattern}'

    text = (app.outdir / 'any-role.html').read_text(encoding='utf8')
    for desc_text, ref_text in paren_patterns:
        pattern = f'<li><p>{desc_text}<a .*?><code .*?><span .*?>{ref_text}</span></code></a></p></li>'
        match = re.search(pattern, text)
        assert match is not None, f'Pattern not found in any-role.html:\n\t{pattern}'


@pytest.mark.sphinx('html', testroot='domain-cpp')
def test_domain_cpp_build_xref_consistency(app):
    app.build(force_all=True)

    test = 'xref_consistency.html'
    output = (app.outdir / test).read_text(encoding='utf8')

    def classes(role, tag):
        pattern = (
            rf'{role}-role:.*?'
            rf'<(?P<tag>{tag}) .*?class=["\'](?P<classes>.*?)["\'].*?>'
            r'.*'
            r'</(?P=tag)>'
        )
        result = re.search(pattern, output)
        expect = f"""\
Pattern for role `{role}` with tag `{tag}`
\t{pattern}
not found in `{test}`
"""
        assert result, expect
        return set(result.group('classes').split())

    class RoleClasses:
        """Collect the classes from the layout that was generated for a given role."""

        def __init__(self, role, root, contents):
            self.name = role
            self.classes = classes(role, root)
            self.content_classes = {}
            for tag in contents:
                self.content_classes[tag] = classes(role, tag)

    # not actually used as a reference point
    # code_role = RoleClasses('code', 'code', [])
    any_role = RoleClasses('any', 'a', ['code'])
    cpp_any_role = RoleClasses('cpp-any', 'a', ['code'])
    # NYI: consistent looks
    # texpr_role = RoleClasses('cpp-texpr', 'span', ['a', 'code'])
    expr_role = RoleClasses('cpp-expr', 'span', ['a'])
    texpr_role = RoleClasses('cpp-texpr', 'span', ['a', 'span'])

    # XRefRole-style classes

    # any and cpp:any do not put these classes at the root

    # n.b. the generic any machinery finds the specific 'cpp-class' object type
    any_role_classes = any_role.content_classes['code']
    expect = 'any uses XRefRole classes'
    assert {'xref', 'any', 'cpp', 'cpp-class'} <= any_role_classes, expect

    cpp_any_role_classes = cpp_any_role.content_classes['code']
    expect = 'cpp:any uses XRefRole classes'
    assert {'xref', 'cpp-any', 'cpp'} <= cpp_any_role_classes, expect

    for role in (expr_role, texpr_role):
        name = role.name
        expect = f'`{name}` puts the domain and role classes at its root'
        assert {'sig', 'sig-inline', 'cpp', name} <= role.classes, expect

    # reference classes

    expect = 'the xref roles use the same reference classes'
    assert any_role.classes == cpp_any_role.classes, expect
    assert any_role.classes == expr_role.content_classes['a'], expect
    assert any_role.classes == texpr_role.content_classes['a'], expect


@pytest.mark.sphinx('html', testroot='domain-cpp', confoverrides={'nitpicky': True})
def test_domain_cpp_build_field_role(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'field-role')
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='domain-cpp', confoverrides={'nitpicky': True})
def test_domain_cpp_build_operator_lookup(app):
    app.builder.build_all()
    ws = filter_warnings(app.warning, 'operator-lookup')
    assert len(ws) == 5
    # TODO: the first one should not happen
    assert ':10: WARNING: cpp:identifier reference target not found: _lit' in ws[0]
    assert ':18: WARNING: cpp:func reference target not found: int h' in ws[1]
    assert (
        ':19: WARNING: cpp:func reference target not found: int operator+(bool, bool)'
    ) in ws[2]
    assert (
        ':20: WARNING: cpp:func reference target not found: int operator""_udl'
    ) in ws[3]
    assert ':21: WARNING: cpp:func reference target not found: operator bool' in ws[4]


@pytest.mark.sphinx(
    'html', testroot='domain-cpp-intersphinx', confoverrides={'nitpicky': True}
)
def test_domain_cpp_build_intersphinx(tmp_path, app):
    orig_source = """\
.. cpp:class:: _class
.. cpp:struct:: _struct
.. cpp:union:: _union
.. cpp:function:: void _function()
.. cpp:member:: int _member
.. cpp:var:: int _var
.. cpp:type:: _type
.. cpp:concept:: template<typename T> _concept
.. cpp:enum:: _enum

    .. cpp:enumerator:: _enumerator

.. cpp:enum-struct:: _enumStruct

    .. cpp:enumerator:: _scopedEnumerator

.. cpp:enum-class:: _enumClass
.. cpp:function:: void _functionParam(int param)
.. cpp:function:: template<typename TParam> void _templateParam()
"""
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(
        b"""\
# Sphinx inventory version 2
# Project: C Intersphinx Test
# Version:
# The remainder of this file is compressed using zlib.
"""
        + zlib.compress(b"""\
_class cpp:class 1 index.html#_CPPv46$ -
_concept cpp:concept 1 index.html#_CPPv4I0E8$ -
_concept::T cpp:templateParam 1 index.html#_CPPv4I0E8_concept -
_enum cpp:enum 1 index.html#_CPPv45$ -
_enum::_enumerator cpp:enumerator 1 index.html#_CPPv4N5_enum11_enumeratorE -
_enumClass cpp:enum 1 index.html#_CPPv410$ -
_enumStruct cpp:enum 1 index.html#_CPPv411$ -
_enumStruct::_scopedEnumerator cpp:enumerator 1 index.html#_CPPv4N11_enumStruct17_scopedEnumeratorE -
_enumerator cpp:enumerator 1 index.html#_CPPv4N5_enum11_enumeratorE -
_function cpp:function 1 index.html#_CPPv49_functionv -
_functionParam cpp:function 1 index.html#_CPPv414_functionParami -
_functionParam::param cpp:functionParam 1 index.html#_CPPv414_functionParami -
_member cpp:member 1 index.html#_CPPv47$ -
_struct cpp:class 1 index.html#_CPPv47$ -
_templateParam cpp:function 1 index.html#_CPPv4I0E14_templateParamvv -
_templateParam::TParam cpp:templateParam 1 index.html#_CPPv4I0E14_templateParamvv -
_type cpp:type 1 index.html#_CPPv45$ -
_union cpp:union 1 index.html#_CPPv46$ -
_var cpp:member 1 index.html#_CPPv44$ -
""")
    )
    app.config.intersphinx_mapping = {
        'test': ('https://localhost/intersphinx/cpp/', str(inv_file)),
    }
    app.config.intersphinx_cache_limit = 0
    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'index')
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='root')
def test_domain_cpp_parse_no_index_entry(app):
    text = (
        '.. cpp:function:: void f()\n.. cpp:function:: void g()\n   :no-index-entry:\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('single', 'f (C++ function)', '_CPPv41fv', '', None)],
    )
    assert_node(doctree[2], addnodes.index, entries=[])


@pytest.mark.sphinx('html', testroot='root')
def test_domain_cpp_parse_mix_decl_duplicate(app):
    # Issue 8270
    text = '.. cpp:struct:: A\n.. cpp:function:: void A()\n.. cpp:struct:: A\n'
    restructuredtext.parse(app, text)
    ws = app.warning.getvalue().split('\n')
    assert len(ws) == 5
    assert (
        'index.rst:2: WARNING: Duplicate C++ declaration, also defined at index:1.'
    ) in ws[0]
    assert "Declaration is '.. cpp:function:: void A()'." in ws[1]
    assert (
        'index.rst:3: WARNING: Duplicate C++ declaration, also defined at index:1.'
    ) in ws[2]
    assert "Declaration is '.. cpp:struct:: A'." in ws[3]
    assert ws[4] == ''


# For some reason, using the default testroot of "root" leads to the contents of
# `test-root/objects.txt` polluting the symbol table depending on the test
# execution order.  Using a testroot of "config" seems to avoid that problem.
@pytest.mark.sphinx('html', testroot='config')
def test_domain_cpp_normalize_unspecialized_template_args(make_app, app_params):
    args, kwargs = app_params

    text1 = '.. cpp:class:: template <typename T> A\n'
    text2 = '.. cpp:class:: template <typename T> template <typename U> A<T>::B\n'

    app1 = make_app(*args, **kwargs)
    restructuredtext.parse(app=app1, text=text1, docname='text1')
    root1 = app1.env.domaindata['cpp']['root_symbol']

    assert root1.dump(1) == (
        '  ::\n'
        '    template<typename T> \n'
        '    A: {class} template<typename T> A\t(text1)\n'
        '      T: {templateParam} typename T\t(text1)\n'
    )

    app2 = make_app(*args, **kwargs)
    restructuredtext.parse(app=app2, text=text2, docname='text2')
    root2 = app2.env.domaindata['cpp']['root_symbol']

    assert root2.dump(1) == (
        '  ::\n'
        '    template<typename T> \n'
        '    A\n'
        '      T\n'
        '      template<typename U> \n'
        '      B: {class} template<typename T> template<typename U> A<T>::B\t(text2)\n'
        '        U: {templateParam} typename U\t(text2)\n'
    )

    root2.merge_with(root1, ['text1'], app2.env)

    assert root2.dump(1) == (
        '  ::\n'
        '    template<typename T> \n'
        '    A: {class} template<typename T> A\t(text1)\n'
        '      T: {templateParam} typename T\t(text1)\n'
        '      template<typename U> \n'
        '      B: {class} template<typename T> template<typename U> A<T>::B\t(text2)\n'
        '        U: {templateParam} typename U\t(text2)\n'
    )
    warning = app2._warning.getvalue()
    assert 'Internal C++ domain error during symbol merging' not in warning


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'cpp_maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cpp_function_signature_with_cpp_maximum_signature_line_length_equal(app):
    text = '.. cpp:function:: str hello(str name)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='cpp',
        objtype='function',
        no_index=False,
    )
    assert_node(
        doctree[1][0][0][3],
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'name'],
            ),
        ],
    )
    assert_node(
        doctree[1][0][0][3], desc_parameterlist, multi_line_parameter_list=False
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'cpp_maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cpp_function_signature_with_cpp_maximum_signature_line_length_force_single(
    app,
):
    text = '.. cpp:function:: str hello(str names)\n   :single-line-parameter-list:'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='cpp',
        objtype='function',
        no_index=False,
    )
    assert_node(
        doctree[1][0][0][3],
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(
        doctree[1][0][0][3], desc_parameterlist, multi_line_parameter_list=False
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'cpp_maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cpp_function_signature_with_cpp_maximum_signature_line_length_break(app):
    text = '.. cpp:function:: str hello(str names)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='cpp',
        objtype='function',
        no_index=False,
    )
    assert_node(
        doctree[1][0][0][3],
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(doctree[1][0][0][3], desc_parameterlist, multi_line_parameter_list=True)


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cpp_function_signature_with_maximum_signature_line_length_equal(app):
    text = '.. cpp:function:: str hello(str name)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='cpp',
        objtype='function',
        no_index=False,
    )
    assert_node(
        doctree[1][0][0][3],
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'name'],
            ),
        ],
    )
    assert_node(
        doctree[1][0][0][3], desc_parameterlist, multi_line_parameter_list=False
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cpp_function_signature_with_maximum_signature_line_length_force_single(app):
    text = '.. cpp:function:: str hello(str names)\n   :single-line-parameter-list:'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='cpp',
        objtype='function',
        no_index=False,
    )
    assert_node(
        doctree[1][0][0][3],
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(
        doctree[1][0][0][3], desc_parameterlist, multi_line_parameter_list=False
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cpp_function_signature_with_maximum_signature_line_length_break(app):
    text = '.. cpp:function:: str hello(str names)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='cpp',
        objtype='function',
        no_index=False,
    )
    assert_node(
        doctree[1][0][0][3],
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(doctree[1][0][0][3], desc_parameterlist, multi_line_parameter_list=True)


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'cpp_maximum_signature_line_length': len('str hello(str name)'),
        'maximum_signature_line_length': 1,
    },
)
def test_cpp_maximum_signature_line_length_overrides_global(app):
    text = '.. cpp:function:: str hello(str name)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        ([
                            desc_signature_line,
                            (
                                pending_xref,
                                desc_sig_space,
                                [desc_name, [desc_sig_name, 'hello']],
                                desc_parameterlist,
                            ),
                        ]),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='cpp',
        objtype='function',
        no_index=False,
    )
    assert_node(
        doctree[1][0][0][3],
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'name'],
            ),
        ],
    )
    assert_node(
        doctree[1][0][0][3], desc_parameterlist, multi_line_parameter_list=False
    )


@pytest.mark.sphinx('html', testroot='domain-cpp-cpp_maximum_signature_line_length')
def test_domain_cpp_cpp_maximum_signature_line_length_in_html(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf-8')
    expected = """\

<dl>
<dd>\
<span class="n"><span class="pre">str</span></span>\
<span class="w"> </span>\
<span class="n sig-param"><span class="pre">name</span></span>,\
</dd>
</dl>

<span class="sig-paren">)</span>\
<a class="headerlink" href=\
"""
    assert expected in content


@pytest.mark.sphinx(
    'text',
    testroot='domain-cpp-cpp_maximum_signature_line_length',
)
def test_domain_cpp_cpp_maximum_signature_line_length_in_text(app):
    app.build()
    content = (app.outdir / 'index.txt').read_text(encoding='utf8')
    param_line_fmt = STDINDENT * ' ' + '{}\n'

    expected_parameter_list_hello = '(\n{})'.format(param_line_fmt.format('str name,'))

    assert expected_parameter_list_hello in content


def check_symbol_resolution(
    app, defs: str, expr: str, expected_ids: str, expr_namespace: str | None = None
):
    text = textwrap.dedent(defs)
    if expr_namespace:
        text += f'\n\n.. cpp:namespace:: {expr_namespace}\n\n'
    text += f'\n\n:cpp:expr:`{expr}`\n'
    doctree = restructuredtext.parse(app, text)
    app.env.apply_post_transforms(doctree, 'index')
    ref_paragraph = doctree.children[-1]
    references = [x['refid'] for x in ref_paragraph.findall(condition=nodes.reference)]
    assert references == expected_ids


def test_domain_cpp_resolve_parent_template_arg_mismatch(app):
    check_symbol_resolution(
        app=app,
        defs="""
        .. cpp:class:: template <typename T> Foo

           .. cpp:class:: Bar
        """,
        expr='Foo<int>::Bar',
        expected_ids=['_CPPv4I0E3Foo', '_CPPv4N3Foo3BarE'],
    )
