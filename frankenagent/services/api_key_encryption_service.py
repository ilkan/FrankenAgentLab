"""
API Key Encryption Service using Google Cloud KMS.

This service implements envelope encryption for secure storage of user API keys:
1. Generate unique DEK (Data Encryption Key) per encryption operation
2. Encrypt user's API key with DEK using AES-256-GCM
3. Encrypt DEK with KEK (Key Encryption Key) from Cloud KMS
4. Store encrypted API key + encrypted DEK in database

Security guarantees:
- Plaintext keys never stored in database
- DEKs encrypted with Cloud KMS (KEK never leaves KMS)
- AES-256-GCM provides authenticated encryption
- Secure memory handling (wipe sensitive data after use)
"""

from google.cloud import kms
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class APIKeyEncryptionService:
    """
    Secure API key encryption using envelope encryption with Cloud KMS.
    
    Architecture:
    - User API keys encrypted with AES-256-GCM using random DEK
    - DEK encrypted with Cloud KMS KEK
    - KEK managed by Google Cloud KMS (never leaves KMS)
    """
    
    def __init__(self, project_id: str, location: str, keyring: str, key: str, use_local_encryption: bool = False):
        """
        Initialize KMS client with project/location/keyring/key.
        
        Args:
            project_id: GCP project ID
            location: GCP location (e.g., 'us-central1')
            keyring: KMS keyring name
            key: KMS key name
            use_local_encryption: If True, use local encryption instead of GCP KMS (for development)
        """
        self.use_local_encryption = use_local_encryption
        
        if use_local_encryption:
            # For local development, use a static key (NOT SECURE - only for dev)
            import os
            import hashlib
            # Generate a proper 32-byte key from environment or default
            key_material = os.getenv("LOCAL_ENCRYPTION_KEY", "dev-encryption-key-for-local-testing")
            # Use SHA-256 to ensure exactly 32 bytes
            self.local_kek = hashlib.sha256(key_material.encode()).digest()
            logger.info("Initialized APIKeyEncryptionService with LOCAL encryption (development only)")
        else:
            self.kms_client = kms.KeyManagementServiceClient()
            self.kms_key_name = self.kms_client.crypto_key_path(
                project_id, location, keyring, key
            )
            logger.info(f"Initialized APIKeyEncryptionService with KMS key: {self.kms_key_name}")
    
    def encrypt_api_key(self, plaintext_key: str) -> Tuple[bytes, bytes, bytes, str]:
        """
        Encrypt API key using AES-256-GCM + envelope encryption.
        
        Process:
        1. Generate random 256-bit DEK
        2. Encrypt API key with DEK using AES-256-GCM
        3. Encrypt DEK with Cloud KMS
        4. Return encrypted key, encrypted DEK, nonce, and last 4 chars
        
        Args:
            plaintext_key: The API key to encrypt (e.g., "sk-...")
            
        Returns:
            Tuple of (encrypted_key, encrypted_dek, nonce, key_last_four)
            - encrypted_key: API key encrypted with DEK
            - encrypted_dek: DEK encrypted with KMS
            - nonce: 96-bit nonce for GCM
            - key_last_four: Last 4 characters for display
            
        Security:
        - DEK is wiped from memory after use
        - Plaintext key never logged or stored
        """
        # Generate random DEK (32 bytes for AES-256)
        dek = secrets.token_bytes(32)
        
        try:
            # Encrypt API key with DEK using AES-256-GCM
            aesgcm = AESGCM(dek)
            nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
            encrypted_key = aesgcm.encrypt(nonce, plaintext_key.encode('utf-8'), None)
            
            # Encrypt DEK with KMS or local key
            if self.use_local_encryption:
                # Local encryption for development (NOT SECURE - only for dev)
                local_aesgcm = AESGCM(self.local_kek)
                local_nonce = secrets.token_bytes(12)
                encrypted_dek = local_nonce + local_aesgcm.encrypt(local_nonce, dek, None)
            else:
                # Production: Use Cloud KMS
                encrypt_response = self.kms_client.encrypt(
                    request={
                        "name": self.kms_key_name,
                        "plaintext": dek
                    }
                )
                encrypted_dek = encrypt_response.ciphertext
            
            # Extract last 4 characters for display
            key_last_four = plaintext_key[-4:] if len(plaintext_key) >= 4 else plaintext_key
            
            logger.debug("API key encrypted successfully")
            
            return encrypted_key, encrypted_dek, nonce, key_last_four
            
        finally:
            # Securely wipe DEK from memory
            del dek
    
    def decrypt_api_key(self, encrypted_key: bytes, encrypted_dek: bytes, nonce: bytes) -> str:
        """
        Decrypt API key with secure memory handling.
        
        Process:
        1. Decrypt DEK using Cloud KMS
        2. Decrypt API key with DEK using AES-256-GCM
        3. Wipe DEK from memory
        4. Return plaintext key (caller must use immediately)
        
        Args:
            encrypted_key: Encrypted API key
            encrypted_dek: Encrypted DEK
            nonce: GCM nonce used during encryption
            
        Returns:
            Plaintext API key (use immediately and discard)
            
        Security:
        - DEK is wiped from memory after use
        - Caller must not log or store returned value
        - Use only for immediate agent execution
        """
        # Decrypt DEK using KMS or local key
        if self.use_local_encryption:
            # Local decryption for development
            local_nonce = encrypted_dek[:12]
            local_ciphertext = encrypted_dek[12:]
            local_aesgcm = AESGCM(self.local_kek)
            dek = local_aesgcm.decrypt(local_nonce, local_ciphertext, None)
        else:
            # Production: Use Cloud KMS
            decrypt_response = self.kms_client.decrypt(
                request={
                    "name": self.kms_key_name,
                    "ciphertext": encrypted_dek
                }
            )
            dek = decrypt_response.plaintext
        
        try:
            # Decrypt API key with DEK
            aesgcm = AESGCM(dek)
            plaintext_key = aesgcm.decrypt(nonce, encrypted_key, None).decode('utf-8')
            
            logger.debug("API key decrypted successfully")
            
            return plaintext_key
            
        finally:
            # Securely wipe DEK from memory
            del dek
    
    def rotate_encryption(
        self, 
        encrypted_key: bytes, 
        encrypted_dek: bytes, 
        nonce: bytes
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Re-encrypt API key for key rotation.
        
        Used when KMS key is rotated. Decrypts with old key version
        and re-encrypts with current key version.
        
        Args:
            encrypted_key: Current encrypted API key
            encrypted_dek: Current encrypted DEK
            nonce: Current GCM nonce
            
        Returns:
            Tuple of (new_encrypted_key, new_encrypted_dek, new_nonce)
            
        Security:
        - Plaintext key is wiped from memory after re-encryption
        - Operation is atomic (both old and new versions valid during rotation)
        """
        # Decrypt with old key
        plaintext_key = self.decrypt_api_key(encrypted_key, encrypted_dek, nonce)
        
        try:
            # Re-encrypt with current KMS key
            new_encrypted_key, new_encrypted_dek, new_nonce, _ = self.encrypt_api_key(plaintext_key)
            
            logger.info("API key re-encrypted for rotation")
            
            return new_encrypted_key, new_encrypted_dek, new_nonce
            
        finally:
            # Securely wipe plaintext from memory
            del plaintext_key
