# ============================================
# OBLIVION - Database Layer
# Handles all database operations
# ============================================

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager

# Setup logging
logger = logging.getLogger(__name__)

# ============================================
# DATABASE CONNECTION MANAGER
# ============================================

class DatabaseManager:
    """Manages database connections and operations"""
    
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.db_path = "OBLIVION.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize database with all tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    device_name TEXT,
                    device_model TEXT,
                    manufacturer TEXT,
                    android_version TEXT,
                    security_patch TEXT,
                    imei TEXT,
                    country TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    status TEXT DEFAULT 'active',
                    root_status TEXT DEFAULT 'false',
                    installed_apps TEXT,
                    additional_info TEXT
                )
            ''')
            
            # Commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    command_type TEXT,
                    parameters TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    executed_at TEXT,
                    result TEXT,
                    error TEXT,
                    priority INTEGER DEFAULT 0,
                    FOREIGN KEY (device_id) REFERENCES devices (id)
                )
            ''')
            
            # Extracted data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extracted_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    data_type TEXT,
                    data_content TEXT,
                    timestamp TEXT,
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    hash TEXT,
                    metadata TEXT,
                    FOREIGN KEY (device_id) REFERENCES devices (id)
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    details TEXT,
                    timestamp TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    FOREIGN KEY (device_id) REFERENCES devices (id)
                )
            ''')
            
            # System logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    source TEXT,
                    message TEXT,
                    timestamp TEXT,
                    details TEXT
                )
            ''')
            
            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    username TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_device_id ON commands(device_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_device_id ON extracted_data(device_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_timestamp ON extracted_data(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON alerts(device_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_write(self, query: str, params: tuple = ()):
        """Execute a write operation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def execute_many(self, query: str, params_list: list):
        """Execute multiple write operations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()

# ============================================
# DEVICE OPERATIONS
# ============================================

class DeviceOperations:
    """Operations for device management"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def register_device(self, device_data: dict) -> str:
        """Register a new device or update existing"""
        device_id = device_data.get('id')
        if not device_id:
            import uuid
            device_id = str(uuid.uuid4())
        
        now = datetime.now().isoformat()
        
        # Check if device exists
        existing = self.get_device(device_id)
        
        if existing:
            # Update existing device
            query = '''
                UPDATE devices SET
                    device_name = ?,
                    device_model = ?,
                    manufacturer = ?,
                    android_version = ?,
                    security_patch = ?,
                    imei = ?,
                    country = ?,
                    last_seen = ?,
                    status = ?,
                    root_status = ?,
                    installed_apps = ?,
                    additional_info = ?
                WHERE id = ?
            '''
            params = (
                device_data.get('device_name', 'Unknown'),
                device_data.get('device_model', 'Unknown'),
                device_data.get('manufacturer', 'Unknown'),
                device_data.get('android_version', 'Unknown'),
                device_data.get('security_patch', 'Unknown'),
                device_data.get('imei', 'Unknown'),
                device_data.get('country', 'Unknown'),
                now,
                device_data.get('status', 'active'),
                device_data.get('root_status', 'false'),
                json.dumps(device_data.get('installed_apps', [])),
                json.dumps(device_data.get('additional_info', {})),
                device_id
            )
            self.db.execute_write(query, params)
        else:
            # Insert new device
            query = '''
                INSERT INTO devices (
                    id, device_name, device_model, manufacturer,
                    android_version, security_patch, imei, country,
                    first_seen, last_seen, status, root_status,
                    installed_apps, additional_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                device_id,
                device_data.get('device_name', 'Unknown'),
                device_data.get('device_model', 'Unknown'),
                device_data.get('manufacturer', 'Unknown'),
                device_data.get('android_version', 'Unknown'),
                device_data.get('security_patch', 'Unknown'),
                device_data.get('imei', 'Unknown'),
                device_data.get('country', 'Unknown'),
                now,
                now,
                device_data.get('status', 'active'),
                device_data.get('root_status', 'false'),
                json.dumps(device_data.get('installed_apps', [])),
                json.dumps(device_data.get('additional_info', {}))
            )
            self.db.execute_write(query, params)
        
        return device_id
    
    def get_device(self, device_id: str) -> Optional[dict]:
        """Get device by ID"""
        query = 'SELECT * FROM devices WHERE id = ?'
        result = self.db.execute_query(query, (device_id,))
        if result:
            return dict(result[0])
        return None
    
    def get_all_devices(self, status: str = None) -> List[dict]:
        """Get all devices, optionally filtered by status"""
        if status:
            query = 'SELECT * FROM devices WHERE status = ? ORDER BY last_seen DESC'
            results = self.db.execute_query(query, (status,))
        else:
            query = 'SELECT * FROM devices ORDER BY last_seen DESC'
            results = self.db.execute_query(query)
        
        devices = []
        for row in results:
            device = dict(row)
            # Parse JSON fields
            if device.get('installed_apps'):
                try:
                    device['installed_apps'] = json.loads(device['installed_apps'])
                except:
                    device['installed_apps'] = []
            if device.get('additional_info'):
                try:
                    device['additional_info'] = json.loads(device['additional_info'])
                except:
                    device['additional_info'] = {}
            devices.append(device)
        return devices
    
    def update_device_status(self, device_id: str, status: str):
        """Update device status"""
        query = 'UPDATE devices SET status = ?, last_seen = ? WHERE id = ?'
        self.db.execute_write(query, (status, datetime.now().isoformat(), device_id))
    
    def update_device_heartbeat(self, device_id: str):
        """Update device last seen timestamp"""
        query = 'UPDATE devices SET last_seen = ? WHERE id = ?'
        self.db.execute_write(query, (datetime.now().isoformat(), device_id))
    
    def delete_device(self, device_id: str):
        """Delete a device and all associated data"""
        # Delete related data
        self.db.execute_write('DELETE FROM commands WHERE device_id = ?', (device_id,))
        self.db.execute_write('DELETE FROM extracted_data WHERE device_id = ?', (device_id,))
        self.db.execute_write('DELETE FROM alerts WHERE device_id = ?', (device_id,))
        # Delete device
        self.db.execute_write('DELETE FROM devices WHERE id = ?', (device_id,))
    
    def get_device_count(self) -> int:
        """Get total device count"""
        query = 'SELECT COUNT(*) FROM devices'
        result = self.db.execute_query(query)
        return result[0][0] if result else 0
    
    def get_active_device_count(self) -> int:
        """Get active device count"""
        query = 'SELECT COUNT(*) FROM devices WHERE status = "active"'
        result = self.db.execute_query(query)
        return result[0][0] if result else 0

# ============================================
# COMMAND OPERATIONS
# ============================================

class CommandOperations:
    """Operations for command management"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_command(self, device_id: str, command_type: str, 
                       parameters: dict, priority: int = 0) -> int:
        """Create a new command"""
        query = '''
            INSERT INTO commands (
                device_id, command_type, parameters, status,
                created_at, priority
            ) VALUES (?, ?, ?, ?, ?, ?)
        '''
        params = (
            device_id,
            command_type,
            json.dumps(parameters),
            'pending',
            datetime.now().isoformat(),
            priority
        )
        return self.db.execute_write(query, params)
    
    def get_pending_commands(self, device_id: str) -> List[dict]:
        """Get all pending commands for a device"""
        query = '''
            SELECT * FROM commands 
            WHERE device_id = ? AND status IN ('pending', 'queued')
            ORDER BY priority DESC, created_at ASC
        '''
        results = self.db.execute_query(query, (device_id,))
        commands = []
        for row in results:
            cmd = dict(row)
            if cmd.get('parameters'):
                try:
                    cmd['parameters'] = json.loads(cmd['parameters'])
                except:
                    cmd['parameters'] = {}
            commands.append(cmd)
        return commands
    
    def get_command_history(self, device_id: str, limit: int = 100) -> List[dict]:
        """Get command history for a device"""
        query = '''
            SELECT * FROM commands 
            WHERE device_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        '''
        results = self.db.execute_query(query, (device_id, limit))
        commands = []
        for row in results:
            cmd = dict(row)
            if cmd.get('parameters'):
                try:
                    cmd['parameters'] = json.loads(cmd['parameters'])
                except:
                    cmd['parameters'] = {}
            if cmd.get('result'):
                try:
                    cmd['result'] = json.loads(cmd['result'])
                except:
                    cmd['result'] = {}
            commands.append(cmd)
        return commands
    
    def update_command_status(self, command_id: int, status: str, 
                              result: dict = None, error: str = None):
        """Update command status and result"""
        query = '''
            UPDATE commands 
            SET status = ?, executed_at = ?, result = ?, error = ?
            WHERE id = ?
        '''
        params = (
            status,
            datetime.now().isoformat(),
            json.dumps(result) if result else None,
            error,
            command_id
        )
        self.db.execute_write(query, params)
    
    def get_command(self, command_id: int) -> Optional[dict]:
        """Get command by ID"""
        query = 'SELECT * FROM commands WHERE id = ?'
        result = self.db.execute_query(query, (command_id,))
        if result:
            cmd = dict(result[0])
            if cmd.get('parameters'):
                try:
                    cmd['parameters'] = json.loads(cmd['parameters'])
                except:
                    cmd['parameters'] = {}
            return cmd
        return None
    
    def get_pending_count(self, device_id: str = None) -> int:
        """Get count of pending commands"""
        if device_id:
            query = 'SELECT COUNT(*) FROM commands WHERE device_id = ? AND status = "pending"'
            result = self.db.execute_query(query, (device_id,))
        else:
            query = 'SELECT COUNT(*) FROM commands WHERE status = "pending"'
            result = self.db.execute_query(query)
        return result[0][0] if result else 0

# ============================================
# DATA OPERATIONS
# ============================================

class DataOperations:
    """Operations for extracted data management"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def store_data(self, device_id: str, data_type: str, 
                   data_content: Any, metadata: dict = None) -> int:
        """Store extracted data"""
        query = '''
            INSERT INTO extracted_data (
                device_id, data_type, data_content, timestamp,
                metadata, file_size
            ) VALUES (?, ?, ?, ?, ?, ?)
        '''
        content_json = json.dumps(data_content)
        params = (
            device_id,
            data_type,
            content_json,
            datetime.now().isoformat(),
            json.dumps(metadata) if metadata else None,
            len(content_json)
        )
        return self.db.execute_write(query, params)
    
    def get_device_data(self, device_id: str, data_type: str = None, 
                        limit: int = 100) -> List[dict]:
        """Get extracted data for a device"""
        if data_type:
            query = '''
                SELECT * FROM extracted_data 
                WHERE device_id = ? AND data_type = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            results = self.db.execute_query(query, (device_id, data_type, limit))
        else:
            query = '''
                SELECT * FROM extracted_data 
                WHERE device_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            results = self.db.execute_query(query, (device_id, limit))
        
        data_list = []
        for row in results:
            item = dict(row)
            if item.get('data_content'):
                try:
                    item['data_content'] = json.loads(item['data_content'])
                except:
                    pass
            if item.get('metadata'):
                try:
                    item['metadata'] = json.loads(item['metadata'])
                except:
                    item['metadata'] = {}
            data_list.append(item)
        return data_list
    
    def get_all_data(self, limit: int = 1000) -> List[dict]:
        """Get all extracted data"""
        query = '''
            SELECT * FROM extracted_data 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        results = self.db.execute_query(query, (limit,))
        data_list = []
        for row in results:
            item = dict(row)
            if item.get('data_content'):
                try:
                    item['data_content'] = json.loads(item['data_content'])
                except:
                    pass
            data_list.append(item)
        return data_list
    
    def get_data_count(self) -> int:
        """Get total count of extracted data records"""
        query = 'SELECT COUNT(*) FROM extracted_data'
        result = self.db.execute_query(query)
        return result[0][0] if result else 0
    
    def get_data_by_type(self, data_type: str) -> List[dict]:
        """Get data by type"""
        query = 'SELECT * FROM extracted_data WHERE data_type = ? ORDER BY timestamp DESC'
        results = self.db.execute_query(query, (data_type,))
        data_list = []
        for row in results:
            item = dict(row)
            if item.get('data_content'):
                try:
                    item['data_content'] = json.loads(item['data_content'])
                except:
                    pass
            data_list.append(item)
        return data_list

# ============================================
# ALERT OPERATIONS
# ============================================

class AlertOperations:
    """Operations for alert management"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_alert(self, device_id: str, alert_type: str, 
                     severity: str, details: str) -> int:
        """Create a new alert"""
        query = '''
            INSERT INTO alerts (
                device_id, alert_type, severity, details, timestamp
            ) VALUES (?, ?, ?, ?, ?)
        '''
        params = (
            device_id,
            alert_type,
            severity,
            details,
            datetime.now().isoformat()
        )
        return self.db.execute_write(query, params)
    
    def get_alerts(self, resolved: bool = None, severity: str = None, 
                   limit: int = 100) -> List[dict]:
        """Get alerts with optional filters"""
        query = 'SELECT * FROM alerts WHERE 1=1'
        params = []
        
        if resolved is not None:
            query += ' AND resolved = ?'
            params.append(1 if resolved else 0)
        
        if severity:
            query += ' AND severity = ?'
            params.append(severity)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        results = self.db.execute_query(query, tuple(params))
        alerts = []
        for row in results:
            alert = dict(row)
            alerts.append(alert)
        return alerts
    
    def get_alert_count(self, resolved: bool = False) -> int:
        """Get count of alerts"""
        query = 'SELECT COUNT(*) FROM alerts WHERE resolved = ?'
        result = self.db.execute_query(query, (1 if resolved else 0,))
        return result[0][0] if result else 0
    
    def resolve_alert(self, alert_id: int, resolved_by: str = 'system'):
        """Resolve an alert"""
        query = '''
            UPDATE alerts 
            SET resolved = 1, resolved_at = ?, resolved_by = ?
            WHERE id = ?
        '''
        params = (datetime.now().isoformat(), resolved_by, alert_id)
        self.db.execute_write(query, params)

# ============================================
# SYSTEM LOG OPERATIONS
# ============================================

class SystemLogOperations:
    """Operations for system log management"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def log(self, level: str, source: str, message: str, details: dict = None):
        """Add a system log entry"""
        query = '''
            INSERT INTO system_logs (level, source, message, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        '''
        params = (
            level,
            source,
            message,
            datetime.now().isoformat(),
            json.dumps(details) if details else None
        )
        self.db.execute_write(query, params)
    
    def get_logs(self, level: str = None, limit: int = 100) -> List[dict]:
        """Get system logs"""
        if level:
            query = 'SELECT * FROM system_logs WHERE level = ? ORDER BY timestamp DESC LIMIT ?'
            results = self.db.execute_query(query, (level, limit))
        else:
            query = 'SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT ?'
            results = self.db.execute_query(query, (limit,))
        
        logs = []
        for row in results:
            log = dict(row)
            if log.get('details'):
                try:
                    log['details'] = json.loads(log['details'])
                except:
                    pass
            logs.append(log)
        return logs

# ============================================
# MASTER DATABASE WRAPPER
# ============================================

class Database:
    """Master database wrapper combining all operations"""
    
    def __init__(self):
        self.devices = DeviceOperations()
        self.commands = CommandOperations()
        self.data = DataOperations()
        self.alerts = AlertOperations()
        self.logs = SystemLogOperations()
        self.db_manager = DatabaseManager()
    
    def initialize(self):
        """Initialize database (called on startup)"""
        self.db_manager._init_database()
        self.logs.log('INFO', 'system', 'Database initialized')
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        return {
            'total_devices': self.devices.get_device_count(),
            'active_devices': self.devices.get_active_device_count(),
            'pending_commands': self.commands.get_pending_count(),
            'total_data': self.data.get_data_count(),
            'active_alerts': self.alerts.get_alert_count(resolved=False)
        }
    
    def clear_old_data(self, days: int = 30):
        """Clear data older than specified days"""
        # This would be implemented for data retention
        pass

# ============================================
# SINGLETON INSTANCE
# ============================================

# Create singleton instance
db = Database()

# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Database Layer")
    print("=" * 60)
    
    # Test device operations
    test_device = {
        "id": "test-device-001",
        "device_name": "Test Phone",
        "device_model": "Pixel 6",
        "manufacturer": "Google",
        "android_version": "13",
        "security_patch": "2024-01-01",
        "imei": "354212345678900",
        "country": "KE",
        "status": "active",
        "root_status": "false",
        "installed_apps": ["com.whatsapp", "com.instagram"]
    }
    
    # Register device
    device_id = db.devices.register_device(test_device)
    print(f"✅ Device registered: {device_id}")
    
    # Get device
    device = db.devices.get_device(device_id)
    print(f"📱 Device: {device['device_name']} ({device['device_model']})")
    
    # Test command
    command_id = db.commands.create_command(
        device_id,
        "get_contacts",
        {"full": True},
        priority=1
    )
    print(f"📋 Command created: {command_id}")
    
    # Test data
    data_id = db.data.store_data(
        device_id,
        "contacts",
        [
            {"name": "John Doe", "phone": "+254712345678"},
            {"name": "Jane Doe", "phone": "+254712345679"}
        ]
    )
    print(f"💾 Data stored: {data_id}")
    
    # Test alert
    alert_id = db.alerts.create_alert(
        device_id,
        "suspicious_permission",
        "high",
        "Device has suspicious app installed"
    )
    print(f"🚨 Alert created: {alert_id}")
    
    # Get stats
    stats = db.get_stats()
    print(f"📊 Stats: {stats}")
    
    # Cleanup
    db.devices.delete_device(device_id)
    print("🧹 Device cleaned up")
    
    print("=" * 60)
    print("✅ Database tests passed!")