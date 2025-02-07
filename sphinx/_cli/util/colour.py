"""Format coloured console output."""

from __future__ import annotations

import sys
from os import environ as _environ
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

if False:
    pass

if sys.platform == 'win32':
    import colorama

    colorama.just_fix_windows_console()
    del colorama


_COLOURING_DISABLED = False


def terminal_supports_colour() -> bool:
    """Return True if coloured terminal output is supported."""
    if 'NO_COLOUR' in _environ or 'NO_COLOR' in _environ:
        return False
    if sys.platform == 'win32':
        return True
    if 'FORCE_COLOUR' in _environ or 'FORCE_COLOR' in _environ:
        return True
    if _environ.get('CI', '').lower() in {'true', '1'}:
        return True

    try:
        if not sys.stdout.isatty():
            return False
    except (AttributeError, ValueError):
        # Handle cases where .isatty() is not defined, or where e.g.
        # "ValueError: I/O operation on closed file" is raised
        return False

    # Do not colour output if on a dumb terminal
    return _environ.get('TERM', 'unknown').lower() not in {'dumb', 'unknown'}


def disable_colour() -> None:
    global _COLOURING_DISABLED  # NoQA: PLW0603
    _COLOURING_DISABLED = True


def enable_colour() -> None:
    global _COLOURING_DISABLED  # NoQA: PLW0603
    _COLOURING_DISABLED = False


def colourise(colour_name: str, text: str, /) -> str:
    if _COLOURING_DISABLED:
        return text
    if colour_name.startswith('_') or colour_name in {
        'annotations',
        'sys',
        'terminal_supports_colour',
        'disable_colour',
        'enable_colour',
        'colourise',
    }:
        msg = f'Invalid colour name: {colour_name!r}'
        raise ValueError(msg)
    try:
        return globals()[colour_name](text)
    except KeyError:
        msg = f'Invalid colour name: {colour_name!r}'
        raise ValueError(msg) from None


def _create_colour_func(escape_code: str, /) -> Callable[[str], str]:
    def inner(text: str) -> str:
        if _COLOURING_DISABLED:
            return text
        return f'\x1b[{escape_code}m{text}\x1b[39;49;00m'

    inner.__escape_code = escape_code  # type: ignore[attr-defined]
    return inner


# Wrap escape sequence with ``\1`` and ``\2`` to let readline know
# that the colour escape codes are non-printable characters
# [ https://tiswww.case.edu/php/chet/readline/readline.html ]
#
# Note: This does not work well in Windows
# (see https://github.com/sphinx-doc/sphinx/pull/5059)
if sys.platform == 'win32':
    _create_input_mode_colour_func = _create_colour_func
else:

    def _create_input_mode_colour_func(escape_code: str, /) -> Callable[[str], str]:
        def inner(text: str) -> str:
            if _COLOURING_DISABLED:
                return text
            return f'\1\x1b[{escape_code}m\2{text}\1\x1b[39;49;00m\2'

        return inner


reset = _create_colour_func('39;49;00')
bold = _create_colour_func('01')
faint = _create_colour_func('02')
standout = _create_colour_func('03')
underline = _create_colour_func('04')
blink = _create_colour_func('05')

black = _create_colour_func('30')
darkred = _create_colour_func('31')
darkgreen = _create_colour_func('32')
brown = _create_colour_func('33')
darkblue = _create_colour_func('34')
purple = _create_colour_func('35')
turquoise = _create_colour_func('36')
lightgray = _create_colour_func('37')

darkgray = _create_colour_func('90')
red = _create_colour_func('91')
green = _create_colour_func('92')
yellow = _create_colour_func('93')
blue = _create_colour_func('94')
fuchsia = _create_colour_func('95')
teal = _create_colour_func('96')
white = _create_colour_func('97')
