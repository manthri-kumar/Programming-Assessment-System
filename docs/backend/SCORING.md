# Versioned scoring policies

Both recorded policies retain the original weights: structure 20%, syntax 40%, functional tests 20%, and originality heuristic 20%. Categories use the unrounded total: Good at 75 or above, Average at 50 or above, and Poor below 50. Display rounding happens once, after classification.

`legacy-v1` is a regression description of the prototype. Structure counts lines and selected regex tokens; syntax subtracts ten points for each lowercase `error` substring; tests compare outer-trimmed stdout while ignoring process exit status; originality is inverse raw-text similarity. These behaviors are frozen in `legacy-v1-goldens.json` and mocked-subprocess tests. They are retained for research comparison, not used as safe execution logic.

`core-v1` uses normalized parsed structure, parser/compiler status, weighted isolated test outcomes, and the same text-dissimilarity heuristic. Missing required evidence produces an incomplete result with a null total and category. Weights are never redistributed. Syntax failure is a learner outcome; missing isolation is infrastructure failure.

For the sample components structure 80, syntax 100, tests 50, originality 40, both policies' arithmetic is `16 + 40 + 10 + 8 = 74`, classified Average. Component meanings differ, so equal arithmetic does not imply equal evidence quality.

The originality component describes text dissimilarity only. Identical correct code receives zero under the preserved formula, and superficial rewriting may increase the value. The system must label this limitation and must never present the score as proof of plagiarism, originality, or misconduct.
