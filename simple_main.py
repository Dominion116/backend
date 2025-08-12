from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import hashlib
import secrets
import uuid
import json

# Initialize FastAPI app
app = FastAPI(
    title="Octra Hardware Wallet Simulator API",
    description="REST API for simulating hardware wallet interactions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state - using simple dictionaries instead of Pydantic models
device_state = {
    "is_connected": False,
    "is_unlocked": False,
    "screen": "home",
    "balance": "0.00000000",
    "address": "octra1...",
    "awaiting_confirmation": False
}

logs = []
pending_transaction = None
default_pin = "1234"

def add_log(level: str, message: str):
    """Add log entry"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message
    }
    logs.append(log_entry)
    # Keep only last 50 logs
    if len(logs) > 50:
        logs[:] = logs[-50:]

def create_response(success: bool, message: str, data: Optional[Dict] = None):
    """Create standardized API response"""
    return {
        "success": success,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Octra Hardware Wallet Simulator API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/device/status")
async def get_device_status():
    """Get current device status"""
    return create_response(
        success=True,
        message="Device status retrieved",
        data=device_state.copy()
    )

@app.post("/api/device/connect")
async def connect_device(device_info: Dict[str, Any]):
    """Connect device"""
    global device_state
    
    if device_state["is_connected"]:
        raise HTTPException(status_code=400, detail="Device already connected")
    
    # Validate input
    if not isinstance(device_info, dict) or "device_type" not in device_info:
        raise HTTPException(status_code=400, detail="Invalid device info")
    
    # Simulate connection delay
    await asyncio.sleep(0.5)
    
    device_state["is_connected"] = True
    device_state["screen"] = "home"
    
    device_name = device_info.get("name", device_info["device_type"])
    add_log("success", f"{device_name} connected successfully")
    
    return create_response(
        success=True,
        message=f"{device_name} connected successfully",
        data={
            "connected": True,
            "device": device_info,
            "screen": device_state["screen"]
        }
    )

@app.post("/api/device/disconnect")
async def disconnect_device():
    """Disconnect device"""
    global device_state, pending_transaction
    
    if not device_state["is_connected"]:
        raise HTTPException(status_code=400, detail="No device connected")
    
    # Reset state
    device_state.update({
        "is_connected": False,
        "is_unlocked": False,
        "screen": "home",
        "balance": "0.00000000",
        "address": "octra1...",
        "awaiting_confirmation": False
    })
    pending_transaction = None
    
    add_log("warning", "Device disconnected")
    
    return create_response(
        success=True,
        message="Device disconnected successfully",
        data={"disconnected": True}
    )

@app.put("/api/device/unlock")
async def unlock_device(pin_data: Dict[str, str]):
    """Unlock device with PIN"""
    global device_state
    
    pin = pin_data.get("pin")
    if not pin:
        raise HTTPException(status_code=400, detail="PIN is required")
    
    if not device_state["is_connected"]:
        raise HTTPException(status_code=400, detail="Device not connected")
    
    # Simulate PIN verification delay
    await asyncio.sleep(0.3)
    
    if pin == default_pin:
        device_state.update({
            "is_unlocked": True,
            "screen": "wallet",
            "address": "octra1qpzry9x8gf2tvdw0s3jn54khce6mua7l5ta2m8c",
            "balance": "125.80000000"
        })
        
        add_log("success", "Device unlocked successfully")
        
        return create_response(
            success=True,
            message="Device unlocked successfully",
            data={
                "unlocked": True,
                "address": device_state["address"],
                "balance": device_state["balance"],
                "screen": device_state["screen"]
            }
        )
    else:
        add_log("error", "Invalid PIN")
        raise HTTPException(status_code=400, detail="Invalid PIN")

@app.post("/api/transaction/sign")
async def sign_transaction(transaction: Dict[str, Any]):
    """Sign transaction"""
    global device_state, pending_transaction
    
    if not device_state["is_connected"]:
        raise HTTPException(status_code=400, detail="Device not connected")
    
    if not device_state["is_unlocked"]:
        raise HTTPException(status_code=400, detail="Device not unlocked")
    
    if device_state["awaiting_confirmation"]:
        raise HTTPException(status_code=400, detail="Another transaction pending")
    
    # Validate transaction
    required_fields = ["to_address", "amount"]
    for field in required_fields:
        if field not in transaction:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Store pending transaction
    pending_transaction = transaction
    device_state["awaiting_confirmation"] = True
    device_state["screen"] = "confirm"
    
    add_log("info", f"Transaction signing requested: {transaction['amount']} OCTRA")
    
    return create_response(
        success=True,
        message="Transaction signing initiated",
        data={
            "signing_requested": True,
            "transaction": transaction,
            "awaiting_confirmation": True,
            "screen": device_state["screen"]
        }
    )

@app.post("/api/transaction/confirm")
async def confirm_transaction(confirmation_data: Dict[str, Any]):
    """Confirm or reject transaction"""
    global device_state, pending_transaction
    
    if not device_state["awaiting_confirmation"] or not pending_transaction:
        raise HTTPException(status_code=400, detail="No transaction pending")
    
    confirmed = confirmation_data.get("confirmed", False)
    
    if confirmed:
        # Simulate signing delay
        await asyncio.sleep(1.0)
        
        # Generate mock signature
        tx_data = f"{pending_transaction['to_address']}{pending_transaction['amount']}"
        signature = hashlib.sha256(tx_data.encode()).hexdigest()
        tx_hash = hashlib.sha256(f"{signature}{secrets.token_hex(16)}".encode()).hexdigest()
        
        device_state["screen"] = "signed"
        add_log("success", f"Transaction signed: {tx_hash[:16]}...")
        
        result = {
            "confirmed": True,
            "signature": signature,
            "transaction_hash": tx_hash,
            "screen": device_state["screen"]
        }
        
        # Reset to wallet screen after delay
        async def reset_screen():
            await asyncio.sleep(2.0)
            device_state["screen"] = "wallet"
        
        # Start background task to reset screen
        import asyncio
        asyncio.create_task(reset_screen())
        
    else:
        add_log("warning", "Transaction rejected by user")
        device_state["screen"] = "wallet"
        result = {
            "confirmed": False,
            "rejected": True,
            "screen": device_state["screen"]
        }
    
    # Clear pending transaction
    pending_transaction = None
    device_state["awaiting_confirmation"] = False
    
    return create_response(
        success=True,
        message=f"Transaction {'confirmed' if confirmed else 'rejected'}",
        data=result
    )

@app.get("/api/device/types")
async def get_supported_device_types():
    """Get supported device types"""
    return {
        "success": True,
        "devices": [
            {"id": "ledger", "name": "Ledger Nano S"},
            {"id": "trezor", "name": "Trezor Model T"},
            {"id": "octra", "name": "Octra Device"}
        ]
    }

@app.get("/api/logs")
async def get_device_logs(limit: int = 50):
    """Get device logs"""
    recent_logs = logs[-limit:] if limit > 0 and len(logs) > limit else logs
    return create_response(
        success=True,
        message="Logs retrieved successfully",
        data={"logs": recent_logs}
    )

@app.delete("/api/logs")
async def clear_device_logs():
    """Clear device logs"""
    global logs
    logs.clear()
    add_log("info", "Logs cleared")
    return create_response(
        success=True,
        message="Logs cleared successfully",
        data={"cleared": True}
    )

# Additional endpoint to get current state for debugging
@app.get("/api/debug/state")
async def get_debug_state():
    """Get full application state for debugging"""
    return {
        "device_state": device_state,
        "pending_transaction": pending_transaction,
        "logs_count": len(logs),
        "last_log": logs[-1] if logs else None
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Octra Hardware Wallet Simulator API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Interactive API: http://localhost:8000/docs")
    print("🐛 Debug State: http://localhost:8000/api/debug/state")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )