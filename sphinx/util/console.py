"""Format colored console output."""

from __future__ import annotations

import shutil

import sphinx._cli.util.colour
from sphinx._cli.util.colour import (  # NoQA: F401
    _create_input_mode_colour_func,
    black,
    blink,
    blue,
    bold,
    brown,
    colourise,
    darkblue,
    darkgray,
    darkgreen,
    darkred,
    disable_colour,
    enable_colour,
    faint,
    fuchsia,
    green,
    lightgray,
    purple,
    red,
    reset,
    standout,
    teal,
    terminal_supports_colour,
    turquoise,
    underline,
    white,
    yellow,
)
from sphinx._cli.util.errors import strip_escape_sequences

color_terminal = terminal_supports_colour
nocolor = disable_colour
coloron = enable_colour
strip_colors = strip_escape_sequences


def terminal_safe(s: str) -> str:
    """Safely encode a string for printing to the terminal."""
    return s.encode('ascii', 'backslashreplace').decode('ascii')


def get_terminal_width() -> int:
    """Return the width of the terminal in columns."""
    return shutil.get_terminal_size().columns - 1


_tw: int = get_terminal_width()


def term_width_line(text: str) -> str:
    if sphinx._cli.util.colour._COLOURING_DISABLED:
        # if no coloring, don't output fancy backspaces
        return text + '\n'
    else:
        # codes are not displayed, this must be taken into account
        return text.ljust(_tw + len(text) - len(strip_escape_sequences(text))) + '\r'


def colorize(name: str, text: str, input_mode: bool = False) -> str:
    if input_mode:
        colour_func = globals()[name]
        escape_code = getattr(colour_func, '__escape_code', '')
        if not escape_code:
            return colour_func(text)
        inner = _create_input_mode_colour_func(escape_code)
        return inner(text)

    return colourise(name, text)
