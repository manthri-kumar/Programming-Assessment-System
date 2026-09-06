"""
Call Analysis.

A lightweight heuristic that flags functions which are *defined* but
never actually *invoked* elsewhere in the code. This catches a class
of bugs that pure concept-set comparison cannot see — e.g. a helper
function that exists but was never wired into the program's logic.
"""

import re


def find_uncalled_functions(functions: list[str], code: str) -> list[str]:
    """
    Return the subset of `functions` that appear to be defined but
    never called elsewhere in `code`.

    Heuristic: count occurrences of `name(` in the source. The
    definition itself accounts for exactly one occurrence; if there
    isn't at least one more, the function is treated as unused.
    """
    uncalled = []
    for name in functions:
        occurrences = len(re.findall(rf'\b{re.escape(name)}\s*\(', code))
        if occurrences <= 1:
            uncalled.append(name)
    return uncalled