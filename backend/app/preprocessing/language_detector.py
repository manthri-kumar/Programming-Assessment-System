from pathlib import Path


SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".c": "c",
    ".java": "java",
}


def detect_language_from_filename(filename: str) -> str:
    """
    Detect programming language from a source filename.

    Supported:
        .py   -> Python
        .c    -> C
        .java -> Java
    """

    if not filename:
        raise ValueError("Filename cannot be empty.")

    extension = Path(filename).suffix.lower()

    language = SUPPORTED_LANGUAGES.get(extension)

    if language is None:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported languages: Python, C, Java."
        )

    return language


def detect_language_from_code(code: str) -> str:
    """
    Basic language detection from source code.

    This is a fallback when a filename is not available.
    Filename/extension detection should be preferred when possible.
    """

    if not code or not code.strip():
        raise ValueError("Source code cannot be empty.")

    code_lower = code.lower()

    # Python indicators
    python_indicators = [
        "def ",
        "import ",
        "from ",
        "elif ",
        "print(",
        "__name__",
    ]

    # Java indicators
    java_indicators = [
        "public class ",
        "private class ",
        "public static void main",
        "system.out.println",
        "import java.",
        "static void ",
    ]

    # C indicators
    c_indicators = [
        "#include",
        "printf(",
        "scanf(",
        "int main(",
        "malloc(",
        "struct ",
    ]

    python_score = sum(
        indicator in code_lower for indicator in python_indicators
    )

    java_score = sum(
        indicator in code_lower for indicator in java_indicators
    )

    c_score = sum(
        indicator in code_lower for indicator in c_indicators
    )

    scores = {
        "python": python_score,
        "java": java_score,
        "c": c_score,
    }

    detected_language = max(scores, key=scores.get)

    if scores[detected_language] == 0:
        raise ValueError(
            "Unable to detect programming language from the source code."
        )

    return detected_language


def detect_language(
    filename: str | None = None,
    code: str | None = None,
) -> str:
    """
    Main language detection function.

    Priority:
        1. Filename extension
        2. Source-code analysis
    """

    if filename:
        try:
            return detect_language_from_filename(filename)
        except ValueError:
            pass

    if code:
        return detect_language_from_code(code)

    raise ValueError(
        "Either filename or source code must be provided."
    )