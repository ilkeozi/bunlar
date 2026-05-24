# Data Model: Retire Stale Material-Ingestion Spec

## Entity: SpecBaseline

- Purpose: Represents a specification baseline and its planning status.
- Fields:
  - `feature_directory` (string, required): Relative path to feature spec directory.
  - `status` (enum, required): `active` or `retired`.
  - `title` (string, required): Human-readable feature name.
  - `created_on` (date, required): Baseline creation date.
  - `retired_on` (date, optional): Retirement date when status is `retired`.
  - `retirement_reason` (string, optional): Reason stale baseline was retired.
  - `replacement_feature_directory` (string, optional): Active replacement path.

## Entity: SpecPointerMetadata

- Purpose: Defines active pointer used by Spec Kit commands.
- Fields:
  - `feature_directory` (string, required): Path of active planning baseline.

## Relationships

- One `SpecPointerMetadata` references exactly one `SpecBaseline` with `status=active`.
- A `retired` `SpecBaseline` may optionally reference one replacement `SpecBaseline`.

## Validation Rules

- `feature_directory` must reference an existing folder under `specs/`.
- Only one baseline can be `active` at a time.
- If `status=retired`, `retirement_reason` should be non-empty.
- If `replacement_feature_directory` is present, it must point to an `active` baseline.

## State Transitions

- `active -> retired`: allowed when replacement baseline is designated.
- `retired -> active`: discouraged; allowed only via explicit governance decision.
- `active -> active` (path change): implemented as current active retirement plus new active assignment.
