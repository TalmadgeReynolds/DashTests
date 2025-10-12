# Job State Machine

States: QUEUED → RUNNING → POST → DONE | ERROR

Transitions:
- enqueue -> QUEUED
- worker start -> RUNNING
- provider finished -> (if postfx on) POST else DONE
- postfx ok -> DONE
- any failure -> ERROR (with error_code, error_detail)

Invariants:
- DONE/ERROR are terminal
- Only one active provider_job_id per job.method
