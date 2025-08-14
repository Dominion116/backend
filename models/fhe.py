from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum

class FHEOperation(str, Enum):
    ADD = "add"
    MULTIPLY = "multiply"
    COMPARE = "compare"
    MAX = "max"
    AVERAGE = "average"
    VOTE = "vote"

class FHEDataType(str, Enum):
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"

class EncryptedValue(BaseModel):
    encrypted_data: str
    data_type: FHEDataType
    can_compute: bool = True
    noise_level: int = Field(default=1, ge=1, le=10)

class FHEComputeRequest(BaseModel):
    operation: FHEOperation
    operands: List[EncryptedValue]
    parameters: Optional[Dict[str, Any]] = {}

class FHEComputeResult(BaseModel):
    operation: FHEOperation
    result: EncryptedValue
    computation_time: float
    gas_used: int
    success: bool
    error_message: Optional[str] = None