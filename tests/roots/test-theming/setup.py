from setuptools import find_packages
from setuptools import setup

setup(
    name="test-theme",
    packages=find_packages(),
    include_package_data=True,
    entry_points="""
       [sphinx_themes]
       path = test_theme:get_path
    """,
)
