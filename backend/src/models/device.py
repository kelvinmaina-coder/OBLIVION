# ============================================
# OBLIVION - Device Model
# ============================================

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DeviceBase(BaseModel):
    """Base device model"""
    id: Optional[str] = None
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    manufacturer: Optional[str] = None
    android_version: Optional[str] = None
    security_patch: Optional[str] = None
    imei: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = "active"
    root_status: Optional[str] = "false"
    installed_apps: Optional[List[str]] = []
    additional_info: Optional[Dict[str, Any]] = {}

class DeviceCreate(DeviceBase):
    """Model for creating a device"""
    pass

class DeviceUpdate(DeviceBase):
    """Model for updating a device"""
    pass

class DeviceModel(DeviceBase):
    """Full device model with timestamps"""
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    
    class Config:
        from_attributes = True

class DeviceStats(BaseModel):
    """Device statistics"""
    total_devices: int
    active_devices: int
    online_devices: int
    compromised_devices: int
    by_android_version: Dict[str, int]
    by_manufacturer: Dict[str, int]