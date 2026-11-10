# Rubric Scoring

## Purpose

Preserve the project's rubric lineage while providing transparent, versioned and reproducible grading arithmetic.

## ADDED Requirements

### Requirement: Preserve the legacy scoring baseline
The project SHALL retain a reproducible legacy-v1 characterization of the existing feature-count structure metric, syntax error-count deduction, weighted tests, inverse text similarity, weights and classification thresholds. Intentional changes SHALL be documented against that baseline under a different policy version.

#### Scenario: Legacy characterization
- **WHEN** fixed component inputs and stubbed compiler outcomes are evaluated under legacy-v1
- **THEN** results match the original formulas documented in audit.md without executing submissions on the host

### Requirement: Preserve rubric weights and categories in core policy
core-v1 SHALL use weights structure=0.20, syntax=0.40, tests=0.20 and originality=0.20. Complete finite component scores SHALL be in [0,100]. Total SHALL use unrounded scores; Good begins at 75 and Average at 50. Display rounding SHALL NOT change classification.

#### Scenario: Weighted score
- **WHEN** structure=80, syntax=100, tests=50 and originality=40
- **THEN** total is 74 and category is Average

#### Scenario: Boundary classification
- **WHEN** unrounded total is 49.999, 50, 74.999 or 75
- **THEN** categories are Poor, Average, Average and Good respectively

### Requirement: Explain component policies
core-v1 SHALL use parsed structural evidence, syntax=100 on valid compilation and zero on learner syntax failure, test score=100 times passed weight divided by total weight, and originality=100 times inverse raw-text similarity. Every result SHALL expose the policy version and component evidence; originality SHALL be labeled a heuristic rather than a misconduct determination.

#### Scenario: Weighted test result
- **WHEN** cases with weights 1, 1 and 2 have outcomes pass, pass and fail
- **THEN** test score is 50 and each case's contribution is inspectable

### Requirement: Do not fabricate totals from unavailable stages
Unavailable required components SHALL yield null total and category without silent weight redistribution. Learner syntax failure SHALL produce invalid_submission with syntax zero and skipped dependent stages. Infrastructure or analysis-limit failures SHALL produce incomplete outcomes with reason codes.

#### Scenario: Missing structural evidence
- **WHEN** structure is unavailable due to an analysis limit
- **THEN** total/category are null and other component evidence remains visible without renormalization

#### Scenario: Empty or invalid test weights
- **WHEN** tests are empty or any weight is nonpositive or nonfinite
- **THEN** input is rejected rather than producing a zero or misleading full score

## Inputs and outputs
Inputs are component evidence and a named policy; outputs are bounded component scores, total, category and arithmetic evidence.

## Expected behavior
Approved policy versions preserve rubric lineage and never fabricate totals from unavailable evidence.

## Edge cases and failure handling
Missing components, invalid weights, nonfinite values and policy versions yield explicit errors or null totals.

## Acceptance criteria
Legacy-v1 characterization and core-v1 arithmetic goldens pass without source execution.

## Dependencies
Depends on `evaluation-agent`, `structural-comparison-agent`, `test-execution-agent`, `assessment-validation`.
