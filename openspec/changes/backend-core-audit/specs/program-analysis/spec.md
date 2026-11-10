# Program Analysis

## Purpose

Produce bounded syntax and structural evidence for explicitly supported programs without claiming universal semantic equivalence.

## ADDED Requirements

### Requirement: Declare supported language boundaries
The system SHALL document and report pinned toolchain/parser versions for Python 3.11 standard-library programs, Clang-compiled C11 single translation units with standard headers, and Java 17 single Main.java programs with class Main. Unsupported syntax or dependency layouts SHALL yield explicit unsupported or invalid diagnostics rather than guessed scores.

#### Scenario: Unsupported Java project layout
- **WHEN** a request needs multiple Java source files or external dependencies
- **THEN** analysis reports an unsupported layout and never silently treats it as a supported program

### Requirement: Diagnose syntax from authoritative outcomes
Syntax validation SHALL use parser/compiler success and return structured bounded diagnostics with locations where available. Missing tools and timeouts SHALL be infrastructure or limit outcomes, not learner syntax errors. Failed parsing SHALL NOT fall back silently to regex scoring.

#### Scenario: Compiler failure without error keyword
- **WHEN** the compiler returns failure with diagnostics that do not contain lowercase error
- **THEN** syntax validation reports failure rather than awarding 100

#### Scenario: Toolchain missing
- **WHEN** the required compiler is unavailable
- **THEN** syntax score is unavailable and the reason identifies an infrastructure failure

### Requirement: Compare parsed program structure
Structural comparison SHALL use a versioned normalized representation of functions, loops, branches, calls and operators. Comments, whitespace and identifier-only renaming SHALL NOT change the structural score. Structure SHALL be reported separately from behavioral correctness.

#### Scenario: Keyword inside a comment or string
- **WHEN** a comment or string contains for, while, if or a function-like fragment
- **THEN** it does not create structural control-flow or function features

#### Scenario: Formatting and naming changes
- **WHEN** supported programs differ only in whitespace, comments and consistent identifier renaming
- **THEN** their normalized structures match and receive structural score 100

#### Scenario: Alternate correct algorithm
- **WHEN** a different structure passes the same behavior tests
- **THEN** passed behavior tests remain passed regardless of structural similarity

### Requirement: Bound analysis complexity
The system SHALL enforce documented analysis time, tree-size and comparison-work limits. Limit exhaustion SHALL yield analysis_limit with unavailable structural score, not a crash, host exhaustion or fabricated numeric result.

#### Scenario: Oversized parsed structure
- **WHEN** a parsed program exceeds 10,000 nodes or comparison exceeds 100,000 node-pair operations
- **THEN** structural analysis stops with analysis_limit and no numeric structural score

## Inputs and outputs
Inputs are bounded source and language configuration; outputs are syntax diagnostics, normalized IR and analysis evidence.

## Expected behavior
Supported source is parsed into bounded evidence without silent regex fallback or semantic overclaiming.

## Edge cases and failure handling
Encoding, parser, toolchain, unsupported syntax and complexity-limit failures remain distinguishable.

## Acceptance criteria
Each supported language has valid, malformed, unsupported and boundary fixtures.

## Dependencies
Depends on `python-analysis`, `c-analysis`, `java-analysis`, `normalized-ir`.
