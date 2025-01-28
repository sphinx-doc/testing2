from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.domains.cpp._ast import (
    ASTDeclaration,
    ASTNestedName,
    ASTNestedNameElement,
)
from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from typing import Any, NoReturn

    from sphinx.domains.cpp._ast import (
        ASTIdentifier,
        ASTOperator,
        ASTTemplateArgs,
        ASTTemplateDeclarationPrefix,
        ASTTemplateIntroduction,
        ASTTemplateParams,
    )
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)


class _DuplicateSymbolError(Exception):
    def __init__(self, symbol: Symbol, declaration: ASTDeclaration) -> None:
        assert symbol
        assert declaration
        self.symbol = symbol
        self.declaration = declaration

    def __str__(self) -> str:
        return 'Internal C++ duplicate symbol error:\n%s' % self.symbol.dump(0)


class SymbolLookupResult:
    __slots__ = (
        'symbols',
        'parent_symbol',
        'ident_or_op',
        'template_params',
        'template_args',
    )

    symbols: Iterable[Symbol]
    parent_symbol: Symbol
    ident_or_op: ASTIdentifier | ASTOperator
    template_params: Any
    template_args: ASTTemplateArgs

    def __init__(
        self,
        symbols: Iterable[Symbol],
        parent_symbol: Symbol,
        ident_or_op: ASTIdentifier | ASTOperator,
        template_params: Any,
        template_args: ASTTemplateArgs,
    ) -> None:
        self.symbols = symbols
        self.parent_symbol = parent_symbol
        self.ident_or_op = ident_or_op
        self.template_params = template_params
        self.template_args = template_args

    @property
    def parentSymbol(self) -> Symbol:
        return self.parent_symbol

    @property
    def identOrOp(self) -> ASTIdentifier | ASTOperator:
        return self.ident_or_op

    @property
    def templateParams(self) -> Any:
        return self.template_params

    @property
    def templateArgs(self) -> ASTTemplateArgs:
        return self.template_args


class LookupKey:
    __slots__ = ('data',)

    data: Sequence[
        tuple[
            ASTNestedNameElement,
            ASTTemplateParams | ASTTemplateIntroduction,
            str | None,
        ]
    ]

    def __init__(
        self,
        data: Sequence[
            tuple[
                ASTNestedNameElement,
                ASTTemplateParams | ASTTemplateIntroduction,
                str | None,
            ]
        ],
        /,
    ) -> None:
        self.data = data

    def __repr__(self) -> str:
        return f'LookupKey({self.data!r})'

    def __str__(self) -> str:
        inner = ', '.join(f'({ident}, {id_})' for ident, _, id_ in self.data)
        return f'[{inner}]'


def _is_specialization(
    template_params: ASTTemplateParams | ASTTemplateIntroduction,
    template_args: ASTTemplateArgs,
) -> bool:
    # Checks if `template_args` does not exactly match `template_params`.
    # the names of the template parameters must be given exactly as args
    # and params that are packs must in the args be the name expanded
    if len(template_params.params) != len(template_args.args):
        return True
    # having no template params and no arguments is also a specialization
    if len(template_params.params) == 0:
        return True
    for i in range(len(template_params.params)):
        param = template_params.params[i]
        arg = template_args.args[i]
        # TODO: doing this by string manipulation is probably not the most efficient
        param_name = str(param.name)
        arg_txt = str(arg)
        is_arg_pack_expansion = arg_txt.endswith('...')
        if param.isPack != is_arg_pack_expansion:
            return True
        arg_name = arg_txt[:-3] if is_arg_pack_expansion else arg_txt
        if param_name != arg_name:
            return True
    return False


