#!/usr/bin/env python3
"""Quick test script to verify /health endpoint is registered"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from SHOOTRZ.backend.main import app
    
    # Check if /health route exists
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    health_exists = '/health' in routes
    
    if health_exists:
        print("✅ SUCCESS: /health endpoint is registered!")
        print(f"   Total routes: {len(routes)}")
        print(f"   Health route: /health")
        
        # Try to get the route details
        health_route = [r for r in app.routes if hasattr(r, 'path') and r.path == '/health']
        if health_route:
            print(f"   Methods: {health_route[0].methods}")
        
        sys.exit(0)
    else:
        print("❌ ERROR: /health endpoint NOT found in routes!")
        print(f"   Available routes: {[r for r in routes if r.startswith('/')]}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR importing app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)






