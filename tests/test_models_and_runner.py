import unittest

from backend.models import AssessmentRequest, Language, TestCase, ValidationError
from backend.runner import FailClosedRunner, FakeRunner, RunStatus, RunnerUnavailable, TestRun


class ModelsTests(unittest.TestCase):
    def test_empty_source_is_rejected_before_execution(self):
        with self.assertRaisesRegex(ValidationError, "must not be blank"):
            AssessmentRequest(Language.PYTHON, " ", "print(1)", (TestCase("smoke", "", "", 1.0),))

    def test_request_accepts_supported_shape(self):
        request = AssessmentRequest(
            language=Language.C,
            source="int main(void){return 0;}",
            reference_source="int main(void){return 0;}",
            tests=(TestCase("smoke", "", "", 1.0),),
        )
        self.assertEqual(request.policy_version, "core-v1")

    def test_request_rejects_duplicate_ids_and_invalid_weight(self):
        with self.assertRaises(ValidationError):
            AssessmentRequest(
                language=Language.C,
                source="x",
                reference_source="x",
                tests=(TestCase("same", "", "", 1.0), TestCase("same", "", "", 1.0)),
            )
        with self.assertRaises(ValidationError):
            TestCase("bad", "", "", 0)

    def test_request_rejects_oversized_source(self):
        with self.assertRaises(ValidationError):
            AssessmentRequest(Language.C, "x" * (64 * 1024 + 1), "x", (TestCase("t", "", "", 1),))


class RunnerTests(unittest.TestCase):
    def test_fail_closed_runner_never_executes(self):
        runner = FailClosedRunner()
        self.assertFalse(runner.ready())
        with self.assertRaises(RunnerUnavailable):
            runner.run("c", "int main(){}", "int main(){}", ())

    def test_fake_runner_is_deterministic(self):
        outcomes = (TestRun("t", RunStatus.PASSED, stdout="ok", exit_code=0, weight=1),)
        runner = FakeRunner(outcomes)
        self.assertEqual(runner.run("c", "ignored", "ignored", ()), outcomes)
        self.assertEqual(runner.run("c", "different", "different", ()), outcomes)

    def test_fake_runner_can_represent_all_safety_outcomes(self):
        outcomes = tuple(
            TestRun(case_id, status, weight=1)
            for case_id, status in (
                ("syntax", RunStatus.COMPILE_ERROR),
                ("crash", RunStatus.RUNTIME_ERROR),
                ("timeout", RunStatus.TIMEOUT),
                ("limit", RunStatus.RESOURCE_LIMIT),
                ("wrong", RunStatus.WRONG_OUTPUT),
            )
        )
        self.assertEqual(FakeRunner(outcomes).run("c", "ignored", "ignored", ()), outcomes)


if __name__ == "__main__":
    unittest.main()
