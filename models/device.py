from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class DeviceType(str, Enum):
    LEDGER = "ledger"
    TREZOR = "trezor"
    OCTRA = "octra"

class DeviceScreen(str, Enum):
    HOME = "home"
    WALLET = "wallet"
    CONFIRM = "confirm"
    SIGNED = "signed"
    ERROR = "error"

class LogLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class DeviceInfo(BaseModel):
    device_type: DeviceType
    name: str
    firmware_version: Optional[str] = "1.0.0"
    serial_number: Optional[str] = None
    
    class Config:
        json_encoders = {
            DeviceType: lambda v: v.value
        }

class DeviceState(BaseModel):
    is_connected: bool = False
    is_unlocked: bool = False
    screen: DeviceScreen = DeviceScreen.HOME
    balance: str = "0.00000000"
    address: str = "octra1..."
    awaiting_confirmation: bool = False
    last_activity: Optional[datetime] = None
    device_info: Optional[DeviceInfo] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            DeviceScreen: lambda v: v.value
        }

class TransactionRequest(BaseModel):
    to_address: str = Field(..., description="Recipient address")
    amount: str = Field(..., description="Amount to send")
    fee: Optional[str] = "0.001"
    memo: Optional[str] = None
    gas_limit: Optional[int] = 21000
    
    class Config:
        schema_extra = {
            "example": {
                "to_address": "octra1qpzry9x8gf2tvdw0s3jn54khce6mua7l5ta2m8c",
                "amount": "10.5",
                "fee": "0.001",
                "memo": "Test transaction"
            }
        }

class SignatureResult(BaseModel):
    signature: str
    transaction_hash: str
    signed_at: datetime
    device_type: DeviceType
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    level: LogLevel
    message: str
    device_type: Optional[DeviceType] = None
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AddressInfo(BaseModel):
    address: str
    derivation_path: str = "m/44'/60'/0'/0/0"
    public_key: str
    address_type: str = "octra"

class DeviceCapabilities(BaseModel):
    supports_fhe: bool = False
    supports_multisig: bool = True
    supports_custom_tokens: bool = True
    max_transaction_size: int = 1024
    supported_curves: List[str] = ["secp256k1", "ed25519"]

class PinAttempt(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8)
    attempts_remaining: Optional[int] = None