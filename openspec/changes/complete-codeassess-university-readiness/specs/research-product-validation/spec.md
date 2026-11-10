                                            # Spec Delta

## Purpose

Defines reproducible independent evaluation and evidence-bounded product research for academic validity, performance, and university-readiness decisions.

## ADDED Requirements

### Requirement: Independently reviewed benchmark labels
Published grading metrics SHALL use versioned Python, C, and Java fixtures whose labels and provenance were approved by qualified independent reviewers.

#### Scenario: Candidate label is unreviewed
- **WHEN** a fixture remains `pending-independent-review`
- **THEN** it may validate tooling but SHALL NOT contribute to published project accuracy

#### Scenario: Reviewer changes a label
- **WHEN** independent review corrects an expected outcome
- **THEN** a new immutable corpus version records the rationale, reviewer role, hashes, and split impact

### Requirement: Development and held-out separation
Development and held-out sets SHALL be hash-disjoint, frozen before metric tuning, balanced across languages and outcome classes, and checked for leakage.

#### Scenario: Duplicate source crosses splits
- **WHEN** identical or normalized-equivalent source appears in both splits
- **THEN** corpus validation rejects the release

### Requirement: Reproducible evaluation metrics
Evaluation SHALL report per-language and aggregate accuracy, precision, recall, F1, score error, category agreement, concept detection, recommendation quality, feedback grounding, latency, throughput, and repeatability where labels support them.

#### Scenario: Held-out run repeats
- **WHEN** the approved held-out evaluation runs twice with identical versions
- **THEN** decisions and deterministic metrics match, and operational variance is reported separately

### Requirement: Ablation evidence
Ablation studies SHALL compare functional tests, static analysis, concept analysis, Knowledge Graph reasoning, and feedback composition without changing held-out labels between variants.

#### Scenario: Component contribution is measured
- **WHEN** a component is disabled in an ablation configuration
- **THEN** the report records the exact configuration and metric differences without claiming causality beyond the experiment

### Requirement: Feedback usefulness review
Feedback quality SHALL be assessed with a preregistered human-review rubric covering correctness, evidence grounding, specificity, actionability, confidentiality, and educational usefulness.

#### Scenario: Human review is unavailable
- **WHEN** qualified reviewers have not completed the rubric
- **THEN** feedback usefulness remains BLOCKED and automated proxies are not presented as human validation

### Requirement: Competitive research integrity
Competitive comparisons SHALL cite dated official public sources, compare defined capabilities fairly, respect access controls and terms, and avoid unsupported uniqueness or superiority claims.

#### Scenario: Differentiation claim
- **WHEN** CodeAssess is described as explainable and Knowledge Graph-driven
- **THEN** the claim distinguishes implemented evidence from intended positioning and cites competitor capabilities that were actually reviewed

### Requirement: University-readiness decision
The readiness report SHALL classify each capability as VERIFIED, PARTIALLY VERIFIED, BLOCKED, or NOT IMPLEMENTED and SHALL base pilot recommendations on recorded acceptance evidence.

#### Scenario: Core execution is blocked
- **WHEN** real isolated execution or independent benchmark review is incomplete
- **THEN** production or university-pilot readiness cannot be marked PASS
