import asyncio
import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from models.device import (
    DeviceState, DeviceInfo, DeviceType, DeviceScreen, 
    TransactionRequest, SignatureResult, LogEntry, LogLevel, AddressInfo
)

class DeviceSimulator:
    """Simulates hardware wallet device operations"""
    
    def __init__(self):
        self.state = DeviceState()
        self.logs: List[LogEntry] = []
        self.pending_transaction: Optional[TransactionRequest] = None
        self.default_pin = "1234"
        self.max_pin_attempts = 3
        self.pin_attempts = 0
        
        # Mock addresses for different device types
        self.mock_addresses = {
            DeviceType.LEDGER: "octra1qpzry9x8gf2tvdw0s3jn54khce6mua7l5ta2m8c",
            DeviceType.TREZOR: "octra1abc123def456ghi789jkl012mno345pqr678stu",
            DeviceType.OCTRA: "octra1xyz789abc123def456ghi789jkl012mno345pqr"
        }
        
        self.mock_balances = {
            DeviceType.LEDGER: "125.80000000",
            DeviceType.TREZOR: "89.45123456",
            DeviceType.OCTRA: "203.12345678"
        }
    
    def _add_log(self, level: LogLevel, message: str, context: Optional[Dict] = None):
        """Add an entry to the activity log"""
        log_entry = LogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            device_type=self.state.device_info.device_type if self.state.device_info else None,
            context=context or {}
        )
        self.logs.append(log_entry)
        
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
    
    async def connect_device(self, device_info: DeviceInfo) -> Dict:
        """Simulate device connection"""
        if self.state.is_connected:
            raise Exception("Device already connected")
        
        # Simulate connection delay
        await asyncio.sleep(0.5)
        
        self.state.is_connected = True
        self.state.device_info = device_info
        self.state.last_activity = datetime.utcnow()
        self.state.screen = DeviceScreen.HOME
        self.pin_attempts = 0
        
        self._add_log(
            LogLevel.SUCCESS, 
            f"{device_info.name} connected successfully",
            {"device_type": device_info.device_type.value}
        )
        
        return {
            "connected": True,
            "device": device_info.dict(),
            "screen": self.state.screen.value
        }
    
    def disconnect_device(self) -> Dict:
        """Simulate device disconnection"""
        if not self.state.is_connected:
            raise Exception("No device connected")
        
        device_name = self.state.device_info.name if self.state.device_info else "Unknown device"
        
        # Reset state
        self.state = DeviceState()
        self.pending_transaction = None
        
        self._add_log(LogLevel.WARNING, f"{device_name} disconnected")
        
        return {"disconnected": True}
    
    async def unlock_device(self, pin: str) -> Dict:
        """Simulate device unlock with PIN"""
        if not self.state.is_connected:
            raise Exception("Device not connected")
        
        if self.state.is_unlocked:
            return {"unlocked": True, "already_unlocked": True}
        
        # Simulate PIN verification delay
        await asyncio.sleep(0.3)
        
        if pin == self.default_pin:
            self.state.is_unlocked = True
            self.state.screen = DeviceScreen.WALLET
            self.state.last_activity = datetime.utcnow()
            self.pin_attempts = 0
            
            # Set mock address and balance based on device type
            if self.state.device_info:
                device_type = self.state.device_info.device_type
                self.state.address = self.mock_addresses.get(device_type, "octra1...")
                self.state.balance = self.mock_balances.get(device_type, "0.00000000")
            
            self._add_log(LogLevel.SUCCESS, "Device unlocked successfully")
            
            return {
                "unlocked": True,
                "address": self.state.address,
                "balance": self.state.balance,
                "screen": self.state.screen.value
            }
        else:
            self.pin_attempts += 1
            remaining_attempts = self.max_pin_attempts - self.pin_attempts
            
            self._add_log(
                LogLevel.ERROR, 
                f"Invalid PIN. {remaining_attempts} attempts remaining",
                {"attempts_remaining": remaining_attempts}
            )
            
            if remaining_attempts <= 0:
                # Lock device after max attempts
                self.state.is_connected = False
                self._add_log(LogLevel.ERROR, "Device locked due to too many invalid PIN attempts")
                raise Exception("Device locked due to too many invalid PIN attempts")
            
            return {
                "unlocked": False,
                "error": "Invalid PIN",
                "attempts_remaining": remaining_attempts
            }
    
    async def sign_transaction(self, transaction: TransactionRequest) -> Dict:
        """Simulate transaction signing process"""
        if not self.state.is_connected:
            raise Exception("Device not connected")
        
        if not self.state.is_unlocked:
            raise Exception("Device not unlocked")
        
        if self.state.awaiting_confirmation:
            raise Exception("Another transaction is already pending confirmation")
        
        # Store pending transaction
        self.pending_transaction = transaction
        self.state.awaiting_confirmation = True
        self.state.screen = DeviceScreen.CONFIRM
        self.state.last_activity = datetime.utcnow()
        
        self._add_log(
            LogLevel.INFO,
            f"Transaction signing requested: {transaction.amount} OCTRA to {transaction.to_address[:10]}...",
            {"transaction": transaction.dict()}
        )
        
        return {
            "signing_requested": True,
            "transaction": transaction.dict(),
            "awaiting_confirmation": True,
            "screen": self.state.screen.value
        }
    
    async def confirm_transaction(self, confirmed: bool) -> Dict:
        """Confirm or reject the pending transaction"""
        if not self.state.awaiting_confirmation or not self.pending_transaction:
            raise Exception("No transaction pending confirmation")
        
        if confirmed:
            # Simulate signing delay
            await asyncio.sleep(1.0)
            
            # Generate mock signature
            tx_data = f"{self.pending_transaction.to_address}{self.pending_transaction.amount}{datetime.utcnow().isoformat()}"
            signature = hashlib.sha256(tx_data.encode()).hexdigest()
            tx_hash = hashlib.sha256(f"{signature}{secrets.token_hex(16)}".encode()).hexdigest()
            
            result = SignatureResult(
                signature=signature,
                transaction_hash=tx_hash,
                signed_at=datetime.utcnow(),
                device_type=self.state.device_info.device_type
            )
            
            self.state.screen = DeviceScreen.SIGNED
            self._add_log(LogLevel.SUCCESS, f"Transaction signed successfully: {tx_hash[:16]}...")
            
            # Reset to wallet screen after delay
            await asyncio.sleep(2.0)
            self.state.screen = DeviceScreen.WALLET
            
            response = {
                "confirmed": True,
                "signature_result": result.dict(),
                "screen": self.state.screen.value
            }
        else:
            self._add_log(LogLevel.WARNING, "Transaction rejected by user")
            self.state.screen = DeviceScreen.WALLET
            
            response = {
                "confirmed": False,
                "rejected": True,
                "screen": self.state.screen.value
            }
        
        # Clear pending transaction
        self.pending_transaction = None
        self.state.awaiting_confirmation = False
        self.state.last_activity = datetime.utcnow()
        
        return response
    
    def generate_address(self, derivation_path: str = "m/44'/60'/0'/0/0") -> AddressInfo:
        """Generate a new address (mock implementation)"""
        if not self.state.is_connected or not self.state.is_unlocked:
            raise Exception("Device must be connected and unlocked")
        
        # Mock address generation
        seed = f"{self.state.device_info.device_type.value}{derivation_path}{secrets.token_hex(8)}"
        address_hash = hashlib.sha256(seed.encode()).hexdigest()
        address = f"octra1{address_hash[:32]}"
        public_key = hashlib.sha256(f"pubkey{seed}".encode()).hexdigest()
        
        self._add_log(LogLevel.INFO, f"Generated new address: {address[:16]}...")
        
        return AddressInfo(
            address=address,
            derivation_path=derivation_path,
            public_key=public_key
        )
    
    def get_status(self) -> Dict:
        """Get current device status"""
        return {
            "device_state": self.state.dict(),
            "pending_transaction": self.pending_transaction.dict() if self.pending_transaction else None,
            "pin_attempts_remaining": self.max_pin_attempts - self.pin_attempts
        }
    
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """Get device activity logs"""
        recent_logs = self.logs[-limit:] if limit > 0 else self.logs
        return [log.dict() for log in recent_logs]
    
    def clear_logs(self):
        """Clear all activity logs"""
        self.logs.clear()
        self._add_log(LogLevel.INFO, "Activity logs cleared")
    
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.state.is_connected
    
    def is_unlocked(self) -> bool:
        """Check if device is unlocked"""
        return self.state.is_unlocked
    
    def reset(self):
        """Reset simulator to initial state"""
        self.state = DeviceState()
        self.pending_transaction = None
        self.pin_attempts = 0
        self._add_log(LogLevel.INFO, "Device simulator reset")