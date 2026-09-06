from app.preprocessing.language_detector import (
    detect_language_from_filename,
    detect_language_from_code,
)


def test_python_filename():
    assert detect_language_from_filename("student.py") == "python"


def test_c_filename():
    assert detect_language_from_filename("student.c") == "c"


def test_java_filename():
    assert detect_language_from_filename("Student.java") == "java"


def test_python_code():
    code = """
def find_max(arr):
    return max(arr)
"""

    assert detect_language_from_code(code) == "python"


def test_c_code():
    code = """
#include <stdio.h>

int main() {
    printf("Hello");
    return 0;
}
"""

    assert detect_language_from_code(code) == "c"


def test_java_code():
    code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""

    assert detect_language_from_code(code) == "java"