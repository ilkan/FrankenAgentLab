"""Environment configuration module for FrankenAgent Lab.

This module provides environment-specific configuration management following the KISS principle.
It detects the current environment (development or production) and loads appropriate configuration
from environment-specific .env files.

Key Design Principles:
1. Single Source of Truth: ENVIRONMENT variable determines all configuration
2. Fail Fast: Invalid configuration causes immediate startup failure with clear errors
3. Explicit Over Implicit: No magic defaults, all configuration must be explicit
4. Security by Default: Production requires stricter validation and secure connections
5. Developer Experience: Development setup should be simple and work out of the box
"""

import os
import logging
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types for FrankenAgent Lab."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration for FrankenAgent Lab.
    
    This class encapsulates all configuration needed for the application,
    with environment-specific defaults and validation rules.
    
    Attributes:
        environment: Current environment (development, production, test)
        database_url: Database connection string
        frontend_url: Frontend application URL
        backend_url: Backend API URL
        oauth_redirect_uri: OAuth callback URL
        ssl_verify: Whether to verify SSL certificates
        openai_api_key: OpenAI API key (optional)
        anthropic_api_key: Anthropic API key (optional)
        google_client_id: Google OAuth client ID (optional)
        google_client_secret: Google OAuth client secret (optional)
        github_client_id: GitHub OAuth client ID (optional)
        github_client_secret: GitHub OAuth client secret (optional)
        local_database_url: Optional connection string for local development
        production_database_url: Optional connection string for production
        cloud_sql_instance: Optional Cloud SQL instance connection name
        db_user: Database user for Cloud SQL
        db_password: Database password for Cloud SQL
        db_name: Database name (defaults to frankenagent)
        gcp_project_id: Google Cloud project id
        jwt_secret_key: JWT secret for token signing
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        agno_debug: Enable Agno framework debug mode
    """
    
    environment: Environment
    database_url: str
    frontend_url: str
    backend_url: str
    oauth_redirect_uri: str
    ssl_verify: bool
    
    # LLM Provider Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # OAuth Credentials
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    
    # Database configuration
    local_database_url: Optional[str] = None
    production_database_url: Optional[str] = None
    cloud_sql_instance: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_name: str = "frankenagent"
    gcp_project_id: Optional[str] = None
    
    # JWT
    jwt_secret_key: str = "dev-secret-key-change-me"
    
    # Logging
    log_level: str = "INFO"
    agno_debug: bool = False
    
    @classmethod
    def load(cls) -> "EnvironmentConfig":
        """Load configuration for current environment.
        
        This method:
        1. Detects the environment from ENVIRONMENT variable
        2. Loads the appropriate .env file (.env.development or .env.production)
        3. Falls back to .env if environment-specific file doesn't exist
        4. Creates and returns an EnvironmentConfig instance
        
        Returns:
            EnvironmentConfig: Loaded and validated configuration
            
        Raises:
            ValueError: If environment is invalid or configuration is missing
        """
        # Detect environment
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        
        try:
            environment = Environment(env_str)
        except ValueError:
            raise ValueError(
                f"Invalid ENVIRONMENT value: '{env_str}'. "
                f"Must be one of: {', '.join([e.value for e in Environment])}"
            )
        
        # Load environment-specific .env file
        env_file = cls._get_env_file(environment)
        if env_file.exists():
            logger.info(f"Loading configuration from {env_file}")
            load_dotenv(env_file, override=True)
        else:
            # Fall back to base .env file
            base_env = Path(".env")
            if base_env.exists():
                logger.warning(
                    f"Environment-specific file {env_file} not found. "
                    f"Loading from {base_env}"
                )
                load_dotenv(base_env, override=True)
            else:
                logger.warning("No .env file found. Using environment variables only.")
        
        # Determine base database URL depending on environment.
        # Development/test default to LOCAL_DATABASE_URL or local sqlite.
        # Production expects explicit PRODUCTION_DATABASE_URL or Cloud SQL.
        database_url = os.getenv("DATABASE_URL", "")
        local_database_url = os.getenv("LOCAL_DATABASE_URL")
        production_database_url = os.getenv("PRODUCTION_DATABASE_URL")
        cloud_sql_instance = os.getenv("CLOUD_SQL_CONNECTION_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME", "frankenagent")
        
        if not database_url:
            if environment in (Environment.DEVELOPMENT, Environment.TEST):
                database_url = local_database_url or "sqlite:///./frankenagent.db"
            else:
                if production_database_url:
                    database_url = production_database_url
                elif cloud_sql_instance and db_user and db_password:
                    database_url = (
                        f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}"
                        f"?host=/cloudsql/{cloud_sql_instance}"
                    )
                else:
                    database_url = ""
        
        # Create configuration instance
        config = cls(
            environment=environment,
            database_url=database_url,
            frontend_url=os.getenv("FRONTEND_URL", ""),
            backend_url=os.getenv("BACKEND_URL", ""),
            oauth_redirect_uri=os.getenv("OAUTH_REDIRECT_URI", ""),
            ssl_verify=cls._get_ssl_verify(environment),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            github_client_id=os.getenv("GITHUB_CLIENT_ID"),
            github_client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            local_database_url=local_database_url,
            production_database_url=production_database_url,
            cloud_sql_instance=cloud_sql_instance,
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
            gcp_project_id=os.getenv("GCP_PROJECT_ID"),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            agno_debug=os.getenv("AGNO_DEBUG", "false").lower() == "true",
        )
        
        return config
    
    @staticmethod
    def _get_env_file(environment: Environment) -> Path:
        """Get the path to the environment-specific .env file.
        
        Args:
            environment: The environment to get the file for
            
        Returns:
            Path: Path to the environment-specific .env file
        """
        if environment == Environment.DEVELOPMENT:
            return Path(".env.development")
        elif environment == Environment.PRODUCTION:
            return Path(".env.production")
        elif environment == Environment.TEST:
            return Path(".env.test")
        else:
            return Path(".env")
    
    @staticmethod
    def _get_ssl_verify(environment: Environment) -> bool:
        """Determine SSL verification setting based on environment.
        
        Args:
            environment: The current environment
            
        Returns:
            bool: True if SSL should be verified, False otherwise
        """
        # Allow override via environment variable
        ssl_verify_env = os.getenv("SSL_VERIFY")
        if ssl_verify_env is not None:
            return ssl_verify_env.lower() in ("true", "1", "yes")
        
        # Default: disabled in development/test, enabled in production
        if environment in (Environment.DEVELOPMENT, Environment.TEST):
            logger.warning(
                "SSL verification is DISABLED in development/test environment. "
                "This is normal for local development but should NEVER be used in production."
            )
            return False
        else:
            return True
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors.
        
        This method checks that all required configuration is present and valid
        for the current environment. It enforces stricter validation in production.
        
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []
        
        # Always required
        if not self.database_url:
            errors.append(
                "Database connection is not configured. "
                "Set LOCAL_DATABASE_URL for development or PRODUCTION_DATABASE_URL / "
                "Cloud SQL environment variables (CLOUD_SQL_CONNECTION_NAME, DB_USER, DB_PASSWORD) "
                "for production."
            )
        
        if not self.frontend_url:
            errors.append(
                "FRONTEND_URL is required. "
                f"Example: http://localhost:3000 (development) or "
                f"https://yourdomain.com (production)"
            )
        
        if not self.backend_url:
            errors.append(
                "BACKEND_URL is required. "
                f"Example: http://localhost:8000 (development) or "
                f"https://api.yourdomain.com (production)"
            )
        
        if not self.oauth_redirect_uri:
            errors.append(
                "OAUTH_REDIRECT_URI is required. "
                f"Example: http://localhost:8000/api/auth/callback (development) or "
                f"https://yourdomain.com/api/auth/callback (production)"
            )
        
        # Production-specific validation
        if self.environment == Environment.PRODUCTION:
            errors.extend(self._validate_production())
        
        # Development-specific warnings (not errors)
        if self.environment == Environment.DEVELOPMENT:
            self._warn_development()
        
        return errors
    
    def _validate_production(self) -> List[str]:
        """Validate production-specific requirements.
        
        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        
        # Database requirements
        if not self.database_url:
            errors.append(
                "Production database is not configured. "
                "Set PRODUCTION_DATABASE_URL or configure Cloud SQL via "
                "CLOUD_SQL_CONNECTION_NAME, DB_USER, DB_PASSWORD, and DB_NAME."
            )
        elif "cloudsql" in (self.database_url or "") and not self.cloud_sql_instance:
            errors.append(
                "CLOUD_SQL_CONNECTION_NAME must be set when using Cloud SQL unix sockets."
            )
        
        # JWT secret must not be default
        if self.jwt_secret_key == "dev-secret-key-change-me":
            errors.append(
                "JWT_SECRET_KEY must be changed from default value in production. "
                "Generate a secure random key."
            )
        
        # HTTPS required in production
        if self.frontend_url and not self.frontend_url.startswith("https://"):
            errors.append(
                f"FRONTEND_URL must use HTTPS in production. Got: {self.frontend_url}"
            )
        
        if self.backend_url and not self.backend_url.startswith("https://"):
            errors.append(
                f"BACKEND_URL must use HTTPS in production. Got: {self.backend_url}"
            )
        
        if self.oauth_redirect_uri and not self.oauth_redirect_uri.startswith("https://"):
            errors.append(
                f"OAUTH_REDIRECT_URI must use HTTPS in production. Got: {self.oauth_redirect_uri}"
            )
        
        # SSL verification must be enabled
        if not self.ssl_verify:
            errors.append(
                "SSL verification must be enabled in production. "
                "Remove SSL_VERIFY=false from environment."
            )
        
        return errors
    
    def _warn_development(self) -> None:
        """Log warnings for development environment configuration."""
        if not self.openai_api_key and not self.anthropic_api_key:
            logger.warning(
                "No LLM API keys configured (OPENAI_API_KEY, ANTHROPIC_API_KEY). "
                "Agent execution will fail until keys are provided. "
                "Get keys at: https://platform.openai.com/api-keys or "
                "https://console.anthropic.com/"
            )
        
        if not self.google_client_id or not self.google_client_secret:
            logger.warning(
                "Google OAuth not configured (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET). "
                "Google authentication will not work. "
                "Configure at: https://console.cloud.google.com/apis/credentials"
            )
        
        if not self.github_client_id or not self.github_client_secret:
            logger.warning(
                "GitHub OAuth not configured (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET). "
                "GitHub authentication will not work. "
                "Configure at: https://github.com/settings/developers"
            )
    
    def fail_fast_if_invalid(self) -> None:
        """Validate configuration and raise exception if invalid.
        
        This method should be called during application startup to ensure
        configuration is valid before proceeding.
        
        Raises:
            ValueError: If configuration is invalid
        """
        errors = self.validate()
        if errors:
            error_msg = self._format_validation_errors(errors)
            raise ValueError(error_msg)
    
    def _format_validation_errors(self, errors: List[str]) -> str:
        """Format validation errors into a user-friendly message.
        
        Args:
            errors: List of error messages
            
        Returns:
            str: Formatted error message
        """
        if self.environment == Environment.DEVELOPMENT:
            # Detailed error message for development
            msg = [
                "\n" + "=" * 80,
                "❌ CONFIGURATION ERROR",
                "=" * 80,
                "",
                f"Environment: {self.environment.value}",
                "",
                "The following configuration errors were found:",
                ""
            ]
            
            for i, error in enumerate(errors, 1):
                msg.append(f"{i}. {error}")
            
            msg.extend([
                "",
                "To fix this:",
                "1. Copy .env.example to .env.development",
                "2. Fill in the required values",
                "3. Restart the server",
                "",
                "=" * 80,
                ""
            ])
            
            return "\n".join(msg)
        else:
            # Concise error message for production
            msg = [
                "\n" + "=" * 80,
                "❌ CONFIGURATION VALIDATION FAILED",
                "=" * 80,
                "",
                f"Environment: {self.environment.value}",
                "",
                "Missing or invalid configuration:",
            ]
            
            for error in errors:
                msg.append(f"  - {error}")
            
            msg.extend([
                "",
                "Please check your environment configuration.",
                "=" * 80,
                ""
            ])
            
            return "\n".join(msg)
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == Environment.TEST


# Global configuration instance (loaded on first import)
_config: Optional[EnvironmentConfig] = None


def get_config() -> EnvironmentConfig:
    """Get the global configuration instance.
    
    This function loads the configuration on first call and caches it.
    Subsequent calls return the cached instance.
    
    Returns:
        EnvironmentConfig: The global configuration instance
    """
    global _config
    if _config is None:
        _config = EnvironmentConfig.load()
    return _config


def reload_config() -> EnvironmentConfig:
    """Reload configuration from environment.
    
    This function forces a reload of the configuration, useful for testing
    or when environment variables have changed.
    
    Returns:
        EnvironmentConfig: The newly loaded configuration instance
    """
    global _config
    _config = EnvironmentConfig.load()
    return _config