class Symbol:
    debug_indent = 0
    debug_indent_string = '  '
    debug_lookup = False  # overridden by the corresponding config value
    debug_show_tree = False  # overridden by the corresponding config value

    def __copy__(self) -> NoReturn:
        raise AssertionError  # shouldn't happen

    def __deepcopy__(self, memo: Any) -> Symbol:
        if self.parent:
            raise AssertionError  # shouldn't happen
        # the domain base class makes a copy of the initial data, which is fine
        return Symbol(None, None, None, None, None, None, None)

    @staticmethod
    def debug_print(*args: Any) -> None:
        logger.debug(Symbol.debug_indent_string * Symbol.debug_indent, end='')
        logger.debug(*args)

    def _assert_invariants(self) -> None:
        if not self.parent:
            # parent == None means global scope, so declaration means a parent
            assert not self.identOrOp
            assert not self.templateParams
            assert not self.templateArgs
            assert not self.declaration
            assert not self.docname
        else:
            if self.declaration:
                assert self.docname

    def __setattr__(self, key: str, value: Any) -> None:
        if key == 'children':
            raise AssertionError
        return super().__setattr__(key, value)

    def __init__(
        self,
        parent: Symbol | None,
        identOrOp: ASTIdentifier | ASTOperator | None,
        templateParams: ASTTemplateParams | ASTTemplateIntroduction | None,
        templateArgs: Any,
        declaration: ASTDeclaration | None,
        docname: str | None,
        line: int | None,
    ) -> None:
        self.parent = parent
        # declarations in a single directive are linked together
        self.siblingAbove: Symbol | None = None
        self.siblingBelow: Symbol | None = None
        self.identOrOp = identOrOp
        # Ensure the same symbol for `A` is created for:
        #
        #     .. cpp:class:: template <typename T> class A
        #
        # and
        #
        #     .. cpp:function:: template <typename T> int A<T>::foo()
        if templateArgs is not None and not _is_specialization(
            templateParams, templateArgs
        ):
            templateArgs = None
        self.templateParams = templateParams  # template<templateParams>
        self.templateArgs = templateArgs  # identifier<templateArgs>
        self.declaration = declaration
        self.docname = docname
        self.line = line
        self.isRedeclaration = False
        self._assert_invariants()

        # Remember to modify Symbol.remove if modifications to the parent change.
        self._children: list[Symbol] = []
        self._anon_children: list[Symbol] = []
        # note: _children includes _anon_children
        if self.parent:
            self.parent._children.append(self)
        if self.declaration:
            self.declaration.symbol = self

        # Do symbol addition after self._children has been initialised.
        self._add_template_and_function_params()

    def __repr__(self) -> str:
        return f'<Symbol {self.to_string(indent=0)!r}>'

    def _fill_empty(self, declaration: ASTDeclaration, docname: str, line: int) -> None:
        self._assert_invariants()
        assert self.declaration is None
        assert self.docname is None
        assert self.line is None
        assert declaration is not None
        assert docname is not None
        assert line is not None
        self.declaration = declaration
        self.declaration.symbol = self
        self.docname = docname
        self.line = line
        self._assert_invariants()
        # and symbol addition should be done as well
        self._add_template_and_function_params()

    def _add_template_and_function_params(self) -> None:
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('_add_template_and_function_params:')
        # Note: we may be called from _fill_empty, so the symbols we want
        #       to add may actually already be present (as empty symbols).

        # add symbols for the template params
        if self.templateParams:
            for tp in self.templateParams.params:
                if not tp.get_identifier():
                    continue
                # only add a declaration if we our self are from a declaration
                if self.declaration:
                    decl = ASTDeclaration(objectType='templateParam', declaration=tp)
                else:
                    decl = None
                nne = ASTNestedNameElement(tp.get_identifier(), None)
                nn = ASTNestedName([nne], [False], rooted=False)
                self._add_symbols(nn, [], decl, self.docname, self.line)
        # add symbols for function parameters, if any
        if (
            self.declaration is not None
            and self.declaration.function_params is not None
        ):
            for fp in self.declaration.function_params:
                if fp.arg is None:
                    continue
                nn = fp.arg.name
                if nn is None:
                    continue
                # (comparing to the template params: we have checked that we are a declaration)
                decl = ASTDeclaration(objectType='functionParam', declaration=fp)
                assert not nn.rooted
                assert len(nn.names) == 1
                self._add_symbols(nn, [], decl, self.docname, self.line)
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 1

    def remove(self) -> None:
        if self.parent is None:
            return
        assert self in self.parent._children
        self.parent._children.remove(self)
        self.parent = None

    def clear_doc(self, docname: str) -> None:
        new_children: list[Symbol] = []
        for s_child in self._children:
            s_child.clear_doc(docname)
            if s_child.declaration and s_child.docname == docname:
                s_child.declaration = None
                s_child.docname = None
                s_child.line = None
                if s_child.siblingAbove is not None:
                    s_child.siblingAbove.siblingBelow = s_child.siblingBelow
                if s_child.siblingBelow is not None:
                    s_child.siblingBelow.siblingAbove = s_child.siblingAbove
                s_child.siblingAbove = None
                s_child.siblingBelow = None
            new_children.append(s_child)
        self._children = new_children

    def get_all_symbols(self) -> Iterator[Any]:
        yield self
        for s_child in self._children:
            yield from s_child.get_all_symbols()

    @property
    def children_recurse_anon(self) -> Iterator[Symbol]:
        for c in self._children:
            yield c
            if not c.identOrOp.is_anon():
                continue

            yield from c.children_recurse_anon

    def get_lookup_key(self) -> LookupKey:
        # The pickle files for the environment and for each document are distinct.
        # The environment has all the symbols, but the documents has xrefs that
        # must know their scope. A lookup key is essentially a specification of
        # how to find a specific symbol.
        symbols = []
        s = self
        while s.parent:
            symbols.append(s)
            s = s.parent
        key = [
            (
                ASTNestedNameElement(s.identOrOp, s.templateArgs),
                s.templateParams,
                None if s.declaration is None else s.declaration.get_newest_id(),
            )
            for s in reversed(symbols)
        ]
        return LookupKey(key)

    def get_full_nested_name(self) -> ASTNestedName:
        symbols = []
        s = self
        while s.parent:
            symbols.append(s)
            s = s.parent
        symbols.reverse()
        names = []
        templates = []
        for s in symbols:
            names.append(ASTNestedNameElement(s.identOrOp, s.templateArgs))
            templates.append(False)
        return ASTNestedName(names, templates, rooted=False)

    def _find_first_named_symbol(
        self,
        ident_or_op: ASTIdentifier | ASTOperator,
        template_params: ASTTemplateParams | ASTTemplateIntroduction,
        template_args: ASTTemplateArgs | None,
        template_shorthand: bool,
        match_self: bool,
        recurse_in_anon: bool,
        correct_primary_template_args: bool,
    ) -> Symbol | None:
        if Symbol.debug_lookup:
            Symbol.debug_print('_find_first_named_symbol ->')
        res = self._find_named_symbols(
            ident_or_op,
            template_params,
            template_args,
            template_shorthand,
            match_self,
            recurse_in_anon,
            correct_primary_template_args,
            search_in_siblings=False,
        )
        try:
            return next(res)
        except StopIteration:
            return None

    def _find_named_symbols(
        self,
        ident_or_op: ASTIdentifier | ASTOperator,
        template_params: ASTTemplateParams | ASTTemplateIntroduction,
        template_args: ASTTemplateArgs,
        template_shorthand: bool,
        match_self: bool,
        recurse_in_anon: bool,
        correct_primary_template_args: bool,
        search_in_siblings: bool,
    ) -> Iterator[Symbol]:
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('_find_named_symbols:')
            Symbol.debug_indent += 1
            Symbol.debug_print('self:')
            logger.debug(self.to_string(Symbol.debug_indent + 1), end='')
            Symbol.debug_print('ident_or_op:                  ', ident_or_op)
            Symbol.debug_print('template_params:              ', template_params)
            Symbol.debug_print('template_args:                ', template_args)
            Symbol.debug_print('template_shorthand:           ', template_shorthand)
            Symbol.debug_print('match_self:                   ', match_self)
            Symbol.debug_print('recurse_in_anon:              ', recurse_in_anon)
            Symbol.debug_print(
                'correct_primary_template_args:', correct_primary_template_args
            )
            Symbol.debug_print('search_in_siblings:           ', search_in_siblings)

        if correct_primary_template_args:
            if template_params is not None and template_args is not None:
                # If both are given, but it's not a specialization, then do lookup as if
                # there is no argument list.
                # For example: template<typename T> int A<T>::var;
                if not _is_specialization(template_params, template_args):
                    template_args = None

        def matches(s: Symbol) -> bool:
            if s.identOrOp != ident_or_op:
                return False
            if (s.templateParams is None) != (template_params is None):
                if template_params is not None:
                    # we query with params, they must match params
                    return False
                if not template_shorthand:
                    # we don't query with params, and we do care about them
                    return False
            if template_params:
                # TODO: do better comparison
                if str(s.templateParams) != str(template_params):
                    return False
            if (s.templateArgs is None) != (template_args is None):
                return False
            if s.templateArgs:
                # TODO: do better comparison
                if str(s.templateArgs) != str(template_args):
                    return False
            return True

        def candidates() -> Iterator[Symbol]:
            s = self
            if Symbol.debug_lookup:
                Symbol.debug_print('searching in self:')
                logger.debug(s.to_string(Symbol.debug_indent + 1), end='')
            while True:
                if match_self:
                    yield s
                if recurse_in_anon:
                    yield from s.children_recurse_anon
                else:
                    yield from s._children

                if s.siblingAbove is None:
                    break
                s = s.siblingAbove
                if Symbol.debug_lookup:
                    Symbol.debug_print('searching in sibling:')
                    logger.debug(s.to_string(Symbol.debug_indent + 1), end='')

        for s in candidates():
            if Symbol.debug_lookup:
                Symbol.debug_print('candidate:')
                logger.debug(s.to_string(Symbol.debug_indent + 1), end='')
            if matches(s):
                if Symbol.debug_lookup:
                    Symbol.debug_indent += 1
                    Symbol.debug_print('matches')
                    Symbol.debug_indent -= 3
                yield s
                if Symbol.debug_lookup:
                    Symbol.debug_indent += 2
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 2

    def _symbol_lookup(
        self,
        nested_name: ASTNestedName,
        template_decls: list[Any],
        on_missing_qualified_symbol: Callable[
            [Symbol, ASTIdentifier | ASTOperator, Any, ASTTemplateArgs],
            Symbol | None,
        ],
        strict_template_param_arg_lists: bool,
        ancestor_lookup_type: str,
        template_shorthand: bool,
        match_self: bool,
        recurse_in_anon: bool,
        correct_primary_template_args: bool,
        search_in_siblings: bool,
    ) -> SymbolLookupResult | None:
        # ancestor_lookup_type: if not None, specifies the target type of the lookup
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('_symbol_lookup:')
            Symbol.debug_indent += 1
            Symbol.debug_print('self:')
            logger.debug(self.to_string(Symbol.debug_indent + 1), end='')
            Symbol.debug_print('nested_name:         ', nested_name)
            Symbol.debug_print(
                'template_decls:      ', ','.join(str(t) for t in template_decls)
            )
            Symbol.debug_print(
                'strict_template_param_arg_lists:', strict_template_param_arg_lists
            )
            Symbol.debug_print('ancestor_lookup_type:', ancestor_lookup_type)
            Symbol.debug_print('template_shorthand:  ', template_shorthand)
            Symbol.debug_print('match_self:          ', match_self)
            Symbol.debug_print('recurse_in_anon:     ', recurse_in_anon)
            Symbol.debug_print(
                'correct_primary_template_args:  ', correct_primary_template_args
            )
            Symbol.debug_print('search_in_siblings:  ', search_in_siblings)

        if strict_template_param_arg_lists:
            # Each template argument list must have a template parameter list.
            # But to declare a template there must be an additional template parameter list.
            num_nested_templates = nested_name.num_templates()
            num_template_decls = len(template_decls)
            assert (
                num_nested_templates == num_template_decls
                or num_nested_templates + 1 == num_template_decls
            )
        else:
            assert len(template_decls) <= nested_name.num_templates() + 1

        names = nested_name.names

        # find the right starting point for lookup
        parent_symbol = self
        if nested_name.rooted:
            while parent_symbol.parent:
                parent_symbol = parent_symbol.parent
        if ancestor_lookup_type is not None:
            # walk up until we find the first identifier
            first_name = names[0]
            if not first_name.is_operator():
                while parent_symbol.parent:
                    if parent_symbol.find_identifier(
                        first_name.identOrOp,
                        matchSelf=match_self,
                        recurseInAnon=recurse_in_anon,
                        searchInSiblings=search_in_siblings,
                    ):
                        # if we are in the scope of a constructor but wants to
                        # reference the class we need to walk one extra up
                        if (
                            len(names) == 1
                            and ancestor_lookup_type == 'class'
                            and match_self
                            and parent_symbol.parent
                            and parent_symbol.parent.identOrOp == first_name.identOrOp
                        ):
                            pass
                        else:
                            break
                    parent_symbol = parent_symbol.parent

        if Symbol.debug_lookup:
            Symbol.debug_print('starting point:')
            logger.debug(parent_symbol.to_string(Symbol.debug_indent + 1), end='')

        # and now the actual lookup
        i_template_decl = 0
        for name in names[:-1]:
            ident_or_op = name.identOrOp
            template_args = name.templateArgs
            if strict_template_param_arg_lists:
                # there must be a parameter list
                if template_args:
                    assert i_template_decl < len(template_decls)
                    template_params = template_decls[i_template_decl]
                    i_template_decl += 1
                else:
                    template_params = None
            else:
                # take the next template parameter list if there is one
                # otherwise it's ok
                if template_args and i_template_decl < len(template_decls):
                    template_params = template_decls[i_template_decl]
                    i_template_decl += 1
                else:
                    template_params = None

            symbol = parent_symbol._find_first_named_symbol(
                ident_or_op,
                template_params,
                template_args,
                template_shorthand=template_shorthand,
                match_self=match_self,
                recurse_in_anon=recurse_in_anon,
                correct_primary_template_args=correct_primary_template_args,
            )
            if symbol is None:
                symbol = on_missing_qualified_symbol(
                    parent_symbol, ident_or_op, template_params, template_args
                )
                if symbol is None:
                    if Symbol.debug_lookup:
                        Symbol.debug_indent -= 2
                    return None
            # We have now matched part of a nested name, and need to match more
            # so even if we should match_self before, we definitely shouldn't
            # even more. (see also issue #2666)
            match_self = False
            parent_symbol = symbol

        if Symbol.debug_lookup:
            Symbol.debug_print('handle last name from:')
            logger.debug(parent_symbol.to_string(Symbol.debug_indent + 1), end='')

        # handle the last name
        name = names[-1]
        ident_or_op = name.identOrOp
        template_args = name.templateArgs
        if i_template_decl < len(template_decls):
            assert i_template_decl + 1 == len(template_decls)
            template_params = template_decls[i_template_decl]
        else:
            assert i_template_decl == len(template_decls)
            template_params = None

        symbols = parent_symbol._find_named_symbols(
            ident_or_op,
            template_params,
            template_args,
            template_shorthand=template_shorthand,
            match_self=match_self,
            recurse_in_anon=recurse_in_anon,
            correct_primary_template_args=False,
            search_in_siblings=search_in_siblings,
        )
        if Symbol.debug_lookup:
            symbols = list(symbols)  # type: ignore[assignment]
            Symbol.debug_indent -= 2
        return SymbolLookupResult(
            symbols, parent_symbol, ident_or_op, template_params, template_args
        )

    def _add_symbols(
        self,
        nested_name: ASTNestedName,
        template_decls: list[Any],
        declaration: ASTDeclaration | None,
        docname: str | None,
        line: int | None,
    ) -> Symbol:
        # Used for adding a whole path of symbols, where the last may or may not
        # be an actual declaration.

        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('_add_symbols:')
            Symbol.debug_indent += 1
            Symbol.debug_print('tdecls:', ','.join(str(t) for t in template_decls))
            Symbol.debug_print('nn:       ', nested_name)
            Symbol.debug_print('decl:     ', declaration)
            Symbol.debug_print(f'location: {docname}:{line}')

        def on_missing_qualified_symbol(
            parent_symbol: Symbol,
            ident_or_op: ASTIdentifier | ASTOperator,
            template_params: Any,
            template_args: ASTTemplateArgs,
        ) -> Symbol | None:
            if Symbol.debug_lookup:
                Symbol.debug_indent += 1
                Symbol.debug_print('_add_symbols, on_missing_qualified_symbol:')
                Symbol.debug_indent += 1
                Symbol.debug_print('template_params:', template_params)
                Symbol.debug_print('ident_or_op:    ', ident_or_op)
                Symbol.debug_print('template_args:  ', template_args)
                Symbol.debug_indent -= 2
            return Symbol(
                parent=parent_symbol,
                identOrOp=ident_or_op,
                templateParams=template_params,
                templateArgs=template_args,
                declaration=None,
                docname=None,
                line=None,
            )

        lookup_result = self._symbol_lookup(
            nested_name,
            template_decls,
            on_missing_qualified_symbol,
            strict_template_param_arg_lists=True,
            ancestor_lookup_type=None,
            template_shorthand=False,
            match_self=False,
            recurse_in_anon=False,
            correct_primary_template_args=True,
            search_in_siblings=False,
        )
        # we create symbols all the way, so that can't happen
        assert lookup_result is not None
        symbols = list(lookup_result.symbols)
        if len(symbols) == 0:
            if Symbol.debug_lookup:
                Symbol.debug_print('_add_symbols, result, no symbol:')
                Symbol.debug_indent += 1
                Symbol.debug_print('template_params:', lookup_result.template_params)
                Symbol.debug_print('ident_or_op:    ', lookup_result.ident_or_op)
                Symbol.debug_print('template_args:  ', lookup_result.template_args)
                Symbol.debug_print('declaration:    ', declaration)
                Symbol.debug_print(f'location:      {docname}:{line}')
                Symbol.debug_indent -= 1
            symbol = Symbol(
                parent=lookup_result.parent_symbol,
                identOrOp=lookup_result.ident_or_op,
                templateParams=lookup_result.template_params,
                templateArgs=lookup_result.template_args,
                declaration=declaration,
                docname=docname,
                line=line,
            )
            if Symbol.debug_lookup:
                Symbol.debug_indent -= 2
            return symbol

        if Symbol.debug_lookup:
            Symbol.debug_print('_add_symbols, result, symbols:')
            Symbol.debug_indent += 1
            Symbol.debug_print('number symbols:', len(symbols))
            Symbol.debug_indent -= 1

        if not declaration:
            if Symbol.debug_lookup:
                Symbol.debug_print('no declaration')
                Symbol.debug_indent -= 2
            # good, just a scope creation
            # TODO: what if we have more than one symbol?
            return symbols[0]

        no_decl = []
        with_decl = []
        dup_decl = []
        for s in symbols:
            if s.declaration is None:
                no_decl.append(s)
            elif s.isRedeclaration:
                dup_decl.append(s)
            else:
                with_decl.append(s)
        if Symbol.debug_lookup:
            Symbol.debug_print('#no_decl:  ', len(no_decl))
            Symbol.debug_print('#with_decl:', len(with_decl))
            Symbol.debug_print('#dup_decl: ', len(dup_decl))
        # With partial builds we may start with a large symbol tree stripped of declarations.
        # Essentially any combination of no_decl, with_decl, and dup_decls seems possible.
        # TODO: make partial builds fully work. What should happen when the primary symbol gets
        #  deleted, and other duplicates exist? The full document should probably be rebuild.

        # First check if one of those with a declaration matches.
        # If it's a function, we need to compare IDs,
        # otherwise there should be only one symbol with a declaration.
        def make_cand_symbol() -> Symbol:
            if Symbol.debug_lookup:
                Symbol.debug_print('begin: creating candidate symbol')
            symbol = Symbol(
                parent=lookup_result.parent_symbol,
                identOrOp=lookup_result.ident_or_op,
                templateParams=lookup_result.template_params,
                templateArgs=lookup_result.template_args,
                declaration=declaration,
                docname=docname,
                line=line,
            )
            if Symbol.debug_lookup:
                Symbol.debug_print('end:   creating candidate symbol')
            return symbol

        if len(with_decl) == 0:
            cand_symbol = None
        else:
            cand_symbol = make_cand_symbol()

            def handle_duplicate_declaration(
                symbol: Symbol, cand_symbol: Symbol
            ) -> None:
                if Symbol.debug_lookup:
                    Symbol.debug_indent += 1
                    Symbol.debug_print('redeclaration')
                    Symbol.debug_indent -= 1
                    Symbol.debug_indent -= 2
                # Redeclaration of the same symbol.
                # Let the new one be there, but raise an error to the client
                # so it can use the real symbol as subscope.
                # This will probably result in a duplicate id warning.
                cand_symbol.isRedeclaration = True
                raise _DuplicateSymbolError(symbol, declaration)

            if declaration.objectType != 'function':
                assert len(with_decl) <= 1
                handle_duplicate_declaration(with_decl[0], cand_symbol)
                # (not reachable)

            # a function, so compare IDs
            cand_id = declaration.get_newest_id()
            if Symbol.debug_lookup:
                Symbol.debug_print('cand_id:', cand_id)
            for symbol in with_decl:
                # but all existing must be functions as well,
                # otherwise we declare it to be a duplicate
                if symbol.declaration.objectType != 'function':
                    handle_duplicate_declaration(symbol, cand_symbol)
                    # (not reachable)
                old_id = symbol.declaration.get_newest_id()
                if Symbol.debug_lookup:
                    Symbol.debug_print('old_id: ', old_id)
                if cand_id == old_id:
                    handle_duplicate_declaration(symbol, cand_symbol)
                    # (not reachable)
            # no candidate symbol found with matching ID
        # if there is an empty symbol, fill that one
        if len(no_decl) == 0:
            if Symbol.debug_lookup:
                Symbol.debug_print('no match, no empty')
                if cand_symbol is not None:
                    Symbol.debug_print('result is already created cand_symbol')
                else:
                    Symbol.debug_print('result is make_cand_symbol()')
                Symbol.debug_indent -= 2
            if cand_symbol is not None:
                return cand_symbol
            else:
                return make_cand_symbol()
        else:
            if Symbol.debug_lookup:
                Symbol.debug_print(
                    'no match, but fill an empty declaration, cand_sybmol is not None?:',
                    cand_symbol is not None,
                )
                Symbol.debug_indent -= 2
            if cand_symbol is not None:
                cand_symbol.remove()
            # assert len(no_decl) == 1
            # TODO: enable assertion when we at some point find out how to do cleanup
            # for now, just take the first one, it should work fine ... right?
            symbol = no_decl[0]
            # If someone first opened the scope, and then later
            # declares it, e.g,
            # .. namespace:: Test
            # .. namespace:: nullptr
            # .. class:: Test
            symbol._fill_empty(declaration, docname, line)
            return symbol

    def merge_with(
        self, other: Symbol, docnames: list[str], env: BuildEnvironment
    ) -> None:
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('merge_with:')
        assert other is not None

        def unconditional_add(self: Symbol, other_child: Symbol) -> None:
            # TODO: hmm, should we prune by docnames?
            self._children.append(other_child)
            other_child.parent = self
            other_child._assert_invariants()

        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
        for other_child in other._children:
            if Symbol.debug_lookup:
                Symbol.debug_print(
                    'other_child:\n', other_child.to_string(Symbol.debug_indent)
                )
                Symbol.debug_indent += 1
            if other_child.isRedeclaration:
                unconditional_add(self, other_child)
                if Symbol.debug_lookup:
                    Symbol.debug_print('is_redeclaration')
                    Symbol.debug_indent -= 1
                continue
            candiate_iter = self._find_named_symbols(
                ident_or_op=other_child.identOrOp,
                template_params=other_child.templateParams,
                template_args=other_child.templateArgs,
                template_shorthand=False,
                match_self=False,
                recurse_in_anon=False,
                correct_primary_template_args=False,
                search_in_siblings=False,
            )
            candidates = list(candiate_iter)

            if Symbol.debug_lookup:
                Symbol.debug_print('raw candidate symbols:', len(candidates))
            symbols = [s for s in candidates if not s.isRedeclaration]
            if Symbol.debug_lookup:
                Symbol.debug_print('non-duplicate candidate symbols:', len(symbols))

            if len(symbols) == 0:
                unconditional_add(self, other_child)
                if Symbol.debug_lookup:
                    Symbol.debug_indent -= 1
                continue

            our_child = None
            if other_child.declaration is None:
                if Symbol.debug_lookup:
                    Symbol.debug_print('no declaration in other child')
                our_child = symbols[0]
            else:
                query_id = other_child.declaration.get_newest_id()
                if Symbol.debug_lookup:
                    Symbol.debug_print('query_id:  ', query_id)
                for symbol in symbols:
                    if symbol.declaration is None:
                        if Symbol.debug_lookup:
                            Symbol.debug_print('empty candidate')
                        # if in the end we have non-matching, but have an empty one,
                        # then just continue with that
                        our_child = symbol
                        continue
                    cand_id = symbol.declaration.get_newest_id()
                    if Symbol.debug_lookup:
                        Symbol.debug_print('candidate:', cand_id)
                    if cand_id == query_id:
                        our_child = symbol
                        break
            if Symbol.debug_lookup:
                Symbol.debug_indent -= 1
            if our_child is None:
                unconditional_add(self, other_child)
                continue
            if other_child.declaration and other_child.docname in docnames:
                if not our_child.declaration:
                    our_child._fill_empty(
                        other_child.declaration, other_child.docname, other_child.line
                    )
                elif our_child.docname != other_child.docname:
                    name = str(our_child.declaration)
                    msg = __(
                        'Duplicate C++ declaration, also defined at %s:%s.\n'
                        "Declaration is '.. cpp:%s:: %s'."
                    )
                    logger.warning(
                        msg,
                        our_child.docname,
                        our_child.line,
                        our_child.declaration.directiveType,
                        name,
                        location=(other_child.docname, other_child.line),
                        type='duplicate_declaration',
                        subtype='cpp',
                    )
                else:
                    our_object_type = our_child.declaration.objectType
                    other_object_type = other_child.declaration.objectType
                    our_child_parent_decl = our_child.parent.declaration
                    other_child_parent_decl = other_child.parent.declaration
                    if (
                        other_object_type == our_object_type
                        and other_object_type in {'templateParam', 'functionParam'}
                        and our_child_parent_decl == other_child_parent_decl
                    ):
                        # `our_child` was just created during merging by the call
                        # to `_fill_empty` on the parent and can be ignored.
                        pass
                    else:
                        # Both have declarations, and in the same docname.
                        # This can apparently happen, it should be safe to
                        # just ignore it, right?
                        # Hmm, only on duplicate declarations, right?
                        msg = 'Internal C++ domain error during symbol merging.\n'
                        msg += 'our_child:\n' + our_child.to_string(1)
                        msg += '\nother_child:\n' + other_child.to_string(1)
                        logger.warning(msg, location=other_child.docname)
            our_child.merge_with(other_child, docnames, env)
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 2

    def add_name(
        self,
        nestedName: ASTNestedName,
        templatePrefix: ASTTemplateDeclarationPrefix | None = None,
    ) -> Symbol:
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('add_name:')
        if templatePrefix:
            template_decls = templatePrefix.templates
        else:
            template_decls = []
        res = self._add_symbols(
            nestedName, template_decls, declaration=None, docname=None, line=None
        )
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 1
        return res

    def add_declaration(
        self, declaration: ASTDeclaration, docname: str, line: int
    ) -> Symbol:
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('add_declaration:')
        assert declaration is not None
        assert docname is not None
        assert line is not None
        nested_name = declaration.name
        if declaration.templatePrefix:
            template_decls = declaration.templatePrefix.templates
        else:
            template_decls = []
        res = self._add_symbols(nested_name, template_decls, declaration, docname, line)
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 1
        return res

    def find_identifier(
        self,
        identOrOp: ASTIdentifier | ASTOperator,
        matchSelf: bool,
        recurseInAnon: bool,
        searchInSiblings: bool,
    ) -> Symbol | None:
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('find_identifier:')
            Symbol.debug_indent += 1
            Symbol.debug_print('identOrOp:       ', identOrOp)
            Symbol.debug_print('matchSelf:       ', matchSelf)
            Symbol.debug_print('recurseInAnon:   ', recurseInAnon)
            Symbol.debug_print('searchInSiblings:', searchInSiblings)
            logger.debug(self.to_string(Symbol.debug_indent + 1), end='')
            Symbol.debug_indent -= 2
        current = self
        while current is not None:
            if Symbol.debug_lookup:
                Symbol.debug_indent += 2
                Symbol.debug_print('trying:')
                logger.debug(current.to_string(Symbol.debug_indent + 1), end='')
                Symbol.debug_indent -= 2
            if matchSelf and current.identOrOp == identOrOp:
                return current
            if recurseInAnon:
                children: Iterable[Symbol] = current.children_recurse_anon
            else:
                children = current._children
            for s in children:
                if s.identOrOp == identOrOp:
                    return s
            if not searchInSiblings:
                break
            current = current.siblingAbove
        return None

    def direct_lookup(self, key: LookupKey) -> Symbol:
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('direct_lookup:')
            Symbol.debug_indent += 1
        s = self
        for name, template_params, id_ in key.data:
            if id_ is not None:
                res = None
                for cand in s._children:
                    if cand.declaration is None:
                        continue
                    if cand.declaration.get_newest_id() == id_:
                        res = cand
                        break
                s = res
            else:
                ident_or_op = name.identOrOp
                template_args = name.templateArgs
                s = s._find_first_named_symbol(
                    ident_or_op,
                    template_params,
                    template_args,
                    template_shorthand=False,
                    match_self=False,
                    recurse_in_anon=False,
                    correct_primary_template_args=False,
                )
            if Symbol.debug_lookup:
                Symbol.debug_print('name:           ', name)
                Symbol.debug_print('template_params:', template_params)
                Symbol.debug_print('id:             ', id_)
                if s is not None:
                    logger.debug(s.to_string(Symbol.debug_indent + 1), end='')
                else:
                    Symbol.debug_print('not found')
            if s is None:
                if Symbol.debug_lookup:
                    Symbol.debug_indent -= 2
                return None
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 2
        return s

    def find_name(
        self,
        nestedName: ASTNestedName,
        templateDecls: list[Any],
        typ: str,
        templateShorthand: bool,
        matchSelf: bool,
        recurseInAnon: bool,
        searchInSiblings: bool,
    ) -> tuple[list[Symbol] | None, str]:
        # templateShorthand: missing template parameter lists for templates is ok
        # If the first component is None,
        # then the second component _may_ be a string explaining why.
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('find_name:')
            Symbol.debug_indent += 1
            Symbol.debug_print('self:')
            logger.debug(self.to_string(Symbol.debug_indent + 1), end='')
            Symbol.debug_print('nestedName:       ', nestedName)
            Symbol.debug_print('templateDecls:    ', templateDecls)
            Symbol.debug_print('typ:              ', typ)
            Symbol.debug_print('templateShorthand:', templateShorthand)
            Symbol.debug_print('matchSelf:        ', matchSelf)
            Symbol.debug_print('recurseInAnon:    ', recurseInAnon)
            Symbol.debug_print('searchInSiblings: ', searchInSiblings)

        class QualifiedSymbolIsTemplateParam(Exception):
            pass

        def on_missing_qualified_symbol(
            parent_symbol: Symbol,
            ident_or_op: ASTIdentifier | ASTOperator,
            template_params: Any,
            template_args: ASTTemplateArgs,
        ) -> Symbol | None:
            # TODO: Maybe search without template args?
            #       Though, the correct_primary_template_args does
            #       that for primary templates.
            #       Is there another case where it would be good?
            if parent_symbol.declaration is not None:
                if parent_symbol.declaration.objectType == 'templateParam':
                    raise QualifiedSymbolIsTemplateParam
            return None

        try:
            lookup_result = self._symbol_lookup(
                nestedName,
                templateDecls,
                on_missing_qualified_symbol,
                strict_template_param_arg_lists=False,
                ancestor_lookup_type=typ,
                template_shorthand=templateShorthand,
                match_self=matchSelf,
                recurse_in_anon=recurseInAnon,
                correct_primary_template_args=False,
                search_in_siblings=searchInSiblings,
            )
        except QualifiedSymbolIsTemplateParam:
            return None, 'templateParamInQualified'

        if lookup_result is None:
            # if it was a part of the qualification that could not be found
            if Symbol.debug_lookup:
                Symbol.debug_indent -= 2
            return None, None

        res = list(lookup_result.symbols)
        if len(res) != 0:
            if Symbol.debug_lookup:
                Symbol.debug_indent -= 2
            return res, None

        if lookup_result.parent_symbol.declaration is not None:
            if lookup_result.parent_symbol.declaration.objectType == 'templateParam':
                return None, 'templateParamInQualified'

        # try without template params and args
        symbol = lookup_result.parent_symbol._find_first_named_symbol(
            lookup_result.ident_or_op,
            None,
            None,
            template_shorthand=templateShorthand,
            match_self=matchSelf,
            recurse_in_anon=recurseInAnon,
            correct_primary_template_args=False,
        )
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 2
        if symbol is not None:
            return [symbol], None
        else:
            return None, None

    def find_declaration(
        self,
        declaration: ASTDeclaration,
        typ: str,
        templateShorthand: bool,
        matchSelf: bool,
        recurseInAnon: bool,
    ) -> Symbol | None:
        # templateShorthand: missing template parameter lists for templates is ok
        if Symbol.debug_lookup:
            Symbol.debug_indent += 1
            Symbol.debug_print('find_declaration:')
        nested_name = declaration.name
        if declaration.templatePrefix:
            template_decls = declaration.templatePrefix.templates
        else:
            template_decls = []

        def on_missing_qualified_symbol(
            parent_symbol: Symbol,
            ident_or_op: ASTIdentifier | ASTOperator,
            template_params: Any,
            template_args: ASTTemplateArgs,
        ) -> Symbol | None:
            return None

        lookup_result = self._symbol_lookup(
            nested_name,
            template_decls,
            on_missing_qualified_symbol,
            strict_template_param_arg_lists=False,
            ancestor_lookup_type=typ,
            template_shorthand=templateShorthand,
            match_self=matchSelf,
            recurse_in_anon=recurseInAnon,
            correct_primary_template_args=False,
            search_in_siblings=False,
        )
        if Symbol.debug_lookup:
            Symbol.debug_indent -= 1
        if lookup_result is None:
            return None

        symbols = list(lookup_result.symbols)
        if len(symbols) == 0:
            return None

        query_symbol = Symbol(
            parent=lookup_result.parent_symbol,
            identOrOp=lookup_result.ident_or_op,
            templateParams=lookup_result.template_params,
            templateArgs=lookup_result.template_args,
            declaration=declaration,
            docname='fakeDocnameForQuery',
            line=42,
        )
        query_id = declaration.get_newest_id()
        for symbol in symbols:
            if symbol.declaration is None:
                continue
            cand_id = symbol.declaration.get_newest_id()
            if cand_id == query_id:
                query_symbol.remove()
                return symbol
        query_symbol.remove()
        return None

    def to_string(self, indent: int) -> str:
        res = [Symbol.debug_indent_string * indent]
        if not self.parent:
            res.append('::')
        else:
            if self.templateParams:
                res.extend((
                    str(self.templateParams),
                    '\n',
                    Symbol.debug_indent_string * indent,
                ))
            if self.identOrOp:
                res.append(str(self.identOrOp))
            else:
                res.append(str(self.declaration))
            if self.templateArgs:
                res.append(str(self.templateArgs))
            if self.declaration:
                res.append(': ')
                if self.isRedeclaration:
                    res.append('!!duplicate!! ')
                res.extend((
                    '{',
                    self.declaration.objectType,
                    '} ',
                    str(self.declaration),
                ))
        if self.docname:
            res.extend(('\t(', self.docname, ')'))
        res.append('\n')
        return ''.join(res)

    def dump(self, indent: int) -> str:
        return ''.join([
            self.to_string(indent),
            *(c.dump(indent + 1) for c in self._children),
        ])
