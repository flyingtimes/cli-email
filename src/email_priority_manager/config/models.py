"""
Configuration models for Email Priority Manager.

Pydantic models for type-safe configuration management with validation
and environment variable support.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator, SecretStr
from pydantic.env_settings import BaseSettings
import os


class EmailConfig(BaseModel):
    """Configuration for email server settings."""

    server: str = Field(..., description="SMTP server hostname or IP address")
    port: int = Field(default=587, description="SMTP server port")
    username: str = Field(..., description="Email account username")
    password: SecretStr = Field(..., description="Email account password or auth token")
    use_ssl: bool = Field(default=True, description="Use SSL for connection")
    use_tls: bool = Field(default=True, description="Use TLS for connection")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum connection retries")

    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1:
            raise ValueError('Timeout must be positive')
        return v


class DatabaseConfig(BaseModel):
    """Configuration for database settings."""

    path: str = Field(default="email_priority.db", description="Database file path")
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_interval: int = Field(default=86400, description="Backup interval in seconds")
    backup_count: int = Field(default=7, description="Number of backups to keep")
    echo: bool = Field(default=False, description="Enable SQL echo for debugging")
    pool_size: int = Field(default=5, description="Database connection pool size")
    max_overflow: int = Field(default=10, description="Maximum connection pool overflow")

    @validator('backup_interval')
    def validate_backup_interval(cls, v):
        if v < 3600:  # Minimum 1 hour
            raise ValueError('Backup interval must be at least 3600 seconds (1 hour)')
        return v

    @validator('backup_count')
    def validate_backup_count(cls, v):
        if not 1 <= v <= 30:
            raise ValueError('Backup count must be between 1 and 30')
        return v


class AIConfig(BaseModel):
    """Configuration for AI services."""

    api_key: SecretStr = Field(..., description="BigModel.cn API key")
    model: str = Field(default="text-davinci-003", description="AI model to use")
    max_tokens: int = Field(default=1000, description="Maximum tokens for AI responses")
    temperature: float = Field(default=0.7, description="AI response temperature (0.0-1.0)")
    timeout: int = Field(default=30, description="AI API timeout in seconds")
    base_url: Optional[str] = Field(default=None, description="Custom API base URL")

    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Temperature must be between 0.0 and 1.0')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if not 1 <= v <= 4000:
            raise ValueError('Max tokens must be between 1 and 4000')
        return v


class ProcessingConfig(BaseModel):
    """Configuration for email processing settings."""

    batch_size: int = Field(default=10, description="Number of emails to process in batch")
    max_email_size: int = Field(default=1024 * 1024 * 10, description="Maximum email size in bytes")
    allowed_file_types: List[str] = Field(
        default=["pdf", "doc", "docx", "txt", "rtf"],
        description="Allowed attachment file types"
    )
    scan_interval: int = Field(default=300, description="Email scan interval in seconds")
    priority_threshold: float = Field(default=0.5, description="Priority classification threshold")

    @validator('batch_size')
    def validate_batch_size(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('Batch size must be between 1 and 100')
        return v

    @validator('max_email_size')
    def validate_max_email_size(cls, v):
        if v < 1024:  # Minimum 1KB
            raise ValueError('Max email size must be at least 1024 bytes')
        return v

    @validator('scan_interval')
    def validate_scan_interval(cls, v):
        if v < 60:  # Minimum 1 minute
            raise ValueError('Scan interval must be at least 60 seconds')
        return v

    @validator('priority_threshold')
    def validate_priority_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Priority threshold must be between 0.0 and 1.0')
        return v


class LoggingConfig(BaseModel):
    """Configuration for logging settings."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, description="Number of log backups to keep")

    @validator('level')
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()

    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        if v < 1024:  # Minimum 1KB
            raise ValueError('Max file size must be at least 1024 bytes')
        return v


class AppConfig(BaseSettings):
    """Main application configuration."""

    # Basic settings
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Application environment")

    # Component configurations
    email: EmailConfig
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Paths
    data_dir: str = Field(default="./data", description="Data directory path")
    log_dir: str = Field(default="./logs", description="Log directory path")
    temp_dir: str = Field(default="./temp", description="Temporary directory path")

    class Config:
        env_prefix = "EPM_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @property
        def env_nested_delimiter(self):
            return "__"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.data_dir,
            self.log_dir,
            self.temp_dir,
            os.path.dirname(self.database.path),
        ]

        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f'Environment must be one of {valid_environments}')
        return v.lower()

    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        return f"sqlite:///{self.database.path}"

    def get_log_file_path(self) -> Optional[str]:
        """Get full log file path."""
        if self.logging.file_path:
            return os.path.join(self.log_dir, self.logging.file_path)
        return None

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


class DatabaseSettings(BaseSettings):
    """Database-specific settings that can be loaded from environment."""

    url: str = Field(default="sqlite:///email_priority.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQL echo")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum pool overflow")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")

    class Config:
        env_prefix = "EPM_DB_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class EmailSettings(BaseSettings):
    """Email-specific settings that can be loaded from environment."""

    server: str = Field(..., description="SMTP server")
    port: int = Field(default=587, description="SMTP port")
    username: str = Field(..., description="Email username")
    password: SecretStr = Field(..., description="Email password")
    use_ssl: bool = Field(default=True, description="Use SSL")
    use_tls: bool = Field(default=True, description="Use TLS")
    timeout: int = Field(default=30, description="Connection timeout")

    class Config:
        env_prefix = "EPM_EMAIL_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class AISettings(BaseSettings):
    """AI service settings that can be loaded from environment."""

    api_key: SecretStr = Field(..., description="AI API key")
    model: str = Field(default="text-davinci-003", description="AI model")
    max_tokens: int = Field(default=1000, description="Max tokens")
    temperature: float = Field(default=0.7, description="Temperature")
    timeout: int = Field(default=30, description="API timeout")
    base_url: Optional[str] = Field(default=None, description="Base URL")

    class Config:
        env_prefix = "EPM_AI_"
        env_file = ".env"
        env_file_encoding = "utf-8"