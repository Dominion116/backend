import hashlib
import secrets
import hmac
import base64
from typing import Tuple, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class OctraCrypto:
    """Cryptographic utilities for Octra hardware wallet simulation"""
    
    @staticmethod
    def generate_mnemonic() -> str:
        """Generate a BIP39-style mnemonic phrase (simplified)"""
        # Simplified word list for demo purposes
        words = [
            "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
            "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
            "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
            "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance",
            "advice", "aerobic", "affair", "afford", "afraid", "again", "agent", "agree",
            "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol",
            "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha",
            "already", "also", "alter", "always", "amateur", "amazing", "among", "amount"
        ]
        
        # Generate 12 random words
        mnemonic_words = [secrets.choice(words) for _ in range(12)]
        return " ".join(mnemonic_words)
    
    @staticmethod
    def derive_key_from_mnemonic(mnemonic: str, passphrase: str = "") -> bytes:
        """Derive a master key from mnemonic phrase"""
        # Simplified key derivation (not BIP39 compliant - for demo only)
        seed = f"{mnemonic}{passphrase}".encode('utf-8')
        
        # Use PBKDF2 for key stretching
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'octra_seed_salt',
            iterations=2048,
        )
        
        return kdf.derive(seed)
    
    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """Generate an ECDSA keypair for Octra addresses"""
        # Generate private key
        private_key = ec.generate_private_key(ec.SECP256K1())
        
        # Get private key bytes
        private_bytes = private_key.private_value().to_bytes(32, 'big')
        private_key_hex = private_bytes.hex()
        
        # Get public key
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_key_hex = public_bytes.hex()
        
        return private_key_hex, public_key_hex
    
    @staticmethod
    def derive_address(public_key_hex: str) -> str:
        """Derive Octra address from public key"""
        # Convert hex to bytes
        public_key_bytes = bytes.fromhex(public_key_hex)
        
        # Hash the public key
        hash1 = hashlib.sha256(public_key_bytes).digest()
        hash2 = hashlib.sha256(hash1).digest()
        
        # Take first 20 bytes
        address_bytes = hash2[:20]
        
        # Add Octra prefix and encode
        address = "octra1" + address_bytes.hex()
        
        return address
    
    @staticmethod
    def sign_transaction(private_key_hex: str, transaction_data: Dict[str, Any]) -> str:
        """Sign transaction data with private key"""
        # Create transaction hash
        tx_string = f"{transaction_data['to_address']}{transaction_data['amount']}{transaction_data.get('fee', '0')}"
        tx_hash = hashlib.sha256(tx_string.encode()).digest()
        
        # Load private key
        private_key_int = int(private_key_hex, 16)
        private_key = ec.derive_private_key(private_key_int, ec.SECP256K1())
        
        # Sign the hash
        signature = private_key.sign(tx_hash, ec.ECDSA(hashes.SHA256()))
        
        # Convert to hex
        signature_bytes = signature.signature
        return signature_bytes.hex()
    
    @staticmethod
    def verify_signature(public_key_hex: str, signature_hex: str, transaction_data: Dict[str, Any]) -> bool:
        """Verify transaction signature"""
        try:
            # Recreate transaction hash
            tx_string = f"{transaction_data['to_address']}{transaction_data['amount']}{transaction_data.get('fee', '0')}"
            tx_hash = hashlib.sha256(tx_string.encode()).digest()
            
            # Load public key
            public_key_bytes = bytes.fromhex(public_key_hex)
            public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
            
            # Verify signature
            signature_bytes = bytes.fromhex(signature_hex)
            public_key.verify(signature_bytes, tx_hash, ec.ECDSA(hashes.SHA256()))
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def generate_transaction_hash(transaction_data: Dict[str, Any]) -> str:
        """Generate a unique transaction hash"""
        # Include timestamp for uniqueness
        import time
        tx_data = {
            **transaction_data,
            "timestamp": int(time.time()),
            "nonce": secrets.token_hex(8)
        }
        
        # Create deterministic hash
        tx_string = str(sorted(tx_data.items()))
        tx_hash = hashlib.sha256(tx_string.encode()).hexdigest()
        
        return tx_hash
    
    @staticmethod
    def create_fhe_encrypted_data(data: str, key: str = None) -> Dict[str, str]:
        """Simulate FHE encryption (mock implementation for demo)"""
        if key is None:
            key = secrets.token_hex(32)
        
        # Simple XOR "encryption" for demo purposes
        # In real FHE, this would be much more complex
        data_bytes = data.encode('utf-8')
        key_bytes = bytes.fromhex(key)
        
        encrypted = bytearray()
        for i, byte in enumerate(data_bytes):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return {
            "encrypted_data": encrypted.hex(),
            "encryption_key": key,
            "algorithm": "mock_fhe",
            "can_compute": True
        }
    
    @staticmethod
    def fhe_add_encrypted(enc_a: str, enc_b: str) -> str:
        """Simulate FHE addition on encrypted data"""
        # Mock FHE addition - in reality this would be homomorphic
        bytes_a = bytes.fromhex(enc_a)
        bytes_b = bytes.fromhex(enc_b)
        
        # Simple XOR for demo
        result = bytearray()
        max_len = max(len(bytes_a), len(bytes_b))
        
        for i in range(max_len):
            a_byte = bytes_a[i] if i < len(bytes_a) else 0
            b_byte = bytes_b[i] if i < len(bytes_b) else 0
            result.append(a_byte ^ b_byte)
        
        return result.hex()
    
    @staticmethod
    def generate_device_certificate(device_id: str, device_type: str) -> Dict[str, str]:
        """Generate a mock device certificate"""
        cert_data = {
            "device_id": device_id,
            "device_type": device_type,
            "issued_at": str(int(time.time())),
            "issuer": "Octra Labs",
            "serial": secrets.token_hex(16)
        }
        
        # Create certificate signature
        cert_string = str(sorted(cert_data.items()))
        cert_hash = hashlib.sha256(cert_string.encode()).hexdigest()
        
        return {
            **cert_data,
            "certificate_hash": cert_hash,
            "signature": hmac.new(b"octra_cert_key", cert_hash.encode(), hashlib.sha256).hexdigest()
        }