from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DeviceStatusResponse(ApiResponse):
    """Response for device status queries"""
    pass

class ConnectionResponse(ApiResponse):
    """Response for device connection attempts"""
    pass

class SignatureResponse(ApiResponse):
    """Response for transaction signing operations"""
    pass

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }