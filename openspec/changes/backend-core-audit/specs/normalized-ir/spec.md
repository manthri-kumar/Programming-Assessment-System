# Normalized Intermediate Representation

## Purpose and scope
Provide a language-neutral, versioned representation for comparable program structure.

## ADDED Requirements
### Requirement: Normalize supported constructs
The IR SHALL represent functions, loops, branches, calls, operators, literals and source locations with language and schema versions.
#### Scenario: Formatting and renaming
- **GIVEN** equivalent programs differing only in whitespace, comments and identifier names
- **WHEN** normalized
- **THEN** their structural IR is equal.

### Requirement: Preserve evidence provenance
Each IR node SHALL retain source span and parser evidence without exposing raw source in logs by default.
#### Scenario: Diagnostic location
- **GIVEN** a failing node
- **WHEN** feedback references it
- **THEN** the result contains a stable evidence ID and source location.

## Inputs and outputs
Input is parser output; output is canonical JSON-like IR and a content-derived evidence hash.

## Expected behavior
Normalization SHALL ignore comments/formatting, preserve meaningful operators and remain deterministic.

## Edge cases and failure handling
Unknown constructs become explicit `unsupported_node`; node and comparison limits yield `analysis_limit`.

## Acceptance criteria
Canonical serialization is byte-stable across repeated runs and all three language adapters.

## Test scenarios
Equivalent rewrites, alternate algorithms, unknown nodes and oversized trees are tested.

## Dependencies
Depends on `program-analysis`, `python-analysis`, `c-analysis`, `java-analysis`.
