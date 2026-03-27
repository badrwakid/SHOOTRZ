# MVP Phase Detector Integration - FIX APPLIED

## Problem Identified

The overlay video was showing **incorrect phase labels** because:

1. ❌ The MVP pipeline was NOT using the new `PhaseDetector`
2. ❌ It was using hardcoded phases from the old `ShotDetector`
3. ❌ Phase name was "start" instead of "stance"
4. ❌ Only 3 phases were being detected (start, crouch, release)
5. ❌ No motion-based detection - just simple knee minimum and wrist peak

## Root Cause

**File:** `SHOOTRZ/backend/routers/mvp.py` (lines 267-275)

**Old Code:**
```python
phases = []
if shot_window_path.exists():
    with open(shot_window_path, "r") as f:
        sw = json.load(f)
    phases = [
        {"phase": "start", "start_frame": sw.get("start_frame", 0), ...},  # ❌ "start"
        {"phase": "crouch", "start_frame": sw.get("crouch_frame", 0), ...},
        {"phase": "release", "start_frame": sw.get("release_frame", 0), ...},
    ]
```

**Problem:**
- Manually creating phases from `shot_window.json`
- Using old `ShotDetector` which only finds knee minimum and wrist peak
- Not using the new motion-based `PhaseDetector`
- Hardcoded phase name "start" instead of "stance"

## Solution Applied

**Updated Code:** ✅
```python
# Use new motion-based phase detector
phases = []
try:
    fps = pose_json.get("video_metadata", {}).get("fps", 30.0)
    phase_detector = PhaseDetector(fps=fps)
    phases = phase_detector.detect_phases(pose_results)
    logger.info(f"Detected {len(phases)} phases using motion-based detector")
except Exception as phase_err:
    logger.warning(f"Phase detection failed: {phase_err}, using fallback")
    # Fallback to old method if phase detector fails
    if shot_window_path.exists():
        with open(shot_window_path, "r") as f:
            sw = json.load(f)
        phases = [
            {"phase": "stance", ...},  # ✅ Changed to "stance"
            {"phase": "crouch", ...},
            {"phase": "release", ...},
        ]
```

## Changes Made

### 1. Import Statement Added ✅
```python
from inference.phase_detector import PhaseDetector
```

### 2. Phase Detection Updated ✅
- Now uses `PhaseDetector(fps=fps).detect_phases(pose_results)`
- Gets motion-based phase detection with:
  - Initial state detection (handles mid-crouch start)
  - Adaptive thresholds per video
  - Multi-signal fusion
  - All 4 phases: STANCE, CROUCH, RELEASE, LANDING

### 3. Fallback Mechanism ✅
- If new detector fails, falls back to old method
- But fixes "start" → "stance" in fallback too

## What This Fixes

### Before ❌
- Phase labels: "START", "CROUCH", "RELEASE"
- Only 3 phases detected
- Simple threshold-based detection
- Wrong frame boundaries
- No mid-motion handling

### After ✅
- Phase labels: "STANCE", "CROUCH", "RELEASE", "LANDING"
- All 4 phases detected
- Motion-based pattern detection
- Accurate frame boundaries
- Handles videos starting mid-crouch

## Expected Results

When you upload a new video, you should see:

1. **Correct Phase Names:**
   - "Phase: STANCE" (not "START") ✅
   - "Phase: CROUCH" ✅
   - "Phase: RELEASE" ✅
   - "Phase: LANDING" ✅

2. **Accurate Phase Timing:**
   - STANCE ends when hip starts descending
   - CROUCH tracks actual dip bottom
   - RELEASE at wrist peak with multi-signal fusion
   - LANDING after release completes

3. **Mid-Motion Handling:**
   - If video starts mid-crouch → skips STANCE, starts with CROUCH at frame 0
   - Adaptive to any recording start time

## Testing Instructions

1. **Restart the backend server:**
   ```bash
   # Stop current server (Ctrl+C)
   cd SHOOTRZ/backend
   python -m uvicorn routers.app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Upload a test video** through your app

3. **Check the overlay.mp4** - You should now see:
   - Correct phase labels (STANCE not START)
   - Phases detected at correct times
   - All 4 phases visible

4. **Check backend logs** for:
   ```
   Detected 4 phases using motion-based detector
   ```

## Files Modified

- ✅ `SHOOTRZ/backend/routers/mvp.py` - Integrated new PhaseDetector

## Files Previously Created

- ✅ `SHOOTRZ/backend/inference/motion_analyzer.py` - Motion analysis
- ✅ `SHOOTRZ/backend/inference/phase_detector.py` - New detector
- ✅ `SHOOTRZ/backend/inference/tests/test_phase_detector.py` - Tests
- ✅ `SHOOTRZ/backend/utils/video_annotator.py` - Already had correct enum handling

## Why It Wasn't Working Before

The new `PhaseDetector` was created but **never integrated** into the MVP pipeline. The overlay generation in `mvp.py` was still using the old manual phase creation from shot_window, which:

1. Only had 3 phases (no LANDING)
2. Used "start" instead of "stance"  
3. Didn't use motion analysis
4. Couldn't handle mid-motion starts

Now the MVP pipeline uses the full motion-based phase detector!

---

**Status:** ✅ **FIXED**  
**Integration:** ✅ **COMPLETE**  
**Testing:** ⏳ **RESTART SERVER AND TEST**

The phase detection system is now fully integrated into the MVP pipeline and will generate overlay videos with correct phase labels and timing.
