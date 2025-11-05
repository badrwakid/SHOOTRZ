#!/usr/bin/env python3
"""
SHOOTRZ AI Backend Server Startup Script
"""

import sys
import os

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'mediapipe': 'MediaPipe',
    }
    
    missing = []
    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - MISSING")
            missing.append(name)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install flask flask-cors opencv-python numpy mediapipe pillow requests python-dotenv")
        return False
    
    print("✅ All dependencies installed\n")
    return True

def start_server():
    """Start the Flask server"""
    if not check_dependencies():
        sys.exit(1)
    
    print("=" * 60)
    print("Starting SHOOTRZ AI Backend Server...")
    print("=" * 60)
    
    try:
        # Import the Flask app
        from app import app, privacy_manager
        
        print("\n🚀 Server starting on http://localhost:5000")
        print("\nAvailable endpoints:")
        print("  GET  /health              - Health check")
        print("  POST /api/analyze         - Analyze video")
        print("  GET  /api/video/<id>      - Get annotated video")
        print("  GET  /api/performance     - Performance metrics")
        print("  GET  /api/status          - System status")
        print("  POST /api/cleanup         - Force cleanup")
        print("\n" + "=" * 60)
        print("Press Ctrl+C to stop the server")
        print("=" * 60 + "\n")
        
        # Run the server
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Shutting down server...")
        print("=" * 60)
        try:
            from app import privacy_manager
            privacy_manager.stop_cleanup_thread()
            print("✓ Cleanup thread stopped")
        except:
            pass
        print("✓ Server stopped")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_server()


