from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from models.device import DeviceState, DeviceInfo, TransactionRequest, SignatureResult
from models.responses import DeviceStatusResponse, ConnectionResponse, ApiResponse
from services.device_simulator import DeviceSimulator
from services.websocket_manager import WebSocketManager

from services.fhe_service import FHEService
from models.fhe import FHEComputeRequest, EncryptedValue, FHEDataType

fhe_service = FHEService()

# Initialize FastAPI app
app = FastAPI(
    title="Octra Hardware Wallet Simulator API",
    description="REST API for simulating hardware wallet interactions with Octra blockchain",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://fhe-sim.vercel.app",  # Your Vercel frontend
        "https://*.vercel.app"  # Allow any Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
device_simulator = DeviceSimulator()
websocket_manager = WebSocketManager()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Octra Hardware Wallet Simulator API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Device Management Endpoints

@app.get("/api/device/status", response_model=DeviceStatusResponse)
async def get_device_status():
    """Get current device connection and state"""
    try:
        status = device_simulator.get_status()
        return DeviceStatusResponse(
            success=True,
            data=status,
            message="Device status retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device status: {str(e)}")

@app.post("/api/device/connect", response_model=ConnectionResponse)
async def connect_device(device_info: DeviceInfo):
    """Connect to a hardware wallet device"""
    try:
        result = await device_simulator.connect_device(device_info)
        
        # Broadcast connection status via WebSocket
        await websocket_manager.broadcast({
            "type": "device_connected",
            "device": device_info.dict(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ConnectionResponse(
            success=True,
            data=result,
            message=f"{device_info.name} connected successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@app.post("/api/device/disconnect")
async def disconnect_device():
    """Disconnect from hardware wallet device"""
    try:
        result = device_simulator.disconnect_device()
        
        # Broadcast disconnection via WebSocket
        await websocket_manager.broadcast({
            "type": "device_disconnected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ApiResponse(
            success=True,
            data=result,
            message="Device disconnected successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Disconnection failed: {str(e)}")

@app.put("/api/device/unlock")
async def unlock_device(pin_data: dict):
    """Unlock device with PIN"""
    try:
        pin = pin_data.get("pin")
        if not pin:
            raise HTTPException(status_code=400, detail="PIN is required")
        
        result = await device_simulator.unlock_device(pin)
        
        # Broadcast unlock status via WebSocket
        await websocket_manager.broadcast({
            "type": "device_unlocked" if result["unlocked"] else "unlock_failed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ApiResponse(
            success=True,
            data=result,
            message="Device unlock attempt completed"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unlock failed: {str(e)}")

# Transaction Endpoints

@app.post("/api/transaction/sign")
async def sign_transaction(transaction: TransactionRequest):
    """Sign a transaction with the hardware wallet"""
    try:
        if not device_simulator.is_connected():
            raise HTTPException(status_code=400, detail="Device not connected")
        
        if not device_simulator.is_unlocked():
            raise HTTPException(status_code=400, detail="Device not unlocked")
        
        result = await device_simulator.sign_transaction(transaction)
        
        # Broadcast signing request via WebSocket
        await websocket_manager.broadcast({
            "type": "transaction_sign_request",
            "transaction": transaction.dict(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Return the result directly, not wrapped in ApiResponse
        return {
            "success": True,
            "data": result,  # This contains the signing_requested info
            "message": "Transaction signing initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transaction signing failed: {str(e)}")

@app.post("/api/transaction/confirm")
async def confirm_transaction(confirmation_data: dict):
    """Confirm or reject a pending transaction"""
    try:
        confirmed = confirmation_data.get("confirmed", False)
        result = await device_simulator.confirm_transaction(confirmed)
        
        # Broadcast confirmation via WebSocket
        await websocket_manager.broadcast({
            "type": "transaction_confirmed" if confirmed else "transaction_rejected",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ApiResponse(
            success=True,
            data=result,
            message=f"Transaction {'confirmed' if confirmed else 'rejected'}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transaction confirmation failed: {str(e)}")

# Utility Endpoints

@app.get("/api/device/types")
async def get_supported_device_types():
    """Get list of supported hardware wallet types"""
    return {
        "devices": [
            {"id": "ledger", "name": "Ledger Nano S", "supported_operations": ["sign", "verify", "generate_address"]},
            {"id": "trezor", "name": "Trezor Model T", "supported_operations": ["sign", "verify", "generate_address"]},
            {"id": "octra", "name": "Octra Device", "supported_operations": ["sign", "verify", "generate_address", "fhe_operations"]}
        ]
    }

@app.get("/api/logs")
async def get_device_logs(limit: int = 50):
    """Get device activity logs"""
    try:
        logs = device_simulator.get_logs(limit)
        return ApiResponse(
            success=True,
            data={"logs": logs},
            message="Logs retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

@app.delete("/api/logs")
async def clear_device_logs():
    """Clear all device activity logs"""
    try:
        device_simulator.clear_logs()
        return ApiResponse(
            success=True,
            data={"cleared": True},
            message="Logs cleared successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")
    


@app.post("/api/fhe/encrypt")
async def encrypt_data(data: dict):
    """Encrypt plaintext data for FHE operations"""
    try:
        plaintext = data.get("value")
        data_type = FHEDataType(data.get("data_type", "integer"))
        
        encrypted = fhe_service.encrypt_value(plaintext, data_type)
        
        return ApiResponse(
            success=True,
            data={"encrypted_value": encrypted.dict()},
            message="Data encrypted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Encryption failed: {str(e)}")

@app.post("/api/fhe/compute")
async def compute_fhe(request: FHEComputeRequest):
    """Perform FHE computation on encrypted data"""
    try:
        result = fhe_service.perform_computation(request)
        
        # Broadcast computation via WebSocket
        await websocket_manager.broadcast({
            "type": "fhe_computation_complete",
            "operation": request.operation.value,
            "success": result.success,
            "gas_used": result.gas_used,
            "computation_time": result.computation_time,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ApiResponse(
            success=True,
            data={"computation_result": result.dict()},
            message=f"FHE {request.operation.value} operation completed"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"FHE computation failed: {str(e)}")

@app.get("/api/fhe/demos")
async def get_fhe_demos():
    """Get pre-built FHE demonstration scenarios"""
    demos = fhe_service.get_demo_scenarios()
    return ApiResponse(
        success=True,
        data={"demos": demos},
        message="FHE demo scenarios retrieved"
    )

@app.get("/api/fhe/operations")
async def get_fhe_operations():
    """Get available FHE operations and their costs"""
    return {
        "operations": [
            {"name": "add", "description": "Add encrypted numbers", "gas_cost": 100},
            {"name": "multiply", "description": "Multiply encrypted numbers", "gas_cost": 500},
            {"name": "compare", "description": "Compare encrypted values", "gas_cost": 300},
            {"name": "max", "description": "Find maximum of encrypted values", "gas_cost": 400},
            {"name": "average", "description": "Calculate average of encrypted values", "gas_cost": 600},
            {"name": "vote", "description": "Aggregate encrypted votes", "gas_cost": 200}
        ]
    }


# WebSocket endpoint for real-time updates

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time device updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back or process specific WebSocket commands
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# Error handlers

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "message": "The requested API endpoint does not exist"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting Octra Hardware Wallet Simulator API...")
    print(f"📖 API Documentation: http://localhost:{port}/api/docs")
    print(f"🔌 WebSocket: ws://localhost:{port}/ws")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )