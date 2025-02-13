import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve() / 'src'))

extensions = ['sphinx.ext.apidoc']

apidoc_defaults = {
    'includeprivate': True,
    'followlinks': False,
    'separatemodules': True,
    'noheadings': False,
    'modulefirst': True,
}
apidoc_modules = [
    {
        'path': 'src',
        'destination': 'generated',
        'exclude_patterns': ['src/exclude_package.py'],
        'automodule_options': ['members', 'undoc-members'],
        'maxdepth': 3,
        'implicit_namespaces': False,
    }
]
