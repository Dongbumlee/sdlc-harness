"""Entry point for `python -m {{project_name}}` and for the frozen
(PyInstaller) binary: a thin shell over the Click tree.
"""

from {{project_name}}.cli import cli

if __name__ == "__main__":
    cli()
