import sys

class Parent:

    relation = "Family"

    def __init__(self):
        self.name = "Andrew"
        self.age = 35

    def get_name(self):
        return self.name

    def get_age(self):
        return f"Parent class -  {self.age}"

    # Test mangled name behaviour
    __get_age = get_age  # private copy of original get_age method
    __private_parent_attribute = "Private_parent"


class Child(Parent):

    def __init__(self):
        self.name = "Bobby"
        self.age = 15

    def get_name(self):
        return self.name

    def get_age(self):
        return f"Child class -  {self.age}"

    @staticmethod
    def addition(a, b):
        return a + b


class Baby(Child):
    
    # Test a private attribute
    __private_baby_name = "Private1234"

    def __init__(self):
        self.name = "Charlie"
        self.age = 2

    def get_age(self):
        return f"Baby class - {self.age}"

    class BabyInnerClass():
        baby_inner_attribute = "An attribute of an inner class"


class Job:

    def __init__(self):
        self.salary = 10

    def get_salary(self):
        return self.salary


class Architect(Job):

    def __init__(self):
        self.salary = 20

    def get_age(self):
        return f"Architect age - {self.age}"

# Test a class that inherits multiple classes
class Jerry(Architect, Child):

    def __init__(self):
        self.name = "Jerry"
        self.age = 25


__all__ = ["Parent", "Child", "Baby", "Job", "Architect", "Jerry"]

# The following is used to process the expected builtin members for different
# versions of Python. The base list is for v3.11 (the latest testing when added)
# and new builtin attributes/methods in later versions can be appended below.

members_3_11 = ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__',
                '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__',
                '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__',
                '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
                '__sizeof__', '__str__', '__subclasshook__', '__weakref__']

attr_3_11 = ['__annotations__', '__dict__', '__doc__', '__module__', '__weakref__']


def concat_and_sort(list1, list2):
    return sorted(list1 + list2)


built_in_attr = attr_3_11
built_in_members = members_3_11
# The second test has an extra builtin member
built_in_members2 = ['__annotations__', *members_3_11]

if sys.version_info[:2] >= (3, 13):
    add_3_13 = ['__firstlineno__', '__static_attributes__']
    built_in_attr = concat_and_sort(built_in_attr, add_3_13)
    built_in_members = concat_and_sort(built_in_members, add_3_13)
    built_in_members2 = concat_and_sort(built_in_members2, add_3_13)

if sys.version_info[:2] >= (3, 14):
    built_in_attr = concat_and_sort(built_in_attr, ['__annotate__'])
    built_in_members2 = concat_and_sort(built_in_members2, ['__annotate__'])