# DEPRECATED_MODULES

These modules are currently not on verified active runtime paths.
They should not be extended and are candidates for removal or isolation.

## Frontend

- The previously unwired duplicate API/context/hooks were removed in this branch.
- Remaining legacy candidates should be validated before deletion:
  - `src/services/mediapipe.service.ts` (not used in active MVP flow)
  - `src/services/customEmail.service.ts` (not used by active paths)

## Repository / Legacy

- `__graveyard__/` (archived snapshots and backups)
- stale startup scripts with mismatched paths should be treated as deprecated
  after command verification.

## Notes

- A module listed here is not automatically deleted.
- Removal happens only after grep/import validation and smoke verification.
