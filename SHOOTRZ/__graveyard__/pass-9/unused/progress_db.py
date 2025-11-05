"""
Progress Tracking Database (SQLite)

Stores historical analysis data for tracking improvement over time.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class ProgressDatabase:
    def __init__(self, db_path='database/progress.db'):
        """
        Initialize progress database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analyses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metrics TEXT NOT NULL,
                scores TEXT NOT NULL,
                trajectory TEXT,
                camera_analysis TEXT,
                ml_prediction TEXT,
                video_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                goal_type TEXT NOT NULL,
                target_value REAL NOT NULL,
                current_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_date DATE NOT NULL,
                shot_count INTEGER DEFAULT 0,
                make_count INTEGER DEFAULT 0,
                miss_count INTEGER DEFAULT 0,
                avg_score REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, username: str) -> int:
        """
        Add or get user
        
        Args:
            username: Username
            
        Returns:
            User ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Try to get existing user
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
        else:
            # Create new user
            cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
            user_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        return user_id
    
    def add_analysis(self, user_id: int, analysis_data: Dict) -> int:
        """
        Add analysis record
        
        Args:
            user_id: User ID
            analysis_data: Complete analysis results
            
        Returns:
            Analysis ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract and serialize data
        metrics = json.dumps(analysis_data.get('metrics', {}))
        scores = json.dumps(analysis_data.get('scores', {}))
        trajectory = json.dumps(analysis_data.get('trajectory', {}))
        camera_analysis = json.dumps(analysis_data.get('camera_analysis', {}))
        ml_prediction = json.dumps(analysis_data.get('ml_prediction', {}))
        video_id = analysis_data.get('video_id', '')
        
        cursor.execute('''
            INSERT INTO analyses 
            (user_id, metrics, scores, trajectory, camera_analysis, ml_prediction, video_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, metrics, scores, trajectory, camera_analysis, ml_prediction, video_id))
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return analysis_id
    
    def get_user_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get user's analysis history
        
        Args:
            user_id: User ID
            limit: Maximum number of records
            
        Returns:
            List of analysis records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT analysis_id, timestamp, metrics, scores, trajectory, 
                   camera_analysis, ml_prediction, video_id
            FROM analyses
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'analysis_id': row[0],
                'timestamp': row[1],
                'metrics': json.loads(row[2]),
                'scores': json.loads(row[3]),
                'trajectory': json.loads(row[4]),
                'camera_analysis': json.loads(row[5]),
                'ml_prediction': json.loads(row[6]),
                'video_id': row[7]
            })
        
        return history
    
    def get_progress_trends(self, user_id: int, metric_name: str, 
                           days: int = 30) -> List[Tuple[str, float]]:
        """
        Get trend data for a specific metric
        
        Args:
            user_id: User ID
            metric_name: Name of metric to track
            days: Number of days to look back
            
        Returns:
            List of (timestamp, value) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, metrics, scores
            FROM analyses
            WHERE user_id = ?
            AND datetime(timestamp) >= datetime('now', '-' || ? || ' days')
            ORDER BY timestamp ASC
        ''', (user_id, days))
        
        rows = cursor.fetchall()
        conn.close()
        
        trends = []
        for row in rows:
            timestamp = row[0]
            metrics = json.loads(row[1])
            scores = json.loads(row[2])
            
            # Try to get value from metrics or scores
            value = metrics.get(metric_name) or scores.get(metric_name)
            
            if value is not None:
                trends.append((timestamp, float(value)))
        
        return trends
    
    def get_improvement_summary(self, user_id: int) -> Dict:
        """
        Get improvement summary comparing recent vs initial performance
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with improvement statistics
        """
        history = self.get_user_history(user_id, limit=100)
        
        if len(history) < 2:
            return {
                'success': False,
                'message': 'Insufficient data for comparison'
            }
        
        # Compare first 5 and last 5 analyses
        initial_analyses = history[-min(5, len(history)):]
        recent_analyses = history[:min(5, len(history))]
        
        # Calculate average metrics
        def avg_metrics(analyses):
            metrics_sum = {}
            count = 0
            for analysis in analyses:
                metrics = analysis['metrics']
                scores = analysis['scores']
                combined = {**metrics, **scores}
                
                for key, value in combined.items():
                    if isinstance(value, (int, float)):
                        metrics_sum[key] = metrics_sum.get(key, 0) + value
                count += 1
            
            return {k: v / count for k, v in metrics_sum.items()}
        
        initial_avg = avg_metrics(initial_analyses)
        recent_avg = avg_metrics(recent_analyses)
        
        # Calculate improvements
        improvements = {}
        for key in initial_avg.keys():
            if key in recent_avg:
                change = recent_avg[key] - initial_avg[key]
                percent_change = (change / initial_avg[key] * 100) if initial_avg[key] != 0 else 0
                improvements[key] = {
                    'initial': round(initial_avg[key], 2),
                    'recent': round(recent_avg[key], 2),
                    'change': round(change, 2),
                    'percent_change': round(percent_change, 1)
                }
        
        return {
            'success': True,
            'total_analyses': len(history),
            'initial_count': len(initial_analyses),
            'recent_count': len(recent_analyses),
            'improvements': improvements
        }
    
    def add_goal(self, user_id: int, goal_type: str, target_value: float) -> int:
        """
        Add a goal for user
        
        Args:
            user_id: User ID
            goal_type: Type of goal (metric name)
            target_value: Target value to achieve
            
        Returns:
            Goal ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO goals (user_id, goal_type, target_value)
            VALUES (?, ?, ?)
        ''', (user_id, goal_type, target_value))
        
        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return goal_id
    
    def update_goal_progress(self, user_id: int) -> List[Dict]:
        """
        Update progress for all active goals
        
        Args:
            user_id: User ID
            
        Returns:
            List of updated goals
        """
        # Get recent analyses
        history = self.get_user_history(user_id, limit=5)
        
        if not history:
            return []
        
        # Get average metrics from recent analyses
        recent_metrics = {}
        for analysis in history:
            metrics = analysis['metrics']
            scores = analysis['scores']
            combined = {**metrics, **scores}
            
            for key, value in combined.items():
                if isinstance(value, (int, float)):
                    if key not in recent_metrics:
                        recent_metrics[key] = []
                    recent_metrics[key].append(value)
        
        avg_metrics = {k: sum(v) / len(v) for k, v in recent_metrics.items()}
        
        # Update goals
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT goal_id, goal_type, target_value, current_value
            FROM goals
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        goals = cursor.fetchall()
        updated_goals = []
        
        for goal in goals:
            goal_id, goal_type, target_value, current_value = goal
            
            # Get current value from recent metrics
            new_value = avg_metrics.get(goal_type)
            
            if new_value is not None:
                # Update goal
                cursor.execute('''
                    UPDATE goals
                    SET current_value = ?
                    WHERE goal_id = ?
                ''', (new_value, goal_id))
                
                # Check if goal completed
                if new_value >= target_value:
                    cursor.execute('''
                        UPDATE goals
                        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                        WHERE goal_id = ?
                    ''', (goal_id,))
                    status = 'completed'
                else:
                    status = 'active'
                
                updated_goals.append({
                    'goal_id': goal_id,
                    'goal_type': goal_type,
                    'target_value': target_value,
                    'current_value': new_value,
                    'progress_percent': (new_value / target_value * 100) if target_value > 0 else 0,
                    'status': status
                })
        
        conn.commit()
        conn.close()
        
        return updated_goals
    
    def get_statistics(self, user_id: int) -> Dict:
        """
        Get comprehensive statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total analyses
        cursor.execute('SELECT COUNT(*) FROM analyses WHERE user_id = ?', (user_id,))
        total_analyses = cursor.fetchone()[0]
        
        # Goals
        cursor.execute('''
            SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        active_goals = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'completed'
        ''', (user_id,))
        completed_goals = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_analyses': total_analyses,
            'active_goals': active_goals,
            'completed_goals': completed_goals
        }

