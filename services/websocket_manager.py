import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.utcnow(),
            "client_id": id(websocket)
        }
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to Octra Hardware Wallet Simulator",
            "client_id": id(websocket),
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        print(f"✅ WebSocket connection established: {id(websocket)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_id = self.connection_info.get(websocket, {}).get("client_id")
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            print(f"❌ WebSocket connection closed: {client_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                print(f"Error broadcasting to {id(connection)}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_device_status(self, status: Dict[str, Any]):
        """Broadcast device status updates"""
        await self.broadcast({
            "type": "device_status_update",
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_log_entry(self, log_entry: Dict[str, Any]):
        """Broadcast new log entries"""
        await self.broadcast({
            "type": "new_log_entry",
            "log": log_entry,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connections_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections"""
        return [
            {
                "client_id": info["client_id"],
                "connected_at": info["connected_at"].isoformat(),
                "connection_duration": (datetime.utcnow() - info["connected_at"]).total_seconds()
            }
            for info in self.connection_info.values()
        ]