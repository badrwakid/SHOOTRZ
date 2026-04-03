# ACTIVE_MODULES

This list is for code review and refactor safety. Items here are considered
active and must be preserved unless explicitly migrated.

## Frontend Active Modules

- `index.ts`
- `App.tsx`
- `src/navigation/AppNavigator.tsx`
- `src/context/AuthContext.tsx`
- `src/services/api.service.ts`
- `src/services/storage.service.ts`
- `src/services/chat.service.ts`
- `src/services/chat-storage.service.ts`
- `src/services/supabase.client.ts`
- `src/screens/HomeScreen.tsx`
- `src/screens/MVPAnalysisScreen.tsx`
- `src/screens/ChatScreen.tsx`
- `src/screens/ProgressScreen.tsx`
- `src/screens/ProfileScreen.tsx`
- `src/screens/DrillsScreen.tsx`
- `src/screens/DrillDetailScreen.tsx`
- `src/screens/WorkoutsScreen.tsx`
- `src/screens/LoginScreen.tsx`
- `src/screens/UsernameScreen.tsx`
- `src/screens/OnboardingScreen.tsx`
- `src/screens/SplashScreen.tsx`

## Backend Active Modules

- `backend/main.py`
- `backend/routers/mvp.py`
- `backend/routers/chat.py`
- `backend/routers/history.py`
- `backend/routers/feedback.py`
- `backend/routers/sessions.py`
- `backend/routers/recommendation_routes.py`
- `backend/storage/db.py`
- `backend/storage/supabase_client.py`
- `backend/mvp/core/pipeline.py`
- `backend/mvp/core/run_tracker.py`
- `backend/mvp/core/video_loader.py`
- `backend/mvp/core/pose_estimation.py`
- `backend/mvp/core/signal_smoothing.py`
- `backend/mvp/core/angle_computation.py`
- `backend/mvp/core/shot_detection.py`
- `backend/mvp/core/metrics.py`
- `backend/inference/pose_2d.py`
- `backend/inference/phase_detector.py`
- `backend/utils/video_annotator.py`

## Active Tests (Current Baseline)

- `backend/mvp/tests/test_integration.py`
- `backend/mvp/tests/test_metric_scoring.py`
- `backend/mvp/tests/test_shot_detection.py`
- `backend/mvp/tests/test_angle_computation.py`
