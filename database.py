import sqlite3
import os
import threading
from datetime import datetime
from contextlib import contextmanager

# Database file path
DB_FILE = "data/study_ai.db"

# Thread-local storage for database connections
thread_local = threading.local()

class Database:
    def __init__(self):
        self._init_db()
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(thread_local, 'connection'):
            os.makedirs("data", exist_ok=True)
            thread_local.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
            thread_local.connection.row_factory = sqlite3.Row
            thread_local.connection.execute("PRAGMA foreign_keys = ON")
        return thread_local.connection
    
    def _close_connection(self):
        """Close thread-local database connection"""
        if hasattr(thread_local, 'connection'):
            thread_local.connection.close()
            del thread_local.connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database operations"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _init_db(self):
        """Initialize database with proper schema"""
        with self.get_cursor() as cursor:
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT DEFAULT 'Untitled Session',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    filesize INTEGER,
                    content_text TEXT,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_type TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            ''')
            
            # Create chats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_session ON files(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chats_session ON chats(session_id)')
        
        # Ensure there's at least one active session
        self._ensure_active_session()
    
    def _ensure_active_session(self):
        """Ensure there's always one active session"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT id FROM sessions WHERE is_active = 1 LIMIT 1')
            if not cursor.fetchone():
                cursor.execute('INSERT INTO sessions (session_name, is_active) VALUES (?, ?)', 
                             ('Default Session', 1))
    
    # ================= SESSION MANAGEMENT =================
    
    def create_session(self, session_name=None):
        """Create a new session"""
        if not session_name:
            session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        with self.get_cursor() as cursor:
            cursor.execute('UPDATE sessions SET is_active = 0')
            cursor.execute('INSERT INTO sessions (session_name, is_active) VALUES (?, ?)', 
                         (session_name, 1))
            return cursor.lastrowid
    
    def get_active_session(self):
        """Get the currently active session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT id, session_name, created_at, last_accessed 
                FROM sessions WHERE is_active = 1 LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'session_name': row[1],
                    'created_at': row[2],
                    'last_accessed': row[3]
                }
        return None
    
    def set_active_session(self, session_id):
        """Set a session as active"""
        with self.get_cursor() as cursor:
            cursor.execute('UPDATE sessions SET is_active = 0')
            cursor.execute('''
                UPDATE sessions 
                SET is_active = 1, last_accessed = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (session_id,))
            return cursor.rowcount > 0
    
    def get_all_sessions(self, limit=20):
        """Get all sessions"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT id, session_name, created_at, last_accessed, is_active,
                       (SELECT COUNT(*) FROM files WHERE session_id = sessions.id) as file_count,
                       (SELECT COUNT(*) FROM chats WHERE session_id = sessions.id) as chat_count
                FROM sessions
                ORDER BY last_accessed DESC
                LIMIT ?
            ''', (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'session_name': row[1],
                    'created_at': row[2],
                    'last_accessed': row[3],
                    'is_active': bool(row[4]),
                    'file_count': row[5] or 0,
                    'chat_count': row[6] or 0
                })
            return sessions
    
    def delete_session(self, session_id):
        """Delete a session"""
        with self.get_cursor() as cursor:
            cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            if cursor.rowcount > 0:
                self._ensure_active_session()
                return True
        return False
    
    # ================= FILE MANAGEMENT =================
    
    def add_file(self, session_id, filename, filepath, filesize, content_text="", file_type=""):
        """Add a file to a session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO files (session_id, filename, filepath, filesize, content_text, file_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, filename, filepath, filesize, content_text, file_type))
            
            cursor.execute('''
                UPDATE sessions 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (session_id,))
            
            return cursor.lastrowid
    
    def get_session_files(self, session_id):
        """Get all files for a session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT id, filename, filesize, upload_time, file_type 
                FROM files 
                WHERE session_id = ?
                ORDER BY upload_time DESC
            ''', (session_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'id': row[0],
                    'filename': row[1],
                    'filesize': row[2] or 0,
                    'upload_time': row[3],
                    'file_type': row[4] or 'Unknown'
                })
            return files
    
    def get_file_content(self, file_id):
        """Get content text of a specific file"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT content_text FROM files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            return row[0] if row else ""
    
    def get_session_content(self, session_id):
        """Get all content text from all files in a session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT content_text FROM files 
                WHERE session_id = ? AND content_text IS NOT NULL AND content_text != ''
            ''', (session_id,))
            
            contents = [row[0] for row in cursor.fetchall()]
            return "\n\n".join(contents)
    
    def delete_file(self, file_id):
        """Delete a specific file"""
        with self.get_cursor() as cursor:
            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            return cursor.rowcount > 0
    
    # ================= CHAT MANAGEMENT =================
    
    def add_chat(self, session_id, question, answer):
        """Add a chat message to a session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO chats (session_id, question, answer)
                VALUES (?, ?, ?)
            ''', (session_id, question, answer))
            
            cursor.execute('''
                UPDATE sessions 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (session_id,))
            
            return cursor.lastrowid
    
    def get_session_chats(self, session_id, limit=50):
        """Get all chats for a session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT id, question, answer, created_at 
                FROM chats 
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            ''', (session_id, limit))
            
            chats = []
            for row in cursor.fetchall():
                chats.append({
                    'id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'created_at': row[3]
                })
            return chats
    
    def get_all_chats(self, limit=100):
        """Get all chats across all sessions"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT c.id, c.question, c.answer, c.created_at, s.session_name
                FROM chats c
                JOIN sessions s ON c.session_id = s.id
                ORDER BY c.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            chats = []
            for row in cursor.fetchall():
                chats.append({
                    'id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'created_at': row[3],
                    'session_name': row[4]
                })
            return chats
    
    def delete_session_chats(self, session_id):
        """Delete all chats for a session"""
        with self.get_cursor() as cursor:
            cursor.execute('DELETE FROM chats WHERE session_id = ?', (session_id,))
            return cursor.rowcount
    
    # ================= STATISTICS =================
    
    def get_stats(self):
        """Get database statistics"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM sessions')
            total_sessions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM sessions WHERE is_active = 1')
            active_sessions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM files')
            total_files = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(filesize) FROM files')
            total_size = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM chats')
            total_chats = cursor.fetchone()[0]
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_files': total_files,
                'total_size': total_size,
                'total_chats': total_chats
            }
    
    def clear_all_data(self):
        """Completely clear all data from database"""
        try:
            # Get file paths before deletion
            file_paths = []
            with self.get_cursor() as cursor:
                cursor.execute('SELECT filepath FROM files')
                file_paths = [row[0] for row in cursor.fetchall()]
            
            # Close all connections
            self._close_connection()
            
            # Delete database file
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            
            # Delete uploaded files
            for filepath in file_paths:
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
            
            # Recreate data directory
            os.makedirs("data/uploads", exist_ok=True)
            
            # Reinitialize database
            self._init_db()
            
            return True
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False

# Global database instance
db = Database()