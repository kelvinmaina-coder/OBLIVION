# ============================================
# OBLIVION - Alert Model
# ============================================

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class AlertBase(BaseModel):
    """Base alert model"""
    device_id: str
    alert_type: str
    severity: str = "medium"  # critical, high, medium, low
    details: str
    resolved: Optional[bool] = False

class AlertCreate(AlertBase):
    """Model for creating an alert"""
    pass

class AlertUpdate(BaseModel):
    """Model for updating an alert"""
    resolved: Optional[bool] = None
    resolved_by: Optional[str] = None

class AlertModel(AlertBase):
    """Full alert model with timestamps"""
    id: int
    timestamp: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    
    class Config:
        from_attributes = True

# Alert types constants
class AlertType:
    """Available alert types"""
    # Security alerts
    SUSPICIOUS_PERMISSION = "suspicious_permission"
    UNKNOWN_APP = "unknown_app"
    ROOT_DETECTED = "root_detected"
    DEBUG_DETECTED = "debug_detected"
    EMULATOR_DETECTED = "emulator_detected"
    
    # Surveillance alerts
    GPS_ACTIVATED = "gps_activated"
    CAMERA_ACTIVATED = "camera_activated"
    MIC_ACTIVATED = "mic_activated"
    KEYLOGGER_ACTIVATED = "keylogger_activated"
    SCREEN_CAPTURE = "screen_capture"
    
    # Network alerts
    SUSPICIOUS_TRAFFIC = "suspicious_traffic"
    C2_CONNECTION = "c2_connection"
    DATA_EXFILTRATION = "data_exfiltration"
    
    # System alerts
    DEVICE_COMPROMISED = "device_compromised"
    PERSISTENCE_ESTABLISHED = "persistence_established"
    SELF_DESTRUCT_TRIGGERED = "self_destruct_triggered"
    
    # Custom
    CUSTOM = "custom"

# Severity levels
class Severity:
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
    @classmethod
    def get_color(cls, severity: str) -> str:
        """Get color for severity"""
        colors = {
            cls.CRITICAL: "#ff0000",
            cls.HIGH: "#ff6600",
            cls.MEDIUM: "#ffcc00",
            cls.LOW: "#00ff00"
        }
        return colors.get(severity, "#ffffff")
    
    @classmethod
    def get_priority(cls, severity: str) -> int:
        """Get priority for severity"""
        priorities = {
            cls.CRITICAL: 4,
            cls.HIGH: 3,
            cls.MEDIUM: 2,
            cls.LOW: 1
        }
        return priorities.get(severity, 0)