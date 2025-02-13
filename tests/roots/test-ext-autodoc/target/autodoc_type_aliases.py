from __future__ import annotations

import io  # NoQA: TC003
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    import fractions as frac
    from typing import Optional, Union

myint = int
myfrac = float

#: docstring
variable: myint

#: docstring
variable2 = None  # type: myint

#: docstring
variable3: Optional[myint]  # NoQA: UP045


def read(r: io.BytesIO) -> io.StringIO:
    """docstring"""


def sum(x: myfrac, y: myfrac) -> myfrac:
    """docstring"""
    return x + y


@overload
def mult(x: int, y: int) -> int: ...


@overload
def mult(x: myfrac, y: myfrac) -> myfrac: ...


def mult(x, y):
    """docstring"""
    return x, y


class Foo:
    """docstring"""

    #: docstring
    attr1: Union[frac.Fraction, myint]  # NoQA: UP007

    def __init__(self):
        self.attr2: myint = None  #: docstring

    def method1(self, x: Union[frac.Fraction, myfrac]) -> Union[frac.Fraction, myfrac]:  # NoQA: UP007
        """docstring"""
        return self.attr1 * x

    @overload
    def method2(self, x: frac.Fraction) -> frac.Fraction: ...

    @overload
    def method2(self, x: myfrac) -> myfrac: ...

    @overload
    def method2(
        self,
        x: Union[frac.Fraction, myfrac],  # NoQA: UP007
    ) -> Union[frac.Fraction, myfrac]: ...  # NoQA: UP007

    def method2(self, x):
        """docstring"""
        return self.attr2 * x


@overload
def prod(x: tuple[float, myfrac]) -> float: ...


@overload
def prod(x: tuple[frac.Fraction, myfrac]) -> frac.Fraction: ...


def prod(x):
    """docstring"""
    return x[0] * x[1]


def print_value(x: Union[frac.Fraction, myfrac]) -> None:  # NoQA: UP007
    """docstring"""
    print('value:', x)
