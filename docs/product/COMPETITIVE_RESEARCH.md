# Programming-assessment product research

Research date: 2026-11-08. Sources are official product/project documentation available on that date. This is a capability comparison, not a controlled product evaluation and not a uniqueness claim.

| Product | Officially documented focus | Fair comparison with CodeAssess |
| --- | --- | --- |
| Gradescope | Programming assignments can combine autograding and manual rubric grading; instructors supply flexible autograder setup/scripts and can use code-similarity review. | Mature course and grading workflows are broader. CodeAssess currently emphasizes deterministic two-agent evidence, graph-linked learning guidance, and a local academic prototype; its real worker is not yet verified. |
| PrairieLearn | External grading queues container jobs, supports custom images, records phase timestamps, disables networking by default, and renders detailed test results. | Its documented grader/job infrastructure is a strong reference for CodeAssess isolation and lifecycle acceptance. CodeAssess must not claim comparable operational maturity until its worker gates pass. |
| CodeGrade | AutoTest, rubrics, inline feedback, plagiarism/similarity features, browser editing, and LMS integrations are documented. | CodeGrade has established LMS/product integration. CodeAssess research should evaluate whether evidence-grounded graph recommendations add educational value, not claim categorical superiority. |
| Moodle CodeRunner | Moodle question type for executing many languages, immediate test feedback, resubmission/penalty workflows, and a separate Jobe sandbox for serious deployment. | CodeRunner is an established open educational workflow. CodeAssess differs in its two-agent typed evidence/report model, but that difference is not proof of better grading. |
| HackerRank | Coding questions use predefined sample/hidden tests, standard execution environments, per-test scoring, many languages, and candidate reporting. | Primarily documented for hiring assessment. CodeAssess targets teacher/student course workflows and learning recommendations; its scale and execution assurance are currently much narrower. |
| CodeSignal | Certified/proctored assessments, validated scores, skill-area insights, broad language support, and shareable reports. | CodeSignal documents validated hiring instruments. CodeAssess has no independently measured accuracy or validated score interpretation yet and must present `core-v1` only as its project rubric. |

## Official sources

- Gradescope: [Creating a Programming Assignment](https://guides.gradescope.com/hc/en-us/articles/22254107840909-Creating-a-Programming-Assignment), [Grading a Programming Assignment](https://guides.gradescope.com/hc/en-us/articles/22066635961357-Grading-a-Programming-Assignment)
- PrairieLearn: [External grading](https://docs.prairielearn.com/externalGrading/), [Concepts](https://docs.prairielearn.com/concepts/)
- CodeGrade: [Help Center](https://help.codegrade.com/), [Automatic tests](https://help.codegrade.com/setup-assignment/build-assignment/creating-automatic-tests)
- Moodle CodeRunner: [Project site](https://coderunner.org.nz/)
- HackerRank: [Coding Questions](https://support.hackerrank.com/articles/2474669643-coding-question), [Test Cases](https://support.hackerrank.com/articles/3245197419-test-cases-in-coding-questions)
- CodeSignal: [Certified assessments](https://support.codesignal.com/hc/en-us/articles/4413651969431-What-are-certified-assessments), [Assessment quick start](https://support.codesignal.com/hc/en-us/articles/22112130416535-Quick-Start-Guide-Assessments)

No source reviewed here establishes that CodeAssess is unique, universally accurate, or ready for production deployment.

