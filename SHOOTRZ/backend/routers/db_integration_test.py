from fastapi import APIRouter
from datetime import datetime
import uuid
from ..storage.supabase_client import get_service_client
from ..storage.db import record_video, record_metrics, record_feedback, get_user_history

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/integration-test")
async def integration_test():
    """Test full application flow: analyze endpoint -> database"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_name": "Full Application Integration Test",
        "steps": {},
        "status": "unknown"
    }
    
    # Step 1: Create test user
    try:
        service_client = get_service_client()
        test_email = f"integration-test-{int(datetime.now().timestamp())}@test.com"
        test_user_id = str(uuid.uuid4())
        
        service_client.table("users").insert({
            "id": test_user_id,
            "email": test_email,
            "auth_provider": "test"
        }).execute()
        
        results["steps"]["create_user"] = {
            "status": "success",
            "user_id": test_user_id[:8] + "...",
            "email": test_email
        }
    except Exception as e:
        results["steps"]["create_user"] = {"status": "error", "error": str(e)}
        results["status"] = "error"
        return results
    
    # Step 2: Simulate analyze endpoint (what happens when user uploads video)
    try:
        test_file_url = "https://example.com/test-integration-video.mp4"
        video_id = record_video(
            user_id=test_user_id,
            file_url=test_file_url,
            angle="45",
            fps=30,
            device="mobile"
        )
        
        results["steps"]["analyze_video"] = {
            "status": "success",
            "video_id": video_id[:8] + "...",
            "message": "Video record created (simulates /analyze endpoint)"
        }
    except Exception as e:
        results["steps"]["analyze_video"] = {"status": "error", "error": str(e)}
        results["status"] = "error"
        return results
    
    # Step 3: Record metrics (what backend does after processing)
    try:
        metric_ids = record_metrics(
            video_id,
            [
                {"metric_name": "elbow_angle", "value": 90.5, "confidence": 0.92},
                {"metric_name": "knee_angle", "value": 120.3, "confidence": 0.88},
                {"metric_name": "release_angle", "value": 45.2, "confidence": 0.95}
            ]
        )
        
        results["steps"]["record_metrics"] = {
            "status": "success",
            "metric_count": len(metric_ids),
            "metrics": ["elbow_angle", "knee_angle", "release_angle"]
        }
    except Exception as e:
        results["steps"]["record_metrics"] = {"status": "error", "error": str(e)}
        results["status"] = "partial"
    
    # Step 4: Record feedback (what feedback engine generates)
    try:
        if metric_ids:
            feedback_ids = record_feedback([
                {
                    "metric_id": metric_ids[0],
                    "message": "Great elbow positioning!",
                    "severity": "positive"
                },
                {
                    "metric_id": metric_ids[1],
                    "message": "Consider bending knees more for better power",
                    "severity": "info"
                }
            ])
            
            results["steps"]["record_feedback"] = {
                "status": "success",
                "feedback_count": len(feedback_ids)
            }
        else:
            results["steps"]["record_feedback"] = {"status": "skipped", "reason": "no metrics"}
    except Exception as e:
        results["steps"]["record_feedback"] = {"status": "error", "error": str(e)}
        results["status"] = "partial"
    
    # Step 5: Get history (what frontend calls when user views history)
    try:
        history = get_user_history(test_user_id)
        results["steps"]["get_history"] = {
            "status": "success",
            "video_count": len(history),
            "videos": [
                {
                    "id": v["id"][:8] + "...",
                    "created_at": v.get("created_at", "N/A"),
                    "angle": v.get("angle"),
                    "fps": v.get("fps")
                }
                for v in history[:3]  # Show first 3
            ]
        }
    except Exception as e:
        results["steps"]["get_history"] = {"status": "error", "error": str(e)}
        results["status"] = "partial"
    
    # Step 6: Verify data exists in database
    try:
        service_client = get_service_client()
        
        # Verify video
        video_check = service_client.table("videos").select("id, user_id").eq("id", video_id).execute()
        video_exists = len(video_check.data) > 0
        
        # Verify metrics
        metrics_check = service_client.table("metrics").select("id").eq("video_id", video_id).execute()
        metrics_count = len(metrics_check.data) if metrics_check.data else 0
        
        # Verify feedback
        feedback_check = service_client.table("feedback").select("id").in_("metric_id", metric_ids).execute()
        feedback_count = len(feedback_check.data) if feedback_check.data else 0
        
        results["steps"]["verify_data"] = {
            "status": "success",
            "video_exists": video_exists,
            "metrics_count": metrics_count,
            "feedback_count": feedback_count,
            "data_integrity": "ok" if (video_exists and metrics_count > 0) else "warning"
        }
    except Exception as e:
        results["steps"]["verify_data"] = {"status": "error", "error": str(e)}
        results["status"] = "partial"
    
    # Determine final status
    all_success = all(
        step.get("status") == "success" 
        for step in results["steps"].values() 
        if isinstance(step, dict)
    )
    
    results["status"] = "success" if all_success else ("partial" if any("success" in str(v) for v in results["steps"].values()) else "error")
    
    return results






