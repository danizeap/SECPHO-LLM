# Capability: recommendation-scoring

## Purpose

Ensure the SECPHO assistant describes match scoring with a single, consistent
formula that always agrees with the precomputed scores it serves, upholding the
"math decides, the LLM explains" contract.

## Requirements

### Requirement: Single source of truth for scoring weights
The system SHALL define exactly one in-app representation of the People Matcher
V1.1 scoring weights (`SCORING_WEIGHTS` = profile_similarity 0.44,
structured_overlap 0.24, needs_overlap 0.10, event_interest_overlap_score 0.14,
location_overlap_score 0.06, personal_affinity_score 0.02), and every LLM-facing
path SHALL reference it rather than an inline weight literal.

#### Scenario: Per-person payload exposes the canonical weights
- **WHEN** `llm_payload_for_person` builds context for a member
- **THEN** its `scoring_formula` field equals `SCORING_WEIGHTS`

#### Scenario: Question-answer context exposes the canonical weights
- **WHEN** `llm_answer_question` builds grounded context
- **THEN** its `scoring_formula` field equals `SCORING_WEIGHTS`, not a separate
  literal

### Requirement: Consistent scoring-formula explanation
The system SHALL answer a user question about scoring/weights with a single
plain-English statement (`SCORING_FORMULA_TEXT`) describing all six weighted
signals, consistent with the weights that produced the served match data.

#### Scenario: User asks how scores are computed
- **WHEN** a chat question contains "weight", "score", or "scoring"
- **THEN** `answer_question` returns `SCORING_FORMULA_TEXT`, which names all six
  signals including location overlap and personal affinity

### Requirement: App description matches served data
The system SHALL keep the in-app scoring-formula description aligned with the
weights used to compute the served match CSV, and SHALL NOT present a formula
that disagrees with that data.

#### Scenario: App weights match the CSV-producing weights
- **WHEN** the app describes the scoring formula
- **THEN** the six weights equal the `WEIGHTS` dict in
  `recommendation_engine/build_people_matcher_v1_1_events.py` that produced
  `recommendation_engine/outputs/people_matches_v1_1_events.csv`
