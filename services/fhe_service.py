import time
import random
import hashlib
from typing import List, Dict, Any
from models.fhe import FHEOperation, EncryptedValue, FHEDataType, FHEComputeRequest, FHEComputeResult

class FHEService:
    """Simulates FHE operations for demonstration"""
    
    def __init__(self):
        self.operation_costs = {
            FHEOperation.ADD: 100,
            FHEOperation.MULTIPLY: 500,
            FHEOperation.COMPARE: 300,
            FHEOperation.MAX: 400,
            FHEOperation.AVERAGE: 600,
            FHEOperation.VOTE: 200
        }
    
    def encrypt_value(self, plaintext_value: Any, data_type: FHEDataType) -> EncryptedValue:
        """Encrypt a plaintext value"""
        # Mock encryption - in reality this would use actual FHE
        plaintext_str = str(plaintext_value)
        mock_encrypted = hashlib.sha256(f"FHE_{plaintext_str}_{time.time()}".encode()).hexdigest()
        
        return EncryptedValue(
            encrypted_data=mock_encrypted,
            data_type=data_type,
            can_compute=True,
            noise_level=random.randint(1, 3)
        )
    
    def perform_computation(self, request: FHEComputeRequest) -> FHEComputeResult:
        """Perform FHE computation on encrypted data"""
        start_time = time.time()
        
        try:
            # Simulate computation delay based on operation complexity
            base_delay = {
                FHEOperation.ADD: 0.1,
                FHEOperation.MULTIPLY: 0.5,
                FHEOperation.COMPARE: 0.3,
                FHEOperation.MAX: 0.4,
                FHEOperation.AVERAGE: 0.6,
                FHEOperation.VOTE: 0.2
            }
            
            time.sleep(base_delay.get(request.operation, 0.1))
            
            # Mock computation result
            result_encrypted = self._mock_compute(request.operation, request.operands)
            computation_time = time.time() - start_time
            gas_used = self.operation_costs.get(request.operation, 100)
            
            return FHEComputeResult(
                operation=request.operation,
                result=result_encrypted,
                computation_time=computation_time,
                gas_used=gas_used,
                success=True
            )
            
        except Exception as e:
            return FHEComputeResult(
                operation=request.operation,
                result=EncryptedValue(encrypted_data="", data_type=FHEDataType.INTEGER),
                computation_time=time.time() - start_time,
                gas_used=0,
                success=False,
                error_message=str(e)
            )
    
    def _mock_compute(self, operation: FHEOperation, operands: List[EncryptedValue]) -> EncryptedValue:
        """Mock computation on encrypted values"""
        # Combine all operand data for mock result
        combined_data = "".join([op.encrypted_data for op in operands])
        operation_hash = hashlib.sha256(f"{operation.value}_{combined_data}".encode()).hexdigest()
        
        # Determine result data type
        result_type = operands[0].data_type if operands else FHEDataType.INTEGER
        
        # Increase noise level after computation
        max_noise = max([op.noise_level for op in operands]) if operands else 1
        new_noise = min(max_noise + 1, 10)
        
        return EncryptedValue(
            encrypted_data=operation_hash,
            data_type=result_type,
            can_compute=new_noise < 8,  # Can't compute if too much noise
            noise_level=new_noise
        )
    
    def get_demo_scenarios(self) -> List[Dict[str, Any]]:
        """Get pre-built demo scenarios"""
        return [
            {
                "name": "Private Voting",
                "description": "Count votes without revealing individual choices",
                "operation": FHEOperation.ADD,
                "demo_data": [
                    {"value": 1, "label": "Vote for Proposal A"},
                    {"value": 1, "label": "Vote for Proposal A"},
                    {"value": 0, "label": "Vote against Proposal A"},
                    {"value": 1, "label": "Vote for Proposal A"}
                ],
                "expected_result": "3 votes for, 1 against (without revealing individual votes)"
            },
            {
                "name": "Private Salary Comparison",
                "description": "Compare salaries without revealing actual amounts",
                "operation": FHEOperation.COMPARE,
                "demo_data": [
                    {"value": 85000, "label": "Employee A Salary"},
                    {"value": 92000, "label": "Employee B Salary"}
                ],
                "expected_result": "Employee B earns more (without revealing actual salaries)"
            },
            {
                "name": "Confidential Auction",
                "description": "Find highest bid without revealing bid amounts",
                "operation": FHEOperation.MAX,
                "demo_data": [
                    {"value": 1500, "label": "Bidder 1"},
                    {"value": 2200, "label": "Bidder 2"},
                    {"value": 1800, "label": "Bidder 3"},
                    {"value": 2100, "label": "Bidder 4"}
                ],
                "expected_result": "Bidder 2 wins (without revealing bid amounts)"
            },
            {
                "name": "Private Portfolio Average",
                "description": "Calculate average portfolio value across multiple investors",
                "operation": FHEOperation.AVERAGE,
                "demo_data": [
                    {"value": 150000, "label": "Investor A Portfolio"},
                    {"value": 230000, "label": "Investor B Portfolio"},
                    {"value": 180000, "label": "Investor C Portfolio"}
                ],
                "expected_result": "Average portfolio value (without revealing individual amounts)"
            }
        ]