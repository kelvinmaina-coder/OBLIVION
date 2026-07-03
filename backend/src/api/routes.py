# ============================================
# OBLIVION - API Routes
# All REST API endpoints for the framework
# ============================================

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
import os

# Import database and models
from src.database.db import db
from src.models.device import DeviceModel, DeviceCreate, DeviceUpdate
from src.models.command import CommandModel, CommandCreate, CommandUpdate
from src.models.alert import AlertModel, AlertCreate

# Create router
router = APIRouter(prefix="/api", tags=["API"])

# ============================================
# HELPER FUNCTIONS
# ============================================

def success_response(data: Any = None, message: str = "Success") -> dict:
    """Standard success response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def error_response(message: str, status_code: int = 400) -> dict:
    """Standard error response"""
    return {
        "success": False,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# DEVICE ROUTES
# ============================================

@router.get("/devices")
async def get_devices(
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all devices with optional filters"""
    try:
        devices = db.devices.get_all_devices(status)
        
        # Apply limit
        if len(devices) > limit:
            devices = devices[:limit]
        
        return success_response({
            "devices": devices,
            "total": len(devices),
            "limit": limit
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    """Get specific device details"""
    try:
        device = db.devices.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Check online status (would need WebSocket check)
        # For now, just return device data
        return success_response(device)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/devices/register")
async def register_device(device_data: DeviceCreate):
    """Register a new device"""
    try:
        # Convert to dict
        data = device_data.dict(exclude_none=True)
        
        # Generate ID if not provided
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        
        # Register device
        device_id = db.devices.register_device(data)
        
        # Log the registration
        db.logs.log('INFO', 'api', f'Device registered: {device_id}', {
            'device_name': data.get('device_name'),
            'model': data.get('device_model')
        })
        
        return success_response(
            {"device_id": device_id},
            message="Device registered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/devices/{device_id}")
async def update_device(device_id: str, device_data: DeviceUpdate):
    """Update device information"""
    try:
        # Check if device exists
        existing = db.devices.get_device(device_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Update device
        update_data = device_data.dict(exclude_none=True)
        update_data['id'] = device_id
        db.devices.register_device(update_data)
        
        # Get updated device
        device = db.devices.get_device(device_id)
        
        return success_response(device, message="Device updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    """Delete a device and all associated data"""
    try:
        # Check if device exists
        existing = db.devices.get_device(device_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Delete device
        db.devices.delete_device(device_id)
        
        # Log the deletion
        db.logs.log('WARNING', 'api', f'Device deleted: {device_id}', {
            'device_name': existing.get('device_name')
        })
        
        return success_response(message=f"Device {device_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/devices/{device_id}/heartbeat")
async def device_heartbeat(device_id: str):
    """Update device heartbeat"""
    try:
        # Check if device exists
        existing = db.devices.get_device(device_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Update heartbeat
        db.devices.update_device_heartbeat(device_id)
        
        # Get pending commands
        pending = db.commands.get_pending_commands(device_id)
        
        return success_response({
            "device_id": device_id,
            "status": "active",
            "pending_commands": len(pending),
            "commands": pending
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# COMMAND ROUTES
# ============================================

@router.post("/commands")
async def create_command(command_data: CommandCreate):
    """Create and send a command to a device"""
    try:
        # Check if device exists
        device = db.devices.get_device(command_data.device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create command
        command_id = db.commands.create_command(
            device_id=command_data.device_id,
            command_type=command_data.command_type,
            parameters=command_data.parameters,
            priority=command_data.priority
        )
        
        # Log command creation
        db.logs.log('INFO', 'api', f'Command created: {command_id}', {
            'device_id': command_data.device_id,
            'command_type': command_data.command_type
        })
        
        return success_response(
            {"command_id": command_id},
            message="Command created successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/commands/{device_id}")
async def get_commands(
    device_id: str,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get commands for a device"""
    try:
        # Check if device exists
        device = db.devices.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get commands
        if status == 'pending':
            commands = db.commands.get_pending_commands(device_id)
        else:
            commands = db.commands.get_command_history(device_id, limit)
        
        return success_response({
            "device_id": device_id,
            "commands": commands,
            "total": len(commands),
            "limit": limit
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/commands/{command_id}")
async def update_command(command_id: int, command_data: CommandUpdate):
    """Update command status/result"""
    try:
        # Check if command exists
        existing = db.commands.get_command(command_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Command not found")
        
        # Update command
        db.commands.update_command_status(
            command_id=command_id,
            status=command_data.status,
            result=command_data.result,
            error=command_data.error
        )
        
        # Log update
        db.logs.log('INFO', 'api', f'Command updated: {command_id}', {
            'status': command_data.status
        })
        
        return success_response(
            {"command_id": command_id},
            message="Command updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# DATA ROUTES
# ============================================

@router.post("/data")
async def store_data(data: dict):
    """Store extracted data from device"""
    try:
        device_id = data.get('device_id')
        data_type = data.get('data_type')
        data_content = data.get('data_content')
        
        if not device_id or not data_type:
            raise HTTPException(status_code=400, detail="device_id and data_type required")
        
        # Check if device exists
        device = db.devices.get_device(device_id)
        if not device:
            # Auto-register device
            db.devices.register_device({
                'id': device_id,
                'device_name': data.get('device_name', 'Unknown'),
                'status': 'active'
            })
        
        # Store data
        data_id = db.data.store_data(
            device_id=device_id,
            data_type=data_type,
            data_content=data_content,
            metadata=data.get('metadata')
        )
        
        # Log data storage
        db.logs.log('INFO', 'api', f'Data stored: {data_type}', {
            'device_id': device_id,
            'data_id': data_id,
            'size': len(str(data_content))
        })
        
        return success_response(
            {"data_id": data_id},
            message=f"Data stored successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{device_id}")
async def get_data(
    device_id: str,
    data_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=10000)
):
    """Get extracted data for a device"""
    try:
        # Check if device exists
        device = db.devices.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get data
        data = db.data.get_device_data(device_id, data_type, limit)
        
        return success_response({
            "device_id": device_id,
            "data": data,
            "total": len(data),
            "limit": limit
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data")
async def get_all_data(
    limit: int = Query(1000, ge=1, le=10000)
):
    """Get all extracted data"""
    try:
        data = db.data.get_all_data(limit)
        
        return success_response({
            "data": data,
            "total": len(data),
            "limit": limit
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ALERT ROUTES
# ============================================

@router.post("/alerts")
async def create_alert(alert_data: AlertCreate):
    """Create a new alert"""
    try:
        # Create alert
        alert_id = db.alerts.create_alert(
            device_id=alert_data.device_id,
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            details=alert_data.details
        )
        
        # Log alert
        db.logs.log('WARNING', 'api', f'Alert created: {alert_data.alert_type}', {
            'alert_id': alert_id,
            'severity': alert_data.severity,
            'device_id': alert_data.device_id
        })
        
        return success_response(
            {"alert_id": alert_id},
            message="Alert created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get alerts with optional filters"""
    try:
        alerts = db.alerts.get_alerts(resolved, severity, limit)
        
        return success_response({
            "alerts": alerts,
            "total": len(alerts),
            "limit": limit
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    resolved_by: str = Query("system", description="User or system that resolved the alert")
):
    """Resolve an alert"""
    try:
        # Check if alert exists
        alerts = db.alerts.get_alerts(resolved=False, limit=1000)
        alert_exists = any(a['id'] == alert_id for a in alerts)
        
        if not alert_exists:
            # Check if already resolved
            resolved_alerts = db.alerts.get_alerts(resolved=True, limit=1000)
            if any(a['id'] == alert_id for a in resolved_alerts):
                return success_response(message="Alert already resolved")
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Resolve alert
        db.alerts.resolve_alert(alert_id, resolved_by)
        
        # Log resolution
        db.logs.log('INFO', 'api', f'Alert resolved: {alert_id}', {
            'resolved_by': resolved_by
        })
        
        return success_response(
            {"alert_id": alert_id},
            message="Alert resolved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# STATISTICS ROUTES
# ============================================

@router.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        stats = db.get_stats()
        
        # Add additional info
        stats.update({
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "status": "online"
        })
        
        return success_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_logs(
    level: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get system logs"""
    try:
        logs = db.logs.get_logs(level, limit)
        
        return success_response({
            "logs": logs,
            "total": len(logs),
            "limit": limit
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# SYSTEM ROUTES
# ============================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime": "running"
    }

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"pong": datetime.now().isoformat()}

@router.get("/export/{device_id}")
async def export_device_data(device_id: str):
    """Export all data for a device"""
    try:
        # Check if device exists
        device = db.devices.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get all data
        device_data = {
            "device": device,
            "commands": db.commands.get_command_history(device_id, 1000),
            "data": db.data.get_device_data(device_id, limit=1000),
            "alerts": db.alerts.get_alerts(limit=1000)
        }
        
        # Create export file
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)
        filename = f"{export_dir}/{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(device_data, f, indent=2)
        
        return FileResponse(
            filename,
            media_type='application/json',
            filename=os.path.basename(filename)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# BULK OPERATIONS
# ============================================

@router.post("/commands/bulk")
async def create_bulk_commands(commands_data: List[CommandCreate]):
    """Create multiple commands at once"""
    try:
        created = []
        for cmd_data in commands_data:
            # Check if device exists
            device = db.devices.get_device(cmd_data.device_id)
            if not device:
                continue
            
            # Create command
            command_id = db.commands.create_command(
                device_id=cmd_data.device_id,
                command_type=cmd_data.command_type,
                parameters=cmd_data.parameters,
                priority=cmd_data.priority
            )
            created.append(command_id)
        
        return success_response({
            "created": created,
            "count": len(created),
            "total_requests": len(commands_data)
        }, message=f"Created {len(created)} commands")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# DEBUG ROUTES
# ============================================

@router.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database status"""
    try:
        # Check each table
        tables = ['devices', 'commands', 'extracted_data', 'alerts', 'system_logs', 'sessions']
        status = {}
        
        for table in tables:
            try:
                count = db.db_manager.execute_query(f'SELECT COUNT(*) FROM {table}')
                status[table] = {
                    'exists': True,
                    'count': count[0][0] if count else 0
                }
            except:
                status[table] = {'exists': False, 'count': 0}
        
        return success_response(status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ROUTER INCLUSION CHECK
# ============================================

if __name__ == "__main__":
    print("✅ API Routes loaded successfully")
    print(f"📋 Routes registered:")
    for route in router.routes:
        print(f"  {route.methods} {route.path}")