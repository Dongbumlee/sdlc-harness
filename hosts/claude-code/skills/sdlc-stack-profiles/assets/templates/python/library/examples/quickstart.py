"""Runnable quickstart for {{ProjectName}}.

CI executes this file, so the example can never rot against the
library it demonstrates. The README quickstart shows the same code.
"""

from {{project_name}} import slugify, truncate


def main() -> None:
    print(slugify("Hello, World!"))
    print(truncate("hello world", 8))


if __name__ == "__main__":
    main()
