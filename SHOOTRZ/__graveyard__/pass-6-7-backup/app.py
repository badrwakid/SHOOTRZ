from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime
from video_processor import VideoProcessor
from privacy import PrivacyManager
from evaluator import PerformanceEvaluator

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
MAX_VIDEO_LENGTH = 30  # seconds
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Initialize services
processor = VideoProcessor()
privacy_manager = PrivacyManager()
evaluator = PerformanceEvaluator()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_video_file(file):
    """Validate uploaded video file"""
    if not file or file.filename == '':
        return False, 'No file selected'
    
    if not allowed_file(file.filename):
        return False, f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
    
    # Check file size (if available)
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > MAX_FILE_SIZE:
            return False, f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
    
    return True, 'Valid file'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'SHOOTRZ Pose Detection API',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """
    Analyze basketball shooting form from uploaded video
    
    Returns:
        JSON with metrics, scores, tips, and annotated video ID
    """
    try:
        # Check if video file is present
        if 'video' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No video file provided'
            }), 400
        
        file = request.files['video']
        
        # Validate file
        is_valid, message = validate_video_file(file)
        if not is_valid:
            return jsonify({
                'success': False, 
                'error': message
            }), 400
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        if not filename:
            filename = f'video_{int(time.time())}.mp4'
        
        # Save uploaded video
        video_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(video_path)
        
        print(f"Processing video: {filename}")
        
        # Validate video before processing
        validation_result = processor.validate_video(video_path)
        if not validation_result['valid']:
            # Clean up invalid file
            if os.path.exists(video_path):
                os.remove(video_path)
            return jsonify({
                'success': False,
                'error': validation_result['error']
            }), 400
        
        # Strip metadata for privacy
        privacy_manager.strip_metadata(video_path)
        
        # Process video
        start_time = time.time()
        result = processor.process_video(video_path, PROCESSED_FOLDER)
        processing_time = time.time() - start_time
        
        # Schedule deletion of uploaded video
        privacy_manager.schedule_deletion(video_path)
        if result.get('annotated_video_path'):
            privacy_manager.schedule_deletion(result['annotated_video_path'])
        
        # Record performance metrics
        evaluator.evaluate_analysis(video_path, processor)
        
        if result['success']:
            # Return enhanced analysis results with all new AI features
            response = {
                'success': True,
                'video_id': result['video_id'],
                'metrics': result['metrics'],
                'scores': result['scores'],
                'tips': result['tips'],
                'performance_level': result.get('performance_level', 'Unknown'),
                'processing_stats': {
                    'processing_time': round(processing_time, 2),
                    'total_frames': result.get('total_frames', 0),
                    'processed_frames': result.get('processed_frames', 0),
                    'pose_detection_rate': result.get('pose_detection_rate', 0),
                    'processing_fps': result.get('processing_fps', 0)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Video processing failed')
            }), 500
        
    except Exception as e:
        print(f"Error in analyze_video: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/video/<video_id>', methods=['GET'])
def get_annotated_video(video_id):
    """Get annotated video by ID"""
    try:
        video_path = os.path.join(PROCESSED_FOLDER, f'{video_id}.mp4')
        
        if not os.path.exists(video_path):
            return jsonify({
                'success': False,
                'error': 'Video not found'
            }), 404
        
        # Check if file is still valid (not deleted)
        if not os.path.isfile(video_path):
            return jsonify({
                'success': False,
                'error': 'Video file has been deleted'
            }), 404
        
        # Send file
        return send_file(
            video_path, 
            mimetype='video/mp4', 
            as_attachment=False,
            download_name=f'annotated_{video_id}.mp4'
        )
        
    except Exception as e:
        print(f"Error serving video {video_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error serving video: {str(e)}'
        }), 500

@app.route('/api/performance', methods=['GET'])
def get_performance_metrics():
    """Get performance evaluation metrics"""
    try:
        summary = evaluator.get_summary()
        trends = evaluator.get_performance_trends()
        
        return jsonify({
            'success': True,
            'summary': summary,
            'trends': trends,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error getting performance metrics: {e}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving metrics: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get system status and queue information"""
    try:
        deletion_status = privacy_manager.get_deletion_queue_status()
        
        return jsonify({
            'success': True,
            'system_status': {
                'upload_folder': UPLOAD_FOLDER,
                'processed_folder': PROCESSED_FOLDER,
                'max_video_length': MAX_VIDEO_LENGTH,
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
                'allowed_extensions': list(ALLOWED_EXTENSIONS)
            },
            'privacy_status': deletion_status,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error getting system status: {e}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving status: {str(e)}'
        }), 500

@app.route('/api/cleanup', methods=['POST'])
def force_cleanup():
    """Force cleanup of old files"""
    try:
        # Clean up uploads folder
        privacy_manager.force_cleanup(UPLOAD_FOLDER)
        
        # Clean up processed folder
        privacy_manager.force_cleanup(PROCESSED_FOLDER)
        
        return jsonify({
            'success': True,
            'message': 'Cleanup completed',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in force cleanup: {e}")
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    try:
        # Cleanup old files on startup
        print("Starting SHOOTRZ Pose Detection API...")
        print("Cleaning up old files...")
        privacy_manager.cleanup_old_files(UPLOAD_FOLDER)
        privacy_manager.cleanup_old_files(PROCESSED_FOLDER)
        
        # Start privacy cleanup thread
        privacy_manager.start_cleanup_thread()
        
        print("API ready!")
        print(f"Upload folder: {UPLOAD_FOLDER}")
        print(f"Processed folder: {PROCESSED_FOLDER}")
        print(f"Max video length: {MAX_VIDEO_LENGTH} seconds")
        print(f"Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Run server
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        privacy_manager.stop_cleanup_thread()
        print("Cleanup thread stopped")
    except Exception as e:
        print(f"Error starting server: {e}")
        privacy_manager.stop_cleanup_thread()


