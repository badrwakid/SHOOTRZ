from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid
from ..storage.supabase_client import get_service_client, get_anon_client
from ..storage.db import record_video, record_metrics, record_feedback, get_user_history
from ..utils.config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/test")
async def test_database():
    """Test database connectivity and configuration"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "config_check": {},
        "connection_test": {},
        "operations_test": {},
        "status": "unknown"
    }
    
    # Check configuration
    results["config_check"] = {
        "supabase_url_set": bool(SUPABASE_URL),
        "anon_key_set": bool(SUPABASE_ANON_KEY),
        "service_key_set": bool(SUPABASE_SERVICE_KEY),
        "url_preview": SUPABASE_URL[:30] + "..." if SUPABASE_URL and len(SUPABASE_URL) > 30 else SUPABASE_URL
    }
    
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY]):
        results["status"] = "error"
        results["error"] = "Missing environment variables. Check backend/.env file"
        return results
    
    # Test client connections
    try:
        anon_client = get_anon_client()
        results["connection_test"]["anon_client"] = "✅ Connected"
    except Exception as e:
        results["connection_test"]["anon_client"] = f"❌ Error: {str(e)}"
        results["status"] = "error"
        return results
    
    try:
        service_client = get_service_client()
        results["connection_test"]["service_client"] = "✅ Connected"
    except Exception as e:
        results["connection_test"]["service_client"] = f"❌ Error: {str(e)}"
        results["status"] = "error"
        return results
    
    # Test database operations
    # First, create a test user (or use existing test user)
    test_user_id = None
    test_file_url = "https://example.com/test-video.mp4"
    
    try:
        # Create test user if it doesn't exist
        service_client = get_service_client()
        test_email = f"test-{int(datetime.now().timestamp())}@test.com"
        user_response = service_client.table("users").select("id").eq("email", test_email).execute()
        
        if user_response.data:
            test_user_id = user_response.data[0]["id"]
            results["operations_test"]["test_user"] = f"✅ Using existing test user"
        else:
            # Insert test user
            test_user_id = str(uuid.uuid4())
            service_client.table("users").insert({
                "id": test_user_id,
                "email": test_email,
                "auth_provider": "test"
            }).execute()
            results["operations_test"]["test_user"] = f"✅ Created test user ({test_user_id[:8]}...)"
    except Exception as e:
        results["operations_test"]["test_user"] = f"❌ Error creating user: {str(e)}"
        results["status"] = "partial"
        return results
    
    if not test_user_id:
        results["operations_test"]["test_user"] = "❌ Failed to get test user"
        results["status"] = "error"
        return results
    
    try:
        # Test 1: Insert video record
        video_id = record_video(
            user_id=test_user_id,
            file_url=test_file_url,
            angle="45",
            fps=30,
            device="test"
        )
        results["operations_test"]["record_video"] = f"✅ Success (video_id: {video_id[:8]}...)"
    except Exception as e:
        results["operations_test"]["record_video"] = f"❌ Error: {str(e)}"
        results["status"] = "partial"
        return results
    
    try:
        # Test 2: Insert metrics
        metric_ids = record_metrics(
            video_id,
            [
                {"metric_name": "test_metric", "value": 42.0, "confidence": 0.95}
            ]
        )
        results["operations_test"]["record_metrics"] = f"✅ Success (metric_ids: {len(metric_ids)} created)"
    except Exception as e:
        results["operations_test"]["record_metrics"] = f"❌ Error: {str(e)}"
        results["status"] = "partial"
    
    try:
        # Test 3: Insert feedback (if metrics succeeded)
        if metric_ids:
            record_feedback([
                {
                    "metric_id": metric_ids[0],
                    "message": "Test feedback message",
                    "severity": "info"
                }
            ])
            results["operations_test"]["record_feedback"] = "✅ Success"
        else:
            results["operations_test"]["record_feedback"] = "⚠️ Skipped (no metrics)"
    except Exception as e:
        results["operations_test"]["record_feedback"] = f"❌ Error: {str(e)}"
        results["status"] = "partial"
    
    try:
        # Test 4: Query history
        history = get_user_history(test_user_id)
        results["operations_test"]["get_user_history"] = f"✅ Success (found {len(history)} records)"
    except Exception as e:
        results["operations_test"]["get_user_history"] = f"❌ Error: {str(e)}"
        results["status"] = "partial"
    
    # Determine overall status
    if all("✅" in str(v) for v in results["operations_test"].values() if "Error" not in str(v)):
        results["status"] = "success"
    elif any("✅" in str(v) for v in results["operations_test"].values()):
        results["status"] = "partial"
    else:
        results["status"] = "error"
    
    return results

