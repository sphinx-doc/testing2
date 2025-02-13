extensions = ['sphinx.ext.doctest']

project = 'test project for doctest'
root_doc = 'fail-fast'
source_suffix = {
    '.txt': 'restructuredtext',
}
exclude_patterns = ['_build']

# Set in tests.
# doctest_fail_fast = ...
