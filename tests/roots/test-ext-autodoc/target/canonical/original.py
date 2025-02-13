class Foo:
    """docstring"""

    def meth(self):
        """docstring"""


def bar():
    """docstring"""

    class Bar:
        """docstring"""

    return Bar


Bar = bar()
