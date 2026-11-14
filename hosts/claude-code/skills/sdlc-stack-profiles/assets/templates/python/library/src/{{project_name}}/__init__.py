"""{{ProjectName}} — a Python library.

Quickstart:

>>> from {{project_name}} import slugify, truncate
>>> slugify("Hello, World!")
'hello-world'
>>> truncate("hello world", 8)
'hello w…'

The public surface is exactly the names in ``__all__``; everything
else is internal and may change without a major version bump.
"""

from importlib.metadata import PackageNotFoundError, version

from {{project_name}}.core import slugify, truncate

__all__ = ["slugify", "truncate"]

try:
    __version__ = version("{{project-name}}")
except PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0.0.0"
