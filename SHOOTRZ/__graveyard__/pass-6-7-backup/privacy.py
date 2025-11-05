import hashlib
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict

class PrivacyManager:
    def __init__(self, retention_days=7):
        """
        Initialize privacy manager for video handling
        
        Args:
            retention_days: Number of days to retain files before deletion
        """
        self.video_retention_days = retention_days
        self.deletion_queue = []
        self.cleanup_thread = None
        self.running = False
        
    def anonymize_video_id(self, user_id=None):
        """
        Generate anonymous video ID using SHA-256 hash
        
        Args:
            user_id: Optional user ID for additional entropy
            
        Returns:
            str: Anonymous video ID
        """
        try:
            # Generate random salt
            salt = os.urandom(32)
            timestamp = str(datetime.now().timestamp())
            
            # Create hash input
            data = f"{user_id or 'anonymous'}{salt}{timestamp}"
            
            # Generate SHA-256 hash
            video_id = hashlib.sha256(data.encode()).hexdigest()
            
            return video_id
            
        except Exception as e:
            print(f"Error generating anonymous video ID: {e}")
            # Fallback to timestamp-based ID
            return str(int(time.time() * 1000))
    
    def schedule_deletion(self, file_path, deletion_delay_hours=None):
        """
        Schedule file deletion after retention period
        
        Args:
            file_path: Path to file to be deleted
            deletion_delay_hours: Optional custom delay in hours
        """
        try:
            if deletion_delay_hours:
                deletion_time = datetime.now() + timedelta(hours=deletion_delay_hours)
            else:
                deletion_time = datetime.now() + timedelta(days=self.video_retention_days)
            
            deletion_entry = {
                'path': file_path,
                'deletion_time': deletion_time,
                'created_at': datetime.now()
            }
            
            self.deletion_queue.append(deletion_entry)
            print(f"Scheduled deletion of {file_path} at {deletion_time}")
            
            # Start cleanup thread if not running
            if not self.running:
                self.start_cleanup_thread()
                
        except Exception as e:
            print(f"Error scheduling deletion: {e}")
    
    def strip_metadata(self, video_path):
        """
        Remove EXIF and metadata from video using ffmpeg
        
        Args:
            video_path: Path to video file
        """
        try:
            if not os.path.exists(video_path):
                print(f"Video file not found: {video_path}")
                return False
            
            temp_path = video_path + '.temp.mp4'
            
            # FFmpeg command to strip metadata
            cmd = [
                'ffmpeg', '-i', video_path,
                '-map_metadata', '-1',  # Remove all metadata
                '-c:v', 'copy',         # Copy video stream without re-encoding
                '-c:a', 'copy',         # Copy audio stream without re-encoding
                temp_path, '-y'         # Overwrite output file
            ]
            
            # Run ffmpeg command
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Replace original with metadata-stripped version
            os.replace(temp_path, video_path)
            print(f"Stripped metadata from {video_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error stripping metadata: {e}")
            print(f"FFmpeg stderr: {e.stderr}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
        except Exception as e:
            print(f"Error stripping metadata: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def cleanup_old_files(self, directory):
        """
        Remove files older than retention period
        
        Args:
            directory: Directory to clean up
        """
        try:
            if not os.path.exists(directory):
                return
            
            now = datetime.now()
            deleted_count = 0
            
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                
                if os.path.isfile(filepath):
                    try:
                        # Get file modification time
                        file_age = datetime.fromtimestamp(os.path.getmtime(filepath))
                        
                        # Check if file is older than retention period
                        if (now - file_age).days >= self.video_retention_days:
                            os.remove(filepath)
                            deleted_count += 1
                            print(f"Deleted old file: {filepath}")
                            
                    except Exception as e:
                        print(f"Could not delete {filepath}: {e}")
            
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old files from {directory}")
                
        except Exception as e:
            print(f"Error cleaning up directory {directory}: {e}")
    
    def start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        print("Started cleanup thread")
    
    def _cleanup_worker(self):
        """Background worker for cleanup tasks"""
        while self.running:
            try:
                now = datetime.now()
                files_to_delete = []
                
                # Check deletion queue
                for entry in self.deletion_queue:
                    if now >= entry['deletion_time']:
                        files_to_delete.append(entry)
                
                # Delete scheduled files
                for entry in files_to_delete:
                    try:
                        if os.path.exists(entry['path']):
                            os.remove(entry['path'])
                            print(f"Deleted scheduled file: {entry['path']}")
                        self.deletion_queue.remove(entry)
                    except Exception as e:
                        print(f"Error deleting scheduled file {entry['path']}: {e}")
                
                # Sleep for 1 hour before next check
                time.sleep(3600)
                
            except Exception as e:
                print(f"Error in cleanup worker: {e}")
                time.sleep(60)  # Sleep 1 minute on error
    
    def stop_cleanup_thread(self):
        """Stop background cleanup thread"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        print("Stopped cleanup thread")
    
    def get_deletion_queue_status(self):
        """
        Get status of deletion queue
        
        Returns:
            dict: Status information
        """
        try:
            now = datetime.now()
            pending_deletions = []
            
            for entry in self.deletion_queue:
                time_until_deletion = entry['deletion_time'] - now
                pending_deletions.append({
                    'path': entry['path'],
                    'deletion_time': entry['deletion_time'].isoformat(),
                    'time_until_deletion': str(time_until_deletion),
                    'created_at': entry['created_at'].isoformat()
                })
            
            return {
                'total_pending': len(self.deletion_queue),
                'pending_deletions': pending_deletions,
                'retention_days': self.video_retention_days,
                'cleanup_thread_running': self.running
            }
            
        except Exception as e:
            print(f"Error getting deletion queue status: {e}")
            return {
                'total_pending': 0,
                'pending_deletions': [],
                'retention_days': self.video_retention_days,
                'cleanup_thread_running': False
            }
    
    def force_cleanup(self, directory):
        """
        Force immediate cleanup of directory
        
        Args:
            directory: Directory to clean up immediately
        """
        try:
            print(f"Force cleaning directory: {directory}")
            self.cleanup_old_files(directory)
            
            # Also clean up any files in deletion queue that are past due
            now = datetime.now()
            overdue_files = []
            
            for entry in self.deletion_queue:
                if now >= entry['deletion_time']:
                    overdue_files.append(entry)
            
            for entry in overdue_files:
                try:
                    if os.path.exists(entry['path']):
                        os.remove(entry['path'])
                        print(f"Force deleted overdue file: {entry['path']}")
                    self.deletion_queue.remove(entry)
                except Exception as e:
                    print(f"Error force deleting {entry['path']}: {e}")
                    
        except Exception as e:
            print(f"Error in force cleanup: {e}")
    
    def validate_privacy_compliance(self, file_path):
        """
        Validate that file meets privacy requirements
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            dict: Validation results
        """
        try:
            if not os.path.exists(file_path):
                return {'compliant': False, 'error': 'File does not exist'}
            
            # Check file age
            file_age = datetime.fromtimestamp(os.path.getmtime(file_path))
            age_days = (datetime.now() - file_age).days
            
            if age_days > self.video_retention_days:
                return {'compliant': False, 'error': f'File is {age_days} days old, exceeds {self.video_retention_days} day retention'}
            
            # Check file size (reasonable limit)
            file_size = os.path.getsize(file_path)
            max_size = 500 * 1024 * 1024  # 500MB
            if file_size > max_size:
                return {'compliant': False, 'error': f'File size {file_size} exceeds {max_size} bytes'}
            
            return {
                'compliant': True,
                'age_days': age_days,
                'file_size': file_size,
                'retention_days': self.video_retention_days
            }
            
        except Exception as e:
            return {'compliant': False, 'error': f'Validation error: {str(e)}'}


