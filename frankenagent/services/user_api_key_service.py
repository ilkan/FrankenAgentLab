"""
User API Key Service for secure management of user API keys.

This service provides secure storage and retrieval of user API keys with:
- Encryption using envelope encryption (AES-256-GCM + Cloud KMS)
- Masked display (only last 4 characters shown)
- Secure deletion (permanent removal from database)
- Key rotation support
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from frankenagent.db.models import UserAPIKey
from frankenagent.services.api_key_encryption_service import APIKeyEncryptionService

logger = logging.getLogger(__name__)


class UserAPIKeyService:
    """Service for managing user API keys with secure encryption."""
    
    # Valid LLM and tool providers
    VALID_PROVIDERS = ['openai', 'anthropic', 'groq', 'gemini', 'tavily']
    
    def __init__(self, encryption_service: APIKeyEncryptionService):
        """
        Initialize service with encryption service.
        
        Args:
            encryption_service: APIKeyEncryptionService for encryption/decryption
        """
        self.encryption = encryption_service
    
    def add_api_key(
        self,
        db: Session,
        user_id: UUID,
        provider: str,
        plaintext_key: str,
        key_name: Optional[str] = None
    ) -> UserAPIKey:
        """
        Add and encrypt user API key.
        
        Process:
        1. Validate provider and key format
        2. Encrypt key using envelope encryption
        3. Store encrypted key + metadata in database
        
        Args:
            db: Database session
            user_id: User ID
            provider: LLM provider ('openai', 'anthropic', 'groq', 'gemini')
            plaintext_key: API key to encrypt
            key_name: Optional user-friendly name
            
        Returns:
            UserAPIKey model instance
            
        Raises:
            ValueError: If provider invalid or key format invalid
            
        Security:
        - Plaintext key is never logged or stored
        - Key is encrypted before database write
        """
        # Strip whitespace and newlines from API key (common copy-paste issue)
        plaintext_key = plaintext_key.strip()
        
        # Validate provider
        if provider not in self.VALID_PROVIDERS:
            raise ValueError(f"Invalid provider. Must be one of: {self.VALID_PROVIDERS}")
        
        # Validate key format (basic check)
        if not plaintext_key or len(plaintext_key) < 10:
            raise ValueError("Invalid API key format")
        
        # Check for duplicate provider key
        existing = db.query(UserAPIKey).filter(
            UserAPIKey.user_id == user_id,
            UserAPIKey.provider == provider,
            UserAPIKey.is_active == True
        ).first()
        
        if existing and key_name and existing.key_name == key_name:
            raise ValueError(f"API key with name '{key_name}' already exists for provider '{provider}'")
        
        # Encrypt the key
        encrypted_key, encrypted_dek, nonce, key_last_four = \
            self.encryption.encrypt_api_key(plaintext_key)
        
        # Store in database
        # Get KMS key version (or "local" for development)
        kms_key_version = getattr(self.encryption, 'kms_key_name', 'local-encryption')
        
        api_key = UserAPIKey(
            user_id=user_id,
            provider=provider,
            key_name=key_name or f"{provider.title()} Key",
            encrypted_key=encrypted_key,
            encrypted_dek=encrypted_dek,
            nonce=nonce,
            key_last_four=key_last_four,
            kms_key_version=kms_key_version
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        logger.info(f"API key added for user {user_id}, provider {provider}")
        
        return api_key
    
    def get_user_api_keys(self, db: Session, user_id: UUID) -> List[dict]:
        """
        Get user's API keys (masked for display).
        
        Returns list of API keys with:
        - ID, provider, key_name
        - Masked key preview: "***...xyz123"
        - Created and last used timestamps
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of dictionaries with masked key information
            
        Security:
        - Only last 4 characters shown
        - Full key never returned
        """
        keys = db.query(UserAPIKey).filter(
            UserAPIKey.user_id == user_id,
            UserAPIKey.is_active == True
        ).order_by(UserAPIKey.created_at.desc()).all()
        
        return [
            {
                "id": str(key.id),
                "provider": key.provider,
                "key_name": key.key_name,
                "key_preview": f"***...{key.key_last_four}",
                "created_at": key.created_at.isoformat(),
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None
            }
            for key in keys
        ]
    
    def get_decrypted_key(
        self,
        db: Session,
        user_id: UUID,
        provider: str
    ) -> Optional[str]:
        """
        Decrypt and return API key for agent execution.
        
        Process:
        1. Fetch encrypted key from database
        2. Decrypt using envelope encryption
        3. Update last_used_at timestamp
        4. Return plaintext key
        
        Args:
            db: Database session
            user_id: User ID
            provider: LLM provider
            
        Returns:
            Plaintext API key or None if not found
            
        Security:
        - Key is decrypted in memory only
        - Caller must use immediately and discard
        - Never log or store the returned value
        - DEK is wiped from memory after decryption
        """
        api_key = db.query(UserAPIKey).filter(
            UserAPIKey.user_id == user_id,
            UserAPIKey.provider == provider,
            UserAPIKey.is_active == True
        ).first()
        
        if not api_key:
            logger.warning(f"No API key found for user {user_id}, provider {provider}")
            return None
        
        # Decrypt key
        plaintext_key = self.encryption.decrypt_api_key(
            api_key.encrypted_key,
            api_key.encrypted_dek,
            api_key.nonce
        )
        
        # Update last used timestamp
        api_key.last_used_at = datetime.utcnow()
        db.commit()
        
        logger.debug(f"API key decrypted for user {user_id}, provider {provider}")
        
        return plaintext_key
    
    def delete_api_key(self, db: Session, key_id: UUID, user_id: UUID) -> bool:
        """
        Securely delete API key.
        
        Performs hard delete (not soft delete) to ensure:
        - Encrypted key permanently removed
        - Encrypted DEK permanently removed
        - No recovery possible
        
        Args:
            db: Database session
            key_id: API key ID
            user_id: User ID (for ownership verification)
            
        Returns:
            True if deleted, False if not found
            
        Security:
        - Hard delete ensures no recovery
        - Ownership verified before deletion
        """
        api_key = db.query(UserAPIKey).filter(
            UserAPIKey.id == key_id,
            UserAPIKey.user_id == user_id
        ).first()
        
        if not api_key:
            logger.warning(f"API key not found: {key_id} for user {user_id}")
            return False
        
        # Hard delete (not soft delete) for security
        db.delete(api_key)
        db.commit()
        
        logger.info(f"API key deleted: {key_id} for user {user_id}")
        
        return True
    
    def rotate_all_keys(self, db: Session) -> dict:
        """
        Rotate encryption for all API keys.
        
        Used when KMS key is rotated. Re-encrypts all keys with new key version.
        
        Process:
        1. Fetch all active keys
        2. For each key:
           - Decrypt with old key version
           - Re-encrypt with new key version
           - Update database
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with rotation statistics:
            - total: Total keys processed
            - success: Successfully rotated
            - failed: Failed rotations
            
        Security:
        - Atomic per-key (rollback on failure)
        - Plaintext keys wiped from memory
        """
        keys = db.query(UserAPIKey).filter(UserAPIKey.is_active == True).all()
        
        total = len(keys)
        success = 0
        failed = 0
        
        for key in keys:
            try:
                new_encrypted_key, new_encrypted_dek, new_nonce = \
                    self.encryption.rotate_encryption(
                        key.encrypted_key,
                        key.encrypted_dek,
                        key.nonce
                    )
                
                key.encrypted_key = new_encrypted_key
                key.encrypted_dek = new_encrypted_dek
                key.nonce = new_nonce
                key.kms_key_version = getattr(self.encryption, 'kms_key_name', 'local-encryption')
                
                db.commit()
                success += 1
                logger.info(f"Rotated encryption for key {key.id}")
                
            except Exception as e:
                logger.error(f"Failed to rotate key {key.id}: {e}")
                db.rollback()
                failed += 1
        
        logger.info(f"Key rotation complete: {success}/{total} successful, {failed} failed")
        
        return {
            "total": total,
            "success": success,
            "failed": failed
        }
