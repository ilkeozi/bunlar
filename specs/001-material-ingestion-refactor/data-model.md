# Data Model: Material Ingestion Domain Refactor

## Entity: DomainArea
- Fields:
  - `name` (enum: `shared`, `material-ingestion`, `uns`)
  - `ownership_rules` (list of placement rules)
  - `allowed_dependencies` (list of domain areas this area can depend on)
- Validation Rules:
  - `name` MUST be unique.
  - Domain-specific area MUST NOT host behavior owned by another domain.

## Entity: PlacementRule
- Fields:
  - `id` (string)
  - `description` (string)
  - `match_criteria` (short expression or documented condition)
  - `target_domain_area` (DomainArea.name)
  - `enforcement_level` (enum: `warning`, `blocking`)
- Validation Rules:
  - `target_domain_area` MUST reference a valid DomainArea.
  - Rules that resolve ambiguity MUST be marked `blocking`.

## Entity: PipelineRun
- Fields:
  - `run_id` (string)
  - `context_key` (string)
  - `invocation_channel` (enum: `cli`, `http_api`)
  - `requested_at` (timestamp)
  - `started_at` (timestamp|null)
  - `completed_at` (timestamp|null)
  - `status` (enum: `queued`, `running`, `failed`, `succeeded`)
  - `last_successful_stage` (string|null)
  - `failure_stage` (string|null)
  - `failure_reason` (string|null)
- Validation Rules:
  - `run_id` MUST be unique.
  - Only one `running` PipelineRun per `context_key`.
  - `failure_stage` required when `status=failed`.

## Entity: ExecutionStage
- Fields:
  - `name` (string)
  - `order` (integer)
  - `state` (enum: `pending`, `running`, `succeeded`, `failed`, `skipped`)
  - `input_requirements` (list)
  - `output_guarantees` (list)
- Validation Rules:
  - `order` MUST be unique in a pipeline definition.
  - Stage transition allowed only in deterministic sequence.

## Entity: ContextQueue
- Fields:
  - `context_key` (string)
  - `pending_run_ids` (ordered list)
- Validation Rules:
  - FIFO ordering MUST be preserved.
  - Dequeued run MUST be next queued for same context.

## State Transitions
- `PipelineRun`:
  - `queued -> running` when no active run exists for same context.
  - `running -> succeeded` when all stages succeed.
  - `running -> failed` when any stage fails.
  - `failed -> running` on resume, restarting from `last_successful_stage + 1`.
- `ExecutionStage`:
  - `pending -> running -> succeeded` for healthy path.
  - `running -> failed` on error.
