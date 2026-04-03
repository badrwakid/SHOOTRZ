# MVP Analysis Feature (Target Structure)

This folder documents the intended feature boundary for MVP analysis.
The current implementation still lives primarily in:

- `src/screens/MVPAnalysisScreen.tsx`
- `src/services/api.service.ts`
- `src/components/CameraRecorder.tsx`
- `src/components/AngleGraph.tsx`

## Target Boundary

- UI container (screen-level)
- feature-local hooks (job polling, local mapping)
- feature types mapped from canonical contracts in `src/types/contracts.ts`
- no duplicate API DTO definitions inside screen files

## Migration Guidance

Refactors should be incremental:

1. Extract hooks/utilities without changing behavior.
2. Keep API contract mapping explicit.
3. Validate upload -> poll -> render flow after each step.
