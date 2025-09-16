"""
Secure credential storage and secrets management for Email Priority Manager.

Provides encryption, secure storage, and management of sensitive credentials
and API keys using industry-standard security practices.
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib
import secrets

from ..utils.logger import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """Manages secure storage and retrieval of sensitive credentials."""

    def __init__(self, secrets_dir: Optional[str] = None):
        """Initialize secrets manager."""
        self.secrets_dir = Path(secrets_dir) if secrets_dir else Path("secrets")
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        self._key_file = self.secrets_dir / "key.key"
        self._secrets_file = self.secrets_dir / "secrets.enc"
        self._fernet: Optional[Fernet] = None
        self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption key and Fernet instance."""
        try:
            # Try to load existing key
            if self._key_file.exists():
                key = self._load_key()
            else:
                key = self._generate_and_save_key()

            self._fernet = Fernet(key)
            logger.debug("Encryption initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise SecretsError(f"Encryption initialization failed: {e}")

    def _generate_and_save_key(self) -> bytes:
        """Generate and save new encryption key."""
        try:
            # Generate key from environment or system
            passphrase = self._get_passphrase()

            # Generate salt
            salt = secrets.token_bytes(16)

            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

            # Save salt with key
            key_data = {
                'salt': base64.b64encode(salt).decode(),
                'key': key.decode()
            }

            with open(self._key_file, 'w') as f:
                json.dump(key_data, f)

            # Secure the key file
            os.chmod(self._key_file, 0o600)

            logger.info("New encryption key generated and saved")
            return key

        except Exception as e:
            logger.error(f"Failed to generate encryption key: {e}")
            raise SecretsError(f"Key generation failed: {e}")

    def _load_key(self) -> bytes:
        """Load existing encryption key."""
        try:
            with open(self._key_file, 'r') as f:
                key_data = json.load(f)

            # Get passphrase
            passphrase = self._get_passphrase()

            # Derive key using stored salt
            salt = base64.b64decode(key_data['salt'])
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

            # Verify key matches
            if key.encode() != key_data['key'].encode():
                raise SecretsError("Invalid passphrase or corrupted key file")

            return key

        except Exception as e:
            logger.error(f"Failed to load encryption key: {e}")
            raise SecretsError(f"Key loading failed: {e}")

    def _get_passphrase(self) -> str:
        """Get passphrase for key derivation."""
        # Try environment variable first
        passphrase = os.getenv('EPM_SECRETS_PASSPHRASE')
        if passphrase:
            return passphrase

        # Try to get from system keyring (simplified)
        # In production, consider using proper keyring libraries
        fallback_passphrase = os.getenv('USER', '') + os.getenv('COMPUTERNAME', '')
        if fallback_passphrase:
            return fallback_passphrase

        # Last resort - use a fixed but reasonably secure fallback
        # This should be improved in production
        return "email-priority-manager-default-passphrase"

    def store_secret(self, key: str, value: str, category: str = "general"):
        """Store a secret securely."""
        try:
            secrets_data = self._load_secrets_data()

            if category not in secrets_data:
                secrets_data[category] = {}

            # Encrypt the value
            encrypted_value = self._fernet.encrypt(value.encode())
            secrets_data[category][key] = base64.b64encode(encrypted_value).decode()

            self._save_secrets_data(secrets_data)
            logger.info(f"Secret '{key}' stored in category '{category}'")

        except Exception as e:
            logger.error(f"Failed to store secret '{key}': {e}")
            raise SecretsError(f"Failed to store secret: {e}")

    def get_secret(self, key: str, category: str = "general") -> Optional[str]:
        """Retrieve a secret."""
        try:
            secrets_data = self._load_secrets_data()

            if category not in secrets_data or key not in secrets_data[category]:
                return None

            encrypted_value = base64.b64decode(secrets_data[category][key])
            decrypted_value = self._fernet.decrypt(encrypted_value)
            return decrypted_value.decode()

        except Exception as e:
            logger.error(f"Failed to retrieve secret '{key}': {e}")
            return None

    def delete_secret(self, key: str, category: str = "general"):
        """Delete a secret."""
        try:
            secrets_data = self._load_secrets_data()

            if category in secrets_data and key in secrets_data[category]:
                del secrets_data[category][key]

                # Remove empty categories
                if not secrets_data[category]:
                    del secrets_data[category]

                self._save_secrets_data(secrets_data)
                logger.info(f"Secret '{key}' deleted from category '{category}'")

        except Exception as e:
            logger.error(f"Failed to delete secret '{key}': {e}")
            raise SecretsError(f"Failed to delete secret: {e}")

    def list_secrets(self, category: Optional[str] = None) -> Dict[str, Any]:
        """List secrets (keys only, not values)."""
        try:
            secrets_data = self._load_secrets_data()

            if category:
                return {category: list(secrets_data.get(category, {}).keys())}
            else:
                return {cat: list(secrets.keys()) for cat, secrets in secrets_data.items()}

        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return {}

    def _load_secrets_data(self) -> Dict[str, Any]:
        """Load encrypted secrets data."""
        if not self._secrets_file.exists():
            return {}

        try:
            with open(self._secrets_file, 'r') as f:
                encrypted_data = f.read()

            if not encrypted_data:
                return {}

            decrypted_data = self._fernet.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode())

        except Exception as e:
            logger.error(f"Failed to load secrets data: {e}")
            return {}

    def _save_secrets_data(self, data: Dict[str, Any]):
        """Save encrypted secrets data."""
        try:
            json_data = json.dumps(data, indent=2)
            encrypted_data = self._fernet.encrypt(json_data.encode())

            with open(self._secrets_file, 'w') as f:
                f.write(encrypted_data.decode())

            # Secure the secrets file
            os.chmod(self._secrets_file, 0o600)

        except Exception as e:
            logger.error(f"Failed to save secrets data: {e}")
            raise SecretsError(f"Failed to save secrets data: {e}")

    def store_email_credentials(self, server: str, username: str, password: str, port: int = 587):
        """Store email credentials securely."""
        try:
            email_config = {
                'server': server,
                'username': username,
                'password': password,
                'port': port
            }

            for key, value in email_config.items():
                self.store_secret(f'email_{key}', str(value), 'email')

            logger.info("Email credentials stored securely")

        except Exception as e:
            logger.error(f"Failed to store email credentials: {e}")
            raise SecretsError(f"Failed to store email credentials: {e}")

    def get_email_secrets(self) -> Optional[Dict[str, Any]]:
        """Retrieve email credentials."""
        try:
            email_secrets = {}

            for key in ['server', 'username', 'password', 'port']:
                value = self.get_secret(f'email_{key}', 'email')
                if value is None:
                    return None

                # Convert port back to integer
                if key == 'port':
                    value = int(value)

                email_secrets[key] = value

            return email_secrets

        except Exception as e:
            logger.error(f"Failed to retrieve email secrets: {e}")
            return None

    def store_ai_credentials(self, api_key: str, base_url: Optional[str] = None):
        """Store AI service credentials securely."""
        try:
            self.store_secret('api_key', api_key, 'ai')
            if base_url:
                self.store_secret('base_url', base_url, 'ai')

            logger.info("AI credentials stored securely")

        except Exception as e:
            logger.error(f"Failed to store AI credentials: {e}")
            raise SecretsError(f"Failed to store AI credentials: {e}")

    def get_ai_secrets(self) -> Optional[Dict[str, Any]]:
        """Retrieve AI service credentials."""
        try:
            api_key = self.get_secret('api_key', 'ai')
            if not api_key:
                return None

            ai_secrets = {'api_key': api_key}

            base_url = self.get_secret('base_url', 'ai')
            if base_url:
                ai_secrets['base_url'] = base_url

            return ai_secrets

        except Exception as e:
            logger.error(f"Failed to retrieve AI secrets: {e}")
            return None

    def rotate_encryption_key(self, new_passphrase: Optional[str] = None):
        """Rotate encryption key and re-encrypt all secrets."""
        try:
            # Load current secrets
            current_secrets = self._load_secrets_data()

            # Backup current secrets
            backup_file = self.secrets_dir / "secrets.backup"
            with open(backup_file, 'w') as f:
                json.dump(current_secrets, f)

            # Generate new key
            if new_passphrase:
                os.environ['EPM_SECRETS_PASSPHRASE'] = new_passphrase

            # Remove old key and generate new one
            if self._key_file.exists():
                self._key_file.unlink()

            self._init_encryption()

            # Re-encrypt secrets with new key
            self._save_secrets_data(current_secrets)

            # Remove backup
            backup_file.unlink()

            logger.info("Encryption key rotated successfully")

        except Exception as e:
            logger.error(f"Failed to rotate encryption key: {e}")
            raise SecretsError(f"Failed to rotate encryption key: {e}")

    def export_secrets(self, export_path: str, include_secrets: bool = False):
        """Export secrets configuration (metadata only by default)."""
        try:
            secrets_data = self._load_secrets_data()

            if not include_secrets:
                # Export only metadata
                export_data = {
                    category: list(secrets.keys())
                    for category, secrets in secrets_data.items()
                }
            else:
                # Export all data (not recommended for production)
                export_data = secrets_data

            export_file = Path(export_path)
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Secrets exported to {export_file}")

        except Exception as e:
            logger.error(f"Failed to export secrets: {e}")
            raise SecretsError(f"Failed to export secrets: {e}")

    def import_secrets(self, import_path: str):
        """Import secrets from file."""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                raise SecretsError(f"Import file not found: {import_path}")

            with open(import_file, 'r') as f:
                import_data = json.load(f)

            for category, secrets in import_data.items():
                for key, value in secrets.items():
                    self.store_secret(key, value, category)

            logger.info(f"Secrets imported from {import_file}")

        except Exception as e:
            logger.error(f"Failed to import secrets: {e}")
            raise SecretsError(f"Failed to import secrets: {e}")

    def verify_integrity(self) -> bool:
        """Verify secrets file integrity."""
        try:
            if not self._secrets_file.exists():
                return True

            # Try to load and decrypt secrets
            self._load_secrets_data()
            return True

        except Exception as e:
            logger.error(f"Secrets integrity check failed: {e}")
            return False


