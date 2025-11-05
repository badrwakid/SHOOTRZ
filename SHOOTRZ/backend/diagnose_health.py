#!/usr/bin/env python3
"""Diagnostic script to verify /health endpoint registration"""
import sys
import os

# Ensure we're importing from the right place
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("=" * 60)
print("DIAGNOSING /health ENDPOINT REGISTRATION")
print("=" * 60)

try:
    print("\n[1] Importing app...")
    from SHOOTRZ.backend.main import app, create_app
    print("✅ App imported successfully")
    
    print("\n[2] Creating fresh app instance...")
    test_app = create_app()
    print("✅ Fresh app created")
    
    print("\n[3] Checking all routes...")
    all_routes = [r for r in test_app.routes if hasattr(r, 'path')]
    print(f"   Total routes found: {len(all_routes)}")
    
    print("\n[4] Looking for /health route...")
    health_routes = [r for r in all_routes if r.path == '/health']
    
    if health_routes:
        print(f"✅ FOUND /health route!")
        route = health_routes[0]
        print(f"   Path: {route.path}")
        print(f"   Methods: {route.methods}")
        print(f"   Type: {type(route).__name__}")
        print(f"   Endpoint: {route.endpoint}")
        print(f"   Name: {route.name}")
    else:
        print("❌ /health route NOT FOUND!")
        print("\nAvailable routes:")
        for r in sorted(all_routes, key=lambda x: x.path):
            if r.path.startswith('/'):
                print(f"   {r.path} [{list(r.methods)[0] if r.methods else 'N/A'}]")
    
    print("\n[5] Checking if route is callable...")
    if health_routes:
        route = health_routes[0]
        try:
            # Try to get the endpoint function
            endpoint = route.endpoint
            print(f"   Endpoint is callable: {callable(endpoint)}")
            print(f"   Endpoint type: {type(endpoint)}")
        except Exception as e:
            print(f"   Error checking endpoint: {e}")
    
    print("\n[6] Testing app instance from import...")
    if hasattr(app, 'routes'):
        app_routes = [r for r in app.routes if hasattr(r, 'path') and r.path == '/health']
        print(f"   /health in imported app: {len(app_routes) > 0}")
    
    print("\n" + "=" * 60)
    if health_routes:
        print("✅ DIAGNOSIS: /health endpoint IS registered in code")
        print("⚠️  If server still returns 404, the process needs restart")
    else:
        print("❌ DIAGNOSIS: /health endpoint NOT found in code!")
        print("   There is a code registration issue")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR during diagnosis: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)






