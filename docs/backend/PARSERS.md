# Parser and normalized IR behavior

The analysis layer parses text only and never imports or executes submitted source.

| Language | Parser | Supported boundary | Diagnostics |
| --- | --- | --- | --- |
| Python | CPython 3.11 `ast` | One module; parsing does not resolve imports | `syntax error` with a line when available; `analysis_limit` over 10,000 nodes |
| C | `tree-sitter-c` 0.24.2 | One C translation unit for structural parsing | Tree-sitter error line/column; authoritative Clang 14.0.6 candidate validation awaits the isolated worker |
| Java | `tree-sitter-java` 0.23.5 | One source containing `class Main`; multi-file/dependencies unsupported | Tree-sitter error line/column or strict layout diagnostic |

The normalized IR records named node kinds, normalized identifiers and literal types, child order, and source line metadata. Canonical serialization omits line numbers, so whitespace changes and identifier renaming remain hash-stable. Comments and strings are parsed according to each grammar rather than counted as keywords. Every adapter applies a 10,000-node cap.

The structural score uses bounded unit-cost edit distance over normalized preorder node kinds and stops before more than 100,000 pair operations. It is deterministic, but it does not prove equivalent behavior. Complexity reports IR size, loop nesting/locations, and Python recursion as static indicators; C/Java recursion remains undetermined. Compiler-backed C11/Java 17 diagnostics remain gated on the isolated Linux worker.

Executable fixtures cover valid and invalid syntax for all three languages, comment handling for C, Java `class Main` layout, Python formatting/identifier normalization, and analysis repeatability in `tests/test_analysis_and_agents.py`.