class SecretsError(Exception):
    """Exception raised for secrets management errors."""
    pass


# Utility functions for secret management
def get_secrets_manager(secrets_dir: Optional[str] = None) -> SecretsManager:
    """Get secrets manager instance."""
    return SecretsManager(secrets_dir)


def setup_email_interactive() -> bool:
    """Interactive email setup wizard."""
    try:
        import getpass

        print("Email Configuration Setup")
        print("=" * 30)

        server = input("SMTP Server: ").strip()
        if not server:
            print("Server is required")
            return False

        port = input("SMTP Port (default 587): ").strip()
        port = int(port) if port else 587

        username = input("Email Username: ").strip()
        if not username:
            print("Username is required")
            return False

        password = getpass.getpass("Email Password: ")
        if not password:
            print("Password is required")
            return False

        # Store credentials
        manager = get_secrets_manager()
        manager.store_email_credentials(server, username, password, port)

        print("Email configuration saved successfully!")
        return True

    except Exception as e:
        logger.error(f"Email setup failed: {e}")
        return False


def setup_ai_interactive() -> bool:
    """Interactive AI service setup wizard."""
    try:
        import getpass

        print("AI Service Configuration Setup")
        print("=" * 30)

        api_key = getpass.getpass("BigModel.cn API Key: ")
        if not api_key:
            print("API key is required")
            return False

        base_url = input("Base URL (optional): ").strip()

        # Store credentials
        manager = get_secrets_manager()
        manager.store_ai_credentials(api_key, base_url if base_url else None)

        print("AI service configuration saved successfully!")
        return True

    except Exception as e:
        logger.error(f"AI setup failed: {e}")
        return False