"""OCR adapter contract checks; never launch an OCR executable."""

import hashlib
import io
import subprocess

import pytest

from backend.assignment_import import ImportError, MAX_TEXT, TesseractProvider


class RecordedProcess:
    def __init__(self, stdout=b"Question", stderr=b"", *, timeout=False):
        self.stdout, self.stderr = io.BytesIO(stdout), io.BytesIO(stderr)
        self.returncode = None
        self.killed = False
        self.timeout = timeout

    def poll(self):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -1

    def wait(self, timeout):
        if self.timeout and not self.killed:
            raise subprocess.TimeoutExpired("test-ocr", timeout)
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def test_relative_executable_is_rejected_before_resolving(tmp_path, monkeypatch):
    executable = tmp_path / "tesseract.exe"
    executable.write_bytes(b"not-executable-test-data")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="absolute"):
        TesseractProvider("tesseract.exe", expected_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_ocr_stream_flood_is_killed_without_unbounded_capture(monkeypatch, stream):
    process = RecordedProcess(**{stream: b"x" * (MAX_TEXT + 8192)})
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: process)
    with pytest.raises(ImportError) as error:
        TesseractProvider._capture(["test-only"], 1)
    assert error.value.code == "ocr_output_exceeded"
    assert process.killed and process.stdout.closed and process.stderr.closed


def test_ocr_timeout_kills_process_and_closes_streams(monkeypatch):
    process = RecordedProcess(timeout=True)
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: process)
    with pytest.raises(subprocess.TimeoutExpired):
        TesseractProvider._capture(["test-only"], 1)
    assert process.killed and process.stdout.closed and process.stderr.closed


def test_ocr_success_preserves_text_and_discards_private_diagnostics(monkeypatch):
    process = RecordedProcess(stdout="Question \u2603".encode(), stderr=b"private document path")
    recorded = []
    def popen(command, **kwargs):
        recorded.append((command, kwargs))
        return process
    monkeypatch.setattr(subprocess, "Popen", popen)
    result = TesseractProvider._capture(["test-only", "private-image.png"], 1)
    assert result.stdout == "Question \u2603" and result.stderr == ""
    assert recorded[0][1]["shell"] is False
    assert recorded[0][1]["stdin"] == subprocess.DEVNULL
    assert process.stdout.closed and process.stderr.closed
